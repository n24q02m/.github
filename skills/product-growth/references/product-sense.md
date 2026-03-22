
# Startup & Micro-SaaS Product Sense

**Vai trò**: Product Manager / Indie Hacker Kỳ Cựu. Khắt khe, thực tế và tập trung vào **doanh thu / người dùng thật**.

## Khi Nào Dùng

- Đánh giá ý tưởng sản phẩm mới trước khi code
- Xác định MVP scope cho dự án (dưới 2 tuần)
- Thiết kế chiến lược giá (Pricing) cho SaaS product
- Validate nhu cầu thị trường (fake door, pre-sale)
- Phân tích đối thủ cạnh tranh

> **Test Coverage**: ≥ 95% cho tất cả analytics và validation scripts.

## 1. Tư Duy Validate Ý Tưởng (Idea Validation)
*   **Không code trước khi có nhu cầu**: Trả lời câu hỏi "Vấn đề là gì?", "Tại sao lại giải quyết ngay bây giờ?", "Đang có ai trả tiền cho giải pháp tương đương chưa?".
*   **Bán nháp (Fake Door / Pre-sale)**: Thiết kế Landing Page (bằng Tailwind/Next.js) có nút "Mua" giả để đo lường tỷ lệ Click. Nếu không ai click, đừng code Backend.

```tsx
// Fake Door Landing Page - đo lường nhu cầu trước khi code
export default function LandingPage() {
  const trackClick = () => posthog.capture("pricing_cta_clicked");
  
  return (
    <section>
      <h1>Tự động tổng hợp báo cáo trong 5 giây</h1>
      <p>Không cần copy-paste. AI đọc data và viết báo cáo cho bạn.</p>
      <button onClick={trackClick}>Dùng thử miễn phí</button>
      <small>Không cần thẻ tín dụng. Hủy bất cứ lúc nào.</small>
    </section>
  );
}
```

*   **Phân tích đối thủ**: Tính năng gì họ làm tốt, tính năng gì người dùng đang chê (cào review G2/Capterra/Reddit).

## 2. Xác Định MVP (Minimum Viable Product)
*   **Cắt gọt không thương tiếc**: "Tính năng này có giúp người dùng trả tiền ngay cho bản v1.0 không?" -> KHÔNG -> Đưa vào Backlog, KHÔNG CODE.
*   **Scope dưới 2 tuần**: Một MVP chuẩn của Solo Founder phải ship được trong vòng 2 tuần. Nếu dài hơn, scope đang quá to.
*   **Sử dụng dịch vụ có sẵn**: Dùng Supabase/Firebase Auth, Stripe Checkout, Resend. Đừng tự code hệ thống Đăng nhập / Gửi email / Quản lý mật khẩu.
*   **Làm bằng tay trước (Concierge MVP)**: Ví dụ, ứng dụng tự động tổng hợp báo cáo. Version 1: User nhập form -> Code đẩy vào Telegram của bạn -> Bạn tự tổng hợp bằng ChatGPT -> Gửi lại cho User. Đừng vội code 1 hệ thống Worker phức tạp.

## 3. Chiến Lược Giá (Pricing Strategy)
*   **Đừng miễn phí**: Nếu sản phẩm giải quyết vấn đề thật, hãy thu tiền từ Day 1.
*   **Tier Structure**:
    - *Free*: Tính năng cơ bản, giới hạn số lượng (vd: 5 project). Mục đích: Lấy email và phản hồi.
    - *Pro ($9 - $29/tháng)*: Tính năng cốt lõi cho cá nhân, giới hạn hợp lý.
    - *Team/Lifetime ($49 - $199)*: Tính năng làm việc nhóm, API, Export data.
*   **Value-based Pricing**: Định giá dựa trên số tiền / thời gian bạn tiết kiệm được cho khách hàng, không phải dựa trên chi phí server.

## 4. Metrics Cần Đo Lường (Startup Metrics)
*   **CAC (Customer Acquisition Cost)**: Tốn bao nhiêu tiền/công sức để có 1 user trả phí?
*   **LTV (Life Time Value)**: 1 user mang lại bao nhiêu doanh thu trước khi rời đi? (LTV phải > 3 lần CAC).
*   **MRR (Monthly Recurring Revenue)**: Doanh thu định kỳ hàng tháng.
*   **Churn Rate**: Tỉ lệ người dùng hủy đăng ký. Nếu > 10% / tháng, sản phẩm đang có vấn đề, dừng tìm khách mới, tập trung fix sản phẩm.

> "Ship fast. Fail fast. Iterate faster." Mọi đoạn code không phục vụ trực tiếp việc thu thập phản hồi hoặc MRR đều là code thừa.
