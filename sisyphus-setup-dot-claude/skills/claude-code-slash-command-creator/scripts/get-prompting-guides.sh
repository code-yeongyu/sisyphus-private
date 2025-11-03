#!/bin/bash

# Combined data structure - each element is "name|url"
guides=(
    "Anthropic - Overview|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview.md"
    "Anthropic - Claude 4 Best Practices|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices.md"
    "Anthropic - Prompt Templates and Variables|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-templates-and-variables.md"
    "Anthropic - Be Clear and Direct|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct.md"
    "Anthropic - Multishot Prompting|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting.md"
    "Anthropic - Chain of Thought|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-of-thought.md"
    "Anthropic - Use XML Tags|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags.md"
    "Anthropic - System Prompts|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts.md"
    "Anthropic - Prefill Claude's Response|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prefill-claudes-response.md"
    "Anthropic - Chain Prompts|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts.md"
    "Anthropic - Long Context Tips|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips.md"
    "Anthropic - Extended Thinking Tips|https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/extended-thinking-tips.md"
    "Anthropic - Define Success|https://docs.anthropic.com/en/docs/test-and-evaluate/define-success.md"
    "Anthropic - Develop Tests|https://docs.anthropic.com/en/docs/test-and-evaluate/develop-tests.md"
    "Anthropic - Reduce Hallucinations|https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations.md"
    "Anthropic - Increase Consistency|https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency.md"
    "Prompt Engineering Guide - Settings|https://raw.githubusercontent.com/dair-ai/Prompt-Engineering-Guide/refs/heads/main/pages/introduction/settings.en.mdx"
)

# Create temp directory
temp_dir=$(mktemp -d)
trap "rm -rf $temp_dir" EXIT

# Function to fetch content
fetch_guide() {
    local index=$1
    local entry="${guides[$index]}"
    local name="${entry%%|*}"
    local url="${entry#*|}"
    local output_file="$temp_dir/guide_$(printf "%02d" $index).txt"

    curl -s -L "$url" > "$output_file" 2>/dev/null
}


# Start all fetches in parallel
for i in "${!guides[@]}"; do
    fetch_guide "$i" &
done

# Wait for all background jobs
wait


# Output in order
for i in "${!guides[@]}"; do
    entry="${guides[$i]}"
    name="${entry%%|*}"
    url="${entry#*|}"
    output_file="$temp_dir/guide_$(printf "%02d" $i).txt"

    echo "<guide name=\"$name\" url=\"$url\">"
    if [[ -s "$output_file" ]]; then
        cat "$output_file"
    else
        echo "// Failed to fetch or empty content"
    fi
    echo "</guide>"
    echo ""
done
