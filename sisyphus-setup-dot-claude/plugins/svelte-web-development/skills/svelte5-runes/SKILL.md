---
name: svelte5-runes
description: Svelte 5 runes system for reactive state management and side effects
---

# Svelte 5 Runes

This skill covers the Svelte 5 runes system, which provides powerful primitives for reactive state management, derived values, and side effects in Svelte applications.

## What Are Runes?

Runes are symbols that control the Svelte compiler and provide explicit reactive primitives. They replace the implicit reactivity of Svelte 4 with a more powerful and predictable system.

Key benefits:
- Explicit reactivity that works everywhere (not just component top-level)
- Better TypeScript support
- More predictable behavior
- Works in both components and regular JavaScript/TypeScript files

Reference: https://svelte.dev/docs/svelte/llms.txt

## The $state Rune

The `$state` rune declares reactive state that automatically triggers UI updates when changed.

### Basic Usage

```svelte
<script>
let count = $state(0);

function increment() {
  count += 1;
}
</script>

<button onclick={increment}>
  Clicks: {count}
</button>
```

### State with Objects

```svelte
<script>
let user = $state({
  name: 'Alice',
  age: 30
});

function updateName(newName) {
  user.name = newName;
}

function incrementAge() {
  user.age += 1;
}
</script>

<input value={user.name} oninput={(e) => updateName(e.target.value)} />
<p>{user.name} is {user.age} years old</p>
<button onclick={incrementAge}>Birthday!</button>
```

### State with Arrays

```svelte
<script>
let items = $state([]);

function addItem(item) {
  items.push(item);
}

function removeItem(index) {
  items.splice(index, 1);
}

function clearItems() {
  items = [];
}
</script>

<button onclick={() => addItem('New Item')}>Add Item</button>
<button onclick={clearItems}>Clear All</button>

<ul>
  {#each items as item, i}
    <li>
      {item}
      <button onclick={() => removeItem(i)}>Remove</button>
    </li>
  {/each}
</ul>
```

### Deep Reactivity

```svelte
<script>
let app = $state({
  user: {
    profile: {
      name: 'Bob',
      settings: {
        theme: 'dark'
      }
    }
  }
});

function toggleTheme() {
  // Deep updates work automatically
  app.user.profile.settings.theme = 
    app.user.profile.settings.theme === 'dark' ? 'light' : 'dark';
}
</script>

<p>Current theme: {app.user.profile.settings.theme}</p>
<button onclick={toggleTheme}>Toggle Theme</button>
```

## The $derived Rune

The `$derived` rune creates values that automatically update when their dependencies change.

### Basic Derived Values

```svelte
<script>
let count = $state(0);
let doubled = $derived(count * 2);
let quadrupled = $derived(doubled * 2);

function increment() {
  count += 1;
}
</script>

<p>Count: {count}</p>
<p>Doubled: {doubled}</p>
<p>Quadrupled: {quadrupled}</p>
<button onclick={increment}>Increment</button>
```

### Derived with Complex Logic

```svelte
<script>
let items = $state([
  { name: 'Apple', price: 1.5, quantity: 3 },
  { name: 'Banana', price: 0.5, quantity: 6 },
  { name: 'Orange', price: 2.0, quantity: 2 }
]);

let total = $derived(
  items.reduce((sum, item) => sum + item.price * item.quantity, 0)
);

let averagePrice = $derived(
  items.length > 0 
    ? items.reduce((sum, item) => sum + item.price, 0) / items.length
    : 0
);

function updateQuantity(index, newQuantity) {
  items[index].quantity = newQuantity;
}
</script>

<p>Total: ${total.toFixed(2)}</p>
<p>Average Price: ${averagePrice.toFixed(2)}</p>

{#each items as item, i}
  <div>
    {item.name}: ${item.price} x {item.quantity}
    <input 
      type="number" 
      value={item.quantity}
      oninput={(e) => updateQuantity(i, +e.target.value)}
    />
  </div>
{/each}
```

### Chaining Derived Values

```svelte
<script>
let celsius = $state(0);
let fahrenheit = $derived((celsius * 9/5) + 32);
let kelvin = $derived(celsius + 273.15);
let temperatureDescription = $derived(
  celsius < 0 ? 'Freezing' :
  celsius < 10 ? 'Cold' :
  celsius < 20 ? 'Cool' :
  celsius < 30 ? 'Warm' : 'Hot'
);

function setCelsius(value) {
  celsius = value;
}
</script>

<input 
  type="range" 
  min="-20" 
  max="50" 
  value={celsius}
  oninput={(e) => setCelsius(+e.target.value)}
/>

<p>{celsius}°C = {fahrenheit.toFixed(1)}°F = {kelvin.toFixed(1)}K</p>
<p>Status: {temperatureDescription}</p>
```

### Derived with Conditionals

```svelte
<script>
let user = $state({ isLoggedIn: false, name: '', role: '' });

let greeting = $derived(
  user.isLoggedIn 
    ? `Welcome back, ${user.name}!`
    : 'Please log in'
);

let permissions = $derived(
  user.role === 'admin' 
    ? ['read', 'write', 'delete']
    : user.role === 'editor'
    ? ['read', 'write']
    : ['read']
);

function login(name, role) {
  user.isLoggedIn = true;
  user.name = name;
  user.role = role;
}
</script>

<p>{greeting}</p>
<p>Permissions: {permissions.join(', ')}</p>
<button onclick={() => login('Alice', 'admin')}>Login as Admin</button>
```

## The $derived.by Rune

The `$derived.by` rune is used when the derivation logic is complex enough to warrant a function.

### Complex Calculations

```svelte
<script>
let numbers = $state([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);

let statistics = $derived.by(() => {
  const sum = numbers.reduce((a, b) => a + b, 0);
  const mean = sum / numbers.length;
  const sorted = [...numbers].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const max = Math.max(...numbers);
  const min = Math.min(...numbers);
  
  return { sum, mean, median, max, min };
});

function addNumber(num) {
  numbers.push(num);
}
</script>

<p>Sum: {statistics.sum}</p>
<p>Mean: {statistics.mean.toFixed(2)}</p>
<p>Median: {statistics.median}</p>
<p>Max: {statistics.max}</p>
<p>Min: {statistics.min}</p>
```

### Filtering and Mapping

```svelte
<script>
let tasks = $state([
  { id: 1, text: 'Buy groceries', completed: false, priority: 'high' },
  { id: 2, text: 'Walk dog', completed: true, priority: 'medium' },
  { id: 3, text: 'Write code', completed: false, priority: 'high' }
]);

let filter = $state('all');

let filteredTasks = $derived.by(() => {
  if (filter === 'completed') {
    return tasks.filter(t => t.completed);
  } else if (filter === 'active') {
    return tasks.filter(t => !t.completed);
  } else if (filter === 'high-priority') {
    return tasks.filter(t => t.priority === 'high');
  }
  return tasks;
});

let taskStats = $derived.by(() => {
  const total = tasks.length;
  const completed = tasks.filter(t => t.completed).length;
  const active = total - completed;
  const completionRate = total > 0 ? (completed / total * 100).toFixed(0) : 0;
  
  return { total, completed, active, completionRate };
});

function toggleTask(id) {
  const task = tasks.find(t => t.id === id);
  if (task) task.completed = !task.completed;
}
</script>

<div>
  <button onclick={() => filter = 'all'}>All</button>
  <button onclick={() => filter = 'active'}>Active</button>
  <button onclick={() => filter = 'completed'}>Completed</button>
  <button onclick={() => filter = 'high-priority'}>High Priority</button>
</div>

<p>Stats: {taskStats.completed}/{taskStats.total} completed ({taskStats.completionRate}%)</p>

{#each filteredTasks as task}
  <div>
    <input type="checkbox" checked={task.completed} onchange={() => toggleTask(task.id)} />
    {task.text} ({task.priority})
  </div>
{/each}
```

### Async Derived Values

```svelte
<script>
let userId = $state(1);

let userData = $derived.by(async () => {
  const response = await fetch(`https://api.example.com/users/${userId}`);
  return await response.json();
});
</script>

{#await userData}
  <p>Loading user data...</p>
{:then user}
  <p>Name: {user.name}</p>
  <p>Email: {user.email}</p>
{:catch error}
  <p>Error: {error.message}</p>
{/await}
```

## The $effect Rune

The `$effect` rune runs side effects when its dependencies change.

### Basic Side Effects

```svelte
<script>
let count = $state(0);

$effect(() => {
  console.log(`Count changed to: ${count}`);
});

$effect(() => {
  document.title = `Count: ${count}`;
});

function increment() {
  count += 1;
}
</script>

<button onclick={increment}>Count: {count}</button>
```

### localStorage Synchronization

```svelte
<script>
let theme = $state(localStorage.getItem('theme') || 'light');

$effect(() => {
  localStorage.setItem('theme', theme);
  document.body.className = theme;
});

function toggleTheme() {
  theme = theme === 'light' ? 'dark' : 'light';
}
</script>

<button onclick={toggleTheme}>Toggle Theme</button>
<p>Current theme: {theme}</p>
```

### API Calls

```svelte
<script>
let searchQuery = $state('');
let results = $state([]);
let isLoading = $state(false);

$effect(() => {
  if (searchQuery.length < 3) {
    results = [];
    return;
  }

  isLoading = true;
  
  const controller = new AbortController();
  
  fetch(`https://api.example.com/search?q=${searchQuery}`, {
    signal: controller.signal
  })
    .then(res => res.json())
    .then(data => {
      results = data;
      isLoading = false;
    })
    .catch(err => {
      if (err.name !== 'AbortError') {
        console.error(err);
        isLoading = false;
      }
    });
  
  return () => {
    controller.abort();
  };
});
</script>

<input 
  type="text" 
  value={searchQuery}
  oninput={(e) => searchQuery = e.target.value}
  placeholder="Search (min 3 chars)..."
/>

{#if isLoading}
  <p>Loading...</p>
{:else}
  <ul>
    {#each results as result}
      <li>{result.name}</li>
    {/each}
  </ul>
{/if}
```

### Cleanup Functions

```svelte
<script>
let isActive = $state(false);

$effect(() => {
  if (!isActive) return;
  
  const interval = setInterval(() => {
    console.log('Tick');
  }, 1000);
  
  return () => {
    clearInterval(interval);
    console.log('Cleanup: interval cleared');
  };
});

function toggle() {
  isActive = !isActive;
}
</script>

<button onclick={toggle}>
  {isActive ? 'Stop' : 'Start'} Timer
</button>
```

## Migration from Svelte 4

### Reactive Declarations

```svelte
<!-- Svelte 4 -->
<script>
let count = 0;
$: doubled = count * 2;
$: console.log('count changed:', count);
</script>

<!-- Svelte 5 -->
<script>
let count = $state(0);
let doubled = $derived(count * 2);

$effect(() => {
  console.log('count changed:', count);
});
</script>
```

### Stores to Runes

```svelte
<!-- Svelte 4 with stores -->
<script>
import { writable, derived } from 'svelte/store';

const count = writable(0);
const doubled = derived(count, $count => $count * 2);
</script>

<p>Count: {$count}</p>
<p>Doubled: {$doubled}</p>
<button onclick={() => count.update(n => n + 1)}>Increment</button>

<!-- Svelte 5 with runes -->
<script>
let count = $state(0);
let doubled = $derived(count * 2);
</script>

<p>Count: {count}</p>
<p>Doubled: {doubled}</p>
<button onclick={() => count += 1}>Increment</button>
```

### Props

```svelte
<!-- Svelte 4 -->
<script>
export let name;
export let age = 0;
</script>

<!-- Svelte 5 -->
<script>
let { name, age = 0 } = $props();
</script>
```

## Best Practices

### Keep Derived Logic Pure

```svelte
<script>
let items = $state([1, 2, 3]);

// GOOD: Pure derivation
let sum = $derived(items.reduce((a, b) => a + b, 0));

// AVOID: Side effects in derived
// let sum = $derived(() => {
//   console.log('calculating sum');  // Side effect!
//   return items.reduce((a, b) => a + b, 0);
// });

// Use $effect for side effects instead
$effect(() => {
  console.log('Sum changed:', sum);
});
</script>
```

### Minimize Effect Dependencies

```svelte
<script>
let count = $state(0);
let name = $state('Alice');

// GOOD: Specific effect
$effect(() => {
  console.log('Count changed:', count);
});

// AVOID: Unnecessary dependencies
// $effect(() => {
//   console.log('Count changed:', count);
//   // This effect reruns when name changes too
//   const userName = name;
// });
</script>
```

### Use $derived.by for Complex Logic

```svelte
<script>
let data = $state([...largeDataset]);

// GOOD: Complex logic in $derived.by
let processed = $derived.by(() => {
  return data
    .filter(item => item.active)
    .map(item => transform(item))
    .sort((a, b) => compare(a, b));
});

// AVOID: Inline complex logic in $derived
// let processed = $derived(data.filter(...).map(...).sort(...));
</script>
```

This skill provides a comprehensive foundation for using Svelte 5 runes effectively in your applications.
