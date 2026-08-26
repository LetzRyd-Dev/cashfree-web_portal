import { chromium } from 'playwright';

async function testTestNumber() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 420, height: 900 },
    deviceScaleFactor: 2
  });

  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));

  await page.goto('http://localhost:3002/');
  await page.waitForTimeout(1000);

  const phoneInput = page.locator('input[type="tel"]');
  await phoneInput.fill('9876543210');
  await page.waitForTimeout(300);

  console.log('Clicking Get OTP for 9876543210...');
  await page.locator('button:has-text("Get OTP")').click();
  await page.waitForTimeout(2000);

  console.log('Filling OTP 123456...');
  const otpInput = page.locator('input[placeholder="••••••"]');
  await otpInput.fill('123456');
  await page.waitForTimeout(300);

  console.log('Clicking Verify...');
  await page.locator('button:has-text("Verify & Enter Portal")').click();
  await page.waitForTimeout(2000);

  await page.screenshot({
    path: 'C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots/29_test_number_auth.png'
  });
  console.log('Saved 29_test_number_auth.png successfully!');

  await browser.close();
}

testTestNumber().catch(console.error);
