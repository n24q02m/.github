
# Game Development với Godot & Rust (gdext)

Thiết kế game và ứng dụng tương tác bằng **Godot Engine 4.x** (Front-end, Cấu trúc UI/Scene) và **Rust (`gdext`)** (Logic nặng, Backend, Hệ thống cốt lõi).
Tự động hóa mọi bước sử dụng MCP server **better-godot-mcp**.

## Khi Nào Dùng

- Tạo game mới với Godot Engine 4.x
- Implement game logic bằng Rust (gdext)
- Thiết kế scene tree và UI flow trong Godot
- Sử dụng better-godot-mcp để tự động hóa Godot workflows

> **Test Coverage**: ≥ 95% cho tất cả Rust game logic và GDScript.

## Kiến Trúc (Architecture)

### 1. Phân chia trách nhiệm
*   **Godot (GDScript / `.tscn`)**: Xử lý Animation, Audio, UI Flow, Particle Effects, Cấu hình Scene Tree. Tín hiệu đầu ra đơn giản.
*   **Rust (gdext)**: Xử lý Toán học, AI, Pathfinding phức tạp, Tương tác Server, Sinh vật lý, Quản lý State lớn. Gửi signals lại cho Godot để hiển thị.

### 2. Tổ chức Thư Mục Chuẩn
- `godot/`: Chứa file `.godot`, `.tscn`, `res://` assets, `.gd`.
- `rust/`: Thư mục crate Rust (file `Cargo.toml`, `src/lib.rs`). Chứa logic extension.
- Dùng file `.gdextension` để map thư viện `.dll`, `.so`, `.dylib` từ Rust sang Godot.

```gdscript
# Ví dụ: Signal từ Rust extension
extends Node2D

@onready var rust_ai = $RustAIComponent

func _ready():
    rust_ai.connect("path_calculated", _on_path_calculated)
    rust_ai.request_pathfinding(global_position, target_position)

func _on_path_calculated(path: PackedVector2Array):
    $PathFollower.path = path
```

## Workflow Sử Dụng Better-Godot-MCP

**TUYỆT ĐỐI KHÔNG** sinh mã nguồn GDScript thô rồi bắt người dùng tự tạo file và copy paste. Hãy sử dụng MCP Tools:

1.  **Composite Actions (`create_scene`, vân vân)**: Khi cần thiết kế một object (ví dụ Player, Enemy), dùng tool để tạo luôn cấu trúc `.tscn` chuẩn từ trong console, tự động gắn script.
2.  **GDScript CRUD (`read_script`, `write_script`, `attach_script`)**: Cập nhật logic thẳng vào file `.gd` hoặc tạo script tự động gắn vào node gốc.
3.  **Quản lý Input / Project Settings (`input_map`, `project_settings`)**: Update Input Actions (di chuyển, nhảy) không cần bật Editor.
4.  **Rust Cấu Hình (`cargo build`)**: Agent tự động nhắc việc build file `rust` library sau khi thay đổi, hoặc dùng background-agents để tự động chạy watch/build.

## Cú Pháp gdext (Rust 1.80+ / Godot 4.x)
- Khai báo class: `#[derive(GodotClass)] #[class(base=Node3D)] pub struct MyPlayer { ... }`
- Implement phương thức: `#[godot_api] impl IMyPlayer for MyPlayer { ... }`
- Biến exported: `#[export] speed: f32`
- Khởi tạo Signals và Gọi methods của base Godot class một cách memory-safe qua system references.

## Quy Tắc Hiệu Suất
- Hạn chế update per-frame (`_process` / `_physics_process`) trong GDScript nếu logic phức tạp. Đẩy sang Rust.
- Tái sử dụng đối tượng (Object Pooling) cho đạn, quái vật.
- Dùng `Signal` thay vì query `get_node()` liên tục trong loop.
