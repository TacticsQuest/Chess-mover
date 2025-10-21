# 06 - Testing & Verification Strategy
**Version:** 1.0.0
**Last Updated:** 2025-10-10
**Purpose:** Comprehensive testing strategy for all project types with Claude Code-friendly approaches

---

## ⚠️ **DO NOT MODIFY THIS DOCUMENT**

**This is a REFERENCE document. Exception:** Only modify if user explicitly requests.

---

## 📋 TESTING PYRAMID

```
        /\
       /E2E\          Few (Critical user flows)
      /------\
     /Integration\    Some (Feature workflows)
    /------------\
   /  Unit Tests  \   Many (Individual functions)
  /----------------\
```

**Goal:** 80%+ code coverage, focus on critical paths

---

## 🧪 TEST TYPES

### 1. Unit Tests
**What:** Test individual functions/components in isolation
**When:** For every utility function, hook, service function
**Tools:** Vitest (preferred) or Jest

```typescript
// utils/format.test.ts
import { formatPercent } from './format';

describe('formatPercent', () => {
  it('formats decimal as percentage', () => {
    expect(formatPercent(0.685)).toBe('68.5%');
  });

  it('handles zero', () => {
    expect(formatPercent(0)).toBe('0.0%');
  });

  it('handles decimals parameter', () => {
    expect(formatPercent(0.12345, 2)).toBe('12.35%');
  });
});
```

### 2. Component Tests
**What:** Test UI components with Testing Library
**When:** For every component
**Tools:** @testing-library/react + Vitest

```typescript
// components/LeaderboardTable.test.tsx
import { render, screen } from '@testing-library/react';
import { LeaderboardTable } from './LeaderboardTable';

describe('LeaderboardTable', () => {
  const mockData = [
    { rank: 1, username: 'Alice', rating: 2800 },
    { rank: 2, username: 'Bob', rating: 2750 },
  ];

  it('renders leaderboard data', () => {
    render(<LeaderboardTable data={mockData} />);

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('2800')).toBeInTheDocument();
  });

  it('displays empty state when no data', () => {
    render(<LeaderboardTable data={[]} />);

    expect(screen.getByText(/no players found/i)).toBeInTheDocument();
  });
});
```

### 3. Integration Tests
**What:** Test multiple units working together
**When:** For critical workflows (auth flow, data submission)
**Tools:** Vitest + MSW (Mock Service Worker)

```typescript
// tests/integration/auth-flow.test.ts
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginPage } from '@/app/login/page';

describe('Authentication Flow', () => {
  it('logs in user successfully', async () => {
    const user = userEvent.setup();

    render(<LoginPage />);

    // Fill form
    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify redirect
    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard');
    });
  });
});
```

### 4. E2E Tests
**What:** Test complete user journeys in real browser
**When:** For critical paths only (login, checkout, core feature)
**Tools:** Playwright (preferred)

```typescript
// tests/e2e/leaderboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Leaderboard Feature', () => {
  test('displays top 10 players', async ({ page }) => {
    await page.goto('/leaderboard');

    // Wait for data to load
    await page.waitForSelector('table tbody tr');

    // Verify top 10 displayed
    const rows = await page.locator('table tbody tr').count();
    expect(rows).toBe(10);

    // Verify rank order
    const firstRank = await page.locator('table tbody tr:first-child td:first-child').textContent();
    expect(firstRank).toContain('1');
  });

  test('filters by time period', async ({ page }) => {
    await page.goto('/leaderboard');

    // Change filter
    await page.selectOption('select#timeframe', 'thisWeek');

    // Wait for re-fetch
    await page.waitForTimeout(1000);

    // Verify URL updated
    expect(page.url()).toContain('timeframe=thisWeek');
  });
});
```

---

## 📦 PROJECT-SPECIFIC TEST SETUPS

### Next.js + Vitest

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
```

```typescript
// tests/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

### Playwright Setup

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 13'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 🎯 TESTING CHECKLIST

### Before Starting Implementation:
- [ ] Write unit tests for utility functions (TDD)
- [ ] Write component tests with expected behavior
- [ ] Tests should FAIL (feature not implemented yet)

### After Implementation:
- [ ] All unit tests pass
- [ ] Write integration tests for workflows
- [ ] Write E2E tests for critical paths
- [ ] Run full test suite
- [ ] Generate coverage report (≥80%)

### Before PR/Deployment:
- [ ] All tests passing
- [ ] No skipped/disabled tests without justification
- [ ] New features have test coverage
- [ ] Coverage hasn't decreased
- [ ] E2E tests pass on staging

---

## 📊 TEST COMMANDS

```bash
# Run all tests
npm test

# Run unit tests only
npm test -- --testPathPattern=unit

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch

# Run E2E tests
npm run test:e2e

# Run E2E in UI mode (debugging)
npx playwright test --ui

# Run specific test file
npm test leaderboard.test.ts
```

---

## 🔗 RELATED DOCUMENTS

- [04_IMPLEMENTATION.md](04_IMPLEMENTATION.md) - TDD workflow
- [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md) - Quality standards

---

**Remember:** Tests are documentation. Write tests that explain what the code should do!
