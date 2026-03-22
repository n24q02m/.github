
# Monetization & Payment Operations

## Khi Nao Dung

- Tich hop thanh toan Dodo Payments cho san pham moi
- Xay dung Webhook endpoint xu ly payment events
- Thiet ke database schema cho subscriptions
- Debug billing issues (double-charge, webhook failures)
- Setup Customer Portal cho quan ly subscription

> **Test Coverage**: >= 95% cho tat ca webhook handlers va payment logic.

## 1. Dodo Payments = Merchant of Record (Duy Nhat)

> Switched from Paddle on 15/03/2026. See `memory/payment-platform-decision.md` for rationale.

| Feature | Chi tiet |
|:--------|:---------|
| **Fee** | 4% + $0.40/txn (base) + 1.5% international |
| **Thue** | Tu dong thu VAT/GST 220+ quoc gia |
| **VN Seller** | Ho tro truc tiep (khong can US LLC) |
| **Fraud** | Tu dong xu ly chargebacks, disputes |
| **Multi-brand** | 1 account, moi app = 1 brand/business rieng |
| **DX** | MCP server, Expo/RN SDK, Go/TS/Python SDKs |

### Tai Sao Chi Dung Dodo Payments?

- **KHONG dung Apple IAP**: App khong dat link mua trong app. Web checkout tai website (mo hinh Netflix/Spotify)
- **US (05/2025)**: External Purchase Link cho phep, Apple KHONG thu commission (tam thoi, dang khang cao)
- **EU (DMA 06/2025)**: External payment cho phep, Apple thu 2-20% tuy tier
- **VN**: Chua co luat tuong tu -> app KHONG dat link mua trong app
- **KHONG dung Stripe**: VN merchant khong duoc ho tro truc tiep
- **KHONG dung RevenueCat**: Khong can IAP wrapper khi khong dung IAP
- **KHONG dung Paddle**: Multi-app management bat tien, DX kem hon Dodo

## 2. Kien Truc

```text
Web App (getaiora.com/pricing, klprism.com/pricing)
   -> Dodo Payments Checkout (SDK)
       -> Dodo xu ly thanh toan + thue + fraud
           -> Webhook -> Go API / FastAPI
               -> PostgreSQL (webhook_events + user subscription)
```

## 3. Webhook Handler

### 3 Lop Phong Thu (BAT BUOC)

```text
1. Signature Verification: Xac thuc Dodo webhook signature header
2. Idempotency: Luu event_id, skip neu da xu ly
3. Async Processing: Tra 200 ngay, xu ly background
```

### Go Handler (Aiora)

```go
func (h *WebhooksHandler) DodoPayments(c echo.Context) error {
    body, _ := io.ReadAll(c.Request().Body)
    sig := c.Request().Header.Get("Dodo-Signature") // verify exact header name from Dodo docs

    if !verifyDodoSignature(body, sig, h.webhookSecret) {
        return c.JSON(401, map[string]string{"error": "invalid signature"})
    }

    var event DodoEvent
    json.Unmarshal(body, &event)

    // Kiem tra idempotency
    if h.queries.EventExists(ctx, event.EventID) {
        return c.JSON(200, map[string]string{"status": "already_processed"})
    }

    h.queries.SaveEvent(ctx, event.EventID, event.EventType, body)
    go h.processEvent(event) // Xu ly async
    return c.JSON(200, map[string]string{"status": "ok"})
}
```

### Python Handler (KnowledgePrism)

```python
@app.post("/webhooks/dodo")
async def dodo_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Dodo-Signature")  # verify exact header name from Dodo docs

    if not verify_dodo_signature(body, sig, DODO_WEBHOOK_SECRET):
        raise HTTPException(401, "Invalid signature")

    event = json.loads(body)

    if await db.event_exists(event["event_id"]):
        return {"status": "already_processed"}

    await db.save_event(event["event_id"], event["event_type"], body)
    background_tasks.add_task(process_dodo_event, event)
    return {"status": "ok"}
```

## 4. Events Can Xu Ly

| Event | Hanh dong |
|:------|:----------|
| `subscription.activated` | Set plan_tier, luu dodo_customer_id |
| `subscription.updated` | Update plan (upgrade/downgrade) |
| `subscription.canceled` | Set plan = free khi het han |
| `subscription.past_due` | Gui email nhac update thanh toan |
| `transaction.completed` | Log payment, gui receipt |

## 5. Database Schema

```sql
ALTER TABLE users ADD COLUMN
    plan_tier TEXT DEFAULT 'free',           -- free, pro, team
    subscription_status TEXT DEFAULT 'none', -- none, active, past_due, canceled
    current_period_end TIMESTAMPTZ,
    dodo_customer_id TEXT;                   -- Dodo Payments customer ID
    -- NOTE: legacy column paddle_customer_id may exist, migrate data then drop

CREATE TABLE webhook_events (
    event_id TEXT PRIMARY KEY,               -- Dodo event ID
    event_type TEXT NOT NULL,
    user_id UUID REFERENCES users(id),
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 6. Chong That Thoat & Dunning

- Khi `payment_failed`: Gui email than thien, cap grace period 3-7 ngay
- Truoc gia han 3 ngay: Gui thong bao "Sap thu phi X dong"
- Dodo Payments has built-in retry logic for failed payments
- Neu khach yeu cau Refund: Xu ly qua Dodo Dashboard, KHONG tu xoa record

## 7. Checklist

- [ ] Dodo Payments account created, brands setup (1 per app)?
- [ ] Webhook endpoint voi 3 lop phong thu?
- [ ] DB schema (webhook_events + user plan fields)?
- [ ] Test webhook with Dodo sandbox/test mode?
- [ ] Idempotency verified: gui event 2 lan, chi xu ly 1 lan?
- [ ] Grace period cho subscription expiry?
- [ ] Dodo Payments production KYC (domain verify + tax)?
- [ ] Customer Portal link tren website?
- [ ] Test coverage >= 95%?
- [ ] Infisical secrets migrated from PADDLE_* to DODO_*?

## Migration from Paddle (15/03/2026)

| Step | Description | Status |
|------|-------------|--------|
| 1 | Update all documentation | DONE |
| 2 | Create Dodo account + 2 brands | TODO |
| 3 | Migrate Infisical secrets (PADDLE_* -> DODO_*) | TODO |
| 4 | Update Go webhook handler (Aiora) | TODO |
| 5 | Update Go webhook handler (KnowledgePrism) | TODO |
| 6 | Replace Paddle.js with Dodo SDK on /pricing | TODO |
| 7 | Update docker-compose env vars | TODO |
| 8 | E2E test checkout (sandbox) | TODO |
| 9 | Production KYC | TODO |
