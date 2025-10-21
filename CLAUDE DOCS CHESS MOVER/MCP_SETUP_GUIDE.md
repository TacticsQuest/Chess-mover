# MCP Setup Guide
**Last Updated:** 2025-10-10
**Purpose:** Quick guide to install and configure MCPs for all your projects

---

## ⚠️ **DO NOT MODIFY THIS DOCUMENT**

**This is a REFERENCE document. Exception:** Only modify if user explicitly requests.

---

## 🚀 QUICK START (5 Minutes)

### Step 1: Install Critical MCPs

```bash
# 1. Semgrep (Security - CRITICAL)
pip install semgrep

# Verify installation
semgrep --version

# 2. Playwright (Testing - HIGH)
npm install -g @playwright/test
npx playwright install

# Verify installation
npx playwright --version
```

### Step 2: Get API Keys

Visit these links and create API keys:

1. **WebSearch** (Research - CRITICAL)
   - ✅ Already built-in - no setup needed!
   - Use it for all research needs (FREE)

2. **GitHub** (Repo Management - HIGH)
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Scopes: Select `repo` and `workflow`
   - Generate and copy token

3. **Context7** (Documentation - HIGH)
   - Go to: https://context7.com/
   - Sign up and get API key
   - Copy the key

### Step 3: Set Environment Variables (Windows)

```powershell
# Open PowerShell as Administrator
# Set environment variables (persistent)

[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'ghp_your-token-here', 'User')
[System.Environment]::SetEnvironmentVariable('CONTEXT7_API_KEY', 'ctx7_your-key-here', 'User')

# Restart terminal
exit
```

### Step 4: Verify Setup

```powershell
# Open new PowerShell window
# Check environment variables are set

echo $env:GITHUB_TOKEN
echo $env:CONTEXT7_API_KEY

# Test Semgrep
semgrep --version

# Test Playwright
npx playwright --version

# Test WebSearch (built-in)
# Just use it in Claude Code - no setup needed!
```

---

## 📋 COMPLETE INSTALLATION CHECKLIST

### Critical (Install Now)
- [ ] Semgrep installed (`pip install semgrep`)
- [ ] WebSearch available (built-in - no setup!)
- [ ] GitHub token obtained and set
- [ ] Environment variables verified

### High Priority (Install Soon)
- [ ] Playwright installed (`npm install -g @playwright/test`)
- [ ] Context7 API key obtained and set
- [ ] Sentry account created (for production monitoring)

### Medium Priority (Install When Needed)
- [ ] Vibe Check API key (prevents over-engineering)
- [ ] Supabase MCP (if using Supabase)
- [ ] Linear MCP (already configured in TacticsQuest)

### Optional
- [ ] Pieces (local memory)
- [ ] Noteit (note-taking)

---

## 🔧 CONFIGURATION FILES

Your MCP configuration is centralized here:

```
C:\Users\David\Documents\Claude DOCS\
├── MCP_GLOBAL_CONFIG.json      ← All MCP configurations
├── .env.example                ← Template for API keys
├── .env                        ← Your actual API keys (create this)
└── MCP_SETUP_GUIDE.md          ← This file
```

### Creating Your .env File

```bash
# Copy the example
cd "C:\Users\David\Documents\Claude DOCS"
copy .env.example .env

# Edit .env and fill in your API keys
notepad .env
```

---

## 🎯 PER-PROJECT CONFIGURATION

For project-specific MCPs (like TacticsQuest):

### Example: TacticsQuest

```json
// C:\Users\David\Documents\GitHub\TacticsQuest\.mcp.json
{
  "mcpServers": {
    "linear": {
      "type": "http",
      "url": "https://mcp.linear.app/mcp"
    }
  }
}
```

### Example: Chess App with Supabase

```json
// C:\Users\David\Documents\GitHub\ChessApp\.mcp.json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://api.supabase.com/mcp",
      "auth": {
        "type": "bearer",
        "token": "${SUPABASE_SERVICE_ROLE_KEY}"
      }
    }
  }
}
```

And in project `.env.local`:
```bash
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...your-project-specific-key
```

---

## 🔍 TROUBLESHOOTING

### "Command not found: semgrep"

```bash
# Python/pip not installed or not in PATH
# Install Python first: https://www.python.org/downloads/

# Then install semgrep
pip install semgrep

# If still not working, use full path:
python -m pip install semgrep
```

### "Environment variable not set"

```powershell
# Check if variable exists
echo $env:PERPLEXITY_API_KEY

# If empty, set it again:
[System.Environment]::SetEnvironmentVariable('PERPLEXITY_API_KEY', 'your-key', 'User')

# IMPORTANT: Restart your terminal!
exit
# Open new terminal and check again
```

### "API key invalid"

- Double-check you copied the full key (no spaces)
- Verify key hasn't expired
- Check you're using the correct environment variable name
- Some APIs require key prefix (e.g., `sk-`, `ghp_`, `pplx-`)

---

## 📊 VERIFICATION TESTS

### Test Semgrep
```bash
cd "C:\Users\David\Documents\GitHub\TacticsQuest"
semgrep --config=auto --quiet .
# Should scan files and show results
```

### Test Playwright
```bash
cd "C:\Users\David\Documents\GitHub\TacticsQuest"
npx playwright test --list
# Should list available tests
```

### Test Environment Variables
```powershell
# Should output your keys
echo $env:PERPLEXITY_API_KEY
echo $env:GITHUB_TOKEN
echo $env:CONTEXT7_API_KEY
```

---

## 🎯 NEXT STEPS AFTER SETUP

1. **Test with TacticsQuest:**
   - Use Perplexity MCP to research a feature
   - Run Semgrep security scan
   - Use Playwright to test UI

2. **Start New Project:**
   - Follow `PROJECT_INITIALIZATION_TEMPLATE.md`
   - Configure project-specific MCPs
   - Reference global MCPs automatically

3. **Regular Maintenance:**
   - Check for MCP updates monthly
   - Rotate API keys periodically (security best practice)
   - Update `MCP_GLOBAL_CONFIG.json` when discovering new MCPs

---

## 🔗 RELATED DOCUMENTS

- [MCP_GLOBAL_CONFIG.json](MCP_GLOBAL_CONFIG.json) - All MCP configurations
- [08_MCP_TOOLS_REGISTRY.md](08_MCP_TOOLS_REGISTRY.md) - Detailed MCP documentation
- [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md) - How to use MCPs in workflow

---

## 🆘 GETTING HELP

### If you get stuck:

1. **Check official docs:**
   - Semgrep: https://semgrep.dev/docs/
   - Playwright: https://playwright.dev/
   - Perplexity: https://docs.perplexity.ai/

2. **Use Perplexity MCP to research:**
   - "How do I configure Semgrep for Next.js?"
   - "Playwright setup issues on Windows"

3. **Check Claude Code docs:**
   - https://docs.claude.com/en/docs/claude-code/mcp

---

**🎉 Setup complete! You're ready to use MCPs across all your projects!**

**Remember:** These MCPs will make development faster, safer, and more informed. Use Perplexity BEFORE coding, Semgrep BEFORE deploying, and Playwright for all UI testing.
