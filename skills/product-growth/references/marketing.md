
# Growth & Marketing Operations

## Khi Nào Dùng

- Thiết kế landing page cho sản phẩm mới (PAS framework)
- Viết copy marketing, email tăng chuyển đổi
- Cài đặt và cấu hình Analytics (Posthog, Plausible)
- Tối ưu SEO cho website và content
- Lên chiến lược growth cho startup/micro-SaaS

> **Test Coverage**: ≥ 95% cho tất cả analytics integrations và tracking logic.

## 1. Copywriting Landing Page (Thiết Kế Tỉ Lệ Chuyển Đổi)

### Framework Cốt Lõi: PAS (Problem - Agitation - Solution)
Khi viết nội dung, **TUYỆT ĐỐI KHÔNG** dùng: "We provide the best X for Y", "Welcome to our platform".
- **Problem**: Chỉ thẳng vào nỗi đau hiện tại (VD: "Đang tốn 10 tiếng mỗi tuần làm báo cáo?").
- **Agitation**: Nhấn mạnh hậu quả nếu không thay đổi (VD: "Đồng nghiệp chê cười, trễ deadline, sếp mắng.").
- **Solution**: Giới thiệu sản phẩm như viên thuốc giảm đau ngay lập tức (VD: "Click 1 phát, báo cáo AI tự viết xong trong 5 giây.").

### Cấu Trúc Header (Hero Section)
- **H1 (Headline)**: Rõ ràng, đi thẳng vào giá trị. Không bóng bẩy, dùng chữ số nếu có.
- **H2 (Sub-headline)**: Giải thích ngắn gọn cách hoạt động hoặc xử lý sự nghi ngờ.
- **CTA (Nút bấm)**: Động từ mạnh. KHÔNG "Submit", "Learn More". Dùng "Get Started for Free", "Start Generating Now". Kèm theo `Micro-copy` bên dưới (Vd: *No credit card required. Cancel anytime.*).

## 2. AI-SEO & Semantic HTML (Tối Ưu Máy Chủ AI Tìm Kiếm)

### LLM / AI Search Engine Optimization
ChatGPT, Perplexity, Gemini đọc trang web của bạn.
- Cấu trúc thư mục rõ ràng: `/features`, `/pricing`, `/docs/api`.
- Header tags (H1, H2, H3) phải theo thứ tự hợp lý. Máy tính đọc thứ tự, người xem đọc kích cỡ.
- Dùng **Semantic Tags**: `<article>`, `<nav>`, `<aside>`, `<section>` thay vì `<div class="content">`.
- Trả lời thẳng câu hỏi (FAQ) bằng text rõ ràng: "What is [Product]? [Product] is a..." để LLM dễ lấy làm câu trả lời.
- **AI crawlers KHÔNG chạy JavaScript** — server-side rendering (SSR/SSG) là bắt buộc.

### robots.txt Cho AI Bots

```
# AI Search bots — CHO PHÉP để được trích dẫn
User-agent: GPTBot              # OpenAI — ChatGPT search
User-agent: ChatGPT-User        # ChatGPT browsing mode
User-agent: PerplexityBot       # Perplexity AI search
User-agent: ClaudeBot            # Anthropic Claude
User-agent: anthropic-ai         # Anthropic Claude (alternate)
User-agent: Google-Extended      # Google Gemini + AI Overviews
User-agent: Bingbot              # Microsoft Copilot (via Bing)
Allow: /

# Training-only crawlers — CHẶN (không ảnh hưởng citation)
User-agent: CCBot
Disallow: /
```

### GEO — Generative Engine Optimization (Princeton KDD 2024)

Xếp hạng phương pháp tăng visibility trên AI search:

| Phương pháp | Tăng visibility |
|-------------|:---------------:|
| Cite nguồn (thống kê, nghiên cứu) | +40% |
| Thêm số liệu thống kê cụ thể | +37% |
| Thêm trích dẫn chuyên gia | +30% |
| Giọng văn thẩm quyền (authoritative) | +25% |
| Cải thiện độ rõ ràng | +20% |
| Dùng thuật ngữ chuyên ngành đúng chỗ | +18% |
| Tối ưu fluency | +15-30% |
| ~~Keyword stuffing~~ | **-10%** |

> **Combo tối ưu**: Fluency + Statistics = maximum boost. Site ranking thấp được lợi nhiều nhất — tới **+115% visibility** khi thêm citations.

Đoạn tối ưu cho AI citation: **40-60 từ** (optimal cho snippet extraction). Tổng thể passage: **134-167 từ**.

### Platform-Specific AI SEO

Mỗi AI platform có tín hiệu xếp hạng riêng:

| Platform | Tín hiệu quan trọng nhất | Hành động |
|----------|--------------------------|-----------|
| **ChatGPT** | Content-answer fit (55%), Freshness (cập nhật <30 ngày = 3.2x) | Viết theo format ChatGPT trả lời, cập nhật thường xuyên |
| **Perplexity** | FAQ Schema JSON-LD, Public PDFs, Deep research | Thêm FAQ structured data, publish PDFs (whitepapers) |
| **Copilot** | Page speed <2s, LinkedIn/GitHub presence, IndexNow | Submit Bing Webmaster, dùng IndexNow, post LinkedIn |
| **Claude** | Brave Search backend, factual accuracy rất cao | Verify content trên search.brave.com, viết chính xác |
| **Google AIO** | E-E-A-T, Schema, Top-10 ranking (92% citations) | Schema markup, domain authority, experience signals |

### Content Types Được AI Trích Dẫn Nhiều Nhất

| Loại nội dung | Tỉ lệ trích dẫn |
|---------------|:----------------:|
| Bài so sánh (X vs Y) | ~33% |
| Hướng dẫn toàn diện | ~15% |
| Nghiên cứu gốc / data | ~12% |
| Danh sách best-of | ~10% |

**Không hiệu quả**: Blog generic, product page quảng cáo, gated content (AI không truy cập được).

### Brand Mentions > Backlinks (Ahrefs 12/2025, 75,000 brands)

Brand mentions tương quan **3x mạnh hơn** backlinks với AI visibility:

| Tín hiệu | Tương quan với AI citations |
|-----------|-----------------------------|
| YouTube mentions | ~0.737 (mạnh nhất) |
| Reddit mentions | Cao |
| Wikipedia | Cao |
| LinkedIn | Trung bình |
| Domain Rating (backlinks) | ~0.266 (yếu) |

### llms.txt (Chuẩn Mới Cho AI Crawlers)
- Đặt file `/llms.txt` và `/llms-full.txt` tại root domain.
- `llms.txt`: Tóm tắt ngắn gọn sản phẩm, links tài liệu chính, pricing summary.
- `llms-full.txt`: Nội dung đầy đủ (documentation, FAQ, use cases) cho AI crawl sâu.
- Format: Markdown thuần, KHÔNG dùng HTML/JavaScript. AI parsers đọc plain text tốt hơn.

```markdown
# Product Name

> Mô tả ngắn 1-2 câu về sản phẩm.

## Docs
- [Getting Started](https://example.com/docs/getting-started)
- [API Reference](https://example.com/docs/api)

## Pricing
- Free: ...
- Pro: $X/month
```

### Schema Markup (Cập Nhật 2025)

**Đã bị loại bỏ/hạn chế**:
- ~~HowTo~~ → Rich results bị xoá (9/2023)
- ~~FAQ~~ → Chỉ còn cho government và healthcare (8/2023)
- ~~SpecialAnnouncement~~ → Deprecated (7/2025)

**Vẫn hoạt động**: Product, Organization, Breadcrumb, Article, SoftwareApplication.

### Core Web Vitals (2025)

| Metric | Tốt | FID đã bị thay bởi INP (3/2024) |
|--------|-----|----------------------------------|
| LCP | ≤ 2.5s | Largest Contentful Paint |
| INP | ≤ 200ms | Interaction to Next Paint (thay FID) |
| CLS | ≤ 0.1 | Cumulative Layout Shift |

### Thẻ Meta Khắt Khe
- `title` & `description` cho `<head>`.
- `og:image`, `og:title`, `twitter:card` cho Social Sharing. Bắt buộc tạo placeholder hoặc ảnh tĩnh chất lượng cao.

```tsx
// Meta tags cho Landing Page (Next.js)
export const metadata: Metadata = {
  title: "Product Name - Giải quyết [vấn đề] trong 5 giây",
  description: "Mô tả ngắn gọn giá trị sản phẩm. Dưới 160 ký tự.",
  openGraph: {
    title: "Product Name - Headline mạnh",
    description: "Social proof + CTA",
    images: ["/og-image.png"],
  },
};
```

## 3. Analytics & Event Tracking (Đo Lường Sự Chuyển Đổi)

### Cài Đặt Công Cụ
- Dùng **PostHog** (Mạnh về Funnel, Session Replay) hoặc **Plausible** (Gọn, Tôn trọng Privacy, Không Cookie).
- Tránh xa Google Analytics (GA4) vì quá phức tạp cho MVP và block bởi ad-blocker.

### Standard Events
Khi code UI, **PHẢI** nhúng event:
- Nút bấm chính (CTA): `onClick={() => trackEvent('cta_clicked', { location: 'hero' })}`
- Đăng ký thành công: `trackEvent('user_signed_up', { plan: 'free' })`
- Bắt đầu Checkout: `trackEvent('checkout_started', { price_id: id })`
- Xem trang bảng giá: `trackEvent('page_view', { page: 'pricing' })`

## 4. MCP Server Marketing (Kênh Phân Phối Cho Developer Tools)

### Registries (Tự Động + Thủ Công)

| Registry | Loại | Cách submit |
|----------|------|-------------|
| **GitHub MCP Registry** | Tự động | `server.json` + CD workflow (`mcp-publisher` OIDC) |
| **Docker MCP Registry** | PR | Fork `docker/mcp-registry`, thêm `server.yaml`, tạo PR |
| **mcpservers.org** | Form | Submit thủ công qua web form |
| **npm / PyPI** | Tự động | CD workflow publish + keywords SEO |

### README Optimization

**Compatible With badges** — hiển thị tất cả MCP clients tương thích:
```markdown
[![Claude Desktop](https://img.shields.io/badge/Claude_Desktop-F9DC7C?logo=anthropic&logoColor=black)](#quick-start)
[![Claude Code](https://img.shields.io/badge/Claude_Code-000000?logo=anthropic&logoColor=white)](#quick-start)
[![Cursor](https://img.shields.io/badge/Cursor-000000?logo=cursor&logoColor=white)](#quick-start)
[![VS Code Copilot](https://img.shields.io/badge/VS_Code_Copilot-007ACC?logo=visualstudiocode&logoColor=white)](#quick-start)
[![Antigravity](https://img.shields.io/badge/Antigravity-4285F4?logo=google&logoColor=white)](#quick-start)
[![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-8E75B2?logo=googlegemini&logoColor=white)](#quick-start)
[![OpenAI Codex](https://img.shields.io/badge/Codex-412991?logo=openai&logoColor=white)](#quick-start)
[![OpenCode](https://img.shields.io/badge/OpenCode-F7DF1E?logoColor=black)](#quick-start)
```

**Cross-links table** — "Also by author" section link tới các server khác cùng tác giả.

### Community Channels

| Kênh | Strategy |
|------|----------|
| **Reddit r/mcp, r/MCPservers** | Post tổng hợp (1 bài cover nhiều servers), technical tone, include install commands |
| **Hacker News** | Show HN cho server nổi bật nhất, technical deep-dive |
| **dev.to / Hashnode** | Blog "My MCP Stack" — storytelling + code examples |
| **X/Twitter** | Thread series (1 server/tuần), GIF demos, tag @AnthropicAI @cursor_ai |
| **GitHub Discussions** | Enable trên mỗi repo, dùng cho Q&A + feature requests |

### Package Keywords (SEO)

Keywords bắt buộc cho npm `package.json` và PyPI `pyproject.toml`:
```
mcp, mcp-server, model-context-protocol, ai-agent, claude, cursor,
copilot, antigravity, codex, opencode, gemini-cli
```

### Content Template (Reddit All-in-One Post)

```markdown
Title: I built 5 open-source MCP servers for [use cases]

Body:
- Hook: 1-2 sentences about the problem
- Table: Server | Description | Install command
- Per server: 2-3 bullet points (key features)
- Links: GitHub repos, npm/PyPI, Docker
- CTA: "Star if useful, issues/PRs welcome"
```

## 5. Cold Email & Onboarding Email (Email Dẫn Dắt Người Dùng)
- **Tiêu đề**: Ngắn, như email gửi cho bạn bè (Vd: "Quick question about your report", KHÔNG viết hoa chữ cái đầu như báo mạng "Quick Question About Your Report").
- **Nội dung**: Giới hạn trong 3-4 câu. 1 CTA duy nhất. 

## 6. Referral Program (Tăng Trưởng Qua Giới Thiệu)

### Referral Loop

```
Trigger Moment → Share Action → Convert Referred → Reward → (Loop)
```

**Trigger timing** — hiển thị referral prompt ngay SAU:
- Moment "aha" đầu tiên (user nhận được giá trị lần đầu)
- Đạt milestone (VD: hoàn thành 10 task, xuất báo cáo đầu tiên)
- Nhận hỗ trợ tốt
- Gia hạn hoặc nâng cấp plan

### Cơ chế chia sẻ (xếp hạng theo hiệu quả)

1. In-product sharing (chuyển đổi cao nhất)
2. Personalized link
3. Email invitation
4. Social sharing
5. Referral code (hoạt động offline)

### Sizing thưởng

```
Max Referral Reward = (Customer LTV × Gross Margin) - Target CAC
```

- **B2B SaaS**: $50-500 hoặc 1-3 tháng miễn phí
- **Double-sided rewards** (cả 2 bên nhận): chuyển đổi cao hơn đáng kể

### Viral Coefficient

```
K = Invitations × Conversion Rate
K > 1 = Viral growth
```

| Mức | Referral Rate |
|-----|:-------------:|
| Tốt | 10-25% |
| Tuyệt vời | 25-50% |
| Ngoại lệ | 50%+ |

> Khách hàng được giới thiệu: **LTV cao hơn 16-25%**, churn thấp hơn 18-37%, giới thiệu tiếp 2-3x.

### Phòng Fraud

- Email verification bắt buộc
- Device fingerprinting
- Delayed reward (sau khi activation, không phải signup)
- Minimum activity threshold
- Trả thưởng bằng product credit (ít hấp dẫn fraudsters hơn tiền mặt)

## 7. In-Product Cross-Promotion (Quảng Bá Chéo Giữa Sản Phẩm)

### Paywall Trigger Points

4 loại trigger cho upgrade prompt:

| Loại | Khi nào | Pattern |
|------|---------|---------|
| **Feature Gate** | User click tính năng paid | Preview feature + "Unlock with Pro" |
| **Usage Limit** | Đạt giới hạn free tier | Progress bar 100% + upgrade path |
| **Trial Expiration** | Hết trial (cảnh báo: 7, 3, 1 ngày) | Tóm tắt giá trị đã nhận + "Keep access" |
| **Time-Based** | User dùng lâu, chưa upgrade | Highlight tính năng paid chưa dùng |

**Nguyên tắc**: Value Before Ask — user phải đã nhận giá trị trước. KHÔNG show upgrade prompt trong onboarding flow.

**Anti-patterns**: Ẩn nút close, copy gây áy náy, hỏi trước khi trao giá trị, hiển thị quá thường xuyên.

**Frequency rules**: Cool-down SAU khi dismiss = tính bằng ngày, KHÔNG phải giờ. Track annoyance signals.

### "Powered By" Marketing

Thêm "Powered by [Product]" badge vào output của sản phẩm → free impressions.
VD: Email footer, report watermark, exported file metadata.

### Cross-Product Links

| Vị trí | Format |
|--------|--------|
| README "Also by author" | Link table tới các sản phẩm khác |
| Dashboard sidebar | "Explore more tools" section |
| Documentation footer | Links tới sản phẩm liên quan |
| MCP server output | "Built with [Product]" mention |

### ORB Framework (Kênh Phân Phối)

| Kênh | Đặc điểm | Ví dụ |
|------|-----------|-------|
| **Owned** | Truy cập trực tiếp, không phụ thuộc algorithm | Email list, website, docs |
| **Rented** | Platform cung cấp visibility, bạn không kiểm soát | Twitter, Reddit, ProductHunt |
| **Borrowed** | Tận dụng audience của người khác | Guest posts, podcast, newsletter swaps |

> **Chiến lược**: Dùng Rented + Borrowed để drive traffic về Owned channels.

## 8. Churn Prevention (Cancel Flow)

### Dynamic Save Offers — khớp offer với lý do cancel

| Lý do cancel | Offer chính | Offer dự phòng |
|--------------|-------------|-----------------|
| Quá đắt | Giảm giá 20-30% (2-3 tháng) | Downgrade plan thấp hơn |
| Không dùng đủ | Pause 1-3 tháng | Onboarding session miễn phí |
| Thiếu tính năng | Preview roadmap + timeline | Workaround guide |
| Chuyển sang competitor | So sánh cạnh tranh + giảm giá | Feedback session |

> **60-80% người pause** cuối cùng quay lại active.
> **KHÔNG** giảm giá 50%+ (huấn luyện user cancel để lấy deal).

### Health Score (Dự Đoán Churn)

```
Health Score = Login frequency × 0.30 + Feature usage × 0.25
            + Support sentiment × 0.15 + Billing health × 0.15
            + Engagement × 0.15
```

**Tín hiệu nguy hiểm**: Data export = Critical (vài ngày trước cancel). Billing page visits tăng = High risk.

### Involuntary Churn — Dunning

Thất bại thanh toán = 30-50% tổng churn, nhưng dễ fix nhất:

```
Pre-dunning → Smart retry (24h, 3d, 5d, 7d) → Dunning emails → Grace period → Hard cancel
```

> **Dodo Payments** xử lý dunning tự động. Kiểm tra Dodo retry settings và dunning email templates. (Switched from Paddle 15/03/2026)

## 9. Programmatic SEO (pSEO)

### 12 Playbooks

| Playbook | Pattern | Ví dụ |
|----------|---------|-------|
| Comparisons | "[X] vs [Y]" | "notion vs obsidian" |
| Integrations | "[A] [B] integration" | "slack notion integration" |
| Personas | "[product] for [audience]" | "crm for real estate" |
| Glossary | "what is [term]" | "what is mcp" |

**Quy tắc**:
- Dùng subfolders, KHÔNG subdomains (subfolders hợp nhất domain authority)
- ≥ 30-40% nội dung phải genuinely unique giữa 2 trang pSEO bất kỳ
- Progressive rollout: Publish batches 50-100 trang, monitor indexing 2-4 tuần trước khi mở rộng
- Google Scaled Content Abuse policy: nội dung AI phải có E-E-A-T thực sự
- **Email Onboarding**: Drip campaign 3-7 ngày: Day 1 (Welcome + 1 quick win), Day 3 (Check-in, support), Day 7 (Hỏi phản hồi nếu user chưa active).
