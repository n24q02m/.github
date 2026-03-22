
# Test Workflow Guide

## Khi Nào Dùng

- Viết unit tests theo TDD workflow (Red-Green-Refactor)
- Setup Playwright E2E tests với Page Objects pattern
- Tạo test factories và fixtures
- Cấu hình CI test pipeline
- Viết integration tests cho API endpoints
- Chạy live comprehensive test cho MCP servers

> **Test Coverage**: ≥ 95% cho tất cả test suites và test infrastructure.

## TDD Workflow (RED-GREEN-REFACTOR)

```
┌─────────────────────────────────────────────────────────────┐
│  1. RED: Write failing test first                           │
│     - Define expected behavior                              │
│     - Test should fail (no implementation yet)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  2. GREEN: Write minimal code to pass                       │
│     - Just enough to make test pass                         │
│     - Don't optimize yet                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  3. REFACTOR: Clean up while tests pass                     │
│     - Remove duplication                                    │
│     - Improve naming, structure                             │
│     - Tests must still pass                                 │
└─────────────────────────────────────────────────────────────┘
```

> **KHÔNG ĐƯỢC viết production code mà chưa có failing test.**

### Bảng Bác Bỏ Lý Do Bỏ Qua Test

| Lý do | Thực tế |
|-------|---------|
| "Quá đơn giản, không cần test" | Code đơn giản vẫn hỏng. Test tốn 30 giây. |
| "Test sau cũng được" | Test pass ngay = chứng minh không gì cả. |
| "Đã test thủ công rồi" | Test thủ công không lặp lại được, không có record. |
| "Xoá mấy tiếng code phí quá" | Sunk cost fallacy. Giữ code chưa verify = nợ kỹ thuật. |
| "Deadline gấp, không kịp test" | Không test → bug prod → fix lâu hơn gấp 10x. |
| "Chỉ fix bug nhỏ thôi" | Bug nhỏ không có test = bug nhỏ quay lại. |

---

## Test Types & Pyramid

```
           ┌─────────┐
           │  E2E    │  ← Playwright (few, slow, high confidence)
          ─┼─────────┼─
         ╱ │Integration│ ← API tests, DB tests (some)
        ─┼─┬─────────┬─┼─
       ╱   │  Unit   │   ← Fast, isolated (many)
      ─────┴─────────┴─────
```

| Type | Tool | Coverage Target |
|------|------|--------------------|
| Unit (Python) | pytest + **syrupy** (snapshot) | 80%+ |
| Unit (TS/JS) | bun test / vitest | 80%+ |
| Unit (Rust) | cargo test + **rstest** (parameterized) + **insta** (snapshot) | 80%+ |
| Unit/Integration (Go) | `go test` + **testify** + **uber-go/mock** | 80%+ |
| Integration | pytest + fixtures | Critical paths |
| E2E | Playwright | Happy paths |

> **BẮT BUỘC**:
> - **Python**: Dùng `pytest` VỚI `syrupy` cho snapshot tests. Snapshot tests giúp phát hiện regression trong output phức tạp (API responses, serialized data, etc.).
> - **Rust**: Dùng `cargo test` VỚI `rstest` cho parameterized tests và `insta` cho snapshot tests. `rstest` giúp viết test cases gọn hơn với fixtures và `#[case]` macro. **BẮT BUỘC** chạy `cargo clippy` (linting) và `rustfmt` (formatting) trước khi commit.
> - **Go**: Dùng `go test` VỚI `testify` cho assertions/mocking và `uber-go/mock` cho interface mocking. **BẮT BUỘC** chạy `golangci-lint` (linting) và `gofumpt` (formatting) trước khi commit.

---

## Test Factory Functions

### Python
```python
# tests/factories.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

@dataclass
class UserFactory:
    id: str = field(default_factory=lambda: str(uuid4()))
    email: str = field(default_factory=lambda: f"user_{uuid4().hex[:8]}@test.com")
    name: str = "Test User"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def build(self, **overrides) -> dict:
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }
        data.update(overrides)
        return data
    
    async def create(self, db, **overrides) -> User:
        data = self.build(**overrides)
        return await db.users.create(data)

# Usage
user = UserFactory().build(name="Custom Name")
db_user = await UserFactory().create(db, email="custom@test.com")
```

### TypeScript
```typescript
// tests/factories.ts
import { faker } from "@faker-js/faker";

export function createUserFactory(overrides?: Partial<User>): User {
  return {
    id: faker.string.uuid(),
    email: faker.internet.email(),
    name: faker.person.fullName(),
    createdAt: new Date(),
    ...overrides,
  };
}

export function createPostFactory(overrides?: Partial<Post>): Post {
  return {
    id: faker.string.uuid(),
    title: faker.lorem.sentence(),
    content: faker.lorem.paragraphs(3),
    authorId: faker.string.uuid(),
    ...overrides,
  };
}

// Usage
const user = createUserFactory({ name: "Custom Name" });
const post = createPostFactory({ authorId: user.id });
```

---

## Playwright E2E Testing

### Setup
```typescript
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["html", { outputFolder: "playwright-report" }],
    ["junit", { outputFile: "test-results/junit.xml" }],
  ],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
    { name: "mobile", use: { ...devices["iPhone 14"] } },
  ],
  webServer: {
    command: "bun run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
  },
});
```

### Page Objects
```typescript
// e2e/pages/LoginPage.ts
import { Page, Locator } from "@playwright/test";

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel("Email");
    this.passwordInput = page.getByLabel("Password");
    this.submitButton = page.getByRole("button", { name: "Sign in" });
    this.errorMessage = page.getByRole("alert");
  }

  async goto() {
    await this.page.goto("/login");
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }
}
```

### Test Example
```typescript
// e2e/auth.spec.ts
import { test, expect } from "@playwright/test";
import { LoginPage } from "./pages/LoginPage";

test.describe("Authentication", () => {
  test("successful login redirects to dashboard", async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login("user@test.com", "password123");
    
    await expect(page).toHaveURL("/dashboard");
    await expect(page.getByText("Welcome back")).toBeVisible();
  });

  test("invalid credentials show error", async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login("wrong@test.com", "wrongpassword");
    
    await loginPage.expectError("Invalid credentials");
  });
});
```

---

## Smart Error Grouping

### Python (pytest)
```python
# conftest.py
import pytest
from collections import defaultdict

class ErrorRegistry:
    def __init__(self):
        self.errors = defaultdict(list)
    
    def add(self, category: str, test_name: str, error: str):
        self.errors[category].append({
            "test": test_name,
            "error": error,
        })
    
    def report(self):
        for category, failures in self.errors.items():
            print(f"\n=== {category} ({len(failures)} failures) ===")
            for f in failures[:3]:  # Show first 3
                print(f"  - {f['test']}: {f['error'][:100]}")

error_registry = ErrorRegistry()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    if report.failed:
        # Categorize by error type
        error_type = type(call.excinfo.value).__name__
        error_registry.add(
            error_type,
            item.name,
            str(call.excinfo.value),
        )

def pytest_sessionfinish(session, exitstatus):
    error_registry.report()
```

### TypeScript (vitest)
```typescript
// vitest.setup.ts
import { afterAll } from "vitest";

const errorGroups = new Map<string, { test: string; error: string }[]>();

export function trackError(category: string, testName: string, error: Error) {
  if (!errorGroups.has(category)) {
    errorGroups.set(category, []);
  }
  errorGroups.get(category)!.push({
    test: testName,
    error: error.message,
  });
}

afterAll(() => {
  if (errorGroups.size === 0) return;
  
  console.log("\n=== Error Summary ===");
  for (const [category, failures] of errorGroups) {
    console.log(`\n${category} (${failures.length} failures):`);
    failures.slice(0, 3).forEach(f => {
      console.log(`  - ${f.test}: ${f.error.slice(0, 100)}`);
    });
  }
});
```

---

## Test Environments

### Local Environment
```yaml
# docker-compose.test.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_db
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data  # RAM disk for speed

  redis:
    image: redis:7
    ports:
      - "6380:6379"
```

```bash
# Run tests with local services
docker compose -f docker-compose.test.yml up -d
pytest --cov=src --cov-report=html
docker compose -f docker-compose.test.yml down
```

### CI Environment
```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v6
      - uses: jdx/mise-action@v2
      
      - name: Install dependencies
        run: uv sync
        
      - name: Run tests
        run: uv run pytest --cov=src --cov-report=xml
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          
      - name: Upload coverage
        uses: codecov/codecov-action@v6
        with:
          file: ./coverage.xml
```

---

## Workflow Template

```
## PAUSE HERE - Test Plan Review

Trước khi implement tests, review plan:

### Test Cases Identified:
1. [ ] Case 1: Description
2. [ ] Case 2: Description
3. [ ] Case 3: Edge case

### Test Strategy:
- Unit tests: X cases
- Integration tests: Y cases  
- E2E tests: Z cases

### Dependencies:
- [ ] Test fixtures needed
- [ ] Mock services needed
- [ ] Database seeding needed

---
[Proceed after user approval]
```

---

## Fixtures Best Practices

### Python (pytest)
```python
# conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    """Create isolated database session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    """Create test client with database session."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_external_api(mocker):
    """Mock external API calls."""
    return mocker.patch(
        "app.services.external_api.fetch",
        return_value={"status": "ok"},
    )
```

### TypeScript (vitest)
```typescript
// tests/setup.ts
import { beforeAll, afterAll, beforeEach } from "vitest";
import { setupServer } from "msw/node";
import { handlers } from "./mocks/handlers";

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// tests/mocks/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/users", () => {
    return HttpResponse.json([
      { id: "1", name: "Test User" },
    ]);
  }),
  
  http.post("/api/users", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: "2", ...body }, { status: 201 });
  }),
];
```

---

## Go Testing Examples

### Unit Test with testify/assert
```go
// user_service_test.go
package service_test

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCreateUser(t *testing.T) {
	t.Run("valid input creates user", func(t *testing.T) {
		svc := NewUserService(mockDB)
		user, err := svc.Create("test@example.com", "Test User")

		require.NoError(t, err)
		assert.Equal(t, "test@example.com", user.Email)
		assert.Equal(t, "Test User", user.Name)
		assert.NotEmpty(t, user.ID)
	})

	t.Run("duplicate email returns error", func(t *testing.T) {
		svc := NewUserService(mockDB)
		_, _ = svc.Create("dup@example.com", "First")
		_, err := svc.Create("dup@example.com", "Second")

		assert.ErrorIs(t, err, ErrDuplicateEmail)
	})
}
```

### testify/suite for Grouped Tests
```go
// order_service_test.go
package service_test

import (
	"testing"

	"github.com/stretchr/testify/suite"
)

type OrderServiceSuite struct {
	suite.Suite
	svc *OrderService
	db  *TestDB
}

func (s *OrderServiceSuite) SetupTest() {
	s.db = NewTestDB(s.T())
	s.svc = NewOrderService(s.db)
}

func (s *OrderServiceSuite) TearDownTest() {
	s.db.Cleanup()
}

func (s *OrderServiceSuite) TestCreateOrder() {
	order, err := s.svc.Create("user-1", []Item{{SKU: "abc", Qty: 2}})
	s.Require().NoError(err)
	s.Equal("user-1", order.UserID)
	s.Len(order.Items, 1)
}

func TestOrderService(t *testing.T) {
	suite.Run(t, new(OrderServiceSuite))
}
```

### Interface Mocking with uber-go/mock
```go
// Generate mock: mockgen -source=repo.go -destination=mock_repo.go -package=service_test

// repo.go
type UserRepository interface {
	FindByEmail(ctx context.Context, email string) (*User, error)
	Save(ctx context.Context, user *User) error
}

// user_service_test.go
package service_test

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"go.uber.org/mock/gomock"
)

func TestGetUser_WithMock(t *testing.T) {
	ctrl := gomock.NewController(t)

	mockRepo := NewMockUserRepository(ctrl)
	mockRepo.EXPECT().
		FindByEmail(gomock.Any(), "test@example.com").
		Return(&User{ID: "1", Email: "test@example.com"}, nil)

	svc := NewUserService(mockRepo)
	user, err := svc.GetByEmail(context.Background(), "test@example.com")

	assert.NoError(t, err)
	assert.Equal(t, "1", user.ID)
}
```

> **Go Linting/Formatting BẮT BUỘC**:
> - `golangci-lint run` -- chạy trước mỗi commit, cấu hình trong `.golangci.yml`.
> - `gofumpt -w .` -- format code nghiêm ngặt hơn `gofmt`. Cài qua `mise` hoặc `go install mvdan.cc/gofumpt@latest`.
> - CI phải chạy cả hai: `golangci-lint run && gofumpt -d . | diff - /dev/null`.

---

## Rust Testing Examples

### Unit Test with rstest (Parameterized)
```rust
// src/validator.rs
#[cfg(test)]
mod tests {
    use rstest::rstest;
    use super::*;

    #[rstest]
    #[case("user@example.com", true)]
    #[case("invalid-email", false)]
    #[case("", false)]
    #[case("a@b.c", true)]
    fn test_validate_email(#[case] input: &str, #[case] expected: bool) {
        assert_eq!(validate_email(input), expected);
    }
}
```

### rstest Fixtures
```rust
#[cfg(test)]
mod tests {
    use rstest::*;

    #[fixture]
    fn db() -> TestDb {
        TestDb::new_in_memory()
    }

    #[fixture]
    fn user(db: TestDb) -> User {
        db.create_user("test@example.com", "Test User")
    }

    #[rstest]
    fn test_user_creation(user: User) {
        assert_eq!(user.email, "test@example.com");
        assert_eq!(user.name, "Test User");
        assert!(!user.id.is_empty());
    }

    #[rstest]
    fn test_user_update(user: User, db: TestDb) {
        let updated = db.update_user(&user.id, "New Name").unwrap();
        assert_eq!(updated.name, "New Name");
    }
}
```

### Snapshot Testing with insta
```rust
#[cfg(test)]
mod tests {
    use insta::assert_json_snapshot;
    use insta::assert_snapshot;

    #[test]
    fn test_serialize_user() {
        let user = User {
            id: "fixed-id".to_string(),
            email: "test@example.com".to_string(),
            name: "Test User".to_string(),
        };
        // Snapshot stored in snapshots/ directory, auto-created on first run
        assert_json_snapshot!(user, @r###"
        {
          "id": "fixed-id",
          "email": "test@example.com",
          "name": "Test User"
        }
        "###);
    }

    #[test]
    fn test_render_template() {
        let output = render_welcome_email("Test User");
        // Use `cargo insta review` to accept/reject snapshot changes
        assert_snapshot!(output);
    }
}
```

> **Rust Linting/Formatting BẮT BUỘC**:
> - `cargo clippy -- -D warnings` -- chạy trước mỗi commit, treat warnings as errors.
> - `rustfmt --check .` -- kiểm tra formatting. Dùng `cargo fmt` để tự động fix.
> - CI phải chạy cả hai: `cargo clippy -- -D warnings && cargo fmt -- --check`.

---

## MCP Server Live Testing

> **Khi nào áp dụng**: Khi build/cải tiến MCP server. Xem thêm `mcp-server` skill Phase 5.

### Tại sao Unit Tests KHÔNG đủ cho MCP Server

MCP server có đặc điểm khác web app thông thường:
- **Tool dispatch logic** (`match action:`) cần test qua MCP protocol, không chỉ function call
- **Environment-dependent behavior**: paths (`~` expansion), API keys, network access
- **Server process state**: cached connections, singleton instances, startup/shutdown lifecycle
- **Client-server boundary**: serialization, error format, timeout behavior

**Ví dụ thực tế**: Bug `Path("~/.wet-mcp/downloads").resolve()` (thiếu `.expanduser()`) chỉ xảy ra khi server chạy với default config. Unit tests dùng `tmp_path` (absolute path) nên không phát hiện.

### Test Layers cho MCP Server

```
┌─────────────────────────────────────────────────┐
│  Live Comprehensive Test (Phase 5)              │  ← Gọi thực qua MCP protocol
│  Mỗi tool × mỗi action × 3 categories          │     Happy + Error + Security
├─────────────────────────────────────────────────┤
│  Integration Test (pytest -m integration)       │  ← Gọi function trực tiếp
│  Real DB, real network, real filesystem          │     với real dependencies
├─────────────────────────────────────────────────┤
│  Unit Test (pytest)                             │  ← Mock everything
│  Isolated, fast, high coverage                   │     Test logic only
└─────────────────────────────────────────────────┘
```

### Live Test Execution Pattern

```python
# Gọi qua MCP client (hoặc trực tiếp qua tool name trong AI assistant)

# 1. Build matrix từ help tool
help_overview = await help()  # → list of tools
for tool_name in tools:
    help_detail = await help(tool_name=tool_name)  # → list of actions

# 2. Execute happy path (song song khi có thể)
results = {
    "search.search": await search(action="search", query="test"),
    "search.research": await search(action="research", query="test"),
    "extract.extract": await extract(action="extract", urls=["https://httpbin.org/html"]),
    # ... mỗi tool × mỗi action
}

# 3. Verify PASS/FAIL criteria
for key, result in results.items():
    assert not result.startswith("Error:"), f"FAIL: {key} → {result[:100]}"

# 4. Execute error path
error_results = {
    "search.missing_query": await search(action="search"),  # no query
    "config.invalid_key": await config(action="set", key="invalid"),
    # ...
}
for key, result in error_results.items():
    assert "Error" in result, f"FAIL: {key} should return error"
```

### Checklist bổ sung cho MCP Server

- [ ] Live test coverage matrix built (tất cả tools × actions)?
- [ ] Happy path 100% PASS?
- [ ] Error path ≥1 test/tool?
- [ ] Security boundary tested (SSRF, path traversal)?
- [ ] Post-deploy version verified?
- [ ] Results documented với evidence?

---

## Checklist

- [ ] TDD workflow (RED-GREEN-REFACTOR) followed?
- [ ] Test pyramid balanced (Unit > Integration > E2E)?
- [ ] Factory functions for test data?
- [ ] Page Objects for Playwright E2E?
- [ ] Smart error grouping configured?
- [ ] Local test environment với Docker Compose?
- [ ] CI workflow với service containers?
- [ ] Coverage reporting configured?
- [ ] Fixtures properly scoped và isolated?
- [ ] Mock external dependencies?
- [ ] Python: pytest + syrupy cho snapshot tests?
- [ ] Rust: cargo test + rstest (parameterized) + insta (snapshot)?
- [ ] Rust: cargo clippy + rustfmt chạy trước commit?
- [ ] Go: go test + testify + uber-go/mock?
- [ ] Go: golangci-lint + gofumpt chạy trước commit?
- [ ] MCP Server: Live comprehensive test passed (nếu applicable)?
