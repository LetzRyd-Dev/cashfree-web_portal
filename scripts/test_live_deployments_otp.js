import { chromium } from 'playwright';

async function checkUrl(url) {
  console.log(`\nTesting ${url}...`);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => console.log(`[Browser Console ${msg.type()}]:`, msg.text()));
  page.on('pageerror', err => console.log(`[Browser PageError]:`, err.message));

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
    console.log(`Title: ${await page.title()}`);

    // Select Operator Login if available or check role
    const phoneInput = await page.$('input[type="tel"], input[placeholder*="mobile"], input[placeholder*="Phone"], input[type="text"]');
    if (phoneInput) {
      await phoneInput.fill('9691938866');
      console.log('Filled phone number: 9691938866');
      
      const otpButton = await page.$('button:has-text("Get OTP"), button:has-text("Send OTP"), button:has-text("Continue"), button:has-text("Verify")');
      if (otpButton) {
        console.log('Clicking Get OTP button...');
        await otpButton.click();
        await page.waitForTimeout(4000);

        // Check if there is an error message or if it switched to OTP input
        const errorEl = await page.$('.text-red-500, .text-amber-500, [class*="error"], [class*="alert"]');
        if (errorEl) {
          console.log('Error displayed on screen:', await errorEl.textContent());
        }

        const otpInputs = await page.$$('input[maxlength="1"], input[type="password"], input[placeholder*="OTP"], input[placeholder*="code"]');
        console.log(`Found ${otpInputs.length} OTP input boxes on screen.`);
      }
    }
  } catch (err) {
    console.error('Error during test:', err.message);
  } finally {
    await browser.close();
  }
}

async function main() {
  await checkUrl('https://cashfree-web-portal-925756819101.asia-south1.run.app');
  await checkUrl('https://cashfree-web-portal.vercel.app');
}

main();
