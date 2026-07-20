import { mount } from "@vue/test-utils";
import { describe, it, expect } from "vitest";
import ErdRelationEdge from "@src/erd_plugins/ErdRelationEdge.vue";
import { Position, getBezierPath, getSmoothStepPath } from "@vue-flow/core";

describe("ErdRelationEdge.vue", () => {
  const baseProps = {
    id: "e1",
    sourceX: 0,
    sourceY: 0,
    targetX: 200,
    targetY: 0,
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    source: "table_a_id",
    target: "table_b_id",
  };

  const mountComponent = (propsOverride = {}) => {
    return mount(ErdRelationEdge, {
      props: { ...baseProps, ...propsOverride },
    });
  };

  describe("rendering", () => {
    it("renders a path with the computed bezier path", () => {
      const wrapper = mountComponent();

      const path = wrapper.find("path");
      expect(path.attributes("id")).toBe("e1");
      expect(path.attributes("d")).toBe(wrapper.vm.edgePath);
    });

    it("leaves markers untouched when no tabId is provided", () => {
      const wrapper = mountComponent({
        markerEnd: "url(#erd-one-only)",
        markerStart: "url(#erd-one-many)",
      });

      const path = wrapper.find("path");
      expect(path.attributes("marker-end")).toBe("url(#erd-one-only)");
      expect(path.attributes("marker-start")).toBe("url(#erd-one-many)");
    });

    it("scopes url marker ids with the tab id to avoid collisions between open ERD tabs", () => {
      const wrapper = mountComponent({
        markerEnd: "url(#erd-one-only)",
        markerStart: "url(#erd-one-many)",
        tabId: "tab-42",
      });

      const path = wrapper.find("path");
      expect(path.attributes("marker-end")).toBe("url(#erd-one-only-tab-42)");
      expect(path.attributes("marker-start")).toBe("url(#erd-one-many-tab-42)");
    });

    it("leaves non-string markers untouched even with a tabId", () => {
      const markerEnd = { type: "arrowclosed" };
      const wrapper = mountComponent({ markerEnd, tabId: "tab-42" });

      expect(wrapper.vm.scopedMarkerEnd).toEqual(markerEnd);
    });

    it("leaves markers without a '#' untouched even with a tabId", () => {
      const wrapper = mountComponent({
        markerEnd: "erd-one-only",
        tabId: "tab-42",
      });

      expect(wrapper.vm.scopedMarkerEnd).toBe("erd-one-only");
    });
  });

  describe("getHandleSide", () => {
    it.each([
      ["source-right", "right"],
      ["target-left", "left"],
      ["source-left", "left"],
      ["target-right", "right"],
    ])("resolves %s to %s", (handleId, expected) => {
      const wrapper = mountComponent();
      expect(wrapper.vm.getHandleSide(handleId)).toBe(expected);
    });

    it.each([[""], [undefined], ["source-top"]])(
      "returns null for %s",
      (handleId) => {
        const wrapper = mountComponent();
        expect(wrapper.vm.getHandleSide(handleId)).toBeNull();
      },
    );
  });

  describe("isOppositeSideRouteTooClose", () => {
    it("is true for a right-to-left route closer than the minimum distance", () => {
      const wrapper = mountComponent({ sourceX: 100, targetX: 150 });
      expect(wrapper.vm.isOppositeSideRouteTooClose("right", "left")).toBe(
        true,
      );
    });

    it("is false for a right-to-left route farther than the minimum distance", () => {
      const wrapper = mountComponent({ sourceX: 0, targetX: 200 });
      expect(wrapper.vm.isOppositeSideRouteTooClose("right", "left")).toBe(
        false,
      );
    });

    it("is true for a left-to-right route closer than the minimum distance", () => {
      const wrapper = mountComponent({ sourceX: 150, targetX: 100 });
      expect(wrapper.vm.isOppositeSideRouteTooClose("left", "right")).toBe(
        true,
      );
    });

    it("is false for a left-to-right route farther than the minimum distance", () => {
      const wrapper = mountComponent({ sourceX: 200, targetX: 0 });
      expect(wrapper.vm.isOppositeSideRouteTooClose("left", "right")).toBe(
        false,
      );
    });

    it("is false for same-side combinations", () => {
      const wrapper = mountComponent();
      expect(wrapper.vm.isOppositeSideRouteTooClose("left", "left")).toBe(
        false,
      );
    });
  });

  describe("shouldUseSmoothStep", () => {
    it("is false when the source handle side cannot be determined", () => {
      const wrapper = mountComponent({
        sourceHandleId: "",
        targetHandleId: "target-left",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(false);
    });

    it("is false when the target handle side cannot be determined", () => {
      const wrapper = mountComponent({
        sourceHandleId: "source-right",
        targetHandleId: "",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(false);
    });

    it("is true when both handles are on the same side", () => {
      const wrapper = mountComponent({
        sourceHandleId: "source-left",
        targetHandleId: "target-left",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(true);
    });

    it("is false for opposite-side handles that are far apart", () => {
      const wrapper = mountComponent({
        sourceX: 0,
        targetX: 200,
        sourceHandleId: "source-right",
        targetHandleId: "target-left",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(false);
    });

    it("is true for opposite-side handles that are too close", () => {
      const wrapper = mountComponent({
        sourceX: 100,
        targetX: 130,
        sourceHandleId: "source-right",
        targetHandleId: "target-left",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(true);
    });
  });

  describe("getPositionVector", () => {
    it.each([
      [Position.Left, { x: -1, y: 0 }],
      [Position.Right, { x: 1, y: 0 }],
      [Position.Top, { x: 0, y: -1 }],
      [Position.Bottom, { x: 0, y: 1 }],
      ["unknown", { x: 0, y: 0 }],
    ])("maps %s to %o", (position, expected) => {
      const wrapper = mountComponent();
      expect(wrapper.vm.getPositionVector(position)).toEqual(expected);
    });
  });

  describe("getOffsetPoint", () => {
    it("offsets to the right for a right-facing position", () => {
      const wrapper = mountComponent();
      expect(wrapper.vm.getOffsetPoint(10, 20, Position.Right, 25)).toEqual({
        x: 35,
        y: 20,
      });
    });

    it("offsets upward for a top-facing position", () => {
      const wrapper = mountComponent();
      expect(wrapper.vm.getOffsetPoint(10, 20, Position.Top, 25)).toEqual({
        x: 10,
        y: -5,
      });
    });
  });

  describe("pathData / edgePath", () => {
    it("uses a bezier path with a straight offset lead-in/out when handles are far apart on opposite sides", () => {
      const wrapper = mountComponent({
        sourceX: 0,
        sourceY: 0,
        targetX: 200,
        targetY: 100,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        sourceHandleId: "source-right",
        targetHandleId: "target-left",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(false);

      const [bezierMiddle] = getBezierPath({
        sourceX: 25,
        sourceY: 0,
        sourcePosition: Position.Right,
        targetX: 175,
        targetY: 100,
        targetPosition: Position.Left,
        curvature: 0.3,
      });
      const bezierCommand = bezierMiddle.slice(bezierMiddle.indexOf("C"));

      const expectedPath = ["M 0,0", "L 25,0", bezierCommand, "L 200,100"].join(
        " ",
      );

      expect(wrapper.vm.edgePath).toBe(expectedPath);
      expect(wrapper.find("path").attributes("d")).toBe(expectedPath);
    });

    it("falls back to a smoothstep path when both handles are on the same side", () => {
      const wrapper = mountComponent({
        sourceX: 0,
        sourceY: 0,
        targetX: 200,
        targetY: 100,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        sourceHandleId: "source-left",
        targetHandleId: "target-left",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(true);

      const [expectedPath] = getSmoothStepPath({
        sourceX: 0,
        sourceY: 0,
        sourcePosition: Position.Right,
        targetX: 200,
        targetY: 100,
        targetPosition: Position.Left,
        offset: 25,
      });

      expect(wrapper.vm.edgePath).toBe(expectedPath);
      expect(wrapper.find("path").attributes("d")).toBe(expectedPath);
    });

    it("falls back to a smoothstep path when opposite-side handles are too close", () => {
      const wrapper = mountComponent({
        sourceX: 100,
        sourceY: 0,
        targetX: 130,
        targetY: 40,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        sourceHandleId: "source-right",
        targetHandleId: "target-left",
      });

      expect(wrapper.vm.shouldUseSmoothStep).toBe(true);

      const [expectedPath] = getSmoothStepPath({
        sourceX: 100,
        sourceY: 0,
        sourcePosition: Position.Right,
        targetX: 130,
        targetY: 40,
        targetPosition: Position.Left,
        offset: 25,
      });

      expect(wrapper.vm.edgePath).toBe(expectedPath);
    });
  });
});
