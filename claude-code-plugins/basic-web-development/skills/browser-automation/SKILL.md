---
name: browser-automation
description: Common Playwright automation patterns for web testing and scraping via MCP
---

# Browser Automation with Playwright MCP

This skill provides comprehensive patterns for browser automation using the Playwright MCP server. The Playwright MCP uses the accessibility tree for element interaction, which is more reliable and semantic than screenshot-based approaches.

## Overview

Playwright MCP enables:
- Reliable web navigation and page interactions
- Form filling and data extraction
- Element interaction via accessibility tree
- Cross-browser testing automation
- Network request monitoring and mocking

The MCP server runs via `npx @playwright/mcp@latest` and provides tools accessible through the Claude Code interface.

## Navigation Patterns

### Basic Navigation

Navigate to URLs and wait for page load events:

```javascript
// Navigate to a URL
await page.goto('https://example.com');

// Navigate with specific wait conditions
await page.goto('https://example.com', {
  waitUntil: 'networkidle'  // Wait until network is idle
});

// Navigate and wait for a specific element
await page.goto('https://example.com');
await page.waitForSelector('#main-content');
```

### Handling Page Load States

```javascript
// Wait for DOM to be ready
await page.waitForLoadState('domcontentloaded');

// Wait for full page load including resources
await page.waitForLoadState('load');

// Wait for network to be idle (no requests for 500ms)
await page.waitForLoadState('networkidle');
```

### Navigation with Authentication

```javascript
// Navigate with HTTP authentication
await page.goto('https://example.com', {
  waitUntil: 'networkidle',
  timeout: 30000
});

// Set authentication state
await context.addCookies([
  {
    name: 'session',
    value: 'abc123',
    domain: 'example.com',
    path: '/'
  }
]);
```

### Handling Redirects and Popups

```javascript
// Wait for navigation after click (handles redirects)
await Promise.all([
  page.waitForNavigation(),
  page.click('a[href="/login"]')
]);

// Handle popup windows
const [popup] = await Promise.all([
  page.waitForEvent('popup'),
  page.click('button[data-action="open-popup"]')
]);
await popup.waitForLoadState();
```

## Form Filling

### Text Input Fields

```javascript
// Fill text input
await page.fill('input[name="username"]', 'john.doe@example.com');

// Type with realistic delays (simulates human typing)
await page.type('input[name="password"]', 'SecurePass123', {
  delay: 100  // 100ms between keystrokes
});

// Clear and fill
await page.fill('input[name="search"]', '');
await page.fill('input[name="search"]', 'new search term');
```

### Select Dropdowns

```javascript
// Select by value
await page.selectOption('select[name="country"]', 'US');

// Select by label
await page.selectOption('select[name="country"]', { label: 'United States' });

// Select multiple options
await page.selectOption('select[name="interests"]', ['coding', 'testing', 'automation']);

// Select by index
await page.selectOption('select[name="priority"]', { index: 2 });
```

### Checkboxes and Radio Buttons

```javascript
// Check a checkbox
await page.check('input[type="checkbox"][name="terms"]');

// Uncheck a checkbox
await page.uncheck('input[type="checkbox"][name="newsletter"]');

// Select radio button
await page.check('input[type="radio"][value="premium"]');

// Verify checkbox state
const isChecked = await page.isChecked('input[name="terms"]');
```

### Complex Form Interactions

```javascript
// Fill complete form
await page.fill('input[name="firstName"]', 'John');
await page.fill('input[name="lastName"]', 'Doe');
await page.fill('input[name="email"]', 'john.doe@example.com');
await page.selectOption('select[name="country"]', 'US');
await page.check('input[name="terms"]');

// Submit form
await page.click('button[type="submit"]');

// Wait for form submission to complete
await page.waitForURL('**/success');
```

### File Uploads

```javascript
// Upload single file
await page.setInputFiles('input[type="file"]', 'path/to/file.pdf');

// Upload multiple files
await page.setInputFiles('input[type="file"][multiple]', [
  'path/to/file1.jpg',
  'path/to/file2.jpg'
]);

// Clear file input
await page.setInputFiles('input[type="file"]', []);
```

## Data Extraction

### Text Content Extraction

```javascript
// Extract text content
const title = await page.textContent('h1.page-title');

// Extract inner text (visible text only)
const description = await page.innerText('.product-description');

// Extract from multiple elements
const prices = await page.$$eval('.product-price', elements =>
  elements.map(el => el.textContent.trim())
);
```

### Attribute Extraction

```javascript
// Get single attribute
const imageUrl = await page.getAttribute('img.product-image', 'src');

// Get multiple attributes
const linkData = await page.$eval('a.download-link', el => ({
  href: el.getAttribute('href'),
  text: el.textContent,
  target: el.getAttribute('target')
}));

// Extract data attributes
const productId = await page.getAttribute('[data-product-id]', 'data-product-id');
```

### Structured Data Extraction

```javascript
// Extract table data
const tableData = await page.$$eval('table.data-table tbody tr', rows =>
  rows.map(row => {
    const cells = row.querySelectorAll('td');
    return {
      name: cells[0]?.textContent.trim(),
      email: cells[1]?.textContent.trim(),
      role: cells[2]?.textContent.trim()
    };
  })
);

// Extract list items
const items = await page.$$eval('ul.items li', elements =>
  elements.map(el => ({
    text: el.textContent.trim(),
    id: el.getAttribute('data-id')
  }))
);
```

### Pagination and Infinite Scroll

```javascript
// Handle pagination
const allData = [];
let hasNextPage = true;

while (hasNextPage) {
  // Extract current page data
  const pageData = await page.$$eval('.item', items =>
    items.map(item => item.textContent.trim())
  );
  allData.push(...pageData);

  // Check for next page button
  const nextButton = await page.$('button.next-page:not([disabled])');
  if (nextButton) {
    await nextButton.click();
    await page.waitForLoadState('networkidle');
  } else {
    hasNextPage = false;
  }
}

// Handle infinite scroll
await page.evaluate(async () => {
  await new Promise((resolve) => {
    let totalHeight = 0;
    const distance = 100;
    const timer = setInterval(() => {
      const scrollHeight = document.body.scrollHeight;
      window.scrollBy(0, distance);
      totalHeight += distance;

      if (totalHeight >= scrollHeight) {
        clearInterval(timer);
        resolve();
      }
    }, 100);
  });
});
```

## Element Interaction

### Clicking Elements

```javascript
// Simple click
await page.click('button.submit');

// Click with options
await page.click('button.menu', {
  button: 'right',  // Right-click
  clickCount: 2     // Double-click
});

// Force click (bypass actionability checks)
await page.click('.hidden-element', { force: true });

// Click and wait for navigation
await Promise.all([
  page.waitForNavigation(),
  page.click('a.external-link')
]);
```

### Hovering and Focus

```javascript
// Hover over element
await page.hover('.menu-item');

// Focus on input
await page.focus('input[name="search"]');

// Hover and click submenu
await page.hover('.dropdown-menu');
await page.click('.dropdown-menu .submenu-item');
```

### Keyboard Interactions

```javascript
// Press single key
await page.press('input[name="search"]', 'Enter');

// Press key combination
await page.press('body', 'Control+A');

// Type special characters
await page.keyboard.press('ArrowDown');
await page.keyboard.press('Tab');

// Keyboard shortcuts
await page.keyboard.press('Control+C');  // Copy
await page.keyboard.press('Control+V');  // Paste
```

### Drag and Drop

```javascript
// Drag and drop
await page.dragAndDrop('#source-element', '#target-element');

// Manual drag and drop with more control
await page.hover('#draggable');
await page.mouse.down();
await page.hover('#drop-zone');
await page.mouse.up();
```

### Waiting for Elements

```javascript
// Wait for element to appear
await page.waitForSelector('.dynamic-content');

// Wait for element to be visible
await page.waitForSelector('.modal', { state: 'visible' });

// Wait for element to be hidden
await page.waitForSelector('.loading-spinner', { state: 'hidden' });

// Wait for element with timeout
await page.waitForSelector('.slow-element', { timeout: 10000 });
```

### Element State Checks

```javascript
// Check if element is visible
const isVisible = await page.isVisible('.element');

// Check if element is enabled
const isEnabled = await page.isEnabled('button.submit');

// Check if element is editable
const isEditable = await page.isEditable('input[name="email"]');

// Get element count
const count = await page.locator('.item').count();
```

## Accessibility Tree Usage

The Playwright MCP leverages the accessibility tree for more reliable element interaction:

### Using ARIA Roles

```javascript
// Find by role
await page.click('button[role="button"]');
await page.click('[role="menuitem"]');

// Find by accessible name
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');
```

### Using Labels

```javascript
// Find input by label text
await page.getByLabel('Username').fill('john.doe');
await page.getByLabel('Password').fill('SecurePass123');
await page.getByLabel('Remember me').check();
```

### Using Accessible Names

```javascript
// Find by accessible name (aria-label, title, etc.)
await page.getByText('Welcome to our site').click();
await page.getByTitle('Close dialog').click();
await page.getByAltText('Company logo').click();
```

## Best Practices

### Error Handling

```javascript
// Use try-catch for robust automation
try {
  await page.waitForSelector('.element', { timeout: 5000 });
  await page.click('.element');
} catch (error) {
  console.error('Element not found:', error.message);
  // Fallback action
}
```

### Waiting Strategies

```javascript
// Prefer explicit waits over fixed delays
// BAD: await page.waitForTimeout(5000);
// GOOD:
await page.waitForLoadState('networkidle');
await page.waitForSelector('.content');
```

### Selector Best Practices

```javascript
// Prefer semantic selectors
// BAD: await page.click('div > div > button:nth-child(3)');
// GOOD: await page.click('button[data-testid="submit"]');
// BETTER: await page.getByRole('button', { name: 'Submit' }).click();
```

### Performance Optimization

```javascript
// Reuse locators
const submitButton = page.locator('button[type="submit"]');
await submitButton.waitFor();
await submitButton.click();

// Batch operations
await Promise.all([
  page.fill('input[name="field1"]', 'value1'),
  page.fill('input[name="field2"]', 'value2'),
  page.fill('input[name="field3"]', 'value3')
]);
```

## Common Patterns

### Login Flow

```javascript
async function login(page, username, password) {
  await page.goto('https://example.com/login');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard');
}
```

### Form Validation Testing

```javascript
// Submit empty form and check validation
await page.click('button[type="submit"]');
const errorMessage = await page.textContent('.error-message');
expect(errorMessage).toContain('required');

// Fill invalid data and verify
await page.fill('input[name="email"]', 'invalid-email');
await page.click('button[type="submit"]');
const emailError = await page.textContent('.email-error');
expect(emailError).toContain('valid email');
```

### Dynamic Content Handling

```javascript
// Wait for AJAX content to load
await page.click('button.load-more');
await page.waitForResponse(response =>
  response.url().includes('/api/items') && response.status() === 200
);
await page.waitForSelector('.new-items');
```

This skill provides the foundation for reliable browser automation using Playwright MCP's accessibility-focused approach.
