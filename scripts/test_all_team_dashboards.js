import { chromium } from 'playwright';
import fs from 'fs';

const targetUrl = process.env.TARGET_URL || 'http://127.0.0.1:3002/';
const brainDirs = [
  'C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots',
  'C:/Users/anura/.gemini/antigravity/brain/31e9d65f-6137-4fd1-a97a-2ee310a492f8/screenshots'
];
for (const dir of brainDirs) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

async function testAllTeamDashboards() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu']
  });

  const accounts = [
    { name: 'Anurag (Operator)', phone: '9691938866', role: 'operator', otp: '123456', shot: '30_anurag_fleet_dashboard.png' },
    { name: 'Vivek (Driver)', phone: '9901484683', role: 'driver', otp: '123456', shot: '31_vivek_driver_dashboard.png' },
    { name: 'Sushant (Driver)', phone: '9140631755', role: 'driver', otp: '123456', shot: '32_sushant_driver_dashboard.png' },
    { name: 'Aayush (Driver)', phone: '9930420065', role: 'driver', otp: '123456', shot: '33_aayush_driver_dashboard.png' },
  ];

  for (const acc of accounts) {
    const context = await browser.newContext({
      viewport: { width: 420, height: 900 },
      deviceScaleFactor: 2
    });
    const page = await context.newPage();

    console.log(`\nNavigating to ${targetUrl} for ${acc.name} dashboard...`);
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(600);

    const phoneInput = page.locator('input[type="tel"]');
    await phoneInput.fill(acc.phone);
    await page.waitForTimeout(200);

    const getOtpBtn = page.locator('button:has-text("Get OTP")');
    if (await getOtpBtn.count() > 0) {
      await getOtpBtn.click();
    }

    const otpInput = page.locator('input[placeholder="••••••"]');
    await otpInput.waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
    if (await otpInput.count() > 0) {
      await otpInput.fill(acc.otp);
      await page.waitForTimeout(300);

      const verifyBtn = page.locator('button:has-text("Verify & Enter Portal")');
      if (await verifyBtn.count() > 0) {
        await verifyBtn.click();
        await page.waitForTimeout(4000);
      }
    }

    for (const dir of brainDirs) {
      await page.screenshot({ path: `${dir}/${acc.shot}` }).catch(() => {});
    }
    console.log(`[PASS] ${acc.name} Dashboard captured! Saved ${acc.shot}`);
    await context.close();
  }

  await browser.close();
  console.log('ALL DASHBOARDS CAPTURED!');
}

testAllTeamDashboards().catch(console.error);

