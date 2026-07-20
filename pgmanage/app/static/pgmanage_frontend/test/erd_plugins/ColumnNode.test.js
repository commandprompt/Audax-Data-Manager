import { mount } from "@vue/test-utils";
import { describe, it, expect } from "vitest";
import ColumnNode from "@src/erd_plugins/ColumnNode.vue";
import { Position } from "@vue-flow/core";

// The real Handle component needs a live VueFlow/Node injection context
// (it throws "Node not found" otherwise), which isn't relevant here — we
// only care that ColumnNode decides correctly whether/how to render it.
const HandleStub = {
  name: "Handle",
  props: ["id", "type", "position", "connectable"],
  template:
    '<div class="handle-stub" :data-id="id" :data-type="type" :data-position="position" :data-connectable="connectable"></div>',
};

describe("ColumnNode.vue", () => {
  const mountComponent = (props = {}) => {
    return mount(ColumnNode, {
      props: { data: {}, ...props },
      global: { stubs: { Handle: HandleStub } },
    });
  };

  describe("plain column (no pk/fk)", () => {
    it("renders the label in a span with a hidden placeholder icon", () => {
      const wrapper = mountComponent({
        data: { label: "created_at", type: "timestamp" },
      });

      expect(wrapper.find("a").exists()).toBe(false);
      const nameEl = wrapper.find(".vue-flow__node-table__column_name");
      expect(nameEl.element.tagName).toBe("SPAN");
      expect(nameEl.text()).toBe("created_at");
      expect(nameEl.find("i").attributes("style")).toContain("hidden");
    });

    it("does not apply the pk/fk/highlighted classes", () => {
      const wrapper = mountComponent({ data: { label: "created_at" } });

      const column = wrapper.find(".vue-flow__node-table__column");
      expect(column.classes()).not.toContain("pk-column");
      expect(column.classes()).not.toContain("fk-column");
      expect(column.classes()).not.toContain("highlighted");
    });

    it("renders no connection handles", () => {
      const wrapper = mountComponent({ data: { label: "created_at" } });

      expect(wrapper.findAll(".handle-stub")).toHaveLength(0);
    });

    it("shows the type badge only when data.type is set", () => {
      const withType = mountComponent({
        data: { label: "created_at", type: "timestamp" },
      });
      expect(withType.find(".vue-flow__node-table__column_type").text()).toBe(
        "timestamp",
      );

      const withoutType = mountComponent({ data: { label: "created_at" } });
      expect(
        withoutType.find(".vue-flow__node-table__column_type").exists(),
      ).toBe(false);
    });
  });

  describe("foreign key column", () => {
    it("renders as a link with a key icon, the fk-column class and four handles", () => {
      const wrapper = mountComponent({
        data: { label: "user_id", is_fk: true, type: "integer" },
      });

      const link = wrapper.find("a.vue-flow__node-table__column_name");
      expect(link.exists()).toBe(true);
      expect(link.find("i.fa-key").exists()).toBe(true);
      expect(link.text()).toBe("user_id");

      expect(wrapper.find(".vue-flow__node-table__column").classes()).toContain(
        "fk-column",
      );

      const handles = wrapper.findAll(".handle-stub");
      expect(handles).toHaveLength(4);
      expect(handles.map((h) => h.attributes("data-id"))).toEqual([
        "source-left",
        "source-right",
        "target-left",
        "target-right",
      ]);
      expect(handles.map((h) => h.attributes("data-position"))).toEqual([
        Position.Left,
        Position.Right,
        Position.Left,
        Position.Right,
      ]);
    });
  });

  describe("primary key column", () => {
    it("renders as a span with a key icon, the pk-column class and four handles", () => {
      const wrapper = mountComponent({
        data: { label: "id", is_pk: true, type: "integer" },
      });

      expect(wrapper.find("a").exists()).toBe(false);
      const nameEl = wrapper.find(".vue-flow__node-table__column_name");
      expect(nameEl.element.tagName).toBe("SPAN");
      expect(nameEl.find("i.fa-key").exists()).toBe(true);
      expect(nameEl.text()).toBe("id");

      expect(wrapper.find(".vue-flow__node-table__column").classes()).toContain(
        "pk-column",
      );
      expect(wrapper.findAll(".handle-stub")).toHaveLength(4);
    });
  });

  it("prefers the fk rendering when a column is both a primary and a foreign key", () => {
    const wrapper = mountComponent({
      data: { label: "id", is_pk: true, is_fk: true },
    });

    expect(wrapper.find("a.vue-flow__node-table__column_name").exists()).toBe(
      true,
    );
    const column = wrapper.find(".vue-flow__node-table__column");
    expect(column.classes()).toContain("fk-column");
    expect(column.classes()).toContain("pk-column");
  });

  it("applies the highlighted class when data.is_highlighted is true", () => {
    const wrapper = mountComponent({
      data: { label: "x", is_highlighted: true },
    });

    expect(wrapper.find(".vue-flow__node-table__column").classes()).toContain(
      "highlighted",
    );
  });

  it("applies the last-column class to the wrapper only when data.is_last is true", () => {
    const last = mountComponent({ data: { label: "x", is_last: true } });
    expect(last.find(".vue-flow__node-table__column_wrap").classes()).toContain(
      "last-column",
    );

    const notLast = mountComponent({ data: { label: "x", is_last: false } });
    expect(
      notLast.find(".vue-flow__node-table__column_wrap").classes(),
    ).not.toContain("last-column");
  });

  describe("nodeLabel fallback", () => {
    it("uses data.label when present", () => {
      const wrapper = mountComponent({
        data: { label: "from_data" },
        label: "from_prop",
      });

      expect(wrapper.text()).toContain("from_data");
      expect(wrapper.text()).not.toContain("from_prop");
    });

    it("falls back to the label prop when data.label is not set", () => {
      const wrapper = mountComponent({ data: {}, label: "from_prop" });

      expect(wrapper.text()).toContain("from_prop");
    });
  });

  describe("computed properties", () => {
    it("hasRelationship is true when isPk or isFk, false otherwise", () => {
      expect(mountComponent({ data: { is_pk: true } }).vm.hasRelationship).toBe(
        true,
      );
      expect(mountComponent({ data: { is_fk: true } }).vm.hasRelationship).toBe(
        true,
      );
      expect(mountComponent({ data: {} }).vm.hasRelationship).toBe(false);
    });

    it("exposes the left/right vue-flow Position constants", () => {
      const wrapper = mountComponent();
      expect(wrapper.vm.leftPosition).toBe(Position.Left);
      expect(wrapper.vm.rightPosition).toBe(Position.Right);
    });
  });
});
