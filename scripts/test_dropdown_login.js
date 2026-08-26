import { chromium } from 'playwright';

async function testSelect() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 420, height: 900 },
    deviceScaleFactor: 2
  });

  await page.goto('http://localhost:3002/');
  await page.waitForTimeout(1000);
  
  // Open dropdown
  await page.locator('button:has-text("Select a Demo Profile to Login...")').click();
  await page.waitForTimeout(300);

  // Click Saleem Fleet Logistics in dropdown
  await page.locator('button:has-text("Saleem Fleet Logistics")').click();
  await page.waitForTimeout(1000);

  await page.screenshot({
    path: 'C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots/24_saleem_fleet_after_dropdown_login.png'
  });

  await browser.close();
  console.log('Saved 24_saleem_fleet_after_dropdown_login.png');
}

testSelect().catch(console.error);
