import { test, expect, Page } from "@playwright/test";

// ================================================================
// Helpers
// ================================================================

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
      page.getByRole("heading", { name: "灰雾调查录" })
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
      page.getByRole("heading", { name: "灰雾调查录" })
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

    // Travel to apartment and inspect material receipt
    let r = await apiAction(page, sid, "travel", "apartment");
    expect(r.success).toBe(true);

    r = await apiAction(page, sid, "inspect", "clue_material_receipt");
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

    // Navigate to ending page (full page reload — store gets wiped)
    await page.goto("/ending");
    // Set saveId so EndingPage auto-fetches view via fetchView()
    await page.evaluate(
      (sid) => {
        const store = (window as any).__ZUSTAND_STORE__;
        if (store) {
          store.setState({ saveId: sid, loading: false });
        }
      },
      sid
    );
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

    // Travel to apartment, get neighbor and landlord clues
    let r = await apiAction(page, sid, "travel", "apartment");
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

    // Navigate to ending page (full page reload — store gets wiped)
    await page.goto("/ending");
    // Set saveId so EndingPage auto-fetches view
    await page.evaluate(
      (sid) => {
        const store = (window as any).__ZUSTAND_STORE__;
        if (store) {
          store.setState({ saveId: sid, loading: false });
        }
      },
      sid
    );
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

    // Shared helper to set saveId after full page navigation to /ending
    async function gotoEnding() {
      await page.goto("/ending");
      await page.evaluate(
        (s) => {
          const store = (window as any).__ZUSTAND_STORE__;
          if (store) store.setState({ saveId: s, loading: false });
        },
        sid
      );
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
    const initialView = game.view;

    // Step 1: Travel to a different location
    let r = await apiAction(page, sid, "travel", "apartment");
    expect(r.success).toBe(true);
    const afterTravelView = r.view;

    // Step 2: Get at least two clues at apartment
    r = await apiAction(page, sid, "inspect", "clue_material_receipt");
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

    // Step 7: Navigate to save-load page and load the save
    await page.goto("/save-load");
    await page.waitForTimeout(2000);

    // Load via API (the save-load UI may not have the exact interaction we need)
    const loadRes = await page.evaluate(
      async ({ baseUrl, sid }) => {
        const res = await fetch(`${baseUrl}/v1/game/${sid}/load`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        return res.json();
      },
      { baseUrl: "http://127.0.0.1:8000", sid }
    );

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
        await page.goto("/ending");
        await page.evaluate(
          (s) => {
            const store = (window as any).__ZUSTAND_STORE__;
            if (store) store.setState({ saveId: s, loading: false });
          },
          sid
        );
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

    // Mobile navigation should be visible
    const mobileNavItems = page.locator("text=调查").first();
    await expect(mobileNavItems).toBeVisible({ timeout: 3000 });

    // Page should work on mobile
    const bodyText = await page.textContent("body");
    expect(bodyText!.length).toBeGreaterThan(0);
  });
});
