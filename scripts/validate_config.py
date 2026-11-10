#!/usr/bin/env python3
"""Validate the configuration artifacts this repository ships.

Standard library only, so the gate runs with whatever python3 the runner already
has. One check per shipped artifact, and every failure names the file and field:

- every tracked ``*.json`` parses, because a broken renovate.json or ruleset is
  rejected by a consumer far away from the edit;
- ``.github/repo-settings.json`` keeps the shape of ``schema_version: 1``: the
  five keys this repo uses, typed, with GitHub-legal topic names;
- ``.github/rulesets/main.json`` keeps the shape the rulesets API accepts:
  documented enums, no duplicate rule type, and only the parameter keys of the
  rule types this repo enables — the API rejects the whole file otherwise;
- ``.skret.yaml`` keeps the shape skret reads: a version, a ``default_env`` that
  exists under ``environments:``, and a ``path`` per environment. PyYAML is not
  a dependency of this repo (and ``yaml`` is not in the standard library), so
  the file is read by a small scalar reader that fails on anything it cannot
  classify instead of guessing what a real parser would have concluded;
- issue templates keep readable front matter (``name`` and ``about`` present,
  known keys only); GitHub silently drops a template whose front matter it
  cannot parse, which is invisible until someone tries to open the issue.

Usage, from the repository root::

    python3 scripts/validate_config.py [--root DIR]

Exit code 0 means every check passed; 1 means at least one FAIL line was printed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

IGNORED_DIRS = frozenset({".git", "node_modules", ".venv", "__pycache__", "dist", "build"})

TOPIC = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")
OWNER_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
HTTP_URL = re.compile(r"^https?://\S+$")

REPO_SETTINGS_KEYS = frozenset({"schema_version", "tier", "description", "homepage", "topics"})
REPO_SETTINGS_SCHEMA = 1
TIERS = frozenset({1, 2, 3})

RULESET_KEYS = frozenset({
    "name", "target", "source_type", "source", "enforcement",
    "bypass_actors", "conditions", "rules",
})
RULESET_TARGETS = frozenset({"branch", "tag"})
RULESET_SOURCES = frozenset({"Repository", "Organization"})
ENFORCEMENTS = frozenset({"active", "disabled", "evaluate"})
BYPASS_KEYS = frozenset({"actor_id", "actor_type", "bypass_mode"})
ACTOR_TYPES = frozenset({"RepositoryRole", "Team", "Integration", "OrganizationAdmin"})
BYPASS_MODES = frozenset({"always", "pull_request"})
CONDITION_KEYS = frozenset({"ref_name"})
REF_NAME_KEYS = frozenset({"include", "exclude"})
RULE_TYPES = frozenset({
    "branch_name_pattern", "code_scanning", "commit_author_email_pattern",
    "commit_message_pattern", "committer_email_pattern", "copilot_code_review",
    "creation", "deletion", "merge_queue", "non_fast_forward", "pull_request",
    "required_deployments", "required_linear_history", "required_signatures",
    "required_status_checks", "tag_name_pattern", "update", "workflows",
})
MERGE_METHODS = frozenset({"merge", "squash", "rebase"})
# rule type -> {parameter: kind}, kinds resolved in _rule_parameters().
RULE_PARAMETERS: dict[str, dict[str, str]] = {
    "pull_request": {
        "allowed_merge_methods": "merge_methods",
        "dismiss_stale_reviews_on_push": "bool",
        "require_code_owner_review": "bool",
        "require_extra_approval_for_unattributed_changes": "bool",
        "require_last_push_approval": "bool",
        "required_approving_review_count": "count",
        "required_review_thread_resolution": "bool",
    },
    "code_scanning": {
        "code_scanning_tools": "scanning_tools",
    },
}

TEMPLATE_KEYS = frozenset({"name", "about", "title", "labels", "assignees", "projects"})
TEMPLATE_REQUIRED = ("name", "about")

SKRET_ENV_KEYS = ("provider", "region", "path")


def rel(path: Path, root: Path) -> str:
    """Path as it is committed, for messages that match ``git ls-files`` output."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def tracked(root: Path, pattern: str) -> list[Path]:
    """Tracked files matching `pattern`, falling back to a walk outside a checkout."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", pattern],
            capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        proc = None
    if proc is not None:
        names = [n for n in proc.stdout.decode("utf-8", "replace").split("\0") if n]
        if names:
            return [root / n for n in names]
    found = []
    for path in root.rglob(pattern):
        parts = path.relative_to(root).parts[:-1]
        if not IGNORED_DIRS.intersection(parts):
            found.append(path)
    return sorted(found)


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


# --- JSON -------------------------------------------------------------------

def check_json(path: Path, root: Path, failures: list[str]) -> None:
    name = rel(path, root)
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.append(f"FAIL {name}: starts with a UTF-8 BOM")
        return
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        failures.append(f"FAIL {name}: not UTF-8 ({exc})")
        return
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        failures.append(f"FAIL {name}:{exc.lineno}:{exc.colno}: {exc.msg}")
        return
    print(f"ok   {name}: parses")


def check_repo_settings(path: Path, root: Path, failures: list[str]) -> None:
    name = rel(path, root)
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        failures.append(f"FAIL {name}: top level is {type(doc).__name__}, expected object")
        return
    before = len(failures)
    unknown = sorted(set(doc) - REPO_SETTINGS_KEYS)
    if unknown:
        failures.append(f"FAIL {name}: unknown key(s) {', '.join(unknown)}")
    missing = sorted(REPO_SETTINGS_KEYS - set(doc))
    if missing:
        failures.append(f"FAIL {name}: missing key(s) {', '.join(missing)}")
    schema = doc.get("schema_version")
    if not is_int(schema) or schema != REPO_SETTINGS_SCHEMA:
        failures.append(f"FAIL {name}: schema_version is {schema!r}, this checker knows {REPO_SETTINGS_SCHEMA}")
    tier = doc.get("tier")
    if not is_int(tier) or tier not in TIERS:
        failures.append(f"FAIL {name}: tier is {tier!r}, expected one of {sorted(TIERS)}")
    description = doc.get("description")
    if not isinstance(description, str) or not description.strip():
        failures.append(f"FAIL {name}: description must be a non-empty string")
    homepage = doc.get("homepage")
    if not isinstance(homepage, str) or (homepage and not HTTP_URL.match(homepage)):
        failures.append(f"FAIL {name}: homepage is {homepage!r}, expected \"\" or an http(s) URL")
    topics = doc.get("topics")
    if not isinstance(topics, list) or not topics:
        failures.append(f"FAIL {name}: topics must be a non-empty list")
    else:
        for index, topic in enumerate(topics):
            if not isinstance(topic, str) or not TOPIC.match(topic):
                failures.append(f"FAIL {name}: topics[{index}] is {topic!r}, "
                                "expected lowercase letters, digits and hyphens")
        duplicates = sorted({t for t in topics if isinstance(t, str) and topics.count(t) > 1})
        if duplicates:
            failures.append(f"FAIL {name}: duplicate topic(s) {', '.join(duplicates)}")
    if len(failures) == before:
        print(f"ok   {name}: schema_version {REPO_SETTINGS_SCHEMA} contract holds")


def _rule_parameters(index: int, rule: dict, name: str, failures: list[str]) -> None:
    kind = rule["type"]
    params = rule.get("parameters")
    known = RULE_PARAMETERS.get(kind)
    if known is None:
        if params is not None:
            failures.append(f"FAIL {name}: rules[{index}] ({kind}) has parameters this checker "
                            "does not know; add them to validate_config.py")
        return
    if not isinstance(params, dict):
        failures.append(f"FAIL {name}: rules[{index}] ({kind}) needs a parameters object")
        return
    unknown = sorted(set(params) - set(known))
    if unknown:
        failures.append(f"FAIL {name}: rules[{index}] ({kind}) has unknown parameter(s) "
                        f"{', '.join(unknown)}")
    for key, expect in known.items():
        if key not in params:
            failures.append(f"FAIL {name}: rules[{index}] ({kind}) is missing parameter {key}")
            continue
        value = params[key]
        if expect == "bool" and not isinstance(value, bool):
            failures.append(f"FAIL {name}: rules[{index}].parameters.{key} must be true/false")
        elif expect == "count" and (not is_int(value) or value < 0):
            failures.append(f"FAIL {name}: rules[{index}].parameters.{key} must be an integer >= 0")
        elif expect == "merge_methods":
            if not isinstance(value, list) or not value:
                failures.append(f"FAIL {name}: rules[{index}].parameters.{key} must be a non-empty list")
                continue
            bad = [m for m in value if m not in MERGE_METHODS]
            if bad:
                failures.append(f"FAIL {name}: rules[{index}].parameters.{key} has {bad!r}, "
                                f"expected a subset of {sorted(MERGE_METHODS)}")
        elif expect == "scanning_tools":
            if not isinstance(value, list) or not value:
                failures.append(f"FAIL {name}: rules[{index}].parameters.{key} must be a non-empty list")
                continue
            for tool_index, tool in enumerate(value):
                where = f"rules[{index}].parameters.{key}[{tool_index}]"
                if not isinstance(tool, dict):
                    failures.append(f"FAIL {name}: {where} must be an object")
                    continue
                if not isinstance(tool.get("tool"), str) or not tool.get("tool", "").strip():
                    failures.append(f"FAIL {name}: {where}.tool must be a non-empty string")
                for threshold in ("security_alerts_threshold", "alerts_threshold"):
                    if threshold not in tool:
                        continue
                    if not isinstance(tool[threshold], str) or not re.match(r"^[a-z_]+$", tool[threshold]):
                        failures.append(f"FAIL {name}: {where}.{threshold} is {tool[threshold]!r}, "
                                        "expected a lowercase enum token")


def check_ruleset(path: Path, root: Path, failures: list[str]) -> None:
    name = rel(path, root)
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        failures.append(f"FAIL {name}: top level is {type(doc).__name__}, expected object")
        return
    before = len(failures)
    unknown = sorted(set(doc) - RULESET_KEYS)
    if unknown:
        failures.append(f"FAIL {name}: unknown key(s) {', '.join(unknown)}")
    missing = sorted(RULESET_KEYS - set(doc))
    if missing:
        failures.append(f"FAIL {name}: missing key(s) {', '.join(missing)}")
        return  # every check below reads one of them
    if not isinstance(doc["name"], str) or not doc["name"].strip():
        failures.append(f"FAIL {name}: name must be a non-empty string")
    if doc["target"] not in RULESET_TARGETS:
        failures.append(f"FAIL {name}: target is {doc['target']!r}, expected one of {sorted(RULESET_TARGETS)}")
    if doc["source_type"] not in RULESET_SOURCES:
        failures.append(f"FAIL {name}: source_type is {doc['source_type']!r}, "
                        f"expected one of {sorted(RULESET_SOURCES)}")
    source = doc["source"]
    if not isinstance(source, str) or not OWNER_REPO.match(source):
        failures.append(f"FAIL {name}: source is {source!r}, expected owner/repo")
    elif os.environ.get("GITHUB_REPOSITORY") and os.environ["GITHUB_REPOSITORY"] != source:
        failures.append(f"FAIL {name}: source is {source!r} but this run is "
                        f"{os.environ['GITHUB_REPOSITORY']!r}")
    if doc["enforcement"] not in ENFORCEMENTS:
        failures.append(f"FAIL {name}: enforcement is {doc['enforcement']!r}, "
                        f"expected one of {sorted(ENFORCEMENTS)}")

    actors = doc["bypass_actors"]
    if not isinstance(actors, list):
        failures.append(f"FAIL {name}: bypass_actors must be a list")
    else:
        for index, actor in enumerate(actors):
            where = f"bypass_actors[{index}]"
            if not isinstance(actor, dict):
                failures.append(f"FAIL {name}: {where} must be an object")
                continue
            if set(actor) != BYPASS_KEYS:
                failures.append(f"FAIL {name}: {where} keys are {sorted(actor)}, "
                                f"expected {sorted(BYPASS_KEYS)}")
                continue
            if not is_int(actor["actor_id"]):
                failures.append(f"FAIL {name}: {where}.actor_id must be an integer")
            if actor["actor_type"] not in ACTOR_TYPES:
                failures.append(f"FAIL {name}: {where}.actor_type is {actor['actor_type']!r}, "
                                f"expected one of {sorted(ACTOR_TYPES)}")
            if actor["bypass_mode"] not in BYPASS_MODES:
                failures.append(f"FAIL {name}: {where}.bypass_mode is {actor['bypass_mode']!r}, "
                                f"expected one of {sorted(BYPASS_MODES)}")

    conditions = doc["conditions"]
    if not isinstance(conditions, dict):
        failures.append(f"FAIL {name}: conditions must be an object")
    else:
        unknown = sorted(set(conditions) - CONDITION_KEYS)
        if unknown:
            failures.append(f"FAIL {name}: conditions has unknown key(s) {', '.join(unknown)}; "
                            "add them to validate_config.py if the API supports them")
        ref_name = conditions.get("ref_name")
        if not isinstance(ref_name, dict) or set(ref_name) != REF_NAME_KEYS:
            failures.append(f"FAIL {name}: conditions.ref_name keys are "
                            f"{sorted(ref_name) if isinstance(ref_name, dict) else ref_name!r}, "
                            f"expected {sorted(REF_NAME_KEYS)}")
        else:
            for key in sorted(REF_NAME_KEYS):
                value = ref_name[key]
                if not isinstance(value, list) or not all(isinstance(r, str) and r for r in value):
                    failures.append(f"FAIL {name}: conditions.ref_name.{key} must be a list of strings")

    rules = doc["rules"]
    if not isinstance(rules, list) or not rules:
        failures.append(f"FAIL {name}: rules must be a non-empty list")
    else:
        seen: dict[str, int] = {}
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict) or "type" not in rule:
                failures.append(f"FAIL {name}: rules[{index}] must be an object with a type")
                continue
            kind = rule["type"]
            if kind not in RULE_TYPES:
                failures.append(f"FAIL {name}: rules[{index}] type is {kind!r}, "
                                "not one of the rules this checker knows")
                continue
            extra = sorted(set(rule) - {"type", "parameters"})
            if extra:
                failures.append(f"FAIL {name}: rules[{index}] ({kind}) has unknown key(s) "
                                f"{', '.join(extra)}")
            if kind in seen:
                failures.append(f"FAIL {name}: rule type {kind!r} appears at rules[{seen[kind]}] "
                                f"and rules[{index}]; the API allows one rule per type")
            seen[kind] = index
            _rule_parameters(index, rule, name, failures)
    if len(failures) == before:
        print(f"ok   {name}: ruleset shape holds ({len(doc['rules'])} rule(s))")


# --- .skret.yaml ------------------------------------------------------------

class SkretError(Exception):
    """A line the scalar reader cannot classify, with its 1-based number."""

    def __init__(self, line: int, message: str) -> None:
        super().__init__(message)
        self.line = line


def _scalar(raw: str) -> str:
    value = raw.strip()
    if value[:1] in ("'", '"'):
        quote = value[0]
        end = value.find(quote, 1)
        return value[1:end] if end > 0 else value[1:]
    cut = value.find(" #")
    if cut >= 0:
        value = value[:cut].rstrip()
    return value


def read_skret(path: Path) -> dict:
    """Read the subset of YAML skret configs use: scalars under two mapping levels."""
    data: dict = {}
    section = ""
    environment = ""
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise SkretError(number, "tab character (YAML indentation must be spaces)")
        body = line.lstrip(" ")
        indent = len(line) - len(body)
        if indent % 2 or indent > 4:
            raise SkretError(number, f"unexpected indentation of {indent} spaces")
        if body.startswith("- "):
            raise SkretError(number, "list item; this reader only understands scalar mappings")
        key, colon, raw = body.partition(":")
        if not colon or not key.strip():
            raise SkretError(number, "expected 'key: value'")
        value = _scalar(raw)
        if indent == 0:
            environment = ""
            if value:
                section = ""
                data[key] = value
            else:
                section = key
                data.setdefault(key, {})
        elif indent == 2:
            if not section:
                raise SkretError(number, f"nested key {key!r} has no parent section")
            if section == "environments":
                environment = key
                data[section].setdefault(key, {})
            else:
                environment = ""
                data[section][key] = value
        else:
            if section != "environments" or not environment:
                raise SkretError(number, f"key {key!r} is nested under {section or 'nothing'!r}")
            data[section][environment][key] = value
    return data


def check_skret(path: Path, root: Path, failures: list[str]) -> None:
    name = rel(path, root)
    before = len(failures)
    try:
        data = read_skret(path)
    except SkretError as exc:
        failures.append(f"FAIL {name}:{exc.line}: {exc}")
        return
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        failures.append(f"FAIL {name}: version must be a non-empty scalar")
    default_env = data.get("default_env")
    environments = data.get("environments")
    if not isinstance(environments, dict) or not environments:
        failures.append(f"FAIL {name}: environments must be a non-empty mapping")
        return
    if not isinstance(default_env, str) or not default_env:
        failures.append(f"FAIL {name}: default_env must name an environment")
    elif default_env not in environments:
        failures.append(f"FAIL {name}: default_env is {default_env!r}, "
                        f"not one of {sorted(environments)}")
    for env_name in sorted(environments):
        env = environments[env_name]
        if not isinstance(env, dict):
            failures.append(f"FAIL {name}: environments.{env_name} must be a mapping")
            continue
        for key in SKRET_ENV_KEYS:
            value = env.get(key)
            if not isinstance(value, str) or not value:
                failures.append(f"FAIL {name}: environments.{env_name}.{key} must be a non-empty scalar")
        path_value = env.get("path")
        if isinstance(path_value, str) and path_value and not path_value.startswith("/"):
            failures.append(f"FAIL {name}: environments.{env_name}.path is {path_value!r}, "
                            "expected a path starting with /")
    if len(failures) == before:
        print(f"ok   {name}: {len(environments)} environment(s), "
              f"default_env {default_env!r} defined")


# --- issue templates --------------------------------------------------------

def check_template(path: Path, root: Path, failures: list[str]) -> None:
    name = rel(path, root)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        failures.append(f"FAIL {name}: does not start with a --- front matter fence")
        return
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        failures.append(f"FAIL {name}: front matter fence is never closed")
        return
    fields: dict[str, str] = {}
    before = len(failures)
    for number in range(1, end):
        text = lines[number].strip()
        if not text or text.startswith("#"):
            continue
        key, colon, raw = text.partition(":")
        if not colon or not key.strip():
            failures.append(f"FAIL {name}:{number + 1}: expected 'key: value' in front matter")
            continue
        if key.strip() not in TEMPLATE_KEYS:
            failures.append(f"FAIL {name}:{number + 1}: unknown front matter key {key.strip()!r}")
        if key.strip() in fields:
            failures.append(f"FAIL {name}:{number + 1}: duplicate front matter key {key.strip()!r}")
        fields[key.strip()] = _scalar(raw)
    for key in TEMPLATE_REQUIRED:
        if not fields.get(key):
            failures.append(f"FAIL {name}: front matter needs a non-empty {key!r}")
    if len(failures) == before:
        print(f"ok   {name}: front matter holds ({', '.join(sorted(fields))})")


# --- main -------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate this repository's shipped config artifacts.")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    failures: list[str] = []

    json_files = tracked(root, "*.json")
    if not json_files:
        failures.append("FAIL *.json: no tracked JSON file found; the check would pass vacuously")
    for path in json_files:
        check_json(path, root, failures)

    repo_settings = root / ".github" / "repo-settings.json"
    if repo_settings.is_file():
        check_repo_settings(repo_settings, root, failures)
    else:
        failures.append("FAIL .github/repo-settings.json: missing")

    ruleset = root / ".github" / "rulesets" / "main.json"
    if ruleset.is_file():
        check_ruleset(ruleset, root, failures)
    else:
        failures.append("FAIL .github/rulesets/main.json: missing")

    skret = root / ".skret.yaml"
    if skret.is_file():
        check_skret(skret, root, failures)
    else:
        failures.append("FAIL .skret.yaml: missing")

    templates = sorted((root / ".github" / "ISSUE_TEMPLATE").glob("*.md"))
    if not templates:
        failures.append("FAIL .github/ISSUE_TEMPLATE: no issue template found")
    for path in templates:
        check_template(path, root, failures)

    for line in failures:
        print(line)
    print(f"{len(json_files)} JSON + 1 skret + {len(templates)} template(s): "
          f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
