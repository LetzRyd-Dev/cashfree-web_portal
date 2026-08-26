import { chromium } from 'playwright';

async function run() {
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
  
  const dropdownBtn = page.locator('button:has-text("Select a Demo Profile to Login...")');
  await dropdownBtn.click();
  await page.waitForTimeout(500);

  await page.screenshot({
    path: 'C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots/23_quick_switch_dropdown.png'
  });

  await browser.close();
  console.log('Saved 23_quick_switch_dropdown.png successfully');
}

run().catch(console.error);
