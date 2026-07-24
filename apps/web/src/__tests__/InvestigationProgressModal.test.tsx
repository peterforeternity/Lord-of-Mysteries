import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import InvestigationProgressModal from "../components/InvestigationProgressModal";
import type { InvestigationProgress } from "../types";

const mockProgress: InvestigationProgress = {
  phase_level: 1,
  phase_label: "线索浮现",
  evidence_dimensions: [
    { dimension_id: "scene", label: "现场痕迹", status_label: "尚无发现" },
    { dimension_id: "witness", label: "人物证言", status_label: "出现疑点" },
    { dimension_id: "anomaly", label: "异常现象", status_label: "尚无发现" },
    { dimension_id: "items", label: "物品与材料", status_label: "线索增加" },
    { dimension_id: "causality", label: "事件因果", status_label: "尚无发现" },
  ],
  recent_discoveries: ["神秘材料收据", "邻居证词"],
  open_questions: ["材料收据是否与失踪有关？"],
  resolution_available: true,
  new_resolution_available: false,
};

const mockProgressNoResolution: InvestigationProgress = {
  ...mockProgress,
  resolution_available: false,
  new_resolution_available: false,
};

describe("InvestigationProgressModal", () => {
  // 1. Click opens the modal
  it("shows investigation progress title", () => {
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={() => {}}
        onGoToDeduction={() => {}}
      />
    );
    expect(screen.getByText("调查进度")).toBeTruthy();
  });

  // 2. Close button fires onClose
  it("close button calls onClose", () => {
    const onClose = vi.fn();
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={onClose}
        onGoToDeduction={() => {}}
      />
    );
    fireEvent.click(screen.getByLabelText("关闭调查进度"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // 3. Esc key fires onClose
  it("Escape key calls onClose", () => {
    const onClose = vi.fn();
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={onClose}
        onGoToDeduction={() => {}}
      />
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // 4. Backdrop click fires onClose
  it("backdrop click calls onClose", () => {
    const onClose = vi.fn();
    const { container } = render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={onClose}
        onGoToDeduction={() => {}}
      />
    );
    // The outer fixed wrapper is the backdrop
    const backdrop = container.firstElementChild as HTMLElement;
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // 5. Does NOT display found/total counts
  it("does NOT display found or total counts", () => {
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={() => {}}
        onGoToDeduction={() => {}}
      />
    );
    const bodyText = document.body.textContent || "";
    expect(bodyText).not.toContain("2/4");
    expect(bodyText).not.toContain("1/5");
    expect(bodyText).not.toContain("0/2");
    expect(bodyText).not.toContain("found");
    expect(bodyText).not.toContain("total");
  });

  // 6. Does NOT show hidden clue names
  it("only shows discovered clue names", () => {
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={() => {}}
        onGoToDeduction={() => {}}
      />
    );
    expect(screen.getByText("神秘材料收据")).toBeTruthy();
    expect(screen.getByText("邻居证词")).toBeTruthy();
    // Should NOT show undiscovered clue names
    const bodyText = document.body.textContent || "";
    expect(bodyText).not.toContain("工坊燃痕");
    expect(bodyText).not.toContain("诊所报告");
  });

  // 7. Does NOT show hypothesis or ending names
  it("does NOT leak hypothesis or ending names", () => {
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={() => {}}
        onGoToDeduction={() => {}}
      />
    );
    const bodyText = document.body.textContent || "";
    expect(bodyText).not.toContain("假设");
    expect(bodyText).not.toContain("hypothesis");
    expect(bodyText).not.toContain("结局");
    expect(bodyText).not.toContain("ending");
  });

  // 8. Shows status_label instead of exact counts
  it("shows fuzzy status labels for dimensions", () => {
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={() => {}}
        onGoToDeduction={() => {}}
      />
    );
    expect(screen.getAllByText("尚无发现").length).toBeGreaterThan(0);
    expect(screen.getAllByText("出现疑点").length).toBeGreaterThan(0);
    expect(screen.getAllByText("线索增加").length).toBeGreaterThan(0);
  });

  // 9. Continue button does NOT trigger ending
  it("continue button does NOT trigger ending / deduction", () => {
    const onClose = vi.fn();
    const onGoToDeduction = vi.fn();
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={onClose}
        onGoToDeduction={onGoToDeduction}
      />
    );
    fireEvent.click(screen.getByText("继续调查"));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onGoToDeduction).not.toHaveBeenCalled();
  });

  // 10. Enter deduction button navigates
  it("进入推理 button calls onGoToDeduction", () => {
    const onGoToDeduction = vi.fn();
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={() => {}}
        onGoToDeduction={onGoToDeduction}
      />
    );
    fireEvent.click(screen.getByText("进入推理"));
    expect(onGoToDeduction).toHaveBeenCalledTimes(1);
  });

  // 11. Enter deduction hidden when no resolution available
  it("hides 进入推理 button when resolution not available", () => {
    render(
      <InvestigationProgressModal
        progress={mockProgressNoResolution}
        onClose={() => {}}
        onGoToDeduction={() => {}}
      />
    );
    expect(screen.queryByText("进入推理")).toBeNull();
  });

  // 12. Focus trap: dialog has aria-modal
  it("dialog has aria-modal attribute for focus trapping", () => {
    render(
      <InvestigationProgressModal
        progress={mockProgress}
        onClose={() => {}}
        onGoToDeduction={() => {}}
      />
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog.getAttribute("aria-modal")).toBe("true");
  });
});
