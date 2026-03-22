
# Project Management với Notion

Sử dụng **better-notion-mcp** để quản lý tiến độ, chống xao nhãng và theo dõi các task một cách chặt chẽ. Đóng vai trò như một "CEO ảo" cho Solo Founder.

## Khi Nào Dùng

- Bắt đầu phiên làm việc mới, cần review task list
- Quản lý tiến độ project qua Notion
- Note lại quyết định quan trọng để không quên
- Chống xao nhãng khi phát sinh ý tưởng ngoài scope
- Cập nhật status task sau khi hoàn thành module

> **Test Coverage**: ≥ 95% cho tất cả automation scripts và workflow logic.

## Workflow Quản Lý Bắt Buộc

### 1. Bắt Đầu Phiên Làm Việc (Start Session)
- Luôn gọi Notion API để lấy danh sách To-do / In Progress của ngày hôm đó (hoặc của project hiện tại).
- Nếu chưa có plan rõ ràng, dùng Notion để phác thảo các bullet points cần giải quyết, tạo thẻ task mới.
- Đảm bảo Focus: "Hôm nay chúng ta chỉ giải quyết task X, Y. Không lan man sang Z."

### 2. Quá Trình Làm Việc (Mid Session)
- Khi hoàn thành xong một chức năng / module, BẮT BUỘC cập nhật status của thẻ Notion tương ứng sang "Done".
- Nếu phát sinh bug hoặc ý tưởng mới nằm ngoài scope hiện tại, KHÔNG làm ngay, mà ghi chú lại vào Notion (Backlog / Ideas) để không bị xao nhãng.

### 3. Kết Thúc Phiên Làm Việc (End Session)
- Viết 1 đoạn Log Summary vào trang tài liệu của Project trên Notion.
- Ghi lại các quyết định kỹ thuật quan trọng (Ví dụ: "Đã chọn Tailwind thay vì Styled Components vì tốc độ").
- Cập nhật các next steps cho phiên làm việc tiếp theo.

## Sử dụng better-notion-mcp
Sử dụng các composite tools như:
- `search`: Tìm kiếm trang/database.
- `read_page`: Đọc nội dung Markdown của trang.
- `read_database`: Đọc danh sách tasks.
- `update_page`: Cập nhật properties (như Status, Priority) của một thẻ.
- `append_blocks`: Ghi log hoặc note xuống cuối trang.
- `create_page`: Tạo task mới trong database.

```python
# Query tasks từ Notion database
tasks = notion.databases.query(
    database_id=TASKS_DB_ID,
    filter={"property": "Status", "status": {"equals": "In Progress"}},
    sorts=[{"property": "Priority", "direction": "descending"}],
)
for task in tasks["results"]:
    print(f"- {task['properties']['Name']['title'][0]['plain_text']}")
```

> "Discipline equals freedom" - Mọi code viết ra phải map với một task trên Notion. Không code vô tội vạ.
