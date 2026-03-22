
# MCP Server Development Guide

## Chọn Stack

| Stack | Khi nào dùng | SDK |
|-------|--------------|-----|
| **Python (uv)** | Logic phức tạp, AI/ML integration | `mcp[cli]` (FastMCP) |
| **TypeScript (bun)** | API wrappers, npm publish | `@modelcontextprotocol/sdk` |

---

## Khi Nào Dùng

- Tạo MCP server mới bằng Python (FastMCP) hoặc TypeScript
- Implement thêm tool cho MCP server đã có
- Thiết kế tool annotations cho AI assistant integration
- Debug MCP server communication issues
- Chạy live comprehensive test sau release

> **Test Coverage**: ≥ 95% cho tất cả MCP server tools và handlers.

## 5-Phase Workflow

### Phase 1: Research
1. Khảo sát existing MCP servers tương tự
2. Xác định API/service cần integrate
3. List các tools cần implement
4. Đọc MCP specification

### Phase 2: Implement
1. Scaffold project structure
2. Implement tools từng cái một
3. Thêm error handling + logging
4. Viết unit tests

### Phase 3: Test
1. Unit tests cho mỗi tool function (pytest / bun test)
2. Test với MCP Inspector: `bunx @anthropics/mcp-inspector@latest`
3. Test integration với Claude Desktop / OpenCode
4. Kiểm tra edge cases + error paths

### Phase 4: Evaluate
Tạo 10 evaluation questions:
- Complex, realistic use cases
- Read-only, verifiable answers
- Cover all major tools

### Phase 5: Live Comprehensive Test (BẮT BUỘC)

**Thực hiện sau MỖI lần cải tiến, sửa lỗi, hoặc release.**
Xem chi tiết: `references/live-test-protocol.md`

**Quy trình:**
1. **Build Coverage Matrix**: Gọi `help` tool → liệt kê tất cả tools × actions
2. **Execute Tests** (3 categories, song song khi có thể):
   - **Happy path**: Mỗi tool × mỗi action với tham số hợp lệ
   - **Error path**: Mỗi tool ít nhất 1 test thiếu/sai param
   - **Security boundary**: SSRF, path traversal, injection (nếu applicable)
3. **Document Results**: Ghi vào coverage matrix table với bằng chứng cụ thể
4. **Fix & Re-test**: Bất kỳ FAIL nào → fix → test lại TOÀN BỘ matrix
5. **Release Gate**: 100% Happy path PASS mới cho phép release

**Stable test fixtures** (URL ổn định cho live tests):
- Extract: `https://httpbin.org/html` (Moby-Dick excerpt)
- Crawl: `https://docs.python.org/3/library/json.html`
- Map: `https://docs.python.org/3/`
- Media: `https://httpbin.org/image/png`, `https://httpbin.org/image/jpeg`
- Docs: `fastapi`, `requests`, `flask`

**PASS/FAIL criteria**:
- search/research: ≥1 result với url + title + snippet
- extract: Non-empty content
- crawl: ≥1 page with content (dùng server-rendered sites)
- map: ≥1 URL discovered
- media list: Response có images/videos/audio arrays
- media download: File path + size > 0
- media analyze: LLM response HOẶC expected "requires API_KEYS" (not "Access denied")
- config: Correct JSON response matching expected schema
- help: Markdown content ≥100 chars

**Conditional tests**:
- Không có API_KEYS → media analyze PASS nếu trả "requires API_KEYS"
- Server cached version cũ → ghi nhận, test locally, re-test sau restart
- Network offline → SKIP (không count là FAIL)

**Coverage Matrix Template** (copy và fill cho mỗi server):
```markdown
| # | Tool | Action | Status | Evidence |
|---|------|--------|--------|----------|
| 1 | search | search | ✅/❌ | <response summary> |
| 2 | search | research | | |
| 3 | search | docs | | |
| ... | ... | ... | | |
```

> **Lesson**: Unit tests KHÔNG thay thế live tests. Bug `expanduser()` trong wet-mcp
> chỉ phát hiện qua live testing vì unit tests dùng `tmp_path` (absolute) thay vì
> `~/.wet-mcp/downloads` (tilde path) như production.

---

### Phase 6: Distribution & Discovery

Sau khi release, publish server lên các registries để tăng discoverability.

#### 6.1 GitHub MCP Registry

File `server.json` ở root repo, theo schema chuẩn:
```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.<owner>/<repo>",
  "description": "Max 100 chars. Short, clear description.",
  "repository": { "url": "https://github.com/<owner>/<repo>.git", "source": "github" },
  "version": "1.0.0",
  "packages": [
    {
      "registryType": "npm",
      "identifier": "@scope/package-name",
      "version": "1.0.0",
      "runtimeHint": "npx",
      "transport": { "type": "stdio" },
      "environmentVariables": [
        { "name": "API_TOKEN", "description": "...", "isRequired": true, "isSecret": true }
      ]
    },
    {
      "registryType": "oci",
      "identifier": "docker.io/owner/image:latest",
      "runtimeHint": "docker",
      "transport": { "type": "stdio" }
    }
  ]
}
```

**Validation rules (hard-won lessons)**:
- `description`: **max 100 ký tự**
- **OCI packages**: KHÔNG có `version` field (version nằm trong `identifier` tag)
- **Ownership verification** (registry validate khi publish):
  - **npm**: Thêm `"mcpName": "io.github.<owner>/<repo>"` vào `package.json`
  - **PyPI**: Them `mcp-name: io.github.<owner>/<repo>` vao **README.md** (dong rieng, sau title)
  - **OCI**: Them `LABEL io.modelcontextprotocol.server.name="io.github.<owner>/<repo>"` vao **Dockerfile** (final stage)
- CD workflow can **dynamic update version** trong server.json (xem `repo-structure` skill)
- CD workflow `publish-mcp-registry` phải `needs: [merge-docker]` để OCI image sẵn sàng trước validation

Publish tự động qua CD workflow (xem `repo-structure` skill, section `publish-mcp-registry` job).
CLI tool: `mcp-publisher login github-oidc` + `mcp-publisher publish`.
Yêu cầu: `id-token: write` permission trong GitHub Actions.

#### 6.2 Docker MCP Registry

Fork `github.com/docker/mcp-registry`, thêm `servers/<name>/server.yaml`:
```yaml
name: my-mcp
image: owner/my-mcp
type: server
meta:
  category: productivity
  tags: [productivity, api]
about:
  title: My MCP Server
  description: ...
source:
  project: https://github.com/owner/my-mcp
config:
  description: Configure the server
  secrets:
    - name: my-mcp.api_token
      env: API_TOKEN
      example: sk-xxxx
```
Tạo PR vào `docker/mcp-registry` repo. Yêu cầu Docker image đã publish.

#### 6.3 Package Keywords (SEO)

Keywords bắt buộc cho discoverability trên npm/PyPI:
```
mcp, mcp-server, model-context-protocol, claude, cursor, copilot,
antigravity, codex, opencode, gemini-cli
```
Thêm domain-specific keywords tùy server (vd: `notion`, `email`, `web-scraping`).

#### 6.4 mcpservers.org

Submit thủ công qua form trên mcpservers.org. Cung cấp: repo URL, description, install command.

#### 6.5 GitHub Repo Settings

- Enable Discussions: `gh api repos/{owner}/{repo} -X PATCH -F has_discussions=true`
- Topics: `mcp`, `mcp-server`, `model-context-protocol`, `ai-agent`, domain keywords
- Compatible With badges trong README (xem `growth-and-marketing` skill)

### Phase 7: Plugin Packaging (In-repo Plugin Layer)

MCP server code KHONG DOI. Them cac lop boc (onion layers) vao repo hien tai:

```
repo/
├── src/ hoac package code        # Layer 0: MCP Server (KHONG DOI)
├── CLAUDE.md                      # Layer 1a: Claude Code, Copilot CLI, OpenCode, Cline, Antigravity
├── AGENTS.md                      # Layer 1b: Codex, Amp, Antigravity, Gemini (configurable)
├── .agents/skills/                # Layer 2: Cross-compatible skills (6+ agents)
│   └── {skill-name}/SKILL.md
├── hooks/hooks.json               # Layer 3: Claude Code + Codex + Gemini CLI
├── .claude-plugin/                # Layer 4a: Claude Code plugin manifest
│   ├── plugin.json
│   └── marketplace.json
└── gemini-extension.json          # Layer 4b: Gemini CLI extension (optional)
```

#### Layer 1: Context Files (ship ca hai)

| File | Agents doc duoc |
|------|----------------|
| `CLAUDE.md` | Claude Code (primary), Copilot CLI, OpenCode, Cline, Antigravity, Amp (fallback) |
| `AGENTS.md` | Codex (primary), Amp (primary), Antigravity (v1.20.3+), Gemini CLI (via `.agents/`) |

Noi dung giong nhau, ten khac. Neu repo da co `CLAUDE.md`, chi can copy thanh `AGENTS.md`.

#### Layer 2: Skills (cross-compatible)

Format `SKILL.md` voi YAML frontmatter da tro thanh **universal standard**:
- Claude Code (`.claude/skills/`), Copilot CLI (`.github/skills/` + `.claude/skills/`)
- Codex (`.agents/skills/`), Amp (`.agents/skills/`), Gemini CLI (`.gemini/skills/` + `.agents/skills/`)
- Antigravity (`.agent/skills/`)

**Chien luoc**: Ship tai `.agents/skills/` (cross-compatible 5+ agents). Claude Code plugin `skills/` directory la path rieng.

Moi skill la **guided workflow**, KHONG chi list tools:
```markdown
---
name: deep-research
description: Multi-source research with citation and evidence
---
# Deep Research Workflow

1. Search web for initial sources (search tool, action=search)
2. Extract full content from top 3 results (extract tool, action=extract)
3. Cross-reference with academic sources (search tool, action=research)
4. Synthesize findings with citations
```

#### Layer 3: Hooks

`hooks/hooks.json` format tuong thich giua Claude Code va Codex:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [{ "type": "command", "command": "echo '[my-mcp] Ready'" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "my-mcp update 2>/dev/null || true" }]
      }
    ]
  }
}
```

Gemini CLI hooks cau hinh trong `settings.json` (format khac nhung concept giong).

#### Layer 4: Plugin Manifests

**Claude Code** (`.claude-plugin/plugin.json`):
```json
{
  "name": "my-mcp",
  "version": "1.0.0",
  "description": "...",
  "mcpServers": {
    "my-mcp": {
      "command": "uvx",
      "args": ["--python", "3.13", "my-mcp"]
    }
  },
  "skills": "./skills/"
}
```

**Gemini CLI** (`gemini-extension.json`) — optional, chi can neu target Gemini users:
```json
{
  "name": "my-mcp",
  "description": "...",
  "mcpServers": { "my-mcp": { "command": "uvx", "args": ["my-mcp"] } },
  "skills": ["skills/"],
  "contextFileName": "GEMINI.md"
}
```

#### Distribution Channels

| Channel | Audience | Auto via CD? |
|---------|----------|-------------|
| MCP Registry (`server.json`) | Tat ca agents | Co |
| npm / PyPI | Tat ca agents | Co |
| Docker (multi-arch) | Tat ca agents | Co |
| Claude Code Marketplace | Claude Code users | Manual submit |
| Gemini CLI Extension Gallery | Gemini CLI users | Manual submit |
| Own marketplace (`n24q02m/better-mcp-suite`) | Cross-promotion | Manual |
| mcpservers.org | Discovery | Manual |
| Glama.ai | Discovery | Manual |

#### Cross-Agent Compatibility Matrix

| Agent | MCP | CLAUDE.md | AGENTS.md | .agents/skills/ | hooks.json | Plugin |
|-------|-----|-----------|-----------|-----------------|------------|--------|
| Claude Code | stdio/sse/http | Primary | -- | Via plugin | 25+ events | .claude-plugin/ |
| Copilot CLI | stdio/http/sse | Yes | Yes | -- (.github/skills/) | 6 events | /plugin install |
| Codex | stdio/http | Fallback | Primary | Primary | 3 events | Skill dirs |
| Gemini CLI | stdio/sse/http | Configurable | Via .agents/ | Via .agents/ | 11 events | gemini-extension.json |
| Antigravity | stdio | Yes | Yes (v1.20.3+) | .agent/skills/ | -- | MCP Store |
| OpenCode | stdio/sse | Yes | -- | -- (.opencode/commands/) | -- | -- |
| Cursor | stdio/sse/http | -- | -- | -- | -- | -- |
| Windsurf | stdio/sse/http | -- | -- | -- | -- | MCP Store |
| Cline | stdio/sse | Yes | -- | -- | -- | -- |
| Amp | stdio/http | Fallback | Primary | Primary | -- | Skill + MCP |

---

## Architecture Patterns

### Mega-Tool Pattern

Gom nhiều actions liên quan vào 1 tool thay vì tạo tool riêng cho mỗi action.
Giảm số tools client phải load, tối ưu token usage.

```python
@mcp.tool()
async def memory(
    action: str,       # add|search|list|update|delete|export|import|stats
    content: str | None = None,
    query: str | None = None,
    memory_id: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    limit: int = 5,
) -> str:
    """Persistent memory store. Actions: add|search|list|update|delete|export|import|stats."""
    match action:
        case "add": ...
        case "search": ...
        case "list": ...
```

Ưu điểm:
- Ít tools = ít tokens giải thích cho LLM
- Linh hoạt thêm action mà không thêm tool mới
- Nhất quán interface: luôn có `action` parameter

Nhược điểm:
- Annotations không granular (readOnlyHint phải set cho worst-case)
- Description phải compressed vì gom nhiều actions

### Standard Tool Set

Mọi MCP server nên có 3 loại tools:

| Loại | Mục đích | Annotations |
|------|----------|-------------|
| **Main tools** | Core functionality (1-5 mega tools) | Tùy theo action |
| **Config tool** | Server config & management | readOnlyHint=False, idempotentHint=True |
| **Help tool** | Full documentation on demand | readOnlyHint=True, idempotentHint=True |

Config tool chuẩn có các actions:
- `status`: Hiển thị config hiện tại (DB, embedding, cache, sync)
- `set`: Thay đổi runtime setting (key + value)
- `cache_clear`: Xóa cache
- Custom actions tùy server (vd: `docs_reindex`, `sync`)

Help tool load documentation từ markdown files, giữ tool descriptions ngắn gọn:
```python
@mcp.tool()
async def help(tool_name: str = "search") -> str:
    """Full documentation for a tool. Use when compressed descriptions are insufficient."""
    doc_file = files("my_mcp.docs").joinpath(f"{tool_name}.md")
    return doc_file.read_text()
```

### Parallelism & Concurrency

MCP SDK (cả Python và TypeScript) hỗ trợ **parallel tool calls** mặc định:
- **Python (FastMCP)**: anyio TaskGroup `start_soon()` — mỗi tool call chạy song song
- **TypeScript**: `Promise.resolve().then(handler)` fire-and-forget concurrency

**BẮT BUỘC**: Wrap sync DB operations trong `asyncio.to_thread()` để không block event loop:
```python
import asyncio

# Sai: block event loop
result = db.search(query=query)

# Đúng: chạy trong thread pool
result = await asyncio.to_thread(db.search, query=query)
```

Khi dùng `asyncio.to_thread` với SQLite, set `check_same_thread=False`:
```python
self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
```

---

## Python Stack (FastMCP)

### Cấu trúc
```
project/
├── src/<package>/
│   ├── __init__.py     # main() entry point
│   ├── server.py       # MCP server + tools
│   ├── config.py       # Pydantic Settings
│   └── docs/           # Tool documentation (*.md)
│       ├── memory.md
│       ├── config.md
│       └── __init__.py
├── tests/
├── pyproject.toml
└── uv.lock
```

> **Env vars distribution**: MCP server KHÔNG dùng `.env` files. Env vars cấu hình trong **MCP client config** (`"env": {...}` trong jsonc), Pydantic Settings trong `config.py` đọc từ env vars do client inject:
>
> ```jsonc
> // claude_desktop_config.json
> {
>   "mcpServers": {
>     "my-mcp": {
>       "command": "uvx",
>       "args": ["my-mcp"],
>       "env": {
>         "DATABASE_PATH": "~/.my-mcp/data.db",
>         "LITELLM_API_KEY": "sk-xxx"
>       }
>     }
>   }
> }
> ```

### pyproject.toml
```toml
[project]
name = "my-mcp"
requires-python = ">=3.13"
dependencies = [
  "mcp[cli]>=1.0.0",
  "pydantic-settings>=2.0.0",
  "loguru>=0.7.0",
]

[project.scripts]
my-mcp = "my_mcp:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_mcp"]

[dependency-groups]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.25.0", "ruff>=0.8.0", "ty>=0.0.1a10"]
```

### Server Template
```python
import json
import sys
from importlib.resources import files

from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations

from my_mcp.config import settings

mcp = FastMCP(
    "MyServer",
    instructions="Mô tả ngắn về server.",
)


@mcp.tool(
    description="Main tool. Actions: action1|action2|action3.",
    annotations=ToolAnnotations(
        title="Main",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
async def main_tool(action: str, ...) -> str:
    """Execute main action."""
    match action:
        case "action1": ...
        case "action2": ...


@mcp.tool(
    description="Server config. Actions: status|set|cache_clear.",
    annotations=ToolAnnotations(
        title="Config",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def config(action: str, key: str | None = None, value: str | None = None) -> str:
    """Server configuration."""
    ...


@mcp.tool(
    description="Full docs. topic: 'main' | 'config'",
    annotations=ToolAnnotations(
        title="Help",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def help(topic: str = "main") -> str:
    """Load full documentation."""
    doc_file = files("my_mcp.docs").joinpath(f"{topic}.md")
    return doc_file.read_text()


def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    mcp.run()
```

---

## TypeScript Stack

### Cấu trúc
```
project/
├── src/
│   ├── init-server.ts   # Server initialization
│   ├── tools/
│   │   └── registry.ts  # Tool registration (TOOLS array)
│   └── docs/            # Tool documentation (*.md)
├── bin/cli.mjs          # CLI entry point
├── package.json
├── tsconfig.json
├── biome.json
└── bun.lock
```

### package.json
```json
{
  "name": "@user/my-mcp",
  "type": "module",
  "bin": {"my-mcp": "bin/cli.mjs"},
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.21.1",
    "zod": "^4.1.0"
  },
  "devDependencies": {
    "@biomejs/biome": "^2.3.0",
    "typescript": "^5.9.0",
    "esbuild": "^0.25.0"
  },
  "scripts": {
    "build": "tsc -build && node scripts/build-cli.js",
    "dev": "tsx watch src/init-server.ts"
  }
}
```

### Server Template (Low-level SDK)
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const TOOLS = [
  {
    name: "main_tool",
    description: "Main tool. Actions: action1|action2.",
    annotations: {
      title: "Main",
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: false,
    },
    inputSchema: {
      type: "object",
      properties: {
        action: { type: "string", enum: ["action1", "action2"] },
      },
      required: ["action"],
    },
  },
  {
    name: "help",
    description: "Full documentation for a tool.",
    annotations: {
      title: "Help",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    inputSchema: {
      type: "object",
      properties: {
        tool_name: { type: "string", enum: ["main_tool", "config"] },
      },
      required: ["tool_name"],
    },
  },
];

const server = new Server({ name: "my-mcp", version: "1.0.0" });

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  // ... handle tool calls
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

---

## Tool Design Best Practices

### Naming Convention

Hai styles tùy theo kiểu server:

| Style | Pattern | Khi nào dùng |
|-------|---------|--------------|
| **Mega-tool** | `<resource>` + `action` param | Server với nhiều actions/resource |
| **Flat** | `<service>_<action>_<resource>` | Server với ít tools, mỗi tool 1 action |

Mega-tool examples: `memory(action="add")`, `pages(action="create")`, `search(mode="docs")`
Flat examples: `github_create_issue`, `slack_send_message`

### Tool Annotations

```python
from mcp.types import ToolAnnotations

@mcp.tool(
    annotations=ToolAnnotations(
        title="Search Files",       # Human-readable title
        readOnlyHint=True,          # Không modify state
        destructiveHint=False,      # Không xóa data
        idempotentHint=True,        # Safe to retry
        openWorldHint=False,        # Closed set of results
    )
)
async def search(query: str) -> str: ...
```

TypeScript equivalent:
```typescript
{
  name: "search",
  annotations: {
    title: "Search Files",
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
  // ...
}
```

**Quy tắc Mega-tool annotations**: Set cho worst-case action.
Nếu tool có cả read (search) và write (add), thì `readOnlyHint=false`.

### Description Guidelines
- **Compressed**: Bỏ articles, dùng abbreviations cho mega-tools
- Liệt kê actions ngay trong description: `"Actions: add|search|list|update|delete"`
- Thêm "Use help tool for full docs" để redirect đến chi tiết
- Không lặp lại parameter info đã có trong inputSchema

### Error Messages
```python
# Sai
raise ValueError("Error")

# Đúng
raise ValueError(
    f"User {user_id} not found. "
    "Verify the ID exists in the database. "
    "Try listing users first with list_users tool."
)
```

---

## Output Schema (structuredContent)

```python
from mcp.types import TextContent, ImageContent

@app.tool()
async def analyze_image(url: str) -> list[TextContent | ImageContent]:
    """Analyze image and return structured result."""
    analysis = await do_analysis(url)
    return [
        TextContent(type="text", text=f"Analysis: {analysis.summary}"),
        ImageContent(type="image", data=analysis.thumbnail, mimeType="image/png"),
    ]
```

---

## Testing

### Unit Tests
```python
import pytest
from my_mcp.tools import my_tool

@pytest.mark.asyncio
async def test_my_tool():
    result = await my_tool("input")
    assert "expected" in result
```

### MCP Inspector
```bash
# Install
bunx @anthropics/mcp-inspector@latest

# Test server
bunx @anthropics/mcp-inspector python -m my_mcp
```

### Live Test Script (Phase 5 — Self-Contained)

**Uu diem**: Khong can build local, sua file MCP config JSON, hay restart Claude Code.
Script tu spawn server process, giao tiep qua MCP protocol (JSON-RPC stdio), roi tat.

**Cach hoat dong**:
1. Spawn server as subprocess (same as MCP client would)
2. Giao tiep qua MCP SDK Client + StdioClientTransport
3. Test ALL tools x actions qua protocol that
4. Report PASS/FAIL voi evidence

**Python template** (`tests/test_live_mcp.py`):
```python
import asyncio, json, os, sys
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

async def run_tests():
    server_params = StdioServerParameters(
        command="uv", args=["run", "my-mcp"],
        env={**os.environ, "DB_PATH": "/tmp/test.db"},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Test tools
            tools = await session.list_tools()
            result = await session.call_tool("memory", {"action": "add", "content": "test"})
            text = result.content[0].text
            assert "saved" in text

asyncio.run(run_tests())
```

**TypeScript template** (`test-live-mcp.mjs`):
```javascript
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'

const transport = new StdioClientTransport({
  command: 'node', args: ['bin/cli.mjs'],
  env: { MY_TOKEN: process.env.MY_TOKEN || 'fake', PATH: process.env.PATH },
})
const client = new Client({ name: 'live-test', version: '1.0.0' })
await client.connect(transport)
// Test tools
const tools = await client.listTools()
const r = await client.callTool({ name: 'help', arguments: { tool_name: 'search' } })
console.assert(r.content[0].text.length >= 100)
await client.close()
```

**Lưu ý quan trọng**:
- Python env var names: Kiểm tra `config.py` để dùng tên chính xác (vd: `DB_PATH` không phải `DATABASE_PATH`)
- MCP transport có thể parse JSON strings thành objects — dùng list/dict trực tiếp thay vì `json.dumps()`
- Network-dependent tests nên có `skip` logic (không count là FAIL)
- Security tests (SSRF, path traversal, SQL injection) luôn test được offline

---

## Checklist

### Development (Phase 1-2)
- [ ] 5-phase workflow hoàn thành?
- [ ] Standard Tool Set: main + config + help?
- [ ] Mega-tool pattern cho related actions?
- [ ] Annotations set đúng (title, readOnly, destructive, idempotent, openWorld)?
- [ ] Sync DB ops wrapped trong `asyncio.to_thread()`?
- [ ] Description compressed, redirect help tool cho full docs?
- [ ] Error messages actionable?

### Testing (Phase 3-4)
- [ ] Unit tests cho mỗi tool?
- [ ] Tested với MCP Inspector?
- [ ] 10 evaluation questions created?

### Live Comprehensive Test (Phase 5 — BẮT BUỘC)
- [ ] Coverage matrix built (tất cả tools × actions)?
- [ ] Happy path: 100% tools × actions PASS?
- [ ] Error path: ≥1 test/tool cho missing/invalid params?
- [ ] Security boundary: SSRF, path traversal tested (nếu applicable)?
- [ ] Results documented với bằng chứng cụ thể (response data)?
- [ ] Bugs found → fixed → re-tested toàn bộ matrix?
- [ ] Post-deploy version verification (nếu release)?

### Distribution (Phase 6)
- [ ] `server.json` tạo và validate theo schema?
- [ ] CD workflow có `publish-mcp-registry` job (OIDC)?
- [ ] Docker MCP Registry `server.yaml` submitted (nếu có Docker image)?
- [ ] Package keywords đủ (mcp, mcp-server, claude, cursor, copilot, antigravity, codex, opencode, gemini-cli)?
- [ ] mcpservers.org submitted?
- [ ] GitHub Discussions enabled + repo topics set?
- [ ] README có Compatible With badges + cross-links?

### Plugin Packaging (Phase 7)
- [ ] `CLAUDE.md` + `AGENTS.md` ship cùng nội dung?
- [ ] `.agents/skills/` có ít nhất 1 guided workflow?
- [ ] Skills là workflows (không chỉ list tools)?
- [ ] `hooks/hooks.json` dùng valid events (PostToolUse, SessionStart)?
- [ ] `.claude-plugin/plugin.json` khai báo mcpServers + skills?
- [ ] KHONG có `.mcp.json` duplicate (chỉ dùng plugin.json)?
- [ ] `gemini-extension.json` tạo (nếu target Gemini users)?
- [ ] Submit lên Claude Code Marketplace?
- [ ] Submit lên Gemini CLI Extension Gallery (nếu có)?

## Live Test Protocol


Tài liệu tham chiếu cho Phase 5 (Live Comprehensive Test) trong workflow xây dựng MCP server.
**BẮT BUỘC** thực hiện sau mỗi lần cải tiến, sửa lỗi, hoặc release.

---

## 1. Nguyên tắc

| # | Nguyên tắc | Giải thích |
|---|-----------|------------|
| 1 | **100% Coverage** | Mỗi tool × mỗi action = 1 test case bắt buộc |
| 2 | **3 Categories** | Happy path + Error path + Security boundary |
| 3 | **Evidence-based** | Mỗi test phải có bằng chứng (response data), không chỉ "it works" |
| 4 | **Stable Fixtures** | Dùng URL/data ổn định, không phụ thuộc vào service bên thứ ba có thể down |
| 5 | **Conditional Tests** | Ghi rõ yêu cầu (API keys, network, etc.) cho test cần điều kiện đặc biệt |
| 6 | **Version Verification** | Kiểm tra server version khớp expected sau deploy |
| 7 | **Release Gate** | Không release nếu chưa pass 100% live tests |

---

## 2. Quy trình

```
┌──────────────────────────────────────────────────────────┐
│  Step 1: Build Coverage Matrix                           │
│  - Gọi help tool (không tham số) → danh sách tools      │
│  - Gọi help(tool_name=X) cho mỗi tool → danh sách      │
│    actions + parameters                                   │
│  - Tạo matrix: tool × action × category                 │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│  Step 2: Execute Tests (parallel khi có thể)             │
│  - Happy path: gọi với tham số hợp lệ                   │
│  - Error path: gọi thiếu param / param sai              │
│  - Security: gọi với input nguy hiểm (SSRF, traversal)  │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│  Step 3: Document Results                                │
│  - Ghi vào bảng kết quả (xem template bên dưới)         │
│  - Mỗi FAIL → phân tích root cause → tạo fix            │
│  - Sau fix → re-test lại toàn bộ (không chỉ case fail)  │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│  Step 4: Verify & Gate                                   │
│  - 100% Happy path PASS → cho phép release               │
│  - Error path + Security cũng phải PASS                  │
│  - Ghi kết quả vào conversation context cho tracking     │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Coverage Matrix Template

### Happy Path (BẮT BUỘC — mỗi tool × mỗi action)

```markdown
| # | Tool | Action | Test Input | Expected | Status | Evidence |
|---|------|--------|-----------|----------|--------|----------|
| 1 | search | search | query="python testing" | ≥1 result with url, title, snippet | ✅/❌ | 3 results from google/brave |
| 2 | search | research | query="transformer attention" | ≥1 result with source_type="academic" | | |
| 3 | search | docs | library="fastapi", query="routing" | results hoặc indexing_in_progress | | |
| 4 | extract | extract | urls=["https://httpbin.org/html"] | content chứa "Herman Melville" | | |
| 5 | extract | crawl | urls=["https://docs.python.org/3/library/json.html"], depth=1, max_pages=3 | ≥1 page with content | | |
| 6 | extract | map | urls=["https://docs.python.org/3/"], max_pages=5 | ≥2 URLs discovered | | |
| 7 | media | list | url="https://httpbin.org/image" | ≥1 image in response | | |
| 8 | media | download | media_urls=["https://httpbin.org/image/png"] | file path + size > 0 | | |
| 9 | media | analyze | url=<downloaded_file>, prompt="describe" | LLM response hoặc API key error (not "Access denied") | | |
| 10 | config | status | (no params) | JSON with database, embedding, cache keys | | |
| 11 | config | set | key="log_level", value="DEBUG" | {"status": "updated"} | | |
| 12 | config | cache_clear | (no params) | {"status": "cache cleared"} | | |
| 13 | config | docs_reindex | key="<library>" | {"status": "cleared", "library": "..."} | | |
| 14 | help | search | tool_name="search" | Markdown docs chứa "## Actions" | | |
| 15 | help | extract | tool_name="extract" | Markdown docs chứa "## Actions" | | |
| 16 | help | media | tool_name="media" | Markdown docs chứa "## Actions" | | |
| 17 | help | config | tool_name="config" | Markdown docs chứa "## Actions" | | |
| 18 | help | (overview) | tool_name không truyền hoặc "help" | Markdown overview chứa "## Available Tools" | | |
```

### Error Path (BẮT BUỘC — ít nhất 1 test/tool)

```markdown
| # | Tool | Test Case | Input | Expected Response |
|---|------|----------|-------|-------------------|
| 1 | search | Missing query | action="search" (no query) | "Error: query is required" |
| 2 | search | Invalid action | action="invalid" | Error message about invalid action |
| 3 | extract | Missing urls | action="extract" (no urls) | "Error: urls is required" |
| 4 | media | Missing url for list | action="list" (no url) | "Error: url is required" |
| 5 | media | Missing urls for download | action="download" (no media_urls) | Error about missing urls |
| 6 | config | Invalid key | action="set", key="invalid_key" | Error listing valid keys |
| 7 | config | Missing value | action="set", key="log_level" (no value) | Error about missing value |
| 8 | help | Invalid tool | tool_name="nonexistent" | Error or graceful fallback |
```

### Security Boundary (NÊN — test nếu server có security features)

```markdown
| # | Tool | Test Case | Input | Expected |
|---|------|----------|-------|----------|
| 1 | extract | SSRF private IP | urls=["http://169.254.169.254/"] | Blocked / Error |
| 2 | media | Path traversal download | output_dir="/tmp/evil" | Security error |
| 3 | media | Path traversal analyze | url="/etc/passwd" | "Access denied" |
| 4 | extract | SSRF localhost | urls=["http://127.0.0.1:8080"] | Blocked |
```

---

## 4. Stable Test Fixtures

URL ổn định để dùng trong live tests (không thay đổi content thường xuyên):

| Mục đích | URL | Ghi chú |
|----------|-----|---------|
| Extract HTML | `https://httpbin.org/html` | Trả về Moby-Dick excerpt, ổn định |
| Download image | `https://httpbin.org/image/png` | PNG 8KB ổn định |
| Download JPEG | `https://httpbin.org/image/jpeg` | JPEG 35KB ổn định |
| Crawl docs | `https://docs.python.org/3/library/json.html` | Python stdlib docs, ổn định |
| Map site | `https://docs.python.org/3/` | Nhiều internal links |
| Media listing | `https://httpbin.org/image` | Có image resources |
| Docs indexing | `fastapi`, `requests`, `flask` | Libraries phổ biến, docs ổn định |

> **⚠️ LƯU Ý**: httpbin.org crawl có thể trả về empty nếu content là JS-rendered.
> Dùng `docs.python.org` cho crawl tests (server-rendered HTML).

---

## 5. PASS/FAIL Criteria

### Mỗi action type có criteria riêng:

| Action Type | PASS khi | FAIL khi |
|------------|----------|----------|
| **search/research** | ≥1 result với url + title + snippet | Empty results hoặc error |
| **docs** | Results hoặc `indexing_in_progress` status | Error không liên quan đến indexing |
| **extract** | Content non-empty với URL gốc | Empty content hoặc error |
| **crawl** | ≥1 page with content (dùng docs.python.org) | 0 pages hoặc error |
| **map** | ≥1 URL discovered | 0 URLs hoặc error |
| **media list** | Response có images/videos/audio arrays | Error |
| **media download** | File path + size > 0 | Error hoặc size = 0 |
| **media analyze** | LLM response HOẶC API key error (not "Access denied") | "Access denied" hoặc path error |
| **config status** | JSON với database, embedding keys | Error |
| **config set** | `{"status": "updated"}` | Error (trừ khi key/value invalid → đó là error path test) |
| **config cache_clear** | `{"status": "cache cleared"}` | Error |
| **config docs_reindex** | `{"status": "cleared"}` | Error |
| **help** | Markdown content ≥100 chars | Empty hoặc error |

### Conditional Test Rules:

| Điều kiện | Tests bị ảnh hưởng | Cách xử lý |
|-----------|-------------------|------------|
| Không có API_KEYS | media analyze | PASS nếu trả "requires API_KEYS" (expected behavior) |
| Server chưa restart sau deploy | Tất cả | Ghi nhận version mismatch, test lại sau restart |
| Network offline | search, extract, crawl | SKIP với ghi chú, không count là FAIL |

---

## 6. Post-Deploy Verification

Sau khi release lên PyPI/Docker:

```markdown
### Version Check
1. Gọi `config status` → kiểm tra version trong response (nếu có)
2. Hoặc: `pip index versions <package>` → confirm version mới
3. Nếu server đang chạy cached version cũ:
   - Ghi nhận "stale version"
   - Test locally với source code nếu cần
   - Re-test sau khi server restart

### Regression Check
- Chạy lại TOÀN BỘ Happy Path matrix
- Nếu bất kỳ test nào FAIL mà trước đó PASS → regression bug → BLOCK release
```

---

## 7. Lessons Learned

Các bug thực tế đã phát hiện qua live testing (cập nhật liên tục):

| Bug | Phát hiện bởi | Test case | Root cause |
|-----|--------------|-----------|------------|
| `expanduser()` missing in `analyze_media` | media analyze live test | `analyze(url="/home/user/.wet-mcp/downloads/file.jpg")` → "Access denied" | `Path(settings.download_dir).resolve()` không expand `~`, cần `.expanduser().resolve()` |
| SSRF in docs.py (19 httpx clients) | Security review + live test | Extract với internal URLs | httpx clients không có SSRF protection |
| Path traversal in media download | Security review | `output_dir="/tmp/evil"` | Không validate output_dir |
| 10/18 tools thiếu `safeResolve()` | better-godot-mcp live test | Path traversal với `../../../etc/passwd` | Dùng `resolve()` thay vì `safeResolve()` cho user-provided paths |
| Env var name sai trong test | mnemo-mcp live test | `DATABASE_PATH` thay vì `DB_PATH` | Test dùng real DB thay vì temp → stats trả 198 memories |
| MCP transport parse JSON strings | mnemo-mcp live test | `memory(action="import", data=json.dumps({...}))` | `json.dumps()` string bị parse lại thành dict bởi MCP SDK, gây Pydantic validation error |

> **Rule**: Mỗi bug tìm được qua live testing → thêm vào bảng này + thêm test case tương ứng vào Error/Security matrix.

---

## 8. Self-Contained Test Script

Live test script **KHÔNG cần**:
- Build local rồi sửa MCP config JSON
- Restart Claude Code / MCP client
- Cài đặt thêm dependencies

Script tự spawn server subprocess, giao tiếp qua MCP SDK Client (StdioClientTransport), rồi tắt.

### Cách implement:

| Stack | File | Command chạy |
|-------|------|-------------|
| Python (FastMCP) | `tests/test_live_mcp.py` | `uv run python tests/test_live_mcp.py` |
| TypeScript | `test-live-mcp.mjs` | `node test-live-mcp.mjs` |

### Python MCP Client:
```python
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

server_params = StdioServerParameters(
    command="uv", args=["run", "my-mcp"],
    env={**os.environ, "DB_PATH": "/tmp/test.db"},
)
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("tool_name", {"action": "..."})
```

### TypeScript MCP Client:
```javascript
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'

const transport = new StdioClientTransport({
  command: 'node', args: ['bin/cli.mjs'],
  env: { TOKEN: 'xxx', PATH: process.env.PATH },
})
const client = new Client({ name: 'test', version: '1.0.0' })
await client.connect(transport)
const r = await client.callTool({ name: 'tool', arguments: { action: '...' } })
await client.close()
```

### Gotchas:
- **Env var names**: Luôn kiểm tra `config.py` / `config.ts` — tên env var có thể khác với tên ta nghĩ
- **MCP transport parse JSON**: `json.dumps()` string có thể bị parse lại thành dict — dùng list/dict trực tiếp
- **Network tests**: Dùng `skip()` thay vì `fail()` khi network unavailable
- **Fake tokens**: Server cần token để start → dùng fake token, test help/error paths offline
