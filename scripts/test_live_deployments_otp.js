import { chromium } from 'playwright';

async function checkUrl(url) {
  console.log(`\nTesting ${url}...`);
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu']
  });
  const context = await browser.newContext({ viewport: { width: 420, height: 900 } });
  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error' && !msg.text().includes('requestStorageAccess')) {
      console.log(`[Browser Console ${msg.type()}]:`, msg.text());
    }
  });

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
    console.log(`Title: ${await page.title()}`);

    const phoneInput = page.locator('input[type="tel"]');
    if (await phoneInput.count() > 0) {
      await phoneInput.fill('9691938866');
      console.log('Filled phone number: 9691938866');
      
      const otpButton = page.locator('button:has-text("Get OTP")');
      if (await otpButton.count() > 0) {
        console.log('Clicking Get OTP button...');
        await otpButton.click();
        
        const otpInput = page.locator('input[placeholder="••••••"]');
        await otpInput.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
        const count = await otpInput.count();
        console.log(`Found ${count} OTP input boxes on screen.`);
      }
    }
  } catch (err) {
    console.error('Error during test:', err.message);
  } finally {
    await browser.close();
  }
}

async function main() {
  await checkUrl('https://letzryd-portal-925756819101.asia-south1.run.app');
  await checkUrl('https://dev-cashfree-web-portal-925756819101.asia-south1.run.app');
}

main();

