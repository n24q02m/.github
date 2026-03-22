
# Frontend Design System & UI/UX Standards

Thiết kế theo chuẩn "Anti-AI" Aesthetics (Vercel/Linear-style): Tối giản, Mật độ cao nhưng thoáng (High Density but Breathable). Màu sắc/font/theme được thiết kế riêng cho từng app.

## Khi Nào Dùng

- Tạo UI components mới với shadcn/ui và Tailwind CSS
- Review frontend code về accessibility và UX standards
- Thiết kế responsive layouts
- Implement animations và micro-interactions với Framer Motion
- Kiểm tra UI compliance (touch targets, color contrast, loading states)

> **Test Coverage**: ≥ 95% cho tất cả UI components và design system logic.

## 1. UI Stack & Design Tokens
- **Core**: `shadcn/ui` + `clsx` + `tailwind-merge` + `framer-motion`
- **Theme**: Thiết kế riêng cho từng app (colors, dark/light mode). Dùng design tokens/CSS variables thay vì hardcode colors. Palette và accent colors do từng app quyết định — KHÔNG áp đặt constraint về số lượng hay tông màu.
- **Depth & Shadows**: Ưu tiên "Inner Glow" hoặc subtle borders. Tránh large drop shadows.
- **Typography**: Dùng `font-medium` cho subheadings; hạn chế tối đa `font-bold`. Font family do từng app quyết định.
- **Loading State**: Bắt buộc dùng **Skeleton Loading** thay vì Spinners.

## 2. UI/UX Critical Rules (BẮT BUỘC TUÂN THỦ)

### Accessibility (a11y)
- `color-contrast`: Tỉ lệ tương phản tối thiểu 4.5:1 cho text bình thường.
- `focus-states`: BẮT BUỘC có focus ring rõ ràng cho mọi interactive elements (dùng design token, vd: `focus-visible:ring-1 focus-visible:ring-ring`).
- `aria-labels`: Các button chỉ có icon BẮT BUỘC phải có `aria-label`.
- `form-labels`: Input phải có label đi kèm (dùng `htmlFor` hoặc bọc trong label).

### Touch & Interaction
- `touch-target-size`: Nút bấm trên mobile BẮT BUỘC tối thiểu **44x44px**.
- `interactive-states`: MỌI element có thể click phải có đủ 3 states: `:hover`, `:active`, `:focus`.
- `loading-buttons`: Disable button và thêm trạng thái loading khi đang thực hiện async operations.
- `error-feedback`: Thông báo lỗi rõ ràng, nằm ngay cạnh trường dữ liệu bị lỗi (dùng design token `text-destructive`).
- `cursor-pointer`: Phải có `cursor-pointer` cho mọi element click được.

### Data & Content
- **TUYỆT ĐỐI KHÔNG** dùng "Lorem Ipsum". Luôn sinh dữ liệu giả (dummy data) thực tế và có ngữ cảnh.
- Tránh các câu chữ máy móc (ví dụ: "Welcome to our platform"). Dùng copy ngắn gọn, trực diện (vd: "Start building").

## 3. React Performance Patterns (Vercel Best Practices)

### Priority 1: Eliminating Waterfalls (CRITICAL)
```typescript
// ❌ BAD: Sequential fetches
const user = await getUser();
const posts = await getPosts(user.id);

// ✅ GOOD: Parallel fetches
const [user, posts] = await Promise.all([ getUser(), getPosts(userId) ]);
```

### Priority 2: Bundle Size Optimization (CRITICAL)
```typescript
// ❌ BAD: Barrel imports
import { Button, Card, Modal } from "@/components";

// ✅ GOOD: Direct imports
import { Button } from "@/components/ui/button";

// ✅ Dynamic imports cho heavy components (Charts, Maps)
const HeavyChart = dynamic(() => import("@/components/chart"), {
  loading: () => <Skeleton className="h-64" />, ssr: false,
});
```

### Priority 3: Server & Client Optimization
- **Chỉ pass dữ liệu cần thiết** từ Server Component xuống Client Component.
- Dùng `React.memo` cho các list dài và `useCallback` cho event handlers truyền xuống component con.
- Render list dài: Dùng `content-visibility: auto` hoặc virtualization.
- Dùng ternary operator (`? : null`) thay cho `&&` để tránh render số `0` ra UI.

## 4. Animation Guidelines
- Tôn trọng `prefers-reduced-motion`.
- Animation UI feedback (hover, click) không quá `0.2s`.
- Page transition không quá `0.3s`.
- Tránh auto-playing animations gây xao nhãng.

## Checklist Trước Khi Hoàn Thành Code
- [ ] UI có chuẩn "Anti-AI" (subtle borders, inner glow, minimalist)?
- [ ] Các nút bấm có đủ 44x44px trên mobile không?
- [ ] Đã có đủ `:hover`, `:active`, `:focus-visible` states chưa?
- [ ] Đã kiểm tra accessibility (`aria-label`, contrast) chưa?
- [ ] Dữ liệu mẫu có ý nghĩa (không Lorem Ipsum) chưa?
- [ ] Đã import component trực tiếp (tránh barrel file) chưa?
- [ ] Fetch data có bị waterfall không? Đã dùng `Promise.all` chưa?
