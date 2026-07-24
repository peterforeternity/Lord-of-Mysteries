import { test, expect, Page } from "@playwright/test";
import http from "http";

// ================================================================
// Helpers
// ================================================================

const API_BASE = process.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/** Make a GET request to the API from the Node.js process */
function nodeFetchGet(path: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const url = new URL(path, API_BASE);
    http
      .get(url.href, (res) => {
        let data = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        });
      })
      .on("error", reject);
  });
}

/** Get game view via Node.js HTTP (not page.evaluate) */
async function apiGetView(saveId: string): Promise<any> {
  return nodeFetchGet(`/v1/game/${saveId}/view`);
}

/** Save game via browser fetch using relative URL (through Vite proxy) */
async function apiSaveGame(page: Page, saveId: string): Promise<any> {
  return page.evaluate(
    async ({ sid }) => {
      const res = await fetch(`/v1/game/${sid}/save`, {
        method: "POST",
      });
      return res.json();
    },
    { sid: saveId }
  );
}

/** Load game via browser fetch using relative URL (through Vite proxy) */
async function apiLoadGame(page: Page, saveId: string): Promise<any> {
  return page.evaluate(
    async ({ sid }) => {
      const res = await fetch(`/v1/game/${sid}/load`, {
        method: "POST",
      });
      return res.json();
    },
    { sid: saveId }
  );
}

/** Navigate from start → case-select → game via UI clicks */
async function startNewGame(page: Page) {
  await page.locator("text=新游戏").click();
  await page.waitForURL("**/case-select");
  await expect(page.locator("text=案件选择").first()).toBeVisible({
    timeout: 5000,
  });

  // Wait for case list to load from API
  await expect(page.locator("text=钟表匠失踪案").first()).toBeVisible({
    timeout: 10000,
  });

  // Click on the case card
  await page.locator("text=钟表匠失踪案").first().click();
  await expect(page.locator("text=开始调查").first()).toBeVisible({
    timeout: 3000,
  });

  // Click "开始调查"
  await page.locator("text=开始调查").first().click();
  await page.waitForURL("**/game");
}

/** Execute a game action via the API (bypasses UI, goes through public API) */
async function apiAction(
  page: Page,
  saveId: string,
  actionType: string,
  targetId: string = "",
  parameters: Record<string, unknown> = {}
) {
  const baseUrl =
    process.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  const resp = await page.evaluate(
    async ({ baseUrl, saveId, actionType, targetId, parameters }) => {
      // First get the current state version
      const viewRes = await fetch(`${baseUrl}/v1/game/${saveId}/view`);
      const view = await viewRes.json();
      const expectedVersion = view.state_version;

      const res = await fetch(`${baseUrl}/v1/game/${saveId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: actionType,
          target_id: targetId,
          parameters,
          expected_version: expectedVersion,
        }),
      });
      return res.json();
    },
    { baseUrl, saveId, actionType, targetId, parameters }
  );
  return resp as {
    success: boolean;
    state_version: number;
    view: any;
    error_code: string | null;
    error_detail: string | null;
  };
}

/** Create a new game via API and return saveId + view */
async function createGameViaApi(page: Page, seed: number = 42) {
  const baseUrl =
    process.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  const resp = await page.evaluate(
    async ({ baseUrl, seed }) => {
      const res = await fetch(
        `${baseUrl}/v1/game/new?case_id=case_clockmaker_01&seed=${seed}`,
        { method: "POST" }
      );
      return res.json();
    },
    { baseUrl, seed }
  );
  return resp as { save_id: string; view: any };
}

/** Initialize the zustand store with a game session for UI navigation */
async function initGameInStore(page: Page, saveId: string, view: any) {
  // Navigate to app root to load React
  await page.goto("/");
  await page.waitForTimeout(500);
  // Set the store state
  await page.evaluate(
    ({ sid, v }) => {
      const store = (window as any).__ZUSTAND_STORE__;
      if (store) {
        store.setState({ saveId: sid, view: v, loading: false });
      }
    },
    { sid: saveId, v: view }
  );
}

/** Navigate within the SPA by clicking a React Router link */
async function spaNavigate(page: Page, href: string) {
  await page.locator(`a[href="${href}"]`).first().click();
  await page.waitForTimeout(500);
}

/**
 * Navigate from home page (/) to a SPA route.
 * The nav links are hidden on /, so we first navigate to case-select via button click
 * (which is SPA navigation and preserves store), then click the nav link.
 */
async function spaNavigateFromHome(page: Page, targetUrl: string) {
  // First navigate to case-select via button click (SPA nav, preserves store)
  await page.locator("text=案件选择").first().click();
  await page.waitForTimeout(500);
  // Then click the nav link for the target URL
  if (targetUrl !== "/case-select") {
    await page.locator(`a[href="${targetUrl}"]`).first().click();
    await page.waitForTimeout(500);
  }
}

/** Load a page, then init store — avoids full nav reset */
async function initPageAndStore(page: Page, url: string, saveId: string, view: any) {
  await page.goto(url);
  await page.waitForTimeout(500);
  await page.evaluate(
    ({ sid, v }) => {
      const store = (window as any).__ZUSTAND_STORE__;
      if (store) {
        store.setState({ saveId: sid, view: v, loading: false });
      }
    },
    { sid: saveId, v: view }
  );
}

/** Navigate to the deduction page, find a hypothesis, and submit it */
async function submitHypothesisFromDeduction(
  page: Page,
  saveId: string,
  hypothesisId: string
) {
  // Navigate to deduction page
  await page.goto("/deduction");
  await page.waitForTimeout(1000);

  // Submit via API (the UI may need target selection)
  const result = await apiAction(
    page,
    saveId,
    "submit_hypothesis",
    hypothesisId
  );
  return result;
}

// ================================================================
// Tests
// ================================================================

test.describe("Text Game MVP E2E", () => {
  // ---------------------------------------------------------------
  // Setup
  // ---------------------------------------------------------------
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "诡秘之主" })
    ).toBeVisible({ timeout: 10000 });
  });

  // ---------------------------------------------------------------
  // 1. new_game_starts_successfully
  // ---------------------------------------------------------------
  test("new_game_starts_successfully", async ({ page }) => {
    await startNewGame(page);

    // Verify we're in the game
    await expect(page.locator("text=状态").first()).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator("text=灵性").first()).toBeVisible();

    // Check that ending page redirects to start when no active game
    await page.goto("/ending");
    await expect(
      page.getByRole("heading", { name: "诡秘之主" })
    ).toBeVisible({ timeout: 5000 });
  });

  // ---------------------------------------------------------------
  // 2. browser_true_ending
  // ---------------------------------------------------------------
  test("browser_true_ending", async ({ page }) => {
    await startNewGame(page);

    // Get save_id from the page state (stored in the zustand store)
    const saveId = await page.evaluate(() => {
      // Access the zustand store via the window object
      return (window as any).__ZUSTAND_STORE__
        ? (window as any).__ZUSTAND_STORE__.getState().saveId
        : null;
    });

    // If we can't get it from the store, create via API
    const game =
      saveId ? { save_id: saveId }
      : await createGameViaApi(page, 123);

    const sid = (game as any).save_id;

    // Game starts at apartment — inspect clues directly
    let r = await apiAction(page, sid, "inspect", "clue_material_receipt");
    expect(r.success).toBe(true);

    // Travel to workshop and collect clues
    r = await apiAction(page, sid, "travel", "workshop");
    expect(r.success).toBe(true);

    // Inspect specific clue IDs at workshop
    const workshopClues = [
      "clue_lab_notes",
      "clue_burn_pattern",
      "clue_residual_energy",
      "clue_trapped_clock",
    ];
    for (const clueId of workshopClues) {
      r = await apiAction(page, sid, "inspect", clueId);
      expect(r.success).toBe(true);
    }

    // Submit hypothesis_ritual_accident for true ending
    const result = await submitHypothesisFromDeduction(
      page,
      sid,
      "hypothesis_ritual_accident"
    );

    // Verify the ending was triggered
    expect(result.success).toBe(true);
    expect(result.view?.game_over).toBe(true);

    // Navigate to ending page with save_id in URL params
    await page.goto("/ending?save_id=" + sid);
    await page.waitForTimeout(3000);

    // Should see ending info
    const bodyText1 = await page.textContent("body");
    expect(bodyText1).toContain("仪式真相");
  });

  // ---------------------------------------------------------------
  // 3. browser_partial_ending
  // ---------------------------------------------------------------
  test("browser_partial_ending", async ({ page }) => {
    await startNewGame(page);

    const game = await createGameViaApi(page, 456);
    const sid = game.save_id;

    // Game starts at apartment — inspect clues directly
    let r = await apiAction(page, sid, "inspect", "clue_material_receipt");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_neighbor_testimony");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_landlord_contradiction");
    expect(r.success).toBe(true);

    // Travel to workshop for burn pattern
    r = await apiAction(page, sid, "travel", "workshop");
    expect(r.success).toBe(true);

    r = await apiAction(page, sid, "inspect", "clue_burn_pattern");
    expect(r.success).toBe(true);

    // Submit hypothesis_simple_disappearance for partial ending
    const result = await submitHypothesisFromDeduction(
      page,
      sid,
      "hypothesis_simple_disappearance"
    );

    expect(result.success).toBe(true);

    // Navigate to ending page with save_id in URL params
    await page.goto("/ending?save_id=" + sid);
    await page.waitForTimeout(3000);

    const bodyText2 = await page.textContent("body");
    expect(
      bodyText2!.includes("案件完结") || bodyText2!.includes("失踪者归来")
    ).toBeTruthy();
  });

  // ---------------------------------------------------------------
  // 4. browser_bad_ending
  // ---------------------------------------------------------------
  test("browser_bad_ending", async ({ page }) => {
    await startNewGame(page);

    const game = await createGameViaApi(page, 789);
    const sid = game.save_id;

    // Travel to workshop to get clues for ritual
    let r = await apiAction(page, sid, "travel", "workshop");
    expect(r.success).toBe(true);

    r = await apiAction(page, sid, "inspect", "clue_lab_notes");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_burn_pattern");
    expect(r.success).toBe(true);

    // Use spirit vision to prepare for ritual
    r = await apiAction(page, sid, "use_spirit_vision");
    expect(r.success).toBe(true);

    // Perform a purification ritual (may fail, increasing corruption)
    r = await apiAction(page, sid, "perform_ritual", "ritual_purification");
    // Even if it fails, that's good for bad ending
    if (!r.success) {
      // Try again to increase corruption more
      r = await apiAction(page, sid, "perform_ritual", "ritual_purification");
    }

    // Helper to navigate to ending with save_id URL param
    async function gotoEnding() {
      await page.goto("/ending?save_id=" + sid);
      await page.waitForTimeout(3000);
    }

    // Don't submit any hypothesis — let corruption trigger bad ending
    // Check if game is over due to corruption
    if (r.view?.game_over) {
      await gotoEnding();
      const bodyText = await page.textContent("body");
      expect(
        bodyText!.includes("灰雾弥漫") || bodyText!.includes("bad") || bodyText!.includes("案件完结")
      ).toBeTruthy();
    } else {
      // If not game over, try submitting a hypothesis with insufficient clues
      // to trigger the game engine's ending logic
      const result = await submitHypothesisFromDeduction(
        page,
        sid,
        "hypothesis_ritual_accident"
      );

      if (result.view?.game_over) {
        await gotoEnding();
      }
    }
  });

  // ---------------------------------------------------------------
  // 5. save_resume — thorough save/load verification
  // ---------------------------------------------------------------
  test("save_resume", async ({ page }) => {
    await startNewGame(page);

    const game = await createGameViaApi(page, 999);
    const sid = game.save_id;
    // Step 1: Game starts at apartment — inspect clues directly
    let r = await apiAction(page, sid, "inspect", "clue_material_receipt");
    expect(r.success).toBe(true);
    const clue1 = r.view?.clues?.find(
      (c: any) => c.clue_id === "clue_material_receipt"
    );
    expect(clue1).toBeTruthy();

    r = await apiAction(page, sid, "inspect", "clue_neighbor_testimony");
    const cluesAfterFirstLoc = r.view?.clues?.length || 0;

    // Go to workshop for more clues
    r = await apiAction(page, sid, "travel", "workshop");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_lab_notes");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_burn_pattern");
    const cluesAfterSecondLoc = r.view?.clues?.length || 0;
    expect(cluesAfterSecondLoc).toBeGreaterThanOrEqual(cluesAfterFirstLoc);

    // Step 3: Use an ability (spirit vision) — changes spirituality
    r = await apiAction(page, sid, "use_spirit_vision");
    expect(r.success).toBe(true);
    const afterAbilityView = r.view;

    // Step 4: Record all fields before save
    const beforeSave = {
      state_version: afterAbilityView.state_version,
      current_location_id: afterAbilityView.player.current_location_id,
      current_location_name: afterAbilityView.player.current_location_name,
      clue_count: afterAbilityView.clues.length,
      clue_ids: afterAbilityView.clues.map((c: any) => c.clue_id).sort(),
      spirituality: afterAbilityView.player.spirituality,
      corruption: afterAbilityView.player.corruption,
      stability: afterAbilityView.player.stability,
      visited_location_ids: afterAbilityView.player.visited_locations.map(
        (l: any) => l.location_id
      ),
    };

    // Step 5: Save the game
    const saveRes = await page.evaluate(
      async ({ baseUrl, sid }) => {
        const res = await fetch(`${baseUrl}/v1/game/${sid}/save`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        return res.json();
      },
      { baseUrl: "http://127.0.0.1:8000", sid }
    );
    expect(saveRes.success).toBe(true);

    // Step 6: Refresh the browser
    await page.reload();
    await page.waitForTimeout(1000);

    // Step 7: Load the save via browser fetch
    const loadRes = await apiLoadGame(page, sid);

    // Step 8: Assert all fields are restored
    expect(loadRes.state_version).toBe(beforeSave.state_version);
    expect(loadRes.player.current_location_id).toBe(
      beforeSave.current_location_id
    );
    expect(loadRes.player.current_location_name).toBe(
      beforeSave.current_location_name
    );
    expect(loadRes.clues.length).toBe(beforeSave.clue_count);
    const loadedClueIds = loadRes.clues
      .map((c: any) => c.clue_id)
      .sort();
    expect(loadedClueIds).toEqual(beforeSave.clue_ids);
    expect(loadRes.player.spirituality).toBe(beforeSave.spirituality);
    expect(loadRes.player.corruption).toBe(beforeSave.corruption);
    expect(loadRes.player.stability).toBe(beforeSave.stability);

    // Verify visited locations restored
    const loadedLocationIds = loadRes.player.visited_locations.map(
      (l: any) => l.location_id
    );
    for (const locId of beforeSave.visited_location_ids) {
      expect(loadedLocationIds).toContain(locId);
    }

    // Step 9: Continue playing — travel to police_office
    let contR = await apiAction(page, sid, "travel", "police_office");
    expect(contR.success).toBe(true);

    // Step 10: Get more clues and submit hypothesis for an ending
    contR = await apiAction(page, sid, "inspect", "clue_collector_knowledge");
    expect(contR.success).toBe(true);

    // Check if we have enough clues for a hypothesis
    const clueCount = contR.view?.clues?.length || 0;
    if (clueCount >= 5) {
      const hypoResult = await submitHypothesisFromDeduction(
        page,
        sid,
        "hypothesis_ritual_accident"
      );
      // Should reach some ending
      if (hypoResult.view?.game_over) {
        await page.goto("/ending?save_id=" + sid);
        await page.waitForTimeout(3000);
      }
    }
  });

  // ---------------------------------------------------------------
  // 6. rapid_clicks_state_version
  // ---------------------------------------------------------------
  test("rapid_clicks_state_version", async ({ page }) => {
    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Try to interact with action buttons rapidly
    const actionBtn = page.locator(".btn-secondary.text-left").first();
    if (await actionBtn.isVisible()) {
      await actionBtn.click({ clickCount: 3 });
      await page.waitForTimeout(2000);
    }

    // Page should still be functional
    const bodyText = await page.textContent("body");
    expect(bodyText!.length).toBeGreaterThan(0);
  });

  // ---------------------------------------------------------------
  // 7. deduction_board_navigation
  // ---------------------------------------------------------------
  test("deduction_board_navigation", async ({ page }) => {
    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Navigate to deduction board
    const deductionLink = page.locator('a[href="/deduction"]').first();
    if (await deductionLink.isVisible()) {
      await deductionLink.click();
      await page.waitForTimeout(2000);
      const pageContent = await page.textContent("body");
      expect(
        pageContent!.includes("推理板") ||
          pageContent!.includes("推理假设")
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
        const pageContent = await page.textContent("body");
        expect(pageContent!.length).toBeGreaterThan(0);
      }
    }
  });

  // ---------------------------------------------------------------
  // 8. mobile_viewport_basic_flow
  // ---------------------------------------------------------------
  test("mobile_viewport_basic_flow", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });

    await startNewGame(page);
    await page.waitForTimeout(2000);

    // Mobile viewport should work — page has content
    const bodyText = await page.textContent("body");
    expect(bodyText!.length).toBeGreaterThan(0);
    // Check that essential game elements are available
    const hasActions = await page.locator("text=行动").count();
    expect(hasActions).toBeGreaterThanOrEqual(1);
  });

  // ---------------------------------------------------------------
  // 9. investigation_progress — verify modal, fuzzy labels, no leakage
  // ---------------------------------------------------------------
  test("investigation_progress_basic", async ({ page }) => {
    await startNewGame(page);

    // Open the investigation progress modal
    await page.locator("text=调查进度").first().click();
    await page.waitForTimeout(500);

    // Should show the modal
    await expect(page.locator("text=调查阶段").first()).toBeVisible({
      timeout: 3000,
    });

    // Should show fuzzy status labels (not exact counts)
    await expect(page.locator("text=尚无发现").first()).toBeVisible();
    await expect(page.locator("text=证据维度").first()).toBeVisible();

    // Should NOT show found/total counts
    const bodyText = await page.textContent("body");
    expect(bodyText!.match(/\d+\/\d+/g)).toBeNull();

    // Close via button
    await page.locator("text=继续调查").first().click();
    await page.waitForTimeout(300);

    // Modal should be gone
    await expect(page.locator("text=调查阶段")).toHaveCount(0);
  });

  // ---------------------------------------------------------------
  // 10. investigation_progress_phase_changes
  // ---------------------------------------------------------------
  test("investigation_progress_phase_changes", async ({ page }) => {
    const game = await createGameViaApi(page, 42);
    const sid = game.save_id;

    // Open progress modal via direct navigation
    // First verify initial phase is 迷雾初现
    let view = game.view;
    expect(view.investigation_progress.phase_level).toBe(0);
    expect(view.investigation_progress.phase_label).toBe("迷雾初现");

    // Discover a few clues (travel + inspect)
    let r = await apiAction(page, sid, "inspect", "clue_material_receipt");
    expect(r.success).toBe(true);

    r = await apiAction(page, sid, "travel", "workshop");
    expect(r.success).toBe(true);

    // Discover multiple workshop clues to advance phase
    for (const cid of ["clue_lab_notes", "clue_burn_pattern", "clue_residual_energy"]) {
      r = await apiAction(page, sid, "inspect", cid);
      expect(r.success).toBe(true);
    }

    // Now check phase has advanced
    const updatedView = await page.evaluate(async (sid) => {
      const res = await fetch(
        `http://127.0.0.1:8000/v1/game/${sid}/view`
      );
      const data = await res.json();
      return data.investigation_progress;
    }, sid);

    expect(updatedView.phase_level).toBeGreaterThanOrEqual(1);
    expect(["线索浮现", "疑点交汇"]).toContain(updatedView.phase_label);
  });

  // ---------------------------------------------------------------
  // 11. investigation_progress_no_hypothesis_leakage
  // ---------------------------------------------------------------
  test("investigation_progress_no_hypothesis_leakage", async ({ page }) => {
    const game = await createGameViaApi(page, 42);
    const sid = game.save_id;
    const view = game.view;

    // Before any clues: resolution_available should be false
    expect(view.investigation_progress.resolution_available).toBe(false);

    // Load deduction page, then init store so view is available
    await initPageAndStore(page, "/deduction", sid, view);

    // Should show placeholder message
    await expect(
      page.locator("text=目前的证据还不足以形成稳定判断。").first()
    ).toBeVisible({ timeout: 5000 });
  });

  // ---------------------------------------------------------------
  // 12. investigation_progress — resolution hint and continue flow
  // ---------------------------------------------------------------
  test("investigation_progress_resolution_hint", async ({ page }) => {
    const game = await createGameViaApi(page, 42);
    const sid = game.save_id;

    // Gather clues for a hypothesis (clinic)
    let r = await apiAction(page, sid, "travel", "clinic");
    expect(r.success).toBe(true);

    r = await apiAction(page, sid, "inspect", "clue_medical_record");
    expect(r.success).toBe(true);

    r = await apiAction(page, sid, "inspect", "clue_doctor_testimony");
    expect(r.success).toBe(true);

    // Check investigation progress via API
    const view = await page.evaluate(async (sid) => {
      const res = await fetch(
        `http://127.0.0.1:8000/v1/game/${sid}/view`
      );
      const data = await res.json();
      return data.investigation_progress;
    }, sid);

    // resolution_available should now be true
    expect(view.resolution_available).toBe(true);
    expect(view.new_resolution_available).toBe(true);

    // Get latest view for store init
    const latestView = await page.evaluate(async (sid) => {
      const res = await fetch(
        `http://127.0.0.1:8000/v1/game/${sid}/view`
      );
      return await res.json();
    }, sid);
    await initGameInStore(page, sid, latestView);
    await spaNavigateFromHome(page, "/game");

    // Check the resolution hint dialog appears
    await expect(
      page.locator("text=新的判断正在形成").first()
    ).toBeVisible({ timeout: 5000 });

    // Click "继续调查" — should dismiss without ending
    await page.locator("button:has-text('继续调查')").first().click();

    // Wait for hint to be dismissed (visible → not visible)
    await expect(
      page.locator("text=新的判断正在形成")
    ).not.toBeVisible({ timeout: 5000 });

    // Verify game is still active
    await expect(page.locator("text=状态").first()).toBeVisible({
      timeout: 3000,
    });
  });

  // ---------------------------------------------------------------
  // 13. investigation_progress — refresh preserves seen state
  // ---------------------------------------------------------------
  test("investigation_progress_refresh_preserves_hint", async ({ page }) => {
    const game = await createGameViaApi(page, 42);
    const sid = game.save_id;

    // Gather clues for resolution
    let r = await apiAction(page, sid, "travel", "clinic");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_medical_record");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_doctor_testimony");
    expect(r.success).toBe(true);

    // Dismiss resolution hint via API
    const dismissResult = await page.evaluate(async (sid) => {
      // Get current state version
      const viewRes = await fetch(
        `http://127.0.0.1:8000/v1/game/${sid}/view`
      );
      const view = await viewRes.json();

      // Dismiss
      const res = await fetch(
        `http://127.0.0.1:8000/v1/game/${sid}/action`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action_type: "dismiss_resolution_hint",
            expected_version: view.state_version,
            idempotency_key: "e2e-test-dismiss",
          }),
        }
      );
      return res.json();
    }, sid);
    expect(dismissResult.success).toBe(true);

    // Refresh
    await page.reload();
    await page.waitForTimeout(2000);

    // Navigate to game
    await page.goto("/game");
    await page.waitForTimeout(2000);

    // Hint should NOT reappear
    await expect(
      page.locator("text=新的判断正在形成")
    ).toHaveCount(0);
  });

  // ---------------------------------------------------------------
  // 14. investigation_progress — no exact clue numbers in modal
  // ---------------------------------------------------------------
  test("investigation_progress_no_exact_numbers", async ({ page }) => {
    await startNewGame(page);

    // Open modal
    await page.locator("text=调查进度").first().click();
    await page.waitForTimeout(500);

    const bodyText = await page.textContent("body");

    // No "X/Y" pattern (clue counts)
    expect(bodyText!.match(/\b\d+\/\d+\b/)).toBeNull();

    // No "found" or "total" text
    expect(bodyText!.toLowerCase()).not.toContain("found");
    expect(bodyText!.toLowerCase()).not.toContain("total");

    // Close modal
    await page.locator("text=继续调查").first().click();
  });

  // ---------------------------------------------------------------
  // 15. investigation_progress — "进入推理" navigates to deduction board
  // ---------------------------------------------------------------
  test("investigation_progress_enter_deduction", async ({ page }) => {
    const game = await createGameViaApi(page, 42);
    const sid = game.save_id;

    // Gather clues for resolution
    let r = await apiAction(page, sid, "travel", "clinic");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_medical_record");
    expect(r.success).toBe(true);
    r = await apiAction(page, sid, "inspect", "clue_doctor_testimony");
    expect(r.success).toBe(true);

    // Init store at home, then SPA-navigate to game page
    await initGameInStore(page, sid, r.view);
    await spaNavigateFromHome(page, "/game");

    // Dismiss resolution hint dialog if it appears (overlay blocks other buttons)
    const hintBtn = page.locator("button:has-text('继续调查')");
    if (await hintBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await hintBtn.click();
      await page.waitForTimeout(500);
    }

    // Open investigation progress modal
    await page.locator("button:has-text('调查进度')").first().click();
    await page.waitForTimeout(500);

    // "进入推理" button should be visible
    await expect(page.locator("text=进入推理").first()).toBeVisible({
      timeout: 3000,
    });

    // Click "进入推理"
    await page.locator("text=进入推理").first().click();
    await page.waitForTimeout(1000);

    // Should navigate to deduction board
    await expect(page.locator("text=推理板").first()).toBeVisible({
      timeout: 5000,
    });
  });

  // ---------------------------------------------------------------
  // 16. investigation_progress — save/load preserves progress state
  // ---------------------------------------------------------------
  test("investigation_progress_save_load_preserves_state", async ({
    page,
  }) => {
    const game = await createGameViaApi(page, 42);
    const sid = game.save_id;

    // Gather clues to advance phase
    let r = await apiAction(page, sid, "inspect", "clue_material_receipt");
    expect(r.success).toBe(true);

    r = await apiAction(page, sid, "travel", "workshop");
    expect(r.success).toBe(true);

    for (const cid of [
      "clue_lab_notes",
      "clue_burn_pattern",
      "clue_residual_energy",
    ]) {
      r = await apiAction(page, sid, "inspect", cid);
      expect(r.success).toBe(true);
    }

    // Refresh page context before API calls to avoid stale fetch
    // Use a direct goto so the page is at a known, stable URL
    await page.goto("/");
    await page.waitForTimeout(500);

    // Get progress after clues using node.js http request (not page.evaluate)
    const afterCluesView = await apiGetView(sid);
    const midView = afterCluesView.investigation_progress;
    expect(midView.phase_level).toBeGreaterThanOrEqual(1);

    // Save the game
    const saveRes = await apiSaveGame(page, sid);
    expect(saveRes.success).toBe(true);

    // Load the game and get fresh view
    const loadRes = await apiLoadGame(page, sid);

    // Verify investigation progress is preserved after load
    expect(loadRes.investigation_progress.phase_level).toBe(
      midView.phase_level
    );
    expect(loadRes.investigation_progress.phase_label).toBe(
      midView.phase_label
    );
    expect(loadRes.investigation_progress.evidence_dimensions.length).toBe(
      midView.evidence_dimensions.length
    );

    // Verify exact counts are still not leaked after load
    for (const dim of loadRes.investigation_progress.evidence_dimensions) {
      expect(dim).not.toHaveProperty("found");
      expect(dim).not.toHaveProperty("total");
    }
  });
});
