# GitHub MCP Security - Quick Reference

---

## ?? Fix the Security Issue

```bash
./secure_mcp_config_update.sh
```

---

## ?? Documentation

1. **[READY_TO_RUN.md](./READY_TO_RUN.md)** - Complete execution guide (start here)
2. **[README.md](./README.md)** - Quick overview
3. **[secure_token_rotation_runbook.md](./secure_token_rotation_runbook.md)** - Comprehensive reference

---

## ?? What's in This Directory

| File | Purpose |
|------|---------|
| `secure_mcp_config_update.sh` | ? The secure method - run this |
| `READY_TO_RUN.md` | Complete step-by-step guide |
| `README.md` | Quick overview |
| `secure_token_rotation_runbook.md` | Detailed reference documentation |
| `INDEX.md` | This file - quick navigation |

---

## ? Quick Commands

```bash
# Fix the issue
./secure_mcp_config_update.sh

# Revoke old token
open https://github.com/settings/tokens

# Restart apps
killall Cursor && killall "Visual Studio Code"

# Check health
~/bin/cursor-mcp-health-check.sh
```

---

**That's it. Simple and secure.** ??
