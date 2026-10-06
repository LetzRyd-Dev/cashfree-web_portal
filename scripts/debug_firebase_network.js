import { chromium } from 'playwright';

async function testVisibleRecaptcha() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => console.log(`[Browser ${msg.type()}]:`, msg.text()));
  page.on('pageerror', err => console.log(`[Browser PageError]:`, err.message));

  await page.goto('http://localhost:3002/', { waitUntil: 'networkidle' });
  await page.fill('input[type="tel"]', '9691938866');
  
  // Intercept the network calls to firebase identity toolkit
  page.on('response', async response => {
    if (response.url().includes('identitytoolkit') || response.url().includes('sendVerificationCode')) {
      console.log('Firebase Response URL:', response.url());
      console.log('Status:', response.status());
      try {
        console.log('Body:', await response.text());
      } catch (e) {}
    }
  });

  await page.click('button[type="submit"]');
  await page.waitForTimeout(6000);

  await browser.close();
}

testVisibleRecaptcha();
