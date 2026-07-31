import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { BoardResourceIcon, ResourceIcon } from "./ResourceIcons";

const RESOURCES = ["LUMBER", "BRICK", "WOOL", "GRAIN", "ORE", "DESERT"];

describe("ResourceIcon", () => {
  it("renders an <svg> for every resource with no unresolved values", () => {
    for (const r of RESOURCES) {
      const html = renderToStaticMarkup(<ResourceIcon resource={r} />);
      expect(html).toContain("<svg");
      expect(html).not.toContain("undefined");
      expect(html).not.toContain("NaN");
    }
  });

  it("falls back to the desert glyph for an unknown resource", () => {
    const html = renderToStaticMarkup(<ResourceIcon resource="MYSTERY" />);
    expect(html).toContain("<svg");
  });

  it("exposes an accessible label when a title is provided", () => {
    const html = renderToStaticMarkup(<ResourceIcon resource="ORE" title="Ore" />);
    expect(html).toContain("<title>Ore</title>");
    expect(html).toContain('aria-label="Ore"');
  });
});

describe("BoardResourceIcon", () => {
  it("renders a positioned <g> group for board placement", () => {
    const html = renderToStaticMarkup(
      <svg>
        <BoardResourceIcon resource="WOOL" cx={100} cy={50} size={30} />
      </svg>,
    );
    expect(html).toContain("<g");
    expect(html).toContain("translate");
    expect(html).not.toContain("NaN");
  });
});
