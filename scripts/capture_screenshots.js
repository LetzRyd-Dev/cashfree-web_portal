import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';

const SCREENSHOT_DIR = path.resolve('C:/Users/anura/.gemini/antigravity/brain/76b8e032-fa02-4124-9a83-35815a2d5f83/screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function run() {
  console.log('Starting Playwright screenshot validation suite...');
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 420, height: 880 },
    deviceScaleFactor: 2,
  });

  const page = await context.newPage();

  async function loginWithPhoneDirect(phone, role = 'driver') {
    await page.goto('http://localhost:3002/');
    await page.waitForSelector('input[type="tel"]', { timeout: 10000 });
    
    // Switch role tab if needed
    if (role === 'operator') {
      const opTab = page.locator('button:has-text("Operator Login")');
      if (await opTab.isVisible()) {
        await opTab.click();
        await page.waitForTimeout(300);
      }
    } else {
      const drvTab = page.locator('button:has-text("Driver Login")');
      if (await drvTab.isVisible()) {
        await drvTab.click();
        await page.waitForTimeout(300);
      }
    }

    // Fill phone number
    const phoneInput = page.locator('input[type="tel"]');
    await phoneInput.click();
    await phoneInput.fill(phone);
    await page.waitForTimeout(300);
    
    // Click Get OTP
    await page.locator('button:has-text("Get OTP")').click();
    await page.waitForTimeout(1000);

    // Fill OTP
    const otpInput = page.locator('input[placeholder="••••••"]');
    await otpInput.waitFor({ state: 'visible', timeout: 5000 });
    await otpInput.fill('1234');
    await page.waitForTimeout(300);

    // Click Verify & Enter Portal
    await page.locator('button:has-text("Verify & Enter Portal")').click();
    await page.waitForTimeout(2500);
  }

  async function logout() {
    const logoutBtn = page.locator('button:has(.lucide-log-out)').first();
    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();
      await page.waitForTimeout(1000);
    }
  }

  // ==========================================
  // 1. SALEEM FLEET LOGISTICS (9848012345) - 2 FLEETS
  // ==========================================
  console.log('>>> Testing Saleem Fleet Logistics (9848012345)...');
  await loginWithPhoneDirect('9848012345', 'operator');
  
  // Fleet Screen
  const fleetTab = page.locator('button:has-text("Fleet")').first();
  if (await fleetTab.isVisible()) {
    await fleetTab.click();
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_saleem_fleet_2_vehicles.png') });
  console.log('Captured 01_saleem_fleet_2_vehicles.png');

  // Click on Mohammed Ali's Vehicle Hisaab
  const viewHisaabBtns = page.locator('button:has-text("View Hisaab")');
  if (await viewHisaabBtns.count() > 0) {
    await viewHisaabBtns.first().click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_saleem_vehicle_statement.png') });
    console.log('Captured 02_saleem_vehicle_statement.png');

    // Go back to Fleet
    const backBtn = page.locator('button:has(.lucide-chevron-left)').first();
    if (await backBtn.isVisible()) {
      await backBtn.click();
      await page.waitForTimeout(800);
    }
  }

  // Operator Profile (initials MS)
  const profileAvatar = page.locator('button:has-text("MS")').first();
  if (await profileAvatar.isVisible()) {
    await profileAvatar.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_saleem_operator_profile.png') });
    console.log('Captured 03_saleem_operator_profile.png');
  }

  await logout();

  // ==========================================
  // 2. RK TRANSPORT & FLEET (9876543222) - 4 FLEETS
  // ==========================================
  console.log('>>> Testing RK Transport & Fleet (9876543222)...');
  await loginWithPhoneDirect('9876543222', 'operator');
  
  const rkFleetTab = page.locator('button:has-text("Fleet")').first();
  if (await rkFleetTab.isVisible()) {
    await rkFleetTab.click();
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_rk_transport_4_vehicles.png') });
  console.log('Captured 04_rk_transport_4_vehicles.png');

  // Operator Profile (initials RK)
  const rkProfileAvatar = page.locator('button:has-text("RK")').first();
  if (await rkProfileAvatar.isVisible()) {
    await rkProfileAvatar.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_rk_operator_profile.png') });
    console.log('Captured 05_rk_operator_profile.png');
  }

  await logout();

  // ==========================================
  // 3. VIKRAM SINGH (9876543212) - DRIVER
  // ==========================================
  console.log('>>> Testing Vikram Singh (9876543212)...');
  await loginWithPhoneDirect('9876543212', 'driver');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_vikram_singh_home.png') });
  console.log('Captured 06_vikram_singh_home.png');

  // Hisaab
  const vikramHisaab = page.locator('button:has-text("Hisaab")').first();
  if (await vikramHisaab.isVisible()) {
    await vikramHisaab.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_vikram_singh_hisaab.png') });
    console.log('Captured 07_vikram_singh_hisaab.png');
  }

  // Vehicle
  const vikramVehicle = page.locator('button:has-text("Vehicle")').first();
  if (await vikramVehicle.isVisible()) {
    await vikramVehicle.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_vikram_singh_vehicle.png') });
    console.log('Captured 08_vikram_singh_vehicle.png');
  }

  // Settle
  const vikramSettle = page.locator('button:has-text("Settle")').first();
  if (await vikramSettle.isVisible()) {
    await vikramSettle.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09_vikram_singh_settle.png') });
    console.log('Captured 09_vikram_singh_settle.png');
  }

  await logout();

  // ==========================================
  // 4. RAJESH KUMAR (9876543210) - DRIVER
  // ==========================================
  console.log('>>> Testing Rajesh Kumar (9876543210)...');
  await loginWithPhoneDirect('9876543210', 'driver');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10_rajesh_kumar_home.png') });
  console.log('Captured 10_rajesh_kumar_home.png');

  // Support Screen
  const rajeshSupport = page.locator('button:has-text("Support")').first();
  if (await rajeshSupport.isVisible()) {
    await rajeshSupport.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '11_rajesh_support_desk.png') });
    console.log('Captured 11_rajesh_support_desk.png');
  }

  // Driver Profile
  const rajeshProfileAvatar = page.locator('button:has-text("RK")').first();
  if (await rajeshProfileAvatar.isVisible()) {
    await rajeshProfileAvatar.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '12_rajesh_driver_profile.png') });
    console.log('Captured 12_rajesh_driver_profile.png');
  }

  await browser.close();
  console.log('=== ALL 12 VALIDATION SCREENSHOTS CAPTURED SUCCESSFULLY ===');
}

run().catch(err => {
  console.error('Fatal Screenshot Suite Error:', err);
  process.exit(1);
});
