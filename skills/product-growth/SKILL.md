---
name: product-growth
description: "Product, Growth, Marketing, Monetization, Project Management. MVP scoping, pricing, validation, SEO, GEO, PAS copywriting, Dodo Payments, webhooks, subscriptions, Notion task tracking."
---

# Product & Growth

## Khi nao dung

- Danh gia y tuong san pham moi, MVP scoping (duoi 2 tuan)
- Chien luoc gia (Pricing): Free/Pro/Team tiers, value-based
- Validate nhu cau: fake door, pre-sale, PostHog analytics
- Landing page: PAS framework (Problem-Agitation-Solution)
- SEO: AI-SEO, GEO (Generative Engine Optimization), llms.txt
- Copywriting: email, CTA, referral program, churn prevention
- Analytics: PostHog (funnel, session replay), Plausible (privacy-first)
- Dodo Payments: web checkout, webhook handlers, idempotency
- Subscription management: DB schema, dunning, grace period
- Notion project management: task tracking, session workflow, chong xao nhang
- MCP server marketing: registries, README optimization, community channels

## References (doc on demand)

- `references/product-sense.md` -- Idea validation, MVP scoping, pricing strategy, startup metrics (CAC/LTV/MRR/Churn)
- `references/marketing.md` -- PAS copywriting, AI-SEO, GEO, analytics, MCP marketing, referral, churn prevention, pSEO
- `references/monetization.md` -- Dodo Payments (MoR), webhook handlers (Go/Python), DB schema, dunning, migration from Paddle
- `references/notion-pm.md` -- Notion project management via better-notion-mcp, session workflow, task tracking

Doc reference file tuong ung TRUOC KHI bat dau lam viec tren topic do.

## Quy tac chung

- **Dodo Payments** la nen tang thanh toan DUY NHAT (KHONG Stripe/RevenueCat/Apple IAP).
- Web checkout tai website (mo hinh Netflix/Spotify). App KHONG dat link mua trong app.
- Webhook: 3 lop phong thu (Signature Verification + Idempotency + Async Processing).
- KHONG dung "Lorem Ipsum". Luon sinh du lieu gia thuc te va co ngu canh.
- KHONG viet copy may moc ("Welcome to our platform"). Dung copy ngan gon, truc dien.
- Test Coverage >= 95% cho tat ca webhook handlers, analytics integrations, automation scripts.
