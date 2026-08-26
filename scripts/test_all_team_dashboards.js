import { chromium } from 'playwright';

async function testAllTeamDashboards() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 420, height: 900 },
    deviceScaleFactor: 2
  });

  const accounts = [
    { name: 'Anurag (Operator)', phone: '9691938866', role: 'operator', otp: '123456', shot: '30_anurag_fleet_dashboard.png' },
    { name: 'Vivek (Driver)', phone: '9901484683', role: 'driver', otp: '123456', shot: '31_vivek_driver_dashboard.png' },
    { name: 'Sushant (Driver)', phone: '9140631755', role: 'driver', otp: '123456', shot: '32_sushant_driver_dashboard.png' },
    { name: 'Aayush (Driver)', phone: '9930420065', role: 'driver', otp: '123456', shot: '33_aayush_driver_dashboard.png' },
  ];

  for (const acc of accounts) {
    await page.goto('http://localhost:3002/');
    await page.waitForTimeout(600);

    if (acc.role === 'operator') {
      await page.locator('button:has-text("Operator Login")').click();
      await page.waitForTimeout(200);
    } else {
      await page.locator('button:has-text("Driver Login")').click();
      await page.waitForTimeout(200);
    }

    const phoneInput = page.locator('input[type="tel"]');
    await phoneInput.fill(acc.phone);
    await page.waitForTimeout(200);

    await page.locator('button:has-text("Get OTP")').click();
    await page.waitForTimeout(1000);

    const otpInput = page.locator('input[placeholder="••••••"]');
    await otpInput.fill(acc.otp);
    await page.waitForTimeout(200);

    await page.locator('button:has-text("Verify & Enter Portal")').click();
    
    // Wait for the home screen header / bottom nav to appear
    await page.waitForTimeout(3500);

    await page.screenshot({
      path: `C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots/${acc.shot}`
    });
    console.log(`[PASS] ${acc.name} Dashboard captured! Saved ${acc.shot}`);
  }

  await browser.close();
  console.log('ALL DASHBOARDS CAPTURED!');
}

testAllTeamDashboards().catch(console.error);
