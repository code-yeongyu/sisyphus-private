---
name: web-testing
description: Web testing patterns and best practices using Playwright for automated testing
---

# Web Testing with Playwright

This skill covers comprehensive web testing patterns using Playwright, including test structure, assertions, mocking, and best practices for reliable automated testing.

## Test Structure

### Basic Test Organization

```javascript
import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://example.com/login');
  });

  test('should login with valid credentials', async ({ page }) => {
    const username = 'testuser@example.com';
    const password = 'SecurePass123';

    await page.fill('input[name="email"]', username);
    await page.fill('input[name="password"]', password);
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('.welcome-message')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpass');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error-message')).toContainText('Invalid credentials');
  });
});
```

### Test Hooks and Lifecycle

```javascript
import { test } from '@playwright/test';

test.describe('E-commerce Checkout', () => {
  test.beforeAll(async ({ browser }) => {
    console.log('Setting up test database');
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('https://example.com');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
  });

  test.afterEach(async ({ page }) => {
    await page.click('[data-testid="clear-cart"]');
  });

  test.afterAll(async () => {
    console.log('Cleaning up test database');
  });

  test('should add item to cart', async ({ page }) => {
    await page.click('[data-product-id="123"]');
    await page.click('button:has-text("Add to Cart")');
    await expect(page.locator('.cart-count')).toHaveText('1');
  });
});
```

### Parameterized Tests

```javascript
import { test, expect } from '@playwright/test';

const testData = [
  { input: 'john@example.com', expected: true },
  { input: 'invalid-email', expected: false },
  { input: 'another@test.co.uk', expected: true },
  { input: '@nodomain.com', expected: false }
];

testData.forEach(({ input, expected }) => {
  test(`should validate email: ${input}`, async ({ page }) => {
    await page.goto('https://example.com/signup');
    await page.fill('input[name="email"]', input);
    await page.click('button[type="submit"]');

    if (expected) {
      await expect(page.locator('.error-message')).not.toBeVisible();
    } else {
      await expect(page.locator('.error-message')).toBeVisible();
    }
  });
});
```

### Test Fixtures

```javascript
import { test as base, expect } from '@playwright/test';

const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    await page.goto('https://example.com/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');

    await use(page);

    await page.click('[data-testid="logout"]');
  }
});

test('should access protected resource', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('https://example.com/profile');
  await expect(authenticatedPage.locator('h1')).toContainText('My Profile');
});
```

## Assertions

### Element Visibility Assertions

```javascript
import { test, expect } from '@playwright/test';

test('element visibility checks', async ({ page }) => {
  await page.goto('https://example.com');

  await expect(page.locator('.header')).toBeVisible();
  await expect(page.locator('.modal')).toBeHidden();
  await expect(page.locator('.hidden-div')).toBeAttached();
  await expect(page.locator('.removed-element')).not.toBeAttached();
});
```

### Text Content Assertions

```javascript
test('text content checks', async ({ page }) => {
  await page.goto('https://example.com');

  await expect(page.locator('h1')).toHaveText('Welcome');
  await expect(page.locator('.description')).toContainText('product');
  await expect(page.locator('.price')).toHaveText(/\$\d+\.\d{2}/);
  await expect(page.locator('.item-title')).toHaveText([
    'Item 1',
    'Item 2',
    'Item 3'
  ]);
});
```

### Attribute and State Assertions

```javascript
test('attribute and state checks', async ({ page }) => {
  await page.goto('https://example.com/form');

  await expect(page.locator('input[name="email"]')).toHaveAttribute('type', 'email');
  await expect(page.locator('.button')).toHaveClass(/primary/);
  await expect(page.locator('.list-item')).toHaveCount(5);
  await expect(page.locator('input[name="username"]')).toHaveValue('john.doe');
  await expect(page.locator('input[type="checkbox"]')).toBeChecked();
  await expect(page.locator('input[type="checkbox"]')).not.toBeChecked();
  await expect(page.locator('button[type="submit"]')).toBeEnabled();
  await expect(page.locator('button.disabled')).toBeDisabled();
  await expect(page.locator('input[name="email"]')).toBeEditable();
});
```

### URL and Page Assertions

```javascript
test('URL and page checks', async ({ page }) => {
  await page.goto('https://example.com/products');

  await expect(page).toHaveURL('https://example.com/products');
  await expect(page).toHaveURL(/.*products/);
  await expect(page).toHaveTitle('Products - Example Store');
  await expect(page).toHaveTitle(/Products/);
});
```

### Custom Assertions

```javascript
test('custom assertions', async ({ page }) => {
  await page.goto('https://example.com/cart');

  const cartTotal = await page.locator('.cart-total').textContent();
  expect(parseFloat(cartTotal.replace('$', ''))).toBeGreaterThan(0);

  await expect.soft(page.locator('.item')).toHaveCount(3);
  await expect.soft(page.locator('.discount-badge')).toBeVisible();

  const element = page.locator('.product');
  await expect(element).toBeVisible();
  await expect(element).toContainText('Special Offer');
  await expect(element).toHaveClass('highlighted');
});
```

## Mocking

### Network Request Interception

```javascript
import { test, expect } from '@playwright/test';

test('mock API response', async ({ page }) => {
  await page.route('**/api/products', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Mocked Product 1', price: 19.99 },
        { id: 2, name: 'Mocked Product 2', price: 29.99 }
      ])
    });
  });

  await page.goto('https://example.com/products');

  await expect(page.locator('.product').first()).toContainText('Mocked Product 1');
});
```

### Conditional Mocking

```javascript
test('conditional network mocking', async ({ page }) => {
  await page.route('**/api/**', route => {
    const url = route.request().url();

    if (url.includes('/api/slow-endpoint')) {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ data: 'fast response' })
      });
    } else if (url.includes('/api/error-prone')) {
      route.fulfill({ status: 500 });
    } else {
      route.continue();
    }
  });

  await page.goto('https://example.com');
});
```

### Request Modification

```javascript
test('modify outgoing requests', async ({ page }) => {
  await page.route('**/api/data', route => {
    const headers = {
      ...route.request().headers(),
      'Authorization': 'Bearer mock-token-123'
    };

    route.continue({ headers });
  });

  await page.goto('https://example.com/dashboard');
});
```

### Response Delays

```javascript
test('simulate slow network', async ({ page }) => {
  await page.route('**/api/products', async route => {
    await new Promise(resolve => setTimeout(resolve, 3000));

    await route.fulfill({
      status: 200,
      body: JSON.stringify({ products: [] })
    });
  });

  await page.goto('https://example.com/products');
  await expect(page.locator('.loading-spinner')).toBeVisible();
});
```

## Best Practices

### Reliable Selectors

```javascript
// GOOD: Use test IDs
await page.click('[data-testid="submit-button"]');

// GOOD: Use semantic selectors
await page.click('button:has-text("Submit")');
await page.getByRole('button', { name: 'Submit' }).click();

// GOOD: Use labels for inputs
await page.getByLabel('Email address').fill('test@example.com');

// AVOID: Fragile CSS selectors
// await page.click('div > div > button:nth-child(3)');
```

### Wait Strategies

```javascript
test('proper waiting', async ({ page }) => {
  await page.goto('https://example.com');

  await page.waitForLoadState('networkidle');
  await expect(page.locator('.content')).toBeVisible();
  await expect(page.locator('.dynamic-content')).toBeVisible();

  // AVOID: Fixed timeouts like await page.waitForTimeout(5000);
});
```

### Test Independence

```javascript
// GOOD: Each test is independent
test.describe('Product Tests', () => {
  test('test 1', async ({ page }) => {
    await page.goto('https://example.com');
    // Complete test flow
  });

  test('test 2', async ({ page }) => {
    await page.goto('https://example.com');
    // Complete test flow (does not depend on test 1)
  });
});
```

### Error Handling

```javascript
test('handle unexpected states', async ({ page }) => {
  await page.goto('https://example.com');

  const cookieBanner = page.locator('.cookie-banner');
  if (await cookieBanner.isVisible()) {
    await cookieBanner.locator('button:has-text("Accept")').click();
  }

  await page.click('[data-testid="main-action"]');
});
```

### Page Object Model

```javascript
export class LoginPage {
  constructor(page) {
    this.page = page;
    this.emailInput = page.locator('input[name="email"]');
    this.passwordInput = page.locator('input[name="password"]');
    this.submitButton = page.locator('button[type="submit"]');
  }

  async login(email, password) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

import { LoginPage } from './page-objects/LoginPage';

test('login flow', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await page.goto('https://example.com/login');
  await loginPage.login('test@example.com', 'password123');
  await expect(page).toHaveURL(/.*dashboard/);
});
```

### Screenshot and Trace on Failure

```javascript
// playwright.config.js
export default {
  use: {
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure'
  }
};

test('critical flow', async ({ page }) => {
  await page.goto('https://example.com');
  await page.screenshot({ path: 'screenshots/before-action.png' });
  await page.click('[data-testid="critical-button"]');
  await expect(page.locator('.success-message')).toBeVisible();
});
```

### Performance Testing

```javascript
test('page load performance', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('https://example.com');
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - startTime;
  expect(loadTime).toBeLessThan(3000);
});
```

This skill provides a comprehensive foundation for writing reliable, maintainable web tests using Playwright.
