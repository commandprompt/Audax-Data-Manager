import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ContextMenu from "@imengyu/vue3-context-menu";
import { startLoading } from "@src/ajax_control";
import { showAlertHtml, showConfirm } from "@src/notification_control";
import { emitter } from "@src/emitter";
import { tabsStore, connectionsStore } from "@src/stores/stores_initializer.js";
import { Modal } from "bootstrap";
import {
  checkBeforeChangeDatabase,
  renameTab,
  refreshHeights,
  showMenuNewTabOuter,
} from "@src/workspace.js";

vi.mock("@imengyu/vue3-context-menu", () => ({
  default: { showContextMenu: vi.fn() },
}));

vi.mock("@src/ajax_control", () => ({
  startLoading: vi.fn(),
}));

vi.mock("@src/notification_control", () => ({
  showAlertHtml: vi.fn(),
  showConfirm: vi.fn(),
}));

vi.mock("@src/emitter", () => ({
  emitter: { emit: vi.fn() },
}));

vi.mock("@src/stores/stores_initializer.js", () => ({
  tabsStore: {
    selectedPrimaryTab: {
      metaData: { secondaryTabs: [], selectedTab: null },
    },
    createTerminalTab: vi.fn(),
    createConnectionTab: vi.fn(),
  },
  connectionsStore: {
    connections: [],
    groups: [],
    remote_terminals: [],
  },
}));

vi.mock("bootstrap", () => ({
  Modal: {
    getOrCreateInstance: vi.fn(() => ({ show: vi.fn() })),
  },
}));

describe("workspace.js", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("checkBeforeChangeDatabase", () => {
    it("calls okFunction and returns true when there are no troublesome tabs", () => {
      tabsStore.selectedPrimaryTab.metaData.secondaryTabs = [
        { metaData: { mode: "query" } },
      ];
      const okFunction = vi.fn();
      const cancelFunction = vi.fn();

      const result = checkBeforeChangeDatabase(cancelFunction, okFunction);

      expect(result).toBe(true);
      expect(okFunction).toHaveBeenCalled();
      expect(cancelFunction).not.toHaveBeenCalled();
      expect(showAlertHtml).not.toHaveBeenCalled();
    });

    it.each(["edit", "alter", "monitoring_dashboard"])(
      "calls cancelFunction, shows an alert, and returns false when a %s tab is open",
      (mode) => {
        tabsStore.selectedPrimaryTab.metaData.secondaryTabs = [
          { metaData: { mode } },
        ];
        const okFunction = vi.fn();
        const cancelFunction = vi.fn();

        const result = checkBeforeChangeDatabase(cancelFunction, okFunction);

        expect(result).toBe(false);
        expect(cancelFunction).toHaveBeenCalled();
        expect(okFunction).not.toHaveBeenCalled();
        expect(showAlertHtml).toHaveBeenCalled();
      },
    );

    it("does not throw when cancelFunction/okFunction are null", () => {
      tabsStore.selectedPrimaryTab.metaData.secondaryTabs = [
        { metaData: { mode: "edit" } },
      ];
      expect(() => checkBeforeChangeDatabase(null, null)).not.toThrow();

      tabsStore.selectedPrimaryTab.metaData.secondaryTabs = [];
      expect(() => checkBeforeChangeDatabase(null, null)).not.toThrow();
    });
  });

  describe("renameTab", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <input id="tab_name" value="" />
        <button id="modal_message_ok"></button>
        <button id="modal_message_cancel"></button>
      `;
    });

    it("shows a confirm dialog pre-filled with the tab's current name", () => {
      const tab = { name: "My Tab" };

      renameTab(tab);

      expect(showConfirm).toHaveBeenCalledWith(
        expect.stringContaining('value="My Tab"'),
        expect.any(Function),
        null,
        expect.any(Function),
      );
    });

    it("updates the tab name from the input's value when confirmed", () => {
      const tab = { name: "My Tab" };

      renameTab(tab);

      document.getElementById("tab_name").value = "Renamed Tab";
      const confirmCallback = showConfirm.mock.calls[0][1];
      confirmCallback();

      expect(tab.name).toBe("Renamed Tab");
    });

    it("focuses and selects the input via the shown callback", () => {
      const tab = { name: "My Tab" };

      renameTab(tab);

      const input = document.getElementById("tab_name");
      input.value = "My Tab";
      const focusSpy = vi.spyOn(input, "focus");
      const shownCallback = showConfirm.mock.calls[0][3];

      shownCallback();

      expect(focusSpy).toHaveBeenCalled();
      expect(input.selectionStart).toBe(0);
      // selectionEnd clamps to the input's actual text length, well below
      // the 10000 the source sets, confirming the whole value gets selected.
      expect(input.selectionEnd).toBe(input.value.length);
    });

    it("clicks the ok button when Enter is pressed in the input", () => {
      renameTab({ name: "My Tab" });

      const okSpy = vi.spyOn(
        document.getElementById("modal_message_ok"),
        "click",
      );
      window.event = { keyCode: 13 };

      document.getElementById("tab_name").onkeydown();

      expect(okSpy).toHaveBeenCalled();
    });

    it("clicks the cancel button when Escape is pressed in the input", () => {
      renameTab({ name: "My Tab" });

      const cancelSpy = vi.spyOn(
        document.getElementById("modal_message_cancel"),
        "click",
      );
      window.event = { keyCode: 27 };

      document.getElementById("tab_name").onkeydown();

      expect(cancelSpy).toHaveBeenCalled();
    });
  });

  describe("refreshHeights", () => {
    beforeEach(() => {
      vi.useFakeTimers();
      vi.stubGlobal("v_omnis", undefined);
      tabsStore.selectedPrimaryTab.metaData.secondaryTabs = [];
      tabsStore.selectedPrimaryTab.metaData.selectedTab = null;
    });

    afterEach(() => {
      vi.useRealTimers();
      vi.unstubAllGlobals();
    });

    it("emits a resize event when the selected inner tab is in console mode", () => {
      const tab = { id: "console-tab-1", metaData: { mode: "console" } };
      tabsStore.selectedPrimaryTab.metaData.secondaryTabs = [tab];
      tabsStore.selectedPrimaryTab.metaData.selectedTab = tab;

      refreshHeights(true);
      vi.advanceTimersByTime(351);

      expect(emitter.emit).toHaveBeenCalledWith("console-tab-1_resize");
    });

    it("does not emit a resize event when there is no selected inner tab", () => {
      refreshHeights(true);
      vi.advanceTimersByTime(351);

      expect(emitter.emit).not.toHaveBeenCalled();
    });

    it("does not emit a resize event for non-console inner tabs", () => {
      const tab = { id: "query-tab-1", metaData: { mode: "query" } };
      tabsStore.selectedPrimaryTab.metaData.secondaryTabs = [tab];
      tabsStore.selectedPrimaryTab.metaData.selectedTab = tab;

      refreshHeights(true);
      vi.advanceTimersByTime(351);

      expect(emitter.emit).not.toHaveBeenCalled();
    });

    it("does not throw when v_omnis is not set", () => {
      expect(() => {
        refreshHeights(true);
        vi.advanceTimersByTime(351);
      }).not.toThrow();
    });

    it("advances the omnis UI assistant when it is present", () => {
      const goToStep = vi.fn();
      vi.stubGlobal("v_omnis", {
        omnis_ui_assistant: { stepSelected: 2, goToStep },
      });

      refreshHeights(true);
      vi.advanceTimersByTime(351);

      expect(goToStep).toHaveBeenCalledWith(2);
    });

    it("repositions the omnis div relative to its root when there is no UI assistant", () => {
      const root = document.createElement("div");
      vi.spyOn(root, "getBoundingClientRect").mockReturnValue({
        height: 100,
        width: 200,
      });
      const div = document.createElement("div");
      vi.stubGlobal("v_omnis", { root, div });

      refreshHeights(true);
      vi.advanceTimersByTime(351);

      expect(div.style.top).toBe("55px");
      expect(div.style.left).toBe("140px");
    });
  });

  describe("showMenuNewTabOuter", () => {
    beforeEach(() => {
      connectionsStore.connections = [];
      connectionsStore.groups = [];
      connectionsStore.remote_terminals = [];
    });

    it("shows the connections modal when there are no configured connections", () => {
      showMenuNewTabOuter({ x: 0, y: 0 });

      expect(Modal.getOrCreateInstance).toHaveBeenCalledWith(
        "#connections-modal",
      );
      expect(ContextMenu.showContextMenu).not.toHaveBeenCalled();
    });

    it("builds a flat connections menu when there are no groups", () => {
      connectionsStore.connections = [
        { id: 1, technology: "postgresql", alias: "My DB" },
      ];

      showMenuNewTabOuter({ x: 10, y: 20 });

      expect(ContextMenu.showContextMenu).toHaveBeenCalledOnce();
      const config = ContextMenu.showContextMenu.mock.calls[0][0];
      expect(config.x).toBe(10);
      expect(config.y).toBe(20);

      const connectionsGroup = config.items.find(
        (item) => item.label === "Connections",
      );
      expect(connectionsGroup.children).toHaveLength(1);

      connectionsGroup.children[0].onClick();
      expect(tabsStore.createConnectionTab).toHaveBeenCalledWith(
        1,
        true,
        "My DB",
        expect.any(String),
      );
    });

    it("creates a terminal tab when clicking a terminal-technology connection", () => {
      connectionsStore.connections = [
        { id: 2, technology: "terminal", alias: "My SSH", details1: "host" },
      ];

      showMenuNewTabOuter({ x: 0, y: 0 });

      const config = ContextMenu.showContextMenu.mock.calls[0][0];
      const connectionsGroup = config.items.find(
        (item) => item.label === "Connections",
      );

      connectionsGroup.children[0].onClick();
      expect(tabsStore.createTerminalTab).toHaveBeenCalledWith(
        2,
        "My SSH",
        "host",
      );
    });

    it("builds nested groups when connection groups are configured", () => {
      connectionsStore.connections = [
        { id: 1, technology: "postgresql", alias: "DB One" },
        { id: 2, technology: "postgresql", alias: "DB Two" },
      ];
      connectionsStore.groups = [{ name: "My Group", conn_list: [2] }];

      showMenuNewTabOuter({ x: 0, y: 0 });

      const config = ContextMenu.showContextMenu.mock.calls[0][0];
      const connectionsGroup = config.items.find(
        (item) => item.label === "Connections",
      );
      const allConnections = connectionsGroup.children.find(
        (item) => item.label === "All Connections",
      );
      const myGroup = connectionsGroup.children.find(
        (item) => item.label === "My Group",
      );

      expect(allConnections.children).toHaveLength(2);
      expect(myGroup.children).toHaveLength(1);
    });

    it("adds an SSH Consoles submenu when remote terminals are configured", () => {
      connectionsStore.connections = [
        { id: 1, technology: "postgresql", alias: "DB" },
      ];
      connectionsStore.remote_terminals = [
        { id: 5, alias: "Remote", details1: "10.0.0.1" },
      ];

      showMenuNewTabOuter({ x: 0, y: 0 });

      const config = ContextMenu.showContextMenu.mock.calls[0][0];
      const sshGroup = config.items.find(
        (item) => item.label === "SSH Consoles",
      );
      expect(sshGroup.children).toHaveLength(1);

      sshGroup.children[0].onClick();
      expect(tabsStore.createTerminalTab).toHaveBeenCalledWith(
        5,
        "Remote",
        "10.0.0.1",
      );
    });

    it("shows the connections modal when Manage Connections is clicked", () => {
      connectionsStore.connections = [
        { id: 1, technology: "postgresql", alias: "DB" },
      ];

      showMenuNewTabOuter({ x: 0, y: 0 });

      const config = ContextMenu.showContextMenu.mock.calls[0][0];
      const manageConnections = config.items.find(
        (item) => item.label === "Manage Connections",
      );

      manageConnections.onClick();

      expect(Modal.getOrCreateInstance).toHaveBeenCalledWith(
        "#connections-modal",
      );
    });
  });
});
