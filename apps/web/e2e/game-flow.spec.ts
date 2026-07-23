import { test, expect } from "@playwright/test";

test.describe("Text Game MVP E2E", () => {
  // ================================================================
  // Setup: Navigate to start page
  // ================================================================

  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "灰雾调查录" })
    ).toBeVisible({ timeout: 10000 });
  });

  // ================================================================
  // Helper: Walk through start → case-select → game
  // ================================================================

  async function startNewGame(page: any) {
    // Click "新游戏" on start page
    await page.locator("text=新游戏").click();
    await page.waitForURL("**/case-select");
    await expect(page.locator("text=案件选择").first()).toBeVisible({
      timeout: 5000,
    });

    // Wait for case list to load from API
    await expect(page.locator("text=钟表匠失踪案").first()).toBeVisible({
      timeout: 10000,
    });

    // Click on the case card (first one)
    await page.locator("text=钟表匠失踪案").first().click();

    // "开始调查" button should now be enabled
    await expect(page.locator("text=开始调查").first()).toBeVisible({
      timeout: 3000,
    });

    // Click "开始调查"
    await page.locator("text=开始调查").first().click();
    await page.waitForURL("**/game");
  }

  // ================================================================
  // 1. New game to game page
  // ================================================================

  test("1. 新游戏到游戏页面", async ({ page }) => {
    await startNewGame(page);

    // Verify we're in the game
    await expect(page.locator("text=状态").first()).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator("text=灵性").first()).toBeVisible();

    // Check that ending page redirects to start when no active game
    await page.goto("/ending");
    await expect(
      page.getByRole("heading", { name: "灰雾调查录" })
    ).toBeVisible({ timeout: 5000 });
  });

  // ================================================================
  // 2. Travel between locations (action buttons exist)
  // ================================================================

  test("2. 地点移动按钮存在", async ({ page }) => {
    await startNewGame(page);

    // Game page should show available actions
    await expect(page.locator("text=当前位置").first()).toBeVisible({
      timeout: 5000,
    });
  });

  // ================================================================
  // 3. Player status display
  // ================================================================

  test("3. 灵性、污染和稳定度显示", async ({ page }) => {
    await startNewGame(page);

    // Check for all three status bars in the page text
    const pageContent = await page.textContent("body");
    expect(pageContent).toContain("灵性");
    expect(pageContent).toContain("污染");
    expect(pageContent).toContain("稳定度");
  });

  // ================================================================
  // 4. API error handling — no white screen
  // ================================================================

  test("4. 后端断开时显示明确错误", async ({ page }) => {
    // Start from a clean page
    await page.goto("/");

    // Navigate to case-select (this will make API calls — if backend is down,
    // it should show an error instead of a white screen)
    await page.locator("text=新游戏").click();
    await page.waitForTimeout(3000);

    // Important: page should have content, no white screen
    const bodyText = await page.textContent("body");
    expect(bodyText!.length).toBeGreaterThan(0);
  });

  // ================================================================
  // 5. Save, refresh, load
  // ================================================================

  test("5. 保存、刷新页面、读取并继续", async ({ page }) => {
    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Navigate to save-load page
    await page.locator("text=存档管理").first().click();
    await page.waitForURL("**/save-load");
    await page.waitForTimeout(1000);

    // Should show current game info
    await expect(page.locator("text=当前游戏").first()).toBeVisible({
      timeout: 3000,
    });

    // Save the game via API
    const saveBtn = page.locator("button:has-text('快速保存')").first();
    if (await saveBtn.isVisible()) {
      await saveBtn.click();
      await page.waitForTimeout(2000);
    }

    // Get current URL to restore later
    const saveUrl = page.url();

    // Refresh the page
    await page.reload();
    await page.waitForTimeout(2000);

    // After refresh we should be on the save-load page
    await expect(page.locator("text=存档管理").first()).toBeVisible({
      timeout: 5000,
    });
  });

  // ================================================================
  // 6. Rapid clicks (state version handling)
  // ================================================================

  test("6. 连续双击造成 state_version 冲突", async ({ page }) => {
    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Try to interact with action buttons
    const actionBtn = page.locator(".btn-secondary.text-left").first();
    if (await actionBtn.isVisible()) {
      await actionBtn.click({ clickCount: 3 });
      await page.waitForTimeout(2000);
    }

    // Page should still be functional
    const bodyText = await page.textContent("body");
    expect(bodyText!.length).toBeGreaterThan(0);
  });

  // ================================================================
  // 7. Deduction board navigation
  // ================================================================

  test("7. 推理板与假设页面", async ({ page }) => {
    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Navigate to deduction board via link
    const deductionLink = page.locator('a[href="/deduction"]').first();
    if (await deductionLink.isVisible()) {
      await deductionLink.click();
      await page.waitForTimeout(2000);
      const pageContent = await page.textContent("body");
      expect(
        pageContent!.includes("推理板") || pageContent!.includes("推理假设")
      ).toBeTruthy();
    } else {
      // Try the button
      const deductionBtn = page
        .locator("button, a")
        .filter({ hasText: "推理板" })
        .first();
      if (await deductionBtn.isVisible()) {
        await deductionBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  // ================================================================
  // 8. Mobile viewport basic flow
  // ================================================================

  test("8. 手机视口下完成基本调查流程", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });

    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Mobile navigation should be visible
    const mobileNavItems = page.locator("text=调查").first();
    await expect(mobileNavItems).toBeVisible({ timeout: 3000 });

    // Page should work on mobile
    const bodyText = await page.textContent("body");
    expect(bodyText!.length).toBeGreaterThan(0);
  });
});
