# Changes Reference: Memory System & Model Fixes

## Summary of Changes Made

### 1. Model Configuration Fix (CRITICAL)

**Issue:** Setting `model` at `agent.*.model` level causes validation errors when switching agents via tab.

**Root Cause:** OpenCode validates `agent.*.model` stricter than root-level `model`.

**Solution:** Comment out or remove model from agent configurations. Use only root-level `model`.

```json
// BEFORE (causes errors):
"agent": {
  "build": {
    "model": "anthropic/claude-sonnet-4-5"  // ❌ ERROR on tab-switch
  }
}

// AFTER (works):
"agent": {
  "build": {
    // model not specified - uses root level
  }
}
```

### 2. Learn Command Updated in `opencode.json`
```json
"learn": {
  "description": "Save important context to project memory",
  "template": "{file:commands/learn.md}\n\n$ARGUMENTS",
  "agent": "build"
}
```

### 3. Memory File Created
**Path:** `.opencode/memory/DRIPE.md`

Contains:
- Project context template
- Session-based sections
- Auto-loaded on every session start

### 4. Commands/Learn.md Rewritten
Now saves context to memory file instead of just extracting patterns.

### 5. Instructions Updated
- Added Memory System section to `instructions/INSTRUCTIONS.md`
- Added `.opencode/memory/DRIPE.md` to `opencode.json` instructions array

---

## Replication Checklist for Other Projects

### CRITICAL: Agent Model Configuration

**DO NOT set `model` at `agent.*.model` level** - this causes validation errors when switching agents.

Instead:
- Set model only at root level (`model`, `small_model`)
- Leave agent model fields commented or removed

This is a known OpenCode validation quirk.

### Required Changes

#### 1. Agent Model Configuration (MUST DO)
**File:** `.opencode/opencode.json`

Find and replace:
```
"model": "anthropic/claude-sonnet-4-5"
→ "model": "anthropic/claude-sonnet-4-5-20250929"

"model": "anthropic/claude-opus-4-5"
→ "model": "anthropic/claude-opus-4-5-20251101"

"model": "anthropic/claude-haiku-4-5"
→ "model": "anthropic/claude-haiku-4-5-20251001"
```

#### 2. Create Memory Directory and File
```bash
mkdir -p .opencode/memory
```

Create `.opencode/memory/{PROJECT_NAME}.md`:
```markdown
# {PROJECT_NAME} Project Memory

> Persistent context loaded on every session start
> Add important context with `/learn` during or after sessions

---

## Session: [DATE]

### Project Context
- [Description of project purpose]

### Key Decisions
- [Architectural decisions]

### Custom Patterns
- [Project-specific conventions]

### Open Issues
- [Things to remember for next session]

---

*This file is auto-loaded on session start. Use `/learn` to add new context.*
```

#### 3. Update Learn Command
**File:** `.opencode/commands/learn.md`

Replace with memory-writing command (see this project's version).

#### 4. Update opencode.json
Add to `instructions` array:
```json
".opencode/memory/{PROJECT_NAME}.md"
```

Update `learn` command:
```json
"learn": {
  "description": "Save important context to project memory",
  "template": "{file:commands/learn.md}\n\n$ARGUMENTS",
  "agent": "build"
}
```

#### 5. Update INSTRUCTIONS.md
Append Memory System section (see this project's version for reference).

---

## Quick Setup Script

For new projects, run:
```bash
PROJECT_NAME=$(basename "$PWD")
mkdir -p .opencode/memory

cat > ".opencode/memory/${PROJECT_NAME}.md" << 'EOF'
# PROJECT_NAME Project Memory

> Persistent context loaded on every session start
> Add important context with `/learn` during or after sessions

---

## Session: [DATE]

### Project Context
- [Description of project purpose]

### Key Decisions
- [Architectural decisions]

### Custom Patterns
- [Project-specific conventions]

### Open Issues
- [Things to remember for next session]

---

*This file is auto-loaded on session start. Use `/learn` to add new context.*
EOF

# Replace PROJECT_NAME placeholder
sed -i "s/PROJECT_NAME/${PROJECT_NAME}/g" ".opencode/memory/${PROJECT_NAME}.md"

echo "✓ Memory file created at .opencode/memory/${PROJECT_NAME}.md"
echo "✓ Copy learn.md and update INSTRUCTIONS.md from DRIPE project"
```

---

## Valid Model Names (for reference)

### Anthropic Models (confirmed valid)
- `anthropic/claude-sonnet-4-6` ✓
- `anthropic/claude-sonnet-4-5-20250929` ✓
- `anthropic/claude-opus-4-6` ✓
- `anthropic/claude-opus-4-5-20251101` ✓
- `anthropic/claude-haiku-4-5-20251001` ✓

### Models That May NOT Validate
- `anthropic/claude-sonnet-4-5` (without date)
- `anthropic/claude-opus-4-5` (without date)

### Other Providers
Check https://models.dev for full list of valid model identifiers.
