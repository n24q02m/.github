# Web Next.js Static Export

Next.js 16+ với `output: "export"` → static HTML cho Cloudflare Pages.

## Cấu Trúc

```
apps/web/
├── package.json          # bun
├── next.config.ts
├── src/
│   ├── app/
│   │   ├── layout.tsx    # Root layout + providers
│   │   ├── page.tsx      # Landing page
│   │   ├── (auth)/       # Auth routes
│   │   ├── (dashboard)/  # App routes
│   │   └── (marketing)/  # SEO pages
│   ├── components/
│   │   ├── ui/           # shadcn/ui
│   │   └── features/     # Domain components
│   ├── lib/
│   │   ├── api/          # Orval-generated client
│   │   ├── firebase.ts   # Firebase Auth init
│   │   └── analytics.ts  # PostHog/Plausible
│   └── hooks/
├── public/
│   ├── llms.txt          # AI crawler file
│   ├── llms-full.txt     # AI crawler full
│   └── og-image.png
└── orval.config.ts
```

## Key Patterns

### Static Export Config

```typescript
// next.config.ts
const config: NextConfig = {
  output: "export",
  images: { unoptimized: true },
};
```

> **Giới hạn**: KHÔNG dùng Server Components, Server Actions, API Routes, Middleware rewrites, `next/headers`, `next/cookies`. Tất cả `"use client"`.

### Orval API Client → TanStack Query

```typescript
// orval.config.ts
export default defineConfig({
  api: {
    input: "../api/openapi.json",   // Từ FastAPI/Go API
    output: {
      target: "./src/lib/api/generated.ts",
      client: "react-query",
      mode: "tags-split",
    },
  },
});
```

```bash
bun run orval   # Generate hooks từ OpenAPI spec
```

Kết quả: `useGetProduct()`, `useListProducts()`, `useCreateProduct()` — auto-generated hooks.

### Staging Build Trick

```typescript
// next.config.ts
const config: NextConfig = {
  output: "export",
  basePath: process.env.NEXT_PUBLIC_ENV === "staging" ? "/staging" : "",
};
```

Staging và prod dùng chung Cloudflare Pages, phân biệt bằng basePath.

### Firebase Auth Client

```typescript
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";

const auth = getAuth(firebaseApp);
const signIn = () => signInWithPopup(auth, new GoogleAuthProvider());
```

### SEO Landing Pages

```tsx
// src/app/(marketing)/page.tsx
export const metadata: Metadata = {
  title: "Product - Headline mạnh",
  description: "Dưới 160 ký tự",
  openGraph: { images: ["/og-image.png"] },
};
```

## Deploy: Cloudflare Pages

```yaml
# GitHub Actions
- run: bun run build
- uses: cloudflare/wrangler-action@v3
  with:
    command: pages deploy out --project-name=${{ env.PROJECT_NAME }}
```

Branch deploy: `main` → production, `staging` → preview.
