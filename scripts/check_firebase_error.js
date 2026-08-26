import { chromium } from 'playwright';

async function checkFirebaseError() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: false
  });
  const page = await browser.newPage({
    viewport: { width: 420, height: 900 },
    deviceScaleFactor: 2
  });

  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('BROWSER PAGE ERROR:', err.message));

  await page.goto('http://localhost:3002/');
  await page.waitForTimeout(1000);

  const phoneInput = page.locator('input[type="tel"]');
  await phoneInput.fill('9691938866');
  await page.waitForTimeout(300);

  console.log('Clicking Get OTP...');
  await page.locator('button:has-text("Get OTP")').click();

  // Wait for 10 seconds to see response and logs
  await page.waitForTimeout(10000);

  await browser.close();
}

checkFirebaseError().catch(console.error);
