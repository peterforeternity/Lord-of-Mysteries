import { test, expect, Page } from "@playwright/test";

/**
 * Latency measurement for "调查进度" button → modal visible.
 *
 * Measures the time from clicking the "调查进度" button to the modal
 * being fully visible.
 *
 * Reports: p50, p95, p99, max across 100 samples.
 *
 * Uses the same startNewGame flow as the existing tests (tests 9-16)
 * to ensure the zustand store is properly initialized.
 */

const SAMPLE_COUNT = 100;

async function startNewGame(page: Page) {
  await page.locator("text=新游戏").click();
  await page.waitForURL("**/case-select");
  await expect(page.locator("text=案件选择").first()).toBeVisible({
    timeout: 5000,
  });
  await expect(page.locator("text=钟表匠失踪案").first()).toBeVisible({
    timeout: 10000,
  });
  await page.locator("text=钟表匠失踪案").first().click();
  await expect(page.locator("text=开始调查").first()).toBeVisible({
    timeout: 3000,
  });
  await page.locator("text=开始调查").first().click();
  await page.waitForURL("**/game");
}

test.describe("Latency Measurement", () => {
  test("measure popup latency (100 samples)", async ({ page }) => {
    // Navigate to home
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "诡秘之主" })
    ).toBeVisible({ timeout: 10000 });

    // Start new game via UI (this sets the zustand store)
    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Debug: wait for page to be stable
    await page.waitForLoadState("networkidle");

    // Use the same locator style as the existing passing tests
    const progressBtn = page.locator("text=调查进度").first();
    await expect(progressBtn).toBeVisible({ timeout: 5000 });

    const latencies: number[] = [];

    for (let i = 0; i < SAMPLE_COUNT; i++) {
      await expect(progressBtn).toBeVisible({ timeout: 3000 });

      const start = performance.now();

      await progressBtn.click();
      await page.waitForTimeout(100);

      // Use same approach as test 9: wait for "调查阶段"
      await expect(page.locator("text=调查阶段").first()).toBeVisible({
        timeout: 5000,
      });

      const end = performance.now();
      latencies.push(end - start);

      // Close modal - use same approach as test 9
      await page.locator("text=继续调查").first().click();

      // Wait for modal to close
      await expect(page.locator("text=调查阶段")).toHaveCount(0);

      // Brief pause between iterations
      await page.waitForTimeout(50);
    }

    // Sort latencies for percentile calculation
    latencies.sort((a, b) => a - b);

    const p50 = latencies[Math.floor(SAMPLE_COUNT * 0.5)];
    const p95 = latencies[Math.floor(SAMPLE_COUNT * 0.95)];
    const p99 = latencies[Math.floor(SAMPLE_COUNT * 0.99)];
    const max = latencies[SAMPLE_COUNT - 1];
    const min = latencies[0];
    const avg = latencies.reduce((a, b) => a + b, 0) / SAMPLE_COUNT;

    // Log results
    const results = {
      samples: SAMPLE_COUNT,
      p50: Math.round(p50 * 100) / 100,
      p95: Math.round(p95 * 100) / 100,
      p99: Math.round(p99 * 100) / 100,
      max: Math.round(max * 100) / 100,
      min: Math.round(min * 100) / 100,
      avg: Math.round(avg * 100) / 100,
    };

    console.log("\n=== Latency Measurement Results ===");
    console.log(JSON.stringify(results, null, 2));
    console.log(`Samples: ${SAMPLE_COUNT}`);
    console.log(`Min:  ${min.toFixed(2)}ms`);
    console.log(`p50:  ${p50.toFixed(2)}ms`);
    console.log(`p95:  ${p95.toFixed(2)}ms`);
    console.log(`p99:  ${p99.toFixed(2)}ms`);
    console.log(`Max:  ${max.toFixed(2)}ms`);
    console.log(`Avg:  ${avg.toFixed(2)}ms`);

    // Attach full results
    test.info().attach("latency-results", {
      body: JSON.stringify(
        { ...results, all: latencies.map((v) => Math.round(v * 100) / 100) },
        null,
        2
      ),
      contentType: "application/json",
    });

    // Target: p95 ≤ 1000ms (generous threshold for dev environment with HMR)
    expect(p95).toBeLessThanOrEqual(1000);
  });
});
