# 07 - Deployment & DevOps Guide
**Version:** 1.0.0
**Last Updated:** 2025-10-10
**Purpose:** Deployment strategies for Vercel, Railway, Cloudflare, and best practices

---

## ⚠️ **DO NOT MODIFY THIS DOCUMENT**

**This is a REFERENCE document. Exception:** Only modify if user explicitly requests.

---

## 🚀 RECOMMENDED HOSTING BY PROJECT TYPE

| Project Type | Frontend | Backend | Database | Why |
|--------------|----------|---------|----------|-----|
| Web App (SaaS) | Vercel | Railway | Supabase | Best DX, auto-scaling |
| Game | Cloudflare Pages | Railway | Supabase | Global edge, low latency |
| Desktop App | GitHub Releases | - | SQLite local | Native distribution |
| Mobile App | App Store / Google Play | Railway | Firebase/Supabase | Mobile-first |

---

## 📦 DEPLOYMENT WORKFLOWS

### Vercel (Next.js / SvelteKit)

**Setup:**
```bash
# Install Vercel CLI
npm i -g vercel

# Link project
vercel link

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

**Environment Variables:**
```bash
# Set via CLI
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add SUPABASE_SERVICE_KEY production

# Or via dashboard: vercel.com/project/settings/environment-variables
```

**Auto-Deploy via GitHub:**
```yaml
# Vercel automatically deploys:
# - main branch → Production
# - PR branches → Preview
# - Commits → Preview

# No configuration needed!
```

---

### Railway (Backend APIs / Databases)

**Setup:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

**Configuration:**
```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "npm start"
restartPolicyType = "on-failure"
```

**Environment Variables:**
```bash
# Set via CLI
railway variables set DATABASE_URL=postgres://...

# Or via dashboard
```

---

### Cloudflare Pages

**Setup:**
```bash
# Build static site
npm run build

# Deploy
npx wrangler pages deploy dist --project-name=my-app
```

**Configuration:**
```yaml
# wrangler.toml
name = "my-app"
compatibility_date = "2025-01-01"

[site]
bucket = "./dist"
```

---

## 🔒 PRE-DEPLOYMENT CHECKLIST

### Security
- [ ] All secrets in environment variables (not code)
- [ ] `.env` in `.gitignore`
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] CORS configured properly
- [ ] Rate limiting enabled
- [ ] Semgrep scan passed (0 critical/high)

### Performance
- [ ] Lighthouse score ≥90
- [ ] Images optimized (Next.js Image, Cloudflare Images)
- [ ] Bundle size acceptable (<500KB initial)
- [ ] Database indexed properly
- [ ] Caching configured (Redis/CDN)

### Testing
- [ ] All tests passing (unit + integration + E2E)
- [ ] Tested on staging environment
- [ ] Manual QA performed
- [ ] Load testing (if high traffic expected)

### Monitoring
- [ ] Error tracking configured (Sentry MCP)
- [ ] Logging configured (production logs)
- [ ] Analytics configured (optional)
- [ ] Health check endpoint exists

### Documentation
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] API documentation updated
- [ ] Deployment notes documented

---

## 🔄 CI/CD WORKFLOW

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
      - run: npm run build

  security:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: p/security-audit

  deploy:
    runs-on: ubuntu-latest
    needs: [test, security]
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## 📊 DEPLOYMENT MONITORING

### Health Check Endpoint

```typescript
// app/api/health/route.ts
export async function GET() {
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
    timestamp: new Date().toISOString(),
  };

  const allHealthy = Object.values(checks).every(c => c === true || typeof c === 'string');

  return Response.json(checks, {
    status: allHealthy ? 200 : 503,
  });
}
```

### Sentry Integration

```typescript
// lib/sentry.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
  beforeSend(event) {
    // Filter sensitive data
    if (event.request) {
      delete event.request.cookies;
    }
    return event;
  },
});
```

---

## 🚨 ROLLBACK PROCEDURE

If deployment causes issues:

1. **Immediate Rollback (Vercel):**
   ```bash
   vercel rollback
   # Or via dashboard: Deployments → Previous → Promote to Production
   ```

2. **Railway Rollback:**
   ```bash
   railway rollback
   # Or via dashboard: Deployments → Previous → Redeploy
   ```

3. **Investigate:**
   - Check Sentry for errors
   - Review deployment logs
   - Check recent commits
   - Run tests locally

4. **Fix & Redeploy:**
   - Fix issue in new branch
   - Run full test suite
   - Deploy to staging first
   - Deploy to production

---

## 🔗 RELATED DOCUMENTS

- [05_SECURITY_CHECKLIST.md](05_SECURITY_CHECKLIST.md) - Pre-deploy security
- [06_TESTING_VERIFICATION.md](06_TESTING_VERIFICATION.md) - Testing before deploy

---

**Remember:** Never deploy to production without testing on staging first!
