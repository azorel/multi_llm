---
name: Agent Malfunction Report
about: Report when autonomous agents create chaotic files or break system organization
title: '[AGENT-MALFUNCTION] Agent created chaotic files'
labels: ['bug', 'agent-malfunction', 'cleanup-needed']
assignees: []
---

## 🚨 Agent Malfunction Report

**Agent Responsible:** (if known)

**Files Created:**
- List all emergency_*.py, quick_*.py, or random files created
- Include any backup files or test debris

**System Impact:**
- [ ] Created files outside core_system/
- [ ] Bypassed .gitignore protections  
- [ ] Created quick fixes instead of proper solutions
- [ ] Left behind abandoned files

**Evidence:**
```bash
# Paste output of: find . -name "emergency_*.py" -o -name "quick_*.py" -o -name "*backup*"

```

**Expected Behavior:**
All agent work should:
- Use the core_system/ directory structure
- Follow version control workflow
- Create proper solutions, not quick fixes
- Clean up after themselves

**Actual Behavior:**
<!-- Describe what the agent did instead -->

**Recovery Actions Needed:**
- [ ] Remove chaotic files
- [ ] Update .gitignore if needed
- [ ] Rebuild proper solution in core_system/
- [ ] Review agent instructions

## 🔧 Automated Cleanup

If this is a recurring issue, consider running:
```bash
# Remove all chaotic files
find . -name "emergency_*.py" -exec rm {} \;
find . -name "quick_*.py" -exec rm {} \;
find . -name "*backup*" -exec rm {} \;

# Reset to clean state
git checkout -- .
git clean -fd
```

## 📊 Prevention

To prevent future malfunctions:
1. Ensure agents are instructed to use core_system/
2. Verify .gitignore is comprehensive
3. Set up monitoring alerts for file creation outside core_system/
4. Review agent memory and instruction clarity