---
description: Save important context to project memory for future sessions
agent: build
---

# Learn Command - Save Persistent Memory

Save important context, decisions, and patterns to your project memory file.

## Your Task

1. **Identify project name**: Use the project folder name from working directory
2. **Read current memory**: Check `.opencode/memory/{PROJECT_NAME}.md`
3. **Identify new context**: What's important to remember from this session?
4. **Write to memory**: Append new section with today's learnings

## What to Save

Save information that would be valuable in future sessions:
- Project purpose and architecture decisions
- Custom patterns or conventions discovered
- Important bug fixes or workarounds
- Workflow preferences specific to this project
- Open issues or pending decisions
- Key configuration changes made
- Lessons learned from debugging

## Memory File Location

`.opencode/memory/{PROJECT_NAME}.md`

Example: For DRIPE project, file is `.opencode/memory/DRIPE.md`

## Output Format

Append this section to the memory file:

```markdown
## Session: [YYYY-MM-DD]

### What We Did
- [Summary of session work]

### Key Learnings
- [Important things to remember]
- [Patterns discovered]
- [Configuration changes]

### For Next Session
- [Open issues]
- [Pending decisions]
- [Continue from...]
```

## Important Rules

- Read the existing memory file FIRST before writing
- Don't duplicate information already in memory
- Keep entries concise and actionable
- Focus on context that would be lost without it
- Use today's date for the session header
- Preserve existing sections - only append new ones

## User Arguments

If `$ARGUMENTS` is provided, use it as context about what to remember:
- Direct notes: "bug fix for X was tricky"
- Context summary: "decided to use Y approach"
- Reminder: "need to check Z next time"

If no arguments provided, ask the user what they want to remember.

---

**TIP**: Use `/learn` at natural stopping points to save progress.
