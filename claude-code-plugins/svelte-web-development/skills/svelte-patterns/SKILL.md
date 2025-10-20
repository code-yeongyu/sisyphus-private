---
name: svelte-patterns
description: Common Svelte patterns, best practices, and mistakes to avoid
---

# Svelte Patterns and Best Practices

This skill covers common component patterns, frequently made mistakes, best practices, and migration tips for Svelte development.

## Component Patterns

### Prop Patterns

```svelte
<!-- Basic props with defaults -->
<script>
let { 
  title = 'Default Title',
  subtitle,
  isActive = false,
  items = []
} = $props();
</script>

<h1>{title}</h1>
{#if subtitle}
  <h2>{subtitle}</h2>
{/if}

<!-- Rest props pattern -->
<script>
let { class: className, ...restProps } = $props();
</script>

<div class="container {className}" {...restProps}>
  <slot />
</div>
```

### Event Handling Patterns

```svelte
<!-- Custom event callbacks via props -->
<script>
let { 
  onSubmit = () => {},
  onChange = () => {},
  onCancel
} = $props();

let value = $state('');

function handleSubmit(event) {
  event.preventDefault();
  onSubmit(value);
}

function handleChange(event) {
  value = event.target.value;
  onChange(value);
}
</script>

<form onsubmit={handleSubmit}>
  <input type="text" value={value} oninput={handleChange} />
  <button type="submit">Submit</button>
  {#if onCancel}
    <button type="button" onclick={onCancel}>Cancel</button>
  {/if}
</form>
```

### Snippet Pattern (Render Props)

```svelte
<!-- Parent component -->
<script>
import DataList from './DataList.svelte';

let items = $state([
  { id: 1, name: 'Alice', role: 'Developer' },
  { id: 2, name: 'Bob', role: 'Designer' }
]);
</script>

<DataList {items}>
  {#snippet itemRenderer(item)}
    <div class="user-card">
      <h3>{item.name}</h3>
      <p>{item.role}</p>
    </div>
  {/snippet}
</DataList>

<!-- DataList.svelte -->
<script>
let { items, children } = $props();
</script>

<ul>
  {#each items as item}
    <li>
      {@render children.itemRenderer(item)}
    </li>
  {/each}
</ul>
```

### Context API Pattern

```svelte
<!-- ThemeProvider.svelte -->
<script>
import { setContext } from 'svelte';

let { children } = $props();
let theme = $state('light');

setContext('theme', {
  get current() { return theme; },
  toggle: () => { theme = theme === 'light' ? 'dark' : 'light'; }
});
</script>

<div class="theme-{theme}">
  {@render children()}
</div>

<!-- ThemeConsumer.svelte -->
<script>
import { getContext } from 'svelte';

const themeContext = getContext('theme');
</script>

<button onclick={themeContext.toggle}>
  Current theme: {themeContext.current}
</button>
```

### Composition Pattern

```svelte
<!-- useCounter.svelte.js -->
export function useCounter(initialValue = 0) {
  let count = $state(initialValue);
  
  return {
    get value() { return count; },
    increment: () => count++,
    decrement: () => count--,
    reset: () => count = initialValue
  };
}

<!-- Component.svelte -->
<script>
import { useCounter } from './useCounter.svelte.js';

const counter = useCounter(10);
</script>

<p>Count: {counter.value}</p>
<button onclick={counter.increment}>+</button>
<button onclick={counter.decrement}>-</button>
<button onclick={counter.reset}>Reset</button>
```

## Common Mistakes

### Mistake 1: Not Using Runes Properly

```svelte
<!-- WRONG: Mixing old and new syntax -->
<script>
let count = 0;  // Not reactive in Svelte 5!
$: doubled = count * 2;  // Old syntax

function increment() {
  count += 1;  // Won't trigger reactivity
}
</script>

<!-- CORRECT: Use runes -->
<script>
let count = $state(0);
let doubled = $derived(count * 2);

function increment() {
  count += 1;
}
</script>
```

### Mistake 2: Mutating Props Directly

```svelte
<!-- WRONG: Mutating props -->
<script>
let { user } = $props();

function updateName(newName) {
  user.name = newName;  // Don't mutate props!
}
</script>

<!-- CORRECT: Use callbacks -->
<script>
let { user, onUpdateUser } = $props();

function updateName(newName) {
  onUpdateUser({ ...user, name: newName });
}
</script>
```

### Mistake 3: Side Effects in Derived

```svelte
<!-- WRONG: Side effects in $derived -->
<script>
let count = $state(0);

let doubled = $derived(() => {
  console.log('Calculating doubled');  // Side effect!
  localStorage.setItem('count', count);  // Side effect!
  return count * 2;
});
</script>

<!-- CORRECT: Use $effect for side effects -->
<script>
let count = $state(0);
let doubled = $derived(count * 2);

$effect(() => {
  console.log('Count changed to:', count);
  localStorage.setItem('count', count.toString());
});
</script>
```

### Mistake 4: Missing Effect Cleanup

```svelte
<!-- WRONG: No cleanup -->
<script>
let isActive = $state(false);

$effect(() => {
  if (isActive) {
    const interval = setInterval(() => {
      console.log('tick');
    }, 1000);
    // Missing cleanup! Memory leak!
  }
});
</script>

<!-- CORRECT: Return cleanup function -->
<script>
let isActive = $state(false);

$effect(() => {
  if (!isActive) return;
  
  const interval = setInterval(() => {
    console.log('tick');
  }, 1000);
  
  return () => clearInterval(interval);
});
</script>
```

### Mistake 5: Incorrect Reactivity with Objects

```svelte
<!-- WRONG: Reassigning nested properties -->
<script>
let user = $state({ name: 'Alice', settings: { theme: 'light' } });

function toggleTheme() {
  // This works but creates a new object unnecessarily
  user = { 
    ...user, 
    settings: { ...user.settings, theme: 'dark' } 
  };
}
</script>

<!-- CORRECT: Direct mutation with $state -->
<script>
let user = $state({ name: 'Alice', settings: { theme: 'light' } });

function toggleTheme() {
  // $state provides deep reactivity
  user.settings.theme = user.settings.theme === 'light' ? 'dark' : 'light';
}
</script>
```

### Mistake 6: Overusing Effects

```svelte
<!-- WRONG: Using effect for derived values -->
<script>
let count = $state(0);
let doubled = $state(0);

$effect(() => {
  doubled = count * 2;  // This should be $derived!
});
</script>

<!-- CORRECT: Use $derived -->
<script>
let count = $state(0);
let doubled = $derived(count * 2);
</script>
```

### Mistake 7: Not Handling Async Properly

```svelte
<!-- WRONG: Race conditions -->
<script>
let searchQuery = $state('');
let results = $state([]);

$effect(() => {
  fetch(`/api/search?q=${searchQuery}`)
    .then(res => res.json())
    .then(data => {
      results = data;  // May set stale results!
    });
});
</script>

<!-- CORRECT: Handle cancellation -->
<script>
let searchQuery = $state('');
let results = $state([]);

$effect(() => {
  const controller = new AbortController();
  
  fetch(`/api/search?q=${searchQuery}`, { signal: controller.signal })
    .then(res => res.json())
    .then(data => results = data)
    .catch(err => {
      if (err.name !== 'AbortError') console.error(err);
    });
  
  return () => controller.abort();
});
</script>
```

## Best Practices

### Practice 1: Component Organization

```svelte
<script>
// 1. Imports
import { getContext } from 'svelte';
import ChildComponent from './ChildComponent.svelte';

// 2. Props
let { title, items = [], onItemClick } = $props();

// 3. Context
const theme = getContext('theme');

// 4. State
let selectedIndex = $state(0);
let isExpanded = $state(false);

// 5. Derived values
let selectedItem = $derived(items[selectedIndex]);
let itemCount = $derived(items.length);

// 6. Effects
$effect(() => {
  console.log('Selected item changed:', selectedItem);
});

// 7. Functions
function handleItemClick(index) {
  selectedIndex = index;
  onItemClick?.(items[index]);
}

function toggleExpanded() {
  isExpanded = !isExpanded;
}
</script>

<!-- 8. Template -->
<div class="component">
  <!-- content -->
</div>

<!-- 9. Styles -->
<style>
  .component {
    /* styles */
  }
</style>
```

### Practice 2: Type Safety with TypeScript

```svelte
<script lang="ts">
interface User {
  id: number;
  name: string;
  email: string;
}

let { 
  users,
  onUserSelect 
}: { 
  users: User[]; 
  onUserSelect: (user: User) => void;
} = $props();

let selectedUser = $state<User | null>(null);

function selectUser(user: User): void {
  selectedUser = user;
  onUserSelect(user);
}
</script>
```

### Practice 3: Reusable Logic with Modules

```javascript
// useLocalStorage.svelte.js
export function useLocalStorage(key, initialValue) {
  let value = $state(
    typeof window !== 'undefined' 
      ? JSON.parse(localStorage.getItem(key) ?? JSON.stringify(initialValue))
      : initialValue
  );
  
  $effect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  });
  
  return {
    get value() { return value; },
    set value(newValue) { value = newValue; }
  };
}

// Component.svelte
<script>
import { useLocalStorage } from './useLocalStorage.svelte.js';

const storage = useLocalStorage('user-preferences', { theme: 'light' });
</script>

<p>Theme: {storage.value.theme}</p>
<button onclick={() => storage.value = { theme: 'dark' }}>
  Change Theme
</button>
```

### Practice 4: Error Boundaries

```svelte
<!-- ErrorBoundary.svelte -->
<script>
let { children } = $props();
let error = $state(null);

function handleError(event) {
  error = event.error;
  console.error('Caught error:', event.error);
}
</script>

<svelte:window onerror={handleError} />

{#if error}
  <div class="error-boundary">
    <h2>Something went wrong</h2>
    <p>{error.message}</p>
    <button onclick={() => error = null}>Try Again</button>
  </div>
{:else}
  {@render children()}
{/if}
```

### Practice 5: Performance Optimization

```svelte
<script>
let items = $state([...largeDataset]);

// Memoize expensive computations
let sortedItems = $derived.by(() => {
  console.log('Sorting items...');
  return [...items].sort((a, b) => a.name.localeCompare(b.name));
});

// Virtualization for long lists
let visibleRange = $state({ start: 0, end: 20 });
let visibleItems = $derived(sortedItems.slice(visibleRange.start, visibleRange.end));

function handleScroll(event) {
  const scrollTop = event.target.scrollTop;
  const itemHeight = 50;
  const start = Math.floor(scrollTop / itemHeight);
  visibleRange = { start, end: start + 20 };
}
</script>

<div class="list-container" onscroll={handleScroll}>
  {#each visibleItems as item}
    <div class="item">{item.name}</div>
  {/each}
</div>
```

## Migration Tips

### Tip 1: Gradual Migration

```svelte
<!-- You can mix Svelte 4 and 5 syntax during migration -->
<script>
// Svelte 4 style (still works)
export let legacyProp;

// Svelte 5 style (new code)
let { newProp } = $props();
let count = $state(0);

// Gradually migrate reactive declarations
$: doubled = legacyProp * 2;  // Old
let tripled = $derived(newProp * 3);  // New
</script>
```

### Tip 2: Store Migration

```svelte
<!-- Before: Using stores -->
<script>
import { writable } from 'svelte/store';

const count = writable(0);

function increment() {
  count.update(n => n + 1);
}
</script>

<p>{$count}</p>

<!-- After: Using runes -->
<script>
let count = $state(0);

function increment() {
  count += 1;
}
</script>

<p>{count}</p>
```

### Tip 3: Reactive Statement Migration

```svelte
<!-- Before -->
<script>
let firstName = '';
let lastName = '';
$: fullName = `${firstName} ${lastName}`;
$: console.log('Name changed:', fullName);
</script>

<!-- After -->
<script>
let firstName = $state('');
let lastName = $state('');
let fullName = $derived(`${firstName} ${lastName}`);

$effect(() => {
  console.log('Name changed:', fullName);
});
</script>
```

### Tip 4: Component Events Migration

```svelte
<!-- Before: createEventDispatcher -->
<script>
import { createEventDispatcher } from 'svelte';

const dispatch = createEventDispatcher();

function handleClick() {
  dispatch('click', { data: 'value' });
}
</script>

<!-- After: Callback props -->
<script>
let { onClick = () => {} } = $props();

function handleClick() {
  onClick({ data: 'value' });
}
</script>
```

### Tip 5: Two-way Binding Migration

```svelte
<!-- Before: bind directive -->
<script>
export let value;
</script>

<input bind:value />

<!-- After: Explicit binding with snippets -->
<script>
let { value, onValueChange } = $props();
</script>

<input 
  value={value} 
  oninput={(e) => onValueChange(e.target.value)} 
/>
```

## Testing Patterns

```javascript
// Component.test.js
import { render, fireEvent } from '@testing-library/svelte';
import Component from './Component.svelte';

test('increments counter', async () => {
  const { getByText } = render(Component);
  
  const button = getByText('Increment');
  await fireEvent.click(button);
  
  expect(getByText('Count: 1')).toBeInTheDocument();
});

test('calls callback on submit', async () => {
  const handleSubmit = vi.fn();
  const { getByText } = render(Component, { onSubmit: handleSubmit });
  
  const submitButton = getByText('Submit');
  await fireEvent.click(submitButton);
  
  expect(handleSubmit).toHaveBeenCalledOnce();
});
```

This skill provides comprehensive patterns and practices for building robust Svelte applications.
