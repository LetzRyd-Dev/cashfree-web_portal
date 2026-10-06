import { chromium } from 'playwright';

async function testLocalhost() {
  console.log('Testing http://localhost:3002/ ...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => console.log(`[Browser ${msg.type()}]:`, msg.text()));
  page.on('pageerror', err => console.log(`[Browser PageError]:`, err.message));

  try {
    await page.goto('http://localhost:3002/', { waitUntil: 'networkidle', timeout: 15000 });
    console.log(`Page Title: ${await page.title()}`);

    const phoneInput = await page.$('input[type="tel"]');
    if (phoneInput) {
      await phoneInput.fill('9691938866');
      console.log('Entered 9691938866');

      const otpButton = await page.$('button[type="submit"]');
      if (otpButton) {
        console.log('Clicking Get OTP button...');
        await otpButton.click();
        await page.waitForTimeout(5000);

        const toast = await page.$('.fixed, [class*="toast"], [role="alert"]');
        if (toast) {
          console.log('Toast content:', await toast.textContent());
        }
      }
    }
  } catch (err) {
    console.error('Error during test:', err.message);
  } finally {
    await browser.close();
  }
}

testLocalhost();
