import { describe, it, expect, vi, beforeAll } from "vitest";
import { mount } from "@vue/test-utils";
import "ace-builds";
import "ace-builds/esm-resolver";
import "@src/ace_extras/themes/theme-omnidb.js";
import "@src/ace_extras/ext-hoverlink.js";
import TreePropertiesDDL from "@src/components/TreePropertiesDDL.vue";
import { useSettingsStore } from "@src/stores/settings.js";

describe("TreePropertiesDDL.vue", () => {
  let settingsStore;
  beforeAll(() => {
    settingsStore = useSettingsStore();
    settingsStore.setEditorTheme("omnidb");
  });

  it("renders component", () => {
    const wrapper = mount(TreePropertiesDDL);
    expect(wrapper.html()).toContain("Properties");
    expect(wrapper.html()).toContain("DDL");
  });
  it("emits hideTreeTabs event when hide button is clicked", async () => {
    const wrapper = mount(TreePropertiesDDL, {
      props: {
        workspaceId: "workspace-1",
        isVisible: true,
      },
    });

    await wrapper
      .find('[data-testid="tree-tabs-hide-button"]')
      .trigger("click");

    expect(wrapper.emitted("hideTreeTabs")).toBeTruthy();
  });

  it("emits showTreeTabs event when show button is clicked", async () => {
    const wrapper = mount(TreePropertiesDDL, {
      props: {
        workspaceId: "workspace-1",
        isVisible: false,
      },
    });

    await wrapper
      .find('[data-testid="tree-tabs-show-button"]')
      .trigger("click");

    expect(wrapper.emitted("showTreeTabs")).toBeTruthy();
  });
  it("shows loading spinner when showLoading prop is true", async () => {
    const wrapper = mount(TreePropertiesDDL);

    await wrapper.setProps({ showLoading: true });

    expect(wrapper.html()).toContain("Loading...");
  });

  it("emits showTreeTabs event when Properties tab is clicked", async () => {
    const wrapper = mount(TreePropertiesDDL, {
      props: {
        workspaceId: "workspace-1",
        isVisible: false,
      },
    });

    await wrapper
      .find(`[href="#workspace-1_tree_properties"]`)
      .trigger("click");

    expect(wrapper.emitted("showTreeTabs")).toBeTruthy();
  });

  it("emits showTreeTabs event when DDL tab is clicked", async () => {
    const wrapper = mount(TreePropertiesDDL, {
      props: {
        workspaceId: "workspace-1",
        isVisible: false,
      },
    });

    await wrapper.find(`[href="#workspace-1_tree_ddl"]`).trigger("click");

    expect(wrapper.emitted("showTreeTabs")).toBeTruthy();
  });
});
