# Desktop Tauri 2 (Rust + React)

Tauri 2.x với Rust machine core + React frontend (Vite).

## Cấu Trúc

```
apps/desktop/
├── package.json            # bun (frontend)
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json     # App config
│   ├── capabilities/       # Permission policies
│   ├── src/
│   │   ├── lib.rs          # Plugin registration + commands
│   │   ├── commands/       # IPC commands (Rust ↔ React)
│   │   └── machine/        # Core logic chạy offline
│   └── icons/
├── src/                    # React frontend (Vite)
│   ├── App.tsx
│   ├── components/
│   ├── hooks/
│   │   └── useCommand.ts   # IPC hook wrapper
│   └── lib/
└── vite.config.ts
```

## Key Patterns

### IPC Commands (Rust → React)

```rust
// src-tauri/src/commands/analysis.rs
#[tauri::command]
pub async fn analyze_data(input: String) -> Result<AnalysisResult, String> {
    let result = machine::process(&input)
        .map_err(|e| e.to_string())?;
    Ok(result)
}
```

```typescript
// src/hooks/useCommand.ts
import { invoke } from "@tauri-apps/api/core";

export const useAnalyze = () => {
  return useMutation({
    mutationFn: (input: string) =>
      invoke<AnalysisResult>("analyze_data", { input }),
  });
};
```

### Auto-Update

```json
// tauri.conf.json
{
  "plugins": {
    "updater": {
      "endpoints": ["https://releases.product.com/{{target}}/{{arch}}/{{current_version}}"],
      "pubkey": "..."
    }
  }
}
```

```rust
// Check update on startup
use tauri_plugin_updater::UpdaterExt;

app.handle().updater_builder().build()?.check().await?;
```

### CI/CD Build Matrix

```yaml
strategy:
  matrix:
    include:
      - platform: ubuntu-22.04
        target: x86_64-unknown-linux-gnu
      - platform: macos-latest
        target: aarch64-apple-darwin
      - platform: macos-latest
        target: x86_64-apple-darwin
      - platform: windows-latest
        target: x86_64-pc-windows-msvc
```

### Capabilities (Permissions)

```json
// src-tauri/capabilities/default.json
{
  "identifier": "default",
  "permissions": [
    "core:default",
    "fs:allow-read-text-file",
    "shell:allow-open",
    "updater:default"
  ]
}
```

> **Nguyên tắc**: Chỉ cấp quyền tối thiểu. KHÔNG dùng `fs:allow-all` hoặc `shell:allow-all`.

### Machine Core (Rust — chạy offline)

```rust
// src-tauri/src/machine/mod.rs
// Logic nặng chạy trên Rust: file processing, ML inference local,
// encryption, data compression. KHÔNG phụ thuộc network.

pub fn process(input: &str) -> Result<Output, MachineError> {
    // CPU-intensive work runs natively, not in JS
}
```

## Testing

```bash
# Rust tests
cd src-tauri && cargo test

# Frontend tests
bun test --coverage
# Coverage target: ≥ 95%
```
