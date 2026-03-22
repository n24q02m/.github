# python-semantic-release (PSR) v10 Configuration Guide

> Reference file cho `repo-structure` skill. Xem [SKILL.md](../SKILL.md) để hiểu pipeline tổng quan.

---

## Công cụ

[python-semantic-release/python-semantic-release@v10](https://github.com/python-semantic-release/python-semantic-release) (GitHub Action)

**Nguyên tắc**: Automated release qua `workflow_dispatch`. Trigger thủ công → PSR phân tích commits → bump version → update CHANGELOG + version files → commit + tag + push → GitHub Release.

**Tại sao PSR v10 thay vì semantic-release (npm)?**

| Tiêu chí | PSR v10 | semantic-release (npm) |
|---|---|---|
| workflow_dispatch beta+stable từ main | Native: `--as-prerelease` flag | Hack: dynamic `release.config.mjs` |
| Monorepo | Native: `directory` input | Community plugin (không official) |
| Python repos | Native: `version_toml` | Cần `@semantic-release/exec` |
| Non-Python (Rust, Go) | `version_toml` đọc mọi TOML file | Cần `@semantic-release/exec` |
| Node repos | `version_variables` (regex match JSON) | Native |

> PSR thắng 4/5 tiêu chí chức năng. semantic-release npm chỉ tốt hơn ở Node native support.
> Với 2 yêu cầu trọng yếu (workflow_dispatch từ single branch + monorepo), PSR là lựa chọn tối ưu.

---

## Config Location

| Loại repo | Config file | Vị trí |
|-----------|-------------|--------|
| Python | `pyproject.toml` | `[tool.semantic_release]` |
| Non-Python (Node, Rust, Go) | `semantic-release.toml` | `[semantic_release]` |
| Monorepo sub-package | Per-subdir | Mỗi subdir có config riêng |

> **QUAN TRỌNG**: PSR config key dùng **underscore** (`semantic_release`), KHÔNG dùng hyphen.

---

## Config Template — Python

```toml
# pyproject.toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
tag_format = "v{version}"
commit_message = "chore(release): v{version}"
build_command = "uv build"
major_on_zero = false

[tool.semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[tool.semantic_release.remote]
type = "github"
```

### Giải thích:
- `version_toml`: Đọc + cập nhật version trong TOML file. Format: `"file:dotpath"`.
- `tag_format`: Format git tag. `{version}` thay bằng version number.
- `commit_message`: Template commit message cho version bump.
- `build_command`: Chạy sau version stamp, trước tag. Env var `$NEW_VERSION` available.
- `major_on_zero`: `false` → major bump khi v0.x.x sẽ tạo v0.(x+1).0 thay vì v1.0.0.

---

## Config Template — Node/TypeScript

```toml
# semantic-release.toml
[semantic_release]
version_variables = ["package.json:version"]
tag_format = "v{version}"
commit_message = "chore(release): v{version}"
build_command = "bun run build"
major_on_zero = false

[semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[semantic_release.remote]
type = "github"
```

> `version_variables` dùng regex matching: `"package.json:version"` match pattern `"version": "X.Y.Z"` trong JSON.

---

## Config Template — Rust (Cargo)

```toml
# semantic-release.toml
[semantic_release]
version_toml = ["Cargo.toml:workspace.package.version"]
tag_format = "v{version}"
commit_message = "chore(release): v{version}"
major_on_zero = false

[semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[semantic_release.remote]
type = "github"
```

> `version_toml` đọc mọi TOML file. Ví dụ: `"Cargo.toml:workspace.package.version"` → đọc `[workspace.package] version = "X.Y.Z"`.
> Nếu cần cập nhật THÊM `package.json`: dùng kết hợp `version_toml` + `version_variables`:
> ```toml
> version_toml = ["Cargo.toml:workspace.package.version"]
> version_variables = ["package.json:version"]
> ```

---

## Config Template — Go

Go dùng git tags cho versioning, không có version file.

```toml
# semantic-release.toml
[semantic_release]
tag_format = "v{version}"
commit_message = "chore(release): v{version}"
major_on_zero = false

[semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[semantic_release.remote]
type = "github"
```

> Nếu Go project có `version` const trong code, dùng `version_variables`:
> ```toml
> version_variables = ["internal/version/version.go:__version__"]
> ```

---

## Monorepo (Multi-package)

PSR v10 hỗ trợ monorepo qua `directory` input trong GitHub Action. Mỗi sub-package có config riêng.

### Tag format cho monorepo

```
{component}@v{version}
```

Ví dụ: `api@v1.2.0`, `web@v0.5.0`, `worker@v1.0.0`

### Per-package config

**Python sub-package** (`apps/api/pyproject.toml`):
```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
tag_format = "api@v{version}"
commit_message = "chore(release): api@v{version}"
build_command = "uv build"
major_on_zero = false

[tool.semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[tool.semantic_release.remote]
type = "github"
```

**Node sub-package** (`apps/web/semantic-release.toml`):
```toml
[semantic_release]
version_variables = ["package.json:version"]
tag_format = "web@v{version}"
commit_message = "chore(release): web@v{version}"
build_command = "bun run build"
major_on_zero = false

[semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[semantic_release.remote]
type = "github"
```

### GitHub Action cho monorepo

```yaml
jobs:
  release:
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GH_PAT }}
          fetch-depth: 0

      - name: Release API
        id: release-api
        uses: python-semantic-release/python-semantic-release@v10
        with:
          directory: apps/api
          github_token: ${{ secrets.GH_PAT }}
          prerelease: ${{ inputs.release_type == 'beta' }}
          prerelease_token: beta

      - name: Release Web
        id: release-web
        uses: python-semantic-release/python-semantic-release@v10
        with:
          directory: apps/web
          github_token: ${{ secrets.GH_PAT }}
          prerelease: ${{ inputs.release_type == 'beta' }}
          prerelease_token: beta

      # Publish per component
      - name: Publish API to GitHub Release
        uses: python-semantic-release/publish-action@v10
        if: steps.release-api.outputs.released == 'true'
        with:
          directory: apps/api
          github_token: ${{ secrets.GH_PAT }}
          tag: ${{ steps.release-api.outputs.tag }}
```

> **Path splitting**: PSR với `directory` input chỉ phân tích commits có thay đổi file trong package path.
> Commits chỉ thay đổi root-level files (`.github/`, `README.md`) sẽ KHÔNG trigger release cho bất kỳ package nào.

---

## Beta / Pre-release

PSR v10 có native support cho prerelease qua CLI flag hoặc GitHub Action input.

### Cách hoạt động

| Input | Kết quả |
|-------|---------|
| `prerelease: false` (default) | Stable: `v1.2.0` → `v1.3.0` |
| `prerelease: true`, `prerelease_token: beta` | Beta: `v1.2.0` → `v1.3.0-beta.1` → `v1.3.0-beta.2` |

### workflow_dispatch

```yaml
on:
  workflow_dispatch:
    inputs:
      release_type:
        description: "Release type"
        type: choice
        options: [beta, stable]
        required: true

jobs:
  release:
    steps:
      - uses: python-semantic-release/python-semantic-release@v10
        with:
          github_token: ${{ secrets.GH_PAT }}
          prerelease: ${{ inputs.release_type == 'beta' }}
          prerelease_token: beta
```

### Beta → Stable lifecycle

```
main: feat: A → feat: B → feat: C
                ↓ workflow_dispatch (beta)
              v1.1.0-beta.1 (includes A, B, C)
                ↓ feat: D
                ↓ workflow_dispatch (beta)
              v1.1.0-beta.2 (includes D)
                ↓ workflow_dispatch (stable)
              v1.1.0 (includes A, B, C, D — all since last stable)
```

> **QUAN TRỌNG**: Stable release bao gồm TẤT CẢ commits kể từ last stable tag, bao gồm cả những commits đã có trong beta.

---

## GitHub Action Inputs / Outputs

### Inputs (version action)

| Input | Type | Default | Mô tả |
|-------|------|---------|-------|
| `github_token` | string | required | Token cho push + release (phải dùng GH_PAT) |
| `directory` | string | `.` | Working directory (monorepo) |
| `prerelease` | bool | `false` | Tương đương `--as-prerelease` |
| `prerelease_token` | string | `""` | Label: `beta`, `alpha`, `rc` |
| `build` | bool | `true` | Có chạy `build_command` không |
| `changelog` | bool | `true` | Có tạo CHANGELOG không |
| `commit` | bool | `true` | Có commit changes không |
| `push` | bool | `true` | Có push commit + tag không |
| `tag` | bool | `true` | Có tạo git tag không |

### Outputs

| Output | Type | Mô tả |
|--------|------|-------|
| `released` | `"true"/"false"` | Có release mới không |
| `tag` | string | Git tag (e.g., `v1.2.0`) |
| `version` | string | Version number (e.g., `1.2.0`) |
| `is_prerelease` | `"true"/"false"` | Có phải prerelease không |

### Publish action

```yaml
- uses: python-semantic-release/publish-action@v10
  if: steps.release.outputs.released == 'true'
  with:
    github_token: ${{ secrets.GH_PAT }}
    tag: ${{ steps.release.outputs.tag }}
```

> `publish-action` upload build artifacts (từ `dist/`) vào GitHub Release assets.
> Cho Python repos: upload `.whl` + `.tar.gz`.
> Publish to PyPI/npm/Docker: dùng dedicated actions riêng (pypa/gh-action-pypi-publish, etc.).

---

## Concurrency Control

```yaml
concurrency:
  group: release
  cancel-in-progress: false
```

> `cancel-in-progress: false` để KHÔNG cancel release đang chạy.
> Chỉ cho phép 1 release workflow chạy tại 1 thời điểm.
> Nếu trigger beta khi stable đang chạy → beta sẽ queue, chờ stable xong.

---

## Version File Strategies

### `version_toml` — Cho TOML files

```toml
version_toml = [
    "pyproject.toml:project.version",           # Python
    "Cargo.toml:workspace.package.version",      # Rust workspace
    "Cargo.toml:package.version",                # Rust single crate
]
```

Format: `"file:dotpath"` hoặc `"file:dotpath:format_type"`
- `:nf` (number format, default): `1.2.3`
- `:tf` (tag format): `v1.2.3`

### `version_variables` — Cho source files (regex)

```toml
version_variables = [
    "package.json:version",                     # JSON: "version": "1.2.3"
    "src/__init__.py:__version__",              # Python: __version__ = "1.2.3"
    "internal/version/version.go:__version__",  # Go: __version__ = "1.2.3"
]
```

Format: `"file:variable_name"`. PSR dùng regex match pattern: `variable_name = "X.Y.Z"` (hỗ trợ `=`, `:`, `@` operators, optional quotes).

### `build_command` — Custom post-version-stamp logic

```toml
build_command = """
  npm version $NEW_VERSION --no-git-tag-version
  uv build
"""
```

Env vars available: `$NEW_VERSION` (e.g., `1.2.3`), `$PACKAGE_NAME`, `$CI`, `$PATH`, `$HOME`.

---

## Token & Permissions

### GH_PAT (Personal Access Token)

PSR cần push commit + tag trực tiếp lên `main` → phải dùng GH_PAT (admin) để bypass branch ruleset.

| Action | Token | Bypass ruleset |
|--------|-------|----------------|
| PSR commit + push | GH_PAT (admin) | Yes |
| PSR create release | GH_PAT | Yes |
| CI trigger từ release | GH_PAT | - (cần PAT để trigger downstream workflows) |

> `GITHUB_TOKEN` **KHÔNG** bypass rulesets → PSR push sẽ bị reject.
> `GH_PAT` cần scope: `repo`, `workflow`.

---

## Troubleshooting

### "No release will be made" — PSR skip release

**Nguyên nhân**: Không có commit nào có type `feat:`, `fix:`, `perf:`, `breaking:` kể từ last tag.

**Giải pháp**: Push ít nhất 1 commit với user-facing type. Hidden types (`chore:`, `refactor:`, `test:`, `ci:`, `build:`, `style:`, `docs:`) KHÔNG trigger release.

### Version file không được cập nhật

**Nguyên nhân**: Config `version_toml` / `version_variables` path sai.

**Debug**: Chạy dry-run:
```bash
semantic-release version --noop --verbosity=DEBUG
```

### Monorepo: Release không detect commits

**Nguyên nhân**: PSR với `directory` input chỉ đếm commits có thay đổi file trong package path.

**Giải pháp**: Commit phải thay đổi file **bên trong** subdir (ví dụ `apps/api/`). Root-level changes không trigger release.

### Changelog thiếu entries

**Nguyên nhân**: Dùng hidden type (`refactor:`, `chore:`) cho user-facing changes.

**Giải pháp**: Với thay đổi ảnh hưởng user → dùng `feat:`, `fix:`, hoặc `perf:`. Xem Commit Message Guidelines trong [SKILL.md](../SKILL.md).

### uv.lock mismatch sau version bump

**Tương tự release-please**: PSR bump version trong `pyproject.toml` nhưng KHÔNG update `uv.lock`.

**Giải pháp**:
- CI: `uv sync` (không `--locked`)
- Dockerfile: `uv sync --frozen`
- Hoặc thêm `uv lock` vào `build_command`:
  ```toml
  build_command = """
    uv lock --upgrade-package "$PACKAGE_NAME"
    uv build
  """
  ```
