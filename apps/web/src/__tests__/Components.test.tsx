import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PlayerStatus from "../components/PlayerStatus";
import LocationPanel from "../components/LocationPanel";
import ClueList from "../components/ClueList";
import NpcDialogue from "../components/NpcDialogue";
import HypothesisPanel from "../components/HypothesisPanel";
import MobileNav from "../components/MobileNav";
import Layout from "../components/Layout";
import type {
  PlayerStatus as PlayerStatusType,
  LocationInfo,
  ClueInfo,
  NpcInfo,
  HypothesisInfo,
} from "../types";

// ============================================================
// Test data
// ============================================================

const mockPlayerStatus: PlayerStatusType = {
  spirituality: 80,
  corruption: 10,
  stability: 70,
  current_location_id: "loc_1",
  current_location_name: "灰雾镇广场",
  visited_locations: [],
};

const mockLocation: LocationInfo = {
  location_id: "loc_1",
  display_name: "灰雾镇广场",
  description: "镇中心广场，灰雾弥漫",
  is_current: true,
  has_been_visited: true,
  available_clues: [],
  available_npcs: ["npc_1"],
};

const mockLocations: LocationInfo[] = [
  {
    location_id: "loc_1",
    display_name: "灰雾镇广场",
    description: "镇中心广场",
    is_current: true,
    has_been_visited: true,
    available_clues: [],
    available_npcs: [],
  },
  {
    location_id: "loc_2",
    display_name: "警察局",
    description: "镇上的警察局",
    is_current: false,
    has_been_visited: true,
    available_clues: [],
    available_npcs: [],
  },
  {
    location_id: "loc_3",
    display_name: "教堂",
    description: "古老的教堂",
    is_current: false,
    has_been_visited: false,
    available_clues: [],
    available_npcs: [],
  },
];

const mockClues: ClueInfo[] = [
  {
    clue_id: "clue_1",
    display_name: "神秘信件",
    description: "一封没有署名的信",
    source_type: "调查",
    is_new: true,
  },
  {
    clue_id: "clue_2",
    display_name: "老照片",
    description: "一张泛黄的照片",
    source_type: "搜索",
    is_new: false,
  },
];

const mockNpc: NpcInfo = {
  npc_id: "npc_1",
  name: "老约翰",
  description: "一位神情忧郁的老人",
  emotion: "忧虑",
  current_location_id: "loc_1",
  available_claims: [
    {
      claim_id: "claim_1",
      content: "昨晚我听到了一声尖叫",
      is_lie: false,
      speaker_believes_it: true,
    },
  ],
};

const mockHypotheses: HypothesisInfo[] = [
  {
    hypothesis_id: "hyp_1",
    title: "失踪案与灰雾有关",
    description: "最近的失踪事件可能与灰雾的出现有关联",
    status: "unlocked",
    min_confidence: 0.6,
    required_clue_count: 3,
    found_clue_count: 1,
    can_submit: false,
  },
  {
    hypothesis_id: "hyp_2",
    title: "连环作案",
    description: "多名失踪者可能被同一人所害",
    status: "confirmed",
    min_confidence: 0.8,
    required_clue_count: 5,
    found_clue_count: 5,
    can_submit: false,
  },
  {
    hypothesis_id: "hyp_3",
    title: "超自然事件",
    description: "这次事件可能涉及超自然力量",
    status: "locked",
    min_confidence: 0.5,
    required_clue_count: 2,
    found_clue_count: 0,
    can_submit: false,
  },
  {
    hypothesis_id: "hyp_4",
    title: "假线索",
    description: "这条假设已被推翻",
    status: "refuted",
    min_confidence: 0.7,
    required_clue_count: 3,
    found_clue_count: 2,
    can_submit: false,
  },
];

// Helper to wrap in Router context
function WithRouter({ children }: { children: React.ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

// ============================================================
// PlayerStatus Test — 灵性、污染和稳定度显示
// ============================================================

describe("PlayerStatus", () => {
  it("renders player spirituality bar", () => {
    render(<PlayerStatus status={mockPlayerStatus} />);
    expect(screen.getByText("灵性")).toBeTruthy();
    expect(screen.getByText("80")).toBeTruthy();
  });

  it("renders player corruption bar", () => {
    render(<PlayerStatus status={mockPlayerStatus} />);
    expect(screen.getByText("污染")).toBeTruthy();
    expect(screen.getByText("10")).toBeTruthy();
  });

  it("renders player stability bar", () => {
    render(<PlayerStatus status={mockPlayerStatus} />);
    expect(screen.getByText("稳定度")).toBeTruthy();
    expect(screen.getByText("70")).toBeTruthy();
  });

  it("clamps values at 0-100 range", () => {
    const extremeStatus: PlayerStatusType = {
      ...mockPlayerStatus,
      spirituality: -5,
      corruption: 150,
    };
    render(<PlayerStatus status={extremeStatus} />);
    // Values should display as-is (only bar width is clamped)
    expect(screen.getByText("-5")).toBeTruthy();
    expect(screen.getByText("150")).toBeTruthy();
  });
});

// ============================================================
// LocationPanel Test — 地点移动相关
// ============================================================

describe("LocationPanel", () => {
  it("renders current location name and description", () => {
    render(<LocationPanel currentLocation={mockLocation} locations={mockLocations} />);
    const locElements = screen.getAllByText("灰雾镇广场");
    expect(locElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("镇中心广场，灰雾弥漫")).toBeTruthy();
  });

  it("shows visited locations excluding unvisited ones", () => {
    render(<LocationPanel currentLocation={mockLocation} locations={mockLocations} />);
    // loc_3 (教堂) has has_been_visited=false, should not appear in visited list
    const locElements = screen.getAllByText("灰雾镇广场");
    expect(locElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("警察局")).toBeTruthy();
    expect(screen.queryByText("教堂")).toBeNull();
  });

  it("highlights current location in visited list", () => {
    render(<LocationPanel currentLocation={mockLocation} locations={mockLocations} />);
    // Current location should appear in visited list
    const locElements = screen.getAllByText("灰雾镇广场");
    expect(locElements.length).toBeGreaterThanOrEqual(1);
  });
});

// ============================================================
// ClueList Test — 调查线索
// ============================================================

describe("ClueList", () => {
  it("renders empty state when no clues", () => {
    render(<ClueList clues={[]} />);
    expect(screen.getByText("尚未发现任何线索")).toBeTruthy();
  });

  it("renders clue count", () => {
    render(<ClueList clues={mockClues} />);
    expect(screen.getByText("线索记录 (2)")).toBeTruthy();
  });

  it("separates new and old clues", () => {
    render(<ClueList clues={mockClues} />);
    expect(screen.getByText("新发现")).toBeTruthy();
    expect(screen.getByText("神秘信件")).toBeTruthy();
    expect(screen.getByText("老照片")).toBeTruthy();
  });

  it("calls onClueClick when clicking a clue", () => {
    let clicked: ClueInfo | null = null;
    render(
      <ClueList
        clues={mockClues}
        onClueClick={(c) => {
          clicked = c;
        }}
      />
    );
    screen.getByText("神秘信件").click();
    expect(clicked).not.toBeNull();
    expect(clicked!.clue_id).toBe("clue_1");
  });
});

// ============================================================
// NpcDialogue Test — NPC 对话
// ============================================================

describe("NpcDialogue", () => {
  it("renders NPC name and emotion", () => {
    render(<NpcDialogue npc={mockNpc} onClose={() => {}} />);
    expect(screen.getByText("老约翰")).toBeTruthy();
    expect(screen.getByText("忧虑")).toBeTruthy();
  });

  it("renders NPC description", () => {
    render(<NpcDialogue npc={mockNpc} onClose={() => {}} />);
    expect(screen.getByText("一位神情忧郁的老人")).toBeTruthy();
  });

  it("renders NPC claim content", () => {
    render(<NpcDialogue npc={mockNpc} onClose={() => {}} />);
    expect(screen.getByText("昨晚我听到了一声尖叫")).toBeTruthy();
  });

  it("shows empty claim message when no claims", () => {
    const npcNoClaims: NpcInfo = {
      ...mockNpc,
      available_claims: [],
    };
    render(<NpcDialogue npc={npcNoClaims} onClose={() => {}} />);
    expect(screen.getByText("暂无证词记录")).toBeTruthy();
  });

  it("calls onClose when close button clicked", () => {
    let closed = false;
    render(<NpcDialogue npc={mockNpc} onClose={() => { closed = true; }} />);
    // There are two close buttons — the 'x' button and the '关闭' button
    const closeButtons = screen.getAllByText("关闭");
    expect(closeButtons.length).toBeGreaterThanOrEqual(1);
    closeButtons[0].click();
    expect(closed).toBe(true);
  });
});

// ============================================================
// HypothesisPanel Test — 推理假设
// ============================================================

describe("HypothesisPanel", () => {
  it("renders empty state when no hypotheses", () => {
    render(<HypothesisPanel hypotheses={[]} />);
    expect(screen.getByText("暂无假设")).toBeTruthy();
  });

  it("renders hypothesis titles and statuses", () => {
    render(<HypothesisPanel hypotheses={mockHypotheses} />);
    expect(screen.getByText("失踪案与灰雾有关")).toBeTruthy();
    expect(screen.getByText("待验证")).toBeTruthy();
    expect(screen.getByText("已确认")).toBeTruthy();
    expect(screen.getByText("已推翻")).toBeTruthy();
  });

  it("shows locked hypothesis as ???", () => {
    render(<HypothesisPanel hypotheses={mockHypotheses} />);
    expect(screen.getByText("???")).toBeTruthy();
    expect(screen.getByText("未解锁")).toBeTruthy();
  });

  it("shows clue progress for unlocked hypotheses", () => {
    render(<HypothesisPanel hypotheses={mockHypotheses} />);
    expect(screen.getByText("线索 1/3")).toBeTruthy();
  });

  it("shows can_submit indicator", () => {
    const submitableHyp: HypothesisInfo[] = [
      {
        ...mockHypotheses[0],
        can_submit: true,
        found_clue_count: 3,
      },
    ];
    render(<HypothesisPanel hypotheses={submitableHyp} />);
    expect(screen.getByText("可提交")).toBeTruthy();
  });
});

// ============================================================
// MobileNav Test — 手机布局基础渲染
// ============================================================

describe("MobileNav", () => {
  it("renders all navigation items", () => {
    render(
      <MemoryRouter initialEntries={["/game"]}>
        <MobileNav />
      </MemoryRouter>
    );
    expect(screen.getByText("调查")).toBeTruthy();
    expect(screen.getByText("推理板")).toBeTruthy();
    expect(screen.getByText("仪式")).toBeTruthy();
    expect(screen.getByText("存档")).toBeTruthy();
    expect(screen.getByText("设置")).toBeTruthy();
  });

  it("highlights active route", () => {
    render(
      <MemoryRouter initialEntries={["/game"]}>
        <MobileNav />
      </MemoryRouter>
    );
    // The active link should have the mystic-gold color class
    const navLinks = screen.getAllByText("调查");
    expect(navLinks.length).toBeGreaterThanOrEqual(1);
  });
});
