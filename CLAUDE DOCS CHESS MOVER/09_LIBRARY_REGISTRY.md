# 09 - Library Registry
**Version:** 1.1.0
**Last Updated:** 2025-10-10
**Last Research Date:** 2025-10-10
**Next Update Due:** 2025-11-10
**Purpose:** Comprehensive tracking of libraries - what's used, what's available, what's deprecated, and what's recommended

---

## ⚠️ **DO NOT MODIFY THIS DOCUMENT**

**This is a REFERENCE document. Claude Code should READ and FOLLOW this document, but NEVER modify it unless the user explicitly requests an update.**

**Exception:** Only modify if the user specifically asks: "Update the Claude DOCS" or "Modify 09_LIBRARY_REGISTRY.md"

**Note:** Consult this BEFORE adding any new dependency. Check if library is current, maintained, and recommended!

**🔄 AUTO-UPDATE:** Check if today's date is past "Next Update Due" date. If so, run WebSearch on all major libraries to update features, then set new "Next Update Due" to 30 days from today.

---

## 📋 HOW TO USE THIS REGISTRY

### Before Adding ANY Library:

1. **Check this registry** - Is it listed as recommended/deprecated?
2. **WebSearch** - "Is [library] still maintained in 2025?"
3. **Check alternatives** - Are there better options now?
4. **Verify bundle size** - Use bundlephobia.com
5. **Check security** - Any known vulnerabilities?

### Verification Commands:
```bash
# JavaScript/TypeScript
npm outdated
npm audit
npx depcheck

# Python
pip list --outdated
safety check

# Check bundle size
npx bundlephobia [package-name]
```

---

## 🔥 LATEST FEATURES (Researched 2025-10-10)

### Next.js 15 (Oct 2024) & Next.js 16 Beta (Oct 2025)
**Status:** ✅ Stable & Production-Ready

**Breaking Changes:**
- ❗ **Caching now opt-in by default** - fetch requests, GET Route Handlers, and client navigations are uncached by default (use `cache: 'force-cache'` to opt-in)
- React 19 support (stable)
- Turbopack now stable for both dev and production builds

**Performance:**
- 75% faster local server startup with Turbopack
- 95% faster code updates with Fast Refresh
- Turbopack is default bundler for all new projects
- Filesystem caching in development for significantly faster compile times

**New Features:**
- Static route indicator in development
- `unstable_after` API for executing code after response finishes
- `instrumentation.js` API (stable) for server lifecycle observability
- Improved hydration error messages

### Tailwind CSS 4.0 (2025)
**Status:** ✅ Stable & Production-Ready

**Performance:**
- Full builds up to 5x faster
- Incremental builds over 100x faster (measured in microseconds)
- 35% smaller installed size despite heavier native packages
- Rust-powered core for parallelizable operations

**New Features:**
- One-line setup: just `@import "tailwindcss"`
- Zero configuration - automatic content detection
- Native cascade layers (`@layer`)
- CSS `@property` for type-safe custom properties
- `color-mix()` for dynamic opacity adjustments
- Container queries in core with `@min-*` and `@max-*` variants
- Logical properties for RTL support
- Updated oklch color palette for wider gamut
- First-party Vite plugin with Lightning CSS integration

### SvelteKit & Svelte 5 (Oct 2024)
**Status:** ✅ Stable & Production-Ready

**Runes System (Major Overhaul):**
- New reactivity with `$state`, `$derived`, and `$effect`
- 15-30% smaller bundles
- Better tree-shaking
- Explicit, predictable reactivity
- Prevents unnecessary re-renders

**2025 Features:**
- Async Components (experimental, Aug 2025)
- Remote Functions for type-safe server RPC
- Vite 7 and Rolldown support
- Native WebSocket support in SvelteKit
- await expressions for async reactivity

### Supabase (2025)
**Status:** ✅ Stable & Production-Ready

**Realtime Enhancements:**
- Private and Public channel support
- Broadcast and Presence Authorization
- Fine-grain RLS checking for Realtime connections
- Database connection pool size configuration

**Database:**
- Geo-routing for Data API requests (Apr 2025)
- Dedicated Pooler (PgBouncer) for lower latency
- Database-triggered messaging for tens of thousands of users

**Developer Tools:**
- Official MCP server for AI tools (Cursor, Claude)
- Dashboard Edge Functions editor (create, test, deploy)
- Studio improvements (tabs in Table Editor, SQL Editor)
- shadcn components for auth, file upload, realtime, chat

**Auth:**
- Third-party auth with Clerk integration

### Tauri 2.0 (2024 Stable)
**Status:** ✅ Stable & Production-Ready

**Mobile Support:**
- Android and iOS support
- Seamless desktop-to-mobile porting
- Mobile native APIs: notifications, dialogs, NFC, barcode, biometric auth, clipboard, deep links

**Core Features:**
- Multiwebview support (unstable flag)
- Rewritten IPC layer with Raw Payloads
- New permission system (replaces allowlist)
- Hot module replacement on mobile devices

### Flutter 3.27 (Dec 2024) & Later Versions
**Status:** ✅ Stable & Production-Ready

**Performance:**
- Fixed compositor back pressure on iOS (consistent 120Hz)
- Impeller default on modern Android (compile-time shader building)
- Better caching for predictable performance
- Multi-threaded single-frame workloads

**Cupertino Widgets:**
- High fidelity CupertinoCheckbox and CupertinoRadio
- Customizable mouse cursors, semantic labels, thumb images, fill colors

**Developer Experience:**
- `spacing` parameter for Rows/Columns
- DevTools with experimental WebAssembly support
- Material Design 3 tokens (v6.1) applied
- Android 15+ edge-to-edge display

**Note:** Dart SDK versions before 3.0 will be dropped by early 2025

### TypeScript 5.7 (Nov 2024) & 5.8+
**Status:** ✅ Stable & Production-Ready

**Enhanced Type Safety:**
- Improved uninitialized variable detection (including nested functions)
- Stricter return type enforcement
- Implicit any errors for functions returning null/undefined with generic types
- Better computed property names as index signatures

**Module Improvements:**
- Stricter JSON import rules with `--module nodenext`
- Import assertions required for JSON files (aligning with Node.js ES modules)

**ECMAScript 2024 Support:**
- `Object.groupBy()` and `Map.groupBy()`
- Resizable and growable ArrayBuffer/SharedArrayBuffer types

### Semgrep (2025)
**Status:** ✅ Recommended - Critical for Security

**Latest Capabilities:**
- New JavaScript/TypeScript analysis engine (50+ frameworks)
- OWASP Top Ten vulnerability detection
- 25% reduction in false positives
- 250% increase in true positives
- AI-powered triage with Semgrep Assistant (20% noise reduction)
- Step-by-step remediation guidance (>80% actionable)
- Median CI scan time: 10 seconds
- SAST, SCA, and Secrets Detection in one platform

**Supported Frameworks:**
- Express, NestJS, React, Angular, and 50+ more

### Playwright 1.49+ & 1.52 (2025)
**Status:** ✅ Recommended - Best E2E Testing

**Latest Features:**
- Codegen auto-generates `toBeVisible()` assertions
- `expect(locator).toContainClass()` for class name assertions
- `locator.describe()` for trace viewer and reports
- `testProject.workers` to specify concurrent workers
- New headless mode using real Chrome browser
- MCP integration for AI agents (GitHub Copilot built-in)
- Auto-waiting for elements to be actionable
- Tracing with execution traces, videos, screenshots

### Vitest 3.0 (Jan 2025)
**Status:** ✅ Recommended - Fastest Unit Testing

**Performance:**
- 2-5x faster than traditional frameworks
- Test sharding for parallel execution across machines
- Optimized snapshot handling
- Better concurrent execution
- Suite-level test shuffling

**Features:**
- Individual test runs from UI
- Automatic scroll to failed tests
- Toggleable node_modules visibility
- Improved diffing for snapshots
- Smart watch mode (HMR-like)
- Benchmark testing built-in

## 🎯 RECOMMENDED TECH STACKS (By Project Type)

### Web App Stack (SaaS, Dashboards)
**Status:** ✅ Recommended for 2025

```yaml
Frontend Framework: Next.js 15+ (App Router) - Turbopack stable
Styling: Tailwind CSS 4.0+ - 5x faster builds, one-line setup
State Management: Zustand or TanStack Query
Forms: React Hook Form + Zod
UI Components: shadcn/ui or Radix UI
Testing: Playwright 1.49+ + Vitest 3.0+
Build Tool: Vite 6.0+ (or Next.js built-in Turbopack)
Auth: Supabase Auth or NextAuth.js 5+
Database ORM: Prisma 6+ or Drizzle
TypeScript: 5.7+ (stricter type safety)

Backend (if separate): FastAPI (Python) or tRPC 11+ (TypeScript)
Database: Supabase (with geo-routing) or Railway Postgres
Hosting: Vercel (frontend) + Railway (backend)
```

### Game Stack
**Status:** ✅ Recommended for 2025

```yaml
Frontend: SvelteKit (Svelte 5 with Runes) or Next.js 15+
Game Engine: Phaser 3.80+, Three.js r170+, or PixiJS 8+
State: Zustand 5+ (React) or Pinia (Svelte)
Realtime: Supabase Realtime (with Presence Auth) or Socket.IO 4+
Physics: Matter.js or Cannon.js
Testing: Playwright 1.49+ + Vitest 3.0+
Styling: Tailwind CSS 4.0+

Backend: FastAPI 0.115+ or Node.js + Express 5+
Database: Supabase (geo-routing) or Redis + Postgres
Hosting: Vercel + Railway or Cloudflare Pages
```

### Desktop App Stack
**Status:** ✅ Recommended for 2025

```yaml
Framework: Tauri 2.0 (Rust + Web) - Now with mobile support!
Frontend: Svelte 5 (Runes) or React 18.3+
Styling: Tailwind CSS 4.0+ (one-line setup)
Local DB: SQLite (via Tauri SQL plugin)
State: Zustand 5+ or Pinia 2+
Testing: Vitest 3.0+ + Playwright 1.49+
TypeScript: 5.7+ (stricter types)

Alternative: Electron 33+ (if need mature ecosystem)
```

### Mobile App Stack
**Status:** ✅ Recommended for 2025

```yaml
Cross-Platform: Flutter 3.27+ (Impeller rendering, 120Hz support)
State: Riverpod 2+ or Provider
Routing: go_router (latest)
Backend: Supabase (MCP support, geo-routing) or Firebase
Testing: flutter_test + integration_test
Note: Dart 3.0+ required (pre-3.0 dropped in 2025)

Alternative: React Native 0.76+ with Expo 52+
State: Zustand 5+
Navigation: React Navigation 7+
Animations: Reanimated 3+ (60fps)
Testing: Detox or Playwright

Alternative 2: Tauri 2.0 (mobile support for Android/iOS)
```

---

## 📚 LIBRARY STATUS LEGEND

- ✅ **Recommended** - Current, actively maintained, production-ready
- 🟡 **Use with Caution** - Stable but alternatives may be better
- ⚠️ **Deprecated** - Avoid for new projects
- ❌ **Do Not Use** - Outdated, security issues, or abandoned

---

## 🎨 FRONTEND LIBRARIES

### JavaScript Frameworks

#### React Ecosystem

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **React** | 18.3+ (19 in Next.js 15) | ✅ Recommended | UI library | Use with Next.js or Vite |
| **Next.js** | 15+ (16 beta available) | ✅ Recommended | Full-stack framework | Turbopack stable, uncached by default |
| **Vite** | 6.0+ | ✅ Recommended | Build tool | Fastest dev experience |
| **Create React App** | Any | ⚠️ Deprecated | Starter | Use Vite instead |
| **Gatsby** | 5+ | 🟡 Use with Caution | Static sites | Consider Astro instead |

#### Vue Ecosystem

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Vue** | 3.5+ | ✅ Recommended | UI library | Composition API |
| **Nuxt** | 3+ | ✅ Recommended | Full-stack framework | Similar to Next.js |
| **Pinia** | 2+ | ✅ Recommended | State management | Vuex replacement |
| **Vuex** | 4 | 🟡 Use with Caution | State (legacy) | Use Pinia instead |

#### Svelte Ecosystem

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Svelte** | 5+ | ✅ Recommended | UI library | Runes system, 15-30% smaller bundles |
| **SvelteKit** | 2+ | ✅ Recommended | Full-stack framework | Vite 7, WebSockets, Remote Functions |
| **Svelte Motion** | Latest | ✅ Recommended | Animations | Smooth transitions |

#### Other Frameworks

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Solid.js** | 1.9+ | ✅ Recommended | High performance UI | Similar to React |
| **Astro** | 4+ | ✅ Recommended | Content-focused sites | Islands architecture |
| **Remix** | 2+ | ✅ Recommended | Full-stack framework | Excellent UX |
| **Qwik** | 1+ | ✅ Recommended | Resumable apps | Future of SSR |
| **Angular** | 18+ | ✅ Recommended | Enterprise apps | TypeScript-first |

---

### Styling & UI

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Tailwind CSS** | 4.0+ | ✅ Recommended | Utility-first CSS | 5x faster, one-line setup, native layers |
| **shadcn/ui** | Latest | ✅ Recommended | Copy-paste components | Best with Tailwind |
| **Radix UI** | Latest | ✅ Recommended | Unstyled components | Accessible primitives |
| **Headless UI** | Latest | ✅ Recommended | Unstyled components | Tailwind team |
| **DaisyUI** | Latest | ✅ Recommended | Tailwind components | Pre-styled |
| **Material UI** | 6+ | ✅ Recommended | Component library | Material Design |
| **Chakra UI** | 2+ | ✅ Recommended | Component library | Great DX |
| **Ant Design** | 5+ | ✅ Recommended | Enterprise UI | Complete ecosystem |
| **Bootstrap** | 5+ | 🟡 Use with Caution | Classic UI | Outdated patterns |
| **Styled Components** | 6+ | 🟡 Use with Caution | CSS-in-JS | Tailwind better |
| **Emotion** | 11+ | 🟡 Use with Caution | CSS-in-JS | Tailwind better |

---

### State Management

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Zustand** | 5+ | ✅ Recommended | Client state | Simple, lightweight |
| **TanStack Query** | 5+ | ✅ Recommended | Server state | Best for API data |
| **Jotai** | 2+ | ✅ Recommended | Atomic state | Minimalist |
| **Recoil** | Latest | ✅ Recommended | Atomic state | Meta-backed |
| **Redux Toolkit** | 2+ | ✅ Recommended | Complex state | Boilerplate-free Redux |
| **Redux** | 5 | 🟡 Use with Caution | Legacy state | Use RTK instead |
| **MobX** | 6+ | ✅ Recommended | Observable state | Simple reactive |
| **XState** | 5+ | ✅ Recommended | State machines | Complex workflows |

---

### Forms & Validation

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **React Hook Form** | 7+ | ✅ Recommended | Forms | Best performance |
| **Zod** | 3+ | ✅ Recommended | Schema validation | TypeScript-first |
| **Yup** | 1+ | ✅ Recommended | Schema validation | Alternative to Zod |
| **Formik** | 2+ | 🟡 Use with Caution | Forms | RHF better |
| **Valibot** | Latest | ✅ Recommended | Validation | Zod alternative |

---

### Routing & Navigation

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **React Router** | 7+ | ✅ Recommended | Client routing | Industry standard |
| **TanStack Router** | Latest | ✅ Recommended | Type-safe routing | Modern alternative |
| **React Navigation** | 7+ | ✅ Recommended | React Native | Mobile navigation |

---

### Animation

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Framer Motion** | 11+ | ✅ Recommended | Animations | Best DX |
| **React Spring** | 9+ | ✅ Recommended | Physics-based | Smooth animations |
| **GSAP** | 3+ | ✅ Recommended | Complex animations | Industry standard |
| **AutoAnimate** | Latest | ✅ Recommended | Auto animations | Zero config |
| **Motion One** | Latest | ✅ Recommended | Web Animations API | Lightweight |

---

### Data Visualization

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **D3.js** | 7+ | ✅ Recommended | Custom viz | Full control |
| **Chart.js** | 4+ | ✅ Recommended | Simple charts | Easy to use |
| **Recharts** | 2+ | ✅ Recommended | React charts | D3-powered |
| **Visx** | Latest | ✅ Recommended | React viz | Airbnb |
| **Plotly.js** | Latest | ✅ Recommended | Scientific plots | Interactive |

---

### Testing (Frontend)

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Vitest** | 3.0+ | ✅ Recommended | Unit tests | 2-5x faster, test sharding, Jan 2025 |
| **Playwright** | 1.49+ (1.52 latest) | ✅ Recommended | E2E tests | AI MCP integration, real Chrome headless |
| **Testing Library** | Latest | ✅ Recommended | Component tests | User-centric |
| **Jest** | 29+ | ✅ Recommended | Unit tests | Still solid |
| **Cypress** | 13+ | 🟡 Use with Caution | E2E tests | Playwright better |

---

## 🔧 BACKEND LIBRARIES

### Python (FastAPI Stack)

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **FastAPI** | 0.115+ | ✅ Recommended | Web framework | Best Python API |
| **Pydantic** | 2+ | ✅ Recommended | Data validation | Auto docs |
| **SQLAlchemy** | 2+ | ✅ Recommended | ORM | Full-featured |
| **SQLModel** | Latest | ✅ Recommended | ORM | FastAPI-native |
| **Uvicorn** | Latest | ✅ Recommended | ASGI server | Production-ready |
| **Alembic** | Latest | ✅ Recommended | Migrations | SQLAlchemy migrations |
| **Flask** | 3+ | 🟡 Use with Caution | Micro framework | FastAPI better |
| **Django** | 5+ | ✅ Recommended | Full framework | Batteries included |
| **Django REST Framework** | 3+ | ✅ Recommended | REST API | Django extension |

---

### Node.js/TypeScript (Backend)

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Express** | 5+ | ✅ Recommended | Web framework | Minimal |
| **NestJS** | 10+ | ✅ Recommended | Enterprise framework | Angular-like |
| **Fastify** | 5+ | ✅ Recommended | Fast framework | Express alternative |
| **Hono** | Latest | ✅ Recommended | Edge framework | Ultra-fast |
| **tRPC** | 11+ | ✅ Recommended | Type-safe API | End-to-end types |
| **Prisma** | 6+ | ✅ Recommended | ORM | Best DX |
| **Drizzle** | Latest | ✅ Recommended | ORM | Prisma alternative |
| **Socket.IO** | 4+ | ✅ Recommended | WebSockets | Realtime |

---

### Database Clients

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Supabase JS** | 2+ | ✅ Recommended | Supabase client | MCP server, geo-routing, Presence Auth |
| **pg** | 8+ | ✅ Recommended | PostgreSQL | Node.js driver |
| **ioredis** | 5+ | ✅ Recommended | Redis | Best Redis client |
| **MongoDB Node** | 6+ | ✅ Recommended | MongoDB | Official driver |
| **Mongoose** | 8+ | ✅ Recommended | MongoDB ORM | Schema-based |

---

### Authentication

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Supabase Auth** | Latest | ✅ Recommended | Full auth | Managed solution |
| **NextAuth.js** | 5+ | ✅ Recommended | Next.js auth | OAuth support |
| **Passport** | Latest | ✅ Recommended | Node.js auth | Many strategies |
| **Auth0 SDK** | Latest | ✅ Recommended | Enterprise auth | Managed |
| **Clerk** | Latest | ✅ Recommended | User management | Full solution |

---

## 🎮 GAME DEVELOPMENT

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Phaser** | 3.80+ | ✅ Recommended | 2D games | Full-featured |
| **Three.js** | r170+ | ✅ Recommended | 3D graphics | Industry standard |
| **PixiJS** | 8+ | ✅ Recommended | 2D renderer | Fast rendering |
| **Babylon.js** | 7+ | ✅ Recommended | 3D engine | Complete engine |
| **Matter.js** | Latest | ✅ Recommended | 2D physics | Lightweight |
| **Cannon.js** | Latest | ✅ Recommended | 3D physics | Three.js compatible |
| **Rapier** | Latest | ✅ Recommended | Physics | Rust-based, fast |

---

## 📱 MOBILE LIBRARIES

### React Native

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Expo** | 52+ | ✅ Recommended | RN framework | Best DX |
| **React Native** | 0.76+ | ✅ Recommended | Mobile framework | New architecture |
| **Reanimated** | 3+ | ✅ Recommended | Animations | 60fps |
| **React Navigation** | 7+ | ✅ Recommended | Navigation | Official solution |

### Flutter

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Flutter** | 3.27+ (3.32 latest) | ✅ Recommended | Cross-platform | Impeller default, 120Hz, Dart 3.0+ required |
| **Riverpod** | 2+ | ✅ Recommended | State | Provider v2 |
| **go_router** | Latest | ✅ Recommended | Routing | Declarative |
| **Dio** | 5+ | ✅ Recommended | HTTP client | Feature-rich |

---

## 🖥️ DESKTOP LIBRARIES

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Tauri** | 2.0+ | ✅ Recommended | Desktop + Mobile | Rust + Web, Android/iOS support, permissions |
| **Electron** | 33+ | ✅ Recommended | Desktop apps | Mature ecosystem |
| **Neutralino** | Latest | ✅ Recommended | Lightweight desktop | Small bundle |

---

## 🧰 UTILITY LIBRARIES

### Date & Time

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **date-fns** | 4+ | ✅ Recommended | Date utilities | Modular |
| **Day.js** | 1+ | ✅ Recommended | Date utilities | Moment.js alternative |
| **Luxon** | 3+ | ✅ Recommended | Date utilities | Timezone-aware |
| **Moment.js** | Any | ⚠️ Deprecated | Date (legacy) | Use date-fns/Day.js |

### HTTP Clients

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Axios** | 1+ | ✅ Recommended | HTTP client | Feature-rich |
| **Ky** | 1+ | ✅ Recommended | HTTP client | Modern fetch |
| **ofetch** | Latest | ✅ Recommended | HTTP client | Universal |

### Utilities

| Library | Version | Status | Use Case | Notes |
|---------|---------|--------|----------|-------|
| **Lodash** | 4+ | 🟡 Use with Caution | Utilities | Native better |
| **Ramda** | Latest | ✅ Recommended | Functional utils | FP library |
| **Underscore** | Any | ⚠️ Deprecated | Utilities | Use Lodash/native |

---

## 🚨 DEPRECATED / AVOID

### JavaScript

| Library | Reason | Alternative |
|---------|--------|-------------|
| **Create React App** | Unmaintained | Vite, Next.js |
| **Moment.js** | Heavy, mutable | date-fns, Day.js |
| **Underscore** | Outdated | Native JS, Lodash |
| **Bower** | Obsolete | npm, yarn, pnpm |
| **Grunt** | Outdated | Vite, esbuild |
| **Gulp** | Outdated | Vite, esbuild |

### Python

| Library | Reason | Alternative |
|---------|--------|-------------|
| **Flask-RESTX** | Unmaintained | FastAPI |
| **Tornado** | Outdated patterns | FastAPI |
| **Requests** | Sync-only | httpx |

---

## 🔍 HOW TO VERIFY A LIBRARY (Checklist)

Before adding ANY library:

```bash
# 1. Check npm/PyPI page
https://www.npmjs.com/package/[name]
https://pypi.org/project/[name]

# 2. Check GitHub
- Last commit date (< 6 months old = good)
- Open issues count (< 100 = good)
- Weekly downloads (high = popular)

# 3. Check bundle size
npx bundlephobia [package]
# Aim for < 50kb gzipped

# 4. Security check
npm audit
pip-audit  # for Python

# 5. Check compatibility
npx taze  # check for updates
npm outdated

# 6. Use WebSearch (built-in, free)
"Is [library] still maintained in 2025? What are alternatives?"
```

---

## 📊 PROJECT-SPECIFIC REGISTRIES

### TacticsQuest (Chess Game)
```json
{
  "frontend": {
    "framework": "SvelteKit",
    "chess": "chess.js",
    "board": "chessboard.js or custom",
    "testing": "Playwright",
    "ui": "Tailwind CSS"
  },
  "backend": {
    "api": "Node.js Express or FastAPI",
    "database": "Supabase Postgres",
    "realtime": "Supabase Realtime"
  }
}
```

---

## 🔄 UPDATE SCHEDULE

**Claude Code should check library versions:**
- **Weekly:** `npm outdated` or `pip list --outdated`
- **Before new feature:** Verify library is still recommended
- **Monthly:** Run security audit (`npm audit`, `pip-audit`)
- **Quarterly:** Review and update this registry

---

## 🔗 EXTERNAL RESOURCES

- **npm trends:** https://npmtrends.com/
- **Bundlephobia:** https://bundlephobia.com/
- **StackShare:** https://stackshare.io/
- **State of JS:** https://stateofjs.com/
- **Awesome Lists:** https://github.com/sindresorhus/awesome

---

## 🤖 AUTOMATIC MONTHLY UPDATE PROCESS

**When:** Check if today's date > "Next Update Due" date at the top of this document

**Important:** Always use the CURRENT YEAR from the system date, not a hardcoded year!

**Process:**
1. Get current year from system date

2. Run WebSearch on each major library category using current year:
   - "Next.js latest version [CURRENT_YEAR] new features"
   - "Tailwind CSS latest version [CURRENT_YEAR] new features"
   - "SvelteKit latest version [CURRENT_YEAR] new features"
   - "Supabase latest version [CURRENT_YEAR] new features"
   - "Tauri latest version [CURRENT_YEAR] new features"
   - "Flutter latest version [CURRENT_YEAR] new features"
   - "TypeScript latest version [CURRENT_YEAR] new features"
   - "Semgrep latest version [CURRENT_YEAR] new features"
   - "Playwright latest version [CURRENT_YEAR] new features"
   - "Vitest latest version [CURRENT_YEAR] new features"

3. Update the "🔥 LATEST FEATURES" section with new information

4. Update version numbers in library tables

5. Update "Last Research Date" to today's date and "Next Update Due" (30 days from today)

6. Increment version number (e.g., 1.1.0 → 1.2.0)

7. Notify user: "📚 Library Registry updated with latest features as of [date]"

**Example:** If today is 2026-03-15, search for "Next.js latest version 2026 new features"

---

**Remember:** Always consult this registry BEFORE adding dependencies. When in doubt, use WebSearch to verify current best practices!
