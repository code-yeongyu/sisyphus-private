---
name: slash-command-creator
description: Expert prompt engineer for creating high-quality custom slash commands. Activate when user requests to create, design, or improve slash commands (e.g., "create a command for...", "make a slash command that...", "improve this command"). Specializes in applying advanced prompt engineering techniques, iterative refinement with prompt-engineer agent collaboration, and generating commands that maximize Claude's capabilities for specific use cases.
---

# Claude Code Slash Command Creator Skill

Transform user requirements into professional, high-quality slash commands through expert prompt engineering and iterative collaboration.

## What This Skill Does

Create custom slash commands by:
1. Understanding user requirements through dialogue
2. Applying advanced prompt engineering techniques (load prompt engineer skills)
3. Generating well-structured command files
4. Iterating with prompt-engineer agent until approved
5. Supporting both creation and modification of commands

## When to Use This Skill

Activate when user wants to:
- Create a new slash command ("make a command for code analysis")
- Improve existing slash command ("improve my /review-code command")
- Understand slash command design ("how should I structure a command for...")
- Design command workflows ("what's the best way to...")

## Core Process

### Phase 1: Requirements Gathering

**Engage in dialogue to understand:**
- What should the command do?
- What are concrete usage examples?
- What arguments/options are needed?
- Should it be project-level or user-level?
- What language should content be in? (default: English)

**Example questions:**
```
"Can you give me 2-3 examples of how you'd use this command?"
"What tools would this command need? (file reading, git, web search...)"
"Should this be available globally or just in specific projects?"
```

### Phase 2: Load Prompt Engineering Knowledge

**Always execute before designing:**
```bash
bash scripts/get-prompting-guides.sh
```

This loads latest prompt engineering best practices from Anthropic documentation.

### Phase 3: Deep Analysis and Design

**Think deeply about:**
1. **Role Definition**: What expertise should Claude embody?
2. **Task Complexity**: Does it need Chain of Thought? Multi-step reasoning?
3. **Output Format**: What structure optimizes user experience?
4. **Context Scope**: How much context is required?
5. **Tool Requirements**: Minimal necessary permissions?
6. **Edge Cases**: What could go wrong?

**For complex commands, use Sequential Thinking:**
```
Use mcp__sequential-thinking__process_thought to:
- Deeply analyze each requirement
- Explore multiple design approaches
- Anticipate edge cases and failure modes
- Design optimal prompting strategies
```

**Consult references as needed:**
- Read [slash-command-patterns.md](references/slash-command-patterns.md) for proven patterns
- Read [claude-docs-references.md](references/claude-docs-references.md) for technical details

### Phase 4: Implementation

**1. Determine target location:**
```bash
# For user-level (global)
TARGET_DIR="$HOME/.claude/commands"

# For project-level
TARGET_DIR="./.claude/commands"

# Create directory if needed
mkdir -p "$TARGET_DIR"
```

**2. Generate command file:**

Use [command-template.md](assets/command-template.md) as starting structure, then customize:

```markdown
---
allowed-tools: [Minimal necessary permissions]
description: [Specific, searchable description]
argument-hint: <required> [optional] [--flags]
---

# Claude Command: [Name]

## Usage
/command-name <args>

## What this command does
[Clear, one-sentence explanation]

## Role Definition
You are [specific expert role with domain expertise]

## Process
1. **Step One**: [Imperative description]
2. **Step Two**: [Clear actions]
3. **Step Three**: [Validation]

## Output Format
[Structured format specification]

## Quality Assurance
[Validation steps]
```

**3. Apply prompt engineering techniques:**
- Assign specific, detailed role
- Include step-by-step process for complex tasks
- Use XML tags for structure when needed
- Specify explicit output format
- Include error handling
- Default to English unless `--language` specified

**Key principles:**
- **NO EMOJIS** - Use **bold** or UPPERCASE for emphasis
- **Concise** - Avoid token bloat
- **Specific** - Concrete over generic
- **Minimal tools** - Principle of least privilege
- **Verb-noun naming** - `analyze-code` not `code-analyzer`

### Phase 5: Expert Review and Iteration

**Submit to prompt-engineer agent:**
```
Use Task tool with prompt-engineer agent to review the command.

Pass the complete command file path for review.

Request feedback on:
- Prompt engineering quality
- Role definition clarity
- Process structure
- Tool selection
- Edge case handling
```

**Iterate until approved:**
1. Receive feedback
2. Implement improvements
3. Re-submit for review
4. Repeat until agent says "OKAY" or "Approved"

**Do not stop until explicit approval received.**

### Phase 6: Finalization

**1. Write the command file:**
```bash
# Write to target directory
cat > "$TARGET_DIR/command-name.md" <<'EOF'
[Generated command content]
EOF
```

**2. Confirm with user:**
```
Created: [file-path]
Command name: /command-name
Tested with: prompt-engineer agent (approved)

You can now use: /command-name [args]
```

**3. Offer next steps:**
- Test the command with example usage
- Create additional related commands
- Modify based on real usage

## Command Design Patterns

### For Simple Actions
Use Pattern 1 from [slash-command-patterns.md](references/slash-command-patterns.md):
- Single clear purpose
- Minimal process steps
- Straightforward tool usage

### For Analysis Tasks
Use Pattern 2:
- Argument parsing with options
- Analysis phase with depth control
- Structured reporting

### For Multi-Phase Workflows
Use Pattern 3:
- TodoWrite for progress tracking
- Clear phase separation
- Agent collaboration if needed

### For Data Processing
Use Pattern 4:
- Intelligent tool selection
- Performance optimization
- Metrics reporting

### For Project Setup
Use Pattern 5:
- Environment validation
- Step-by-step initialization
- Configuration and verification

**See [slash-command-patterns.md](references/slash-command-patterns.md) for complete pattern library.**

## Quality Standards

A well-designed command must have:
- ✅ Clear, specific description in frontmatter
- ✅ Accurate argument-hint showing required/optional args
- ✅ Minimal necessary tool permissions
- ✅ Step-by-step process with imperative verbs
- ✅ Defined output format
- ✅ Error handling and validation
- ✅ No emojis (use **bold** or UPPERCASE)
- ✅ English by default (unless --language specified)
- ✅ Verb-noun command naming
- ✅ Explicit approval from prompt-engineer agent

## Common Pitfalls to Avoid

**❌ Don't:**
- Include formatters in allowed-tools (no yamlfmt, prettier, etc.)
- Use generic descriptions ("do stuff with code")
- Forget argument-hint in frontmatter
- Use emojis for emphasis
- Grant overly broad tool permissions (Bash(*))
- Create noun-agent command names (code-analyzer)
- Skip prompt-engineer review
- Stop iterating before approval

**✅ Do:**
- Apply principle of least privilege for tools
- Write specific, searchable descriptions
- Use concrete examples in documentation
- Validate all user inputs
- Handle errors gracefully
- Test command before finalizing
- Iterate until expert approval

## Modifying Existing Commands

**When user wants to improve existing command:**

1. **Read existing command:**
   ```bash
   # Find and read the command
   cat ~/.claude/commands/existing-command.md
   # or
   cat ./.claude/commands/existing-command.md
   ```

2. **Understand current implementation:**
   - What does it do well?
   - What are the limitations?
   - What user feedback exists?

3. **Apply full design process:**
   - Go through Phases 2-5
   - Load prompting guides
   - Deep analysis of improvements
   - Generate improved version
   - Submit to prompt-engineer agent
   - Iterate until approved

4. **Create backup before modifying:**
   ```bash
   cp existing-command.md existing-command.md.backup-$(date +%Y%m%d-%H%M%S)
   ```

5. **Write improved version:**
   ```bash
   # Overwrite with improved version
   cat > existing-command.md <<'EOF'
   [Improved command content]
   EOF
   ```

## Language Support

**Default: English**
Unless `--language` parameter explicitly provided, generate ALL content in English:
- Section headers
- Instructions
- Error messages
- Examples

**Supporting multiple languages:**
If command should support language parameter:
```yaml
argument-hint: <action> [--language=<lang>]
```

Then in process:
```markdown
## Process
1. **Parse Language Parameter**
   - Default: English
   - Supported: ANY language (korean, japanese, chinese, spanish, etc.)
2. **Apply Language**
   - Generate all dynamic content in specified language
   - Keep tool names and command structure unchanged
```

## Examples

### Example 1: Creating Simple Analysis Command

**User request:** "Create a command to analyze code complexity"

**Process:**
1. Gather requirements:
   - "Should it analyze specific files or directories?"
   - "What complexity metrics do you want?"
   - "Should it suggest improvements?"

2. Load prompting guides: `bash scripts/get-prompting-guides.sh`

3. Design command using Pattern 2 (Analysis with Options)

4. Generate:
   ```markdown
   ---
   allowed-tools: Read(*), Grep(*), Glob(*)
   description: Analyze code complexity and suggest refactoring improvements
   argument-hint: <file-or-dir> [--depth=<1-5>] [--language=<lang>]
   ---
   ```

5. Submit to prompt-engineer agent for review

6. Iterate based on feedback

7. Finalize at `~/.claude/commands/analyze-complexity.md`

### Example 2: Improving Existing Command

**User request:** "Improve my /commit command"

**Process:**
1. Read existing: `cat ~/.claude/commands/commit.md`

2. Identify improvements:
   - Better error handling?
   - More commit message formats?
   - Conventional commit support?

3. Apply design process with improvements

4. Backup: `cp commit.md commit.md.backup-20250118`

5. Submit improved version to prompt-engineer agent

6. Iterate until approved

7. Overwrite with improved version

## Technical Details

**See [claude-docs-references.md](references/claude-docs-references.md) for:**
- Slash command execution model
- Variable substitution ($ARGUMENTS)
- Directory structure
- Tool permission syntax
- Advanced features (Sequential Thinking, Agent collaboration)

**See [slash-command-patterns.md](references/slash-command-patterns.md) for:**
- Complete pattern library
- Antipatterns to avoid
- Best practices
- Real-world examples

## Success Criteria

Command creation is complete when:
1. ✅ Requirements fully understood through dialogue
2. ✅ Prompt engineering guides loaded and applied
3. ✅ Deep analysis performed (with Sequential Thinking if complex)
4. ✅ Command generated following best practices
5. ✅ Prompt-engineer agent explicitly approved ("OKAY")
6. ✅ File written to correct location
7. ✅ User confirmed and can test the command

**Never stop before explicit agent approval.**
