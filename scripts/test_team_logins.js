import { chromium } from 'playwright';

async function testTeamLogins() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 420, height: 900 },
    deviceScaleFactor: 2
  });

  const accounts = [
    { name: 'Vivek', phone: '9901484683', role: 'driver', shot: '25_vivek_login_home.png' },
    { name: 'Sushant', phone: '9140631755', role: 'driver', shot: '26_sushant_login_home.png' },
    { name: 'Aayush', phone: '9930420065', role: 'driver', shot: '27_aayush_login_home.png' },
    { name: 'Anurag', phone: '9691938866', role: 'operator', shot: '28_anurag_operator_home.png' },
  ];

  for (const acc of accounts) {
    await page.goto('http://localhost:3002/');
    await page.waitForTimeout(600);

    // If operator role needed, click Operator Login tab
    if (acc.role === 'operator') {
      await page.locator('button:has-text("Operator Login")').click();
      await page.waitForTimeout(200);
    } else {
      await page.locator('button:has-text("Driver Login")').click();
      await page.waitForTimeout(200);
    }

    // Fill phone number
    const phoneInput = page.locator('input[type="tel"]');
    await phoneInput.fill(acc.phone);
    await page.waitForTimeout(200);

    // Click Get OTP
    await page.locator('button:has-text("Get OTP")').click();
    await page.waitForTimeout(600);

    // Fill OTP 1234
    const otpInput = page.locator('input[placeholder="• • • •"]');
    await otpInput.fill('1234');
    await page.waitForTimeout(200);

    // Click Verify & Enter Portal
    await page.locator('button:has-text("Verify & Enter Portal")').click();
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: `C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots/${acc.shot}`
    });
    console.log(`Saved screenshot: ${acc.shot}`);
  }

  await browser.close();
  console.log('All team member logins tested successfully!');
}

testTeamLogins().catch(console.error);
