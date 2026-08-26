import { chromium } from 'playwright';

async function testAnuragOperatorFleet() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 420, height: 900 },
    deviceScaleFactor: 2
  });

  await page.goto('http://localhost:3002/');
  await page.waitForTimeout(600);

  // Click Operator Login tab
  await page.locator('button:has-text("Operator Login")').click();
  await page.waitForTimeout(200);

  // Fill Anurag's phone
  const phoneInput = page.locator('input[type="tel"]');
  await phoneInput.fill('9691938866');
  await page.waitForTimeout(200);

  await page.locator('button:has-text("Get OTP")').click();
  await page.waitForTimeout(1000);

  const otpInput = page.locator('input[placeholder="••••••"]');
  await otpInput.fill('123456');
  await page.waitForTimeout(200);

  await page.locator('button:has-text("Verify & Enter Portal")').click();
  
  // Wait until "Loading your profile..." disappears and header appears
  await page.waitForSelector('text=Anurag & RK Fleet Logistics', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1000);

  await page.screenshot({
    path: 'C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots/34_anurag_operator_home.png'
  });
  console.log('Saved 34_anurag_operator_home.png');

  // Click Fleet tab
  const fleetTab = page.locator('button:has-text("Fleet")').or(page.locator('button:has-text("Hisaab")'));
  if (await fleetTab.count() > 0) {
    await fleetTab.first().click();
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: 'C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots/35_anurag_operator_fleet_view.png'
    });
    console.log('Saved 35_anurag_operator_fleet_view.png');
  }

  await browser.close();
}

testAnuragOperatorFleet().catch(console.error);
