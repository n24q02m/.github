# Mobile React Native Expo

Expo managed workflow, BUN only (KHÔNG npm/yarn/pnpm).

## Cấu Trúc

```
apps/mobile/
├── package.json          # bun
├── app.json              # Expo config
├── eas.json              # EAS Build profiles
├── app/
│   ├── _layout.tsx       # Root layout (providers)
│   ├── (tabs)/           # Tab navigation
│   ├── (auth)/           # Auth screens
│   └── (modals)/         # Modal screens
├── components/
│   ├── ui/               # Shared UI
│   └── features/         # Domain components
├── lib/
│   ├── api/              # Orval-generated (shared với web)
│   ├── firebase.ts       # Firebase Auth
│   ├── storage.ts        # MMKV async storage
│   └── analytics.ts
├── hooks/
└── assets/
```

## Key Patterns

### Package Manager: BUN ONLY

```bash
bun install         # KHÔNG npm install
bun add <package>   # KHÔNG npm add
bunx expo start     # KHÔNG npx expo start
```

### Orval Shared API Client

Mobile và Web dùng **chung** Orval config → cùng API hooks:

```typescript
// Shared orval.config.ts (root hoặc packages/api/)
// Output: TanStack Query hooks dùng được cả web và mobile
```

### Zustand + MMKV Persistence

```typescript
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { MMKV } from "react-native-mmkv";

const storage = new MMKV();

const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      setToken: (token: string) => set({ token }),
    }),
    {
      name: "auth-store",
      storage: createJSONStorage(() => ({
        setItem: (key, value) => storage.set(key, value),
        getItem: (key) => storage.getString(key) ?? null,
        removeItem: (key) => storage.delete(key),
      })),
    },
  ),
);
```

### Dodo Payments Checkout (Expo/RN SDK available, or web browser)

```typescript
import { openBrowserAsync } from "expo-web-browser";

const checkout = async (priceId: string) => {
  const url = `https://product.com/checkout?price=${priceId}&uid=${user.uid}`;
  await openBrowserAsync(url);
};
```

> Dodo Payments has native Expo/RN SDK available. Web browser checkout also works.
> Switched from Paddle 15/03/2026.

### EAS Build Profiles

```json
{
  "build": {
    "preview": { "distribution": "internal", "channel": "staging" },
    "production": { "distribution": "store", "channel": "production" }
  }
}
```

### Environment Variables

```bash
# .env.staging (safe to commit — public URLs only)
EXPO_PUBLIC_API_URL=https://staging-api.product.com
EXPO_PUBLIC_ENV=staging

# .env.production
EXPO_PUBLIC_API_URL=https://api.product.com
EXPO_PUBLIC_ENV=production
```

## Testing

```bash
bun test --coverage
# Coverage target: ≥ 95%
```
