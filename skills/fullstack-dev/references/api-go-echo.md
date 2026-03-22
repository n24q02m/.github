# API Go Echo (Core/CRUD Services)

Dùng cho high-performance CRUD endpoints, public-facing APIs.

## Cấu Trúc

```
apps/go-api/
├── go.mod
├── go.sum
├── Dockerfile
├── cmd/
│   └── server/
│       └── main.go         # Entry point
├── internal/
│   ├── config/
│   │   └── config.go       # Env config
│   ├── handler/
│   │   ├── health.go       # Health check
│   │   └── product.go      # Domain handlers
│   ├── middleware/
│   │   ├── auth.go         # Firebase token validation
│   │   └── cors.go
│   ├── model/
│   │   └── product.go      # DB models (sqlc-generated)
│   ├── repository/
│   │   └── queries.sql.go  # sqlc-generated
│   └── service/
│       └── product.go      # Business logic
├── db/
│   ├── migrations/         # golang-migrate
│   ├── queries/            # sqlc SQL queries
│   └── sqlc.yaml
└── tests/
```

## Patterns

### sqlc — Type-safe SQL

```sql
-- db/queries/products.sql

-- name: GetProduct :one
SELECT * FROM products WHERE id = $1;

-- name: ListProducts :many
SELECT * FROM products WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2;

-- name: CreateProduct :one
INSERT INTO products (user_id, name, description)
VALUES ($1, $2, $3) RETURNING *;
```

```bash
# Generate Go code từ SQL
sqlc generate
```

### golang-migrate

```bash
# Tạo migration mới
migrate create -ext sql -dir db/migrations -seq add_products_table

# Chạy migration
migrate -source file://db/migrations -database "$DATABASE_URL" up
```

### Echo Handler Pattern

```go
func (h *Handler) GetProduct(c echo.Context) error {
    id, err := uuid.Parse(c.Param("id"))
    if err != nil {
        return echo.NewHTTPError(http.StatusBadRequest, "invalid id")
    }
    product, err := h.queries.GetProduct(c.Request().Context(), id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return echo.NewHTTPError(http.StatusNotFound, "not found")
        }
        return echo.NewHTTPError(http.StatusInternalServerError)
    }
    return c.JSON(http.StatusOK, product)
}
```

### Firebase Auth Middleware

```go
func AuthMiddleware(firebaseApp *firebase.App) echo.MiddlewareFunc {
    client, _ := firebaseApp.Auth(context.Background())
    return func(next echo.HandlerFunc) echo.HandlerFunc {
        return func(c echo.Context) error {
            token := strings.TrimPrefix(c.Request().Header.Get("Authorization"), "Bearer ")
            decoded, err := client.VerifyIDToken(c.Request().Context(), token)
            if err != nil {
                return echo.NewHTTPError(http.StatusUnauthorized)
            }
            c.Set("uid", decoded.UID)
            return next(c)
        }
    }
}
```

### Structured Logging (slog)

```go
slog.Info("Product created", "user_id", uid, "product_id", product.ID)
slog.Error("DB query failed", "error", err, "query", "GetProduct")
```

## Testing

```bash
go test ./... -v -cover -coverprofile=coverage.out
go tool cover -func=coverage.out
# Coverage target: ≥ 95%
```

## Deploy

Binary rất nhẹ (~40MB RAM), memory limit 0.125G-0.25G là đủ.

```yaml
services:
  go-api:
    build: .
    container_name: oci-<product>-go-api
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 0.25G
    networks:
      - oci-network
```
