import { flushPromises, mount } from "@vue/test-utils";
import CommandsHistoryModal from "@src/components/CommandsHistoryModal.vue";
import { useCommandsHistoryStore } from "@src/stores/commands_history";
import { useCellDataModalStore } from "@src/stores/celldata_modal";
import { emitter } from "@src/emitter";
import { handleError } from "@src/logging/utils";
import axios from "axios";
import { Modal } from "bootstrap";
import $ from "jquery";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// CommandsHistoryModal.vue references the bare `$` global directly (relying
// on jQuery being loaded as a global script in production) rather than
// importing it, so it isn't covered by the @rollup/plugin-inject transform
// that only auto-injects `$` into plain .js files, not .vue SFCs.
vi.stubGlobal("$", $);

vi.mock("@src/logging/utils", () => ({
  handleError: vi.fn(),
}));

vi.mock("bootstrap", () => ({
  Modal: {
    getOrCreateInstance: vi.fn(() => ({
      show: vi.fn(),
      hide: vi.fn(),
    })),
  },
}));

describe("CommandsHistoryModal.vue", () => {
  let wrapper,
    commandsHistoryStore,
    cellDataModalStore,
    unsubscribeOnAction,
    onActionSpy;

  beforeEach(() => {
    commandsHistoryStore = useCommandsHistoryStore();
    cellDataModalStore = useCellDataModalStore();

    axios.get.mockResolvedValue({ data: { data: [] } });

    // mounted() subscribes to commandsHistoryStore.$onAction and never
    // unsubscribes. Since the store is a real, shared singleton (not reset
    // between tests), each fresh mount would otherwise stack another
    // listener acting on a stale component instance, firing (and erroring
    // against a torn-down `this`) whenever a later test calls showModal().
    const realOnAction = commandsHistoryStore.$onAction;
    onActionSpy = vi
      .spyOn(commandsHistoryStore, "$onAction")
      .mockImplementation((cb) => {
        unsubscribeOnAction = realOnAction(cb);
        return unsubscribeOnAction;
      });

    wrapper = mount(CommandsHistoryModal);
  });

  afterEach(() => {
    unsubscribeOnAction?.();
    // Restore just this spy (not restoreAllMocks) so the vi.mock("bootstrap")
    // / vi.mock("@src/logging/utils") factory implementations below survive
    // into the next test.
    onActionSpy.mockRestore();
    commandsHistoryStore.$reset();
    vi.clearAllMocks();
  });

  it("renders the modal with the tab type in the title", async () => {
    commandsHistoryStore.tabType = "Query";
    await flushPromises();

    expect(wrapper.find("#commands-history-modal").exists()).toBe(true);
    expect(wrapper.find(".modal-title").text()).toBe("Query commands history");
  });

  describe("showModal action", () => {
    it("sets up the table, resets fields, shows the modal, and fetches history", async () => {
      axios.post.mockResolvedValueOnce({
        data: { pages: 1, database_names: [], command_list: [] },
      });

      commandsHistoryStore.showModal("tab-1", 5, "Console");
      await flushPromises();

      expect(wrapper.vm.table).toBeTruthy();
      expect(Modal.getOrCreateInstance).toHaveBeenCalledWith(
        wrapper.vm.$refs.historyModal,
      );
      expect(axios.post).toHaveBeenCalledWith(
        "/get_commands_history/",
        expect.objectContaining({
          command_type: "Console",
          database_index: 5,
        }),
      );
    });

    it("destroys the previous table before creating a new one", async () => {
      axios.post.mockResolvedValue({
        data: { pages: 1, database_names: [], command_list: [] },
      });

      commandsHistoryStore.showModal("tab-1", 5, "Console");
      await flushPromises();
      const destroySpy = vi.spyOn(wrapper.vm.table, "destroy");

      commandsHistoryStore.showModal("tab-1", 5, "Console");
      await flushPromises();

      expect(destroySpy).toHaveBeenCalled();
    });
  });

  describe("hidden.bs.modal", () => {
    it("resets the store and removes the daterangepicker", async () => {
      axios.post.mockResolvedValueOnce({
        data: { pages: 1, database_names: [], command_list: [] },
      });

      commandsHistoryStore.showModal("tab-1", 5, "Console");
      await flushPromises();

      const removeSpy = vi.fn();
      $(wrapper.vm.$refs.timeRange).data("daterangepicker", {
        remove: removeSpy,
      });

      wrapper.vm.$refs.historyModal.dispatchEvent(new Event("hidden.bs.modal"));

      expect(removeSpy).toHaveBeenCalled();
      expect(commandsHistoryStore.visible).toBe(false);
      expect(commandsHistoryStore.tabId).toBeNull();
    });
  });

  describe("defaultColumns", () => {
    it("returns Console columns by default", () => {
      commandsHistoryStore.tabType = "Console";

      const fields = wrapper.vm.defaultColumns.map((c) => c.field);
      expect(fields).toEqual(["start_time", "database", "snippet"]);
    });

    it("returns Query columns, including a Status formatter", () => {
      commandsHistoryStore.tabType = "Query";

      const fields = wrapper.vm.defaultColumns.map((c) => c.field);
      expect(fields).toEqual([
        "start_time",
        "end_time",
        "duration",
        "status",
        "database",
        "snippet",
      ]);

      const statusColumn = wrapper.vm.defaultColumns.find(
        (c) => c.field === "status",
      );
      expect(statusColumn.formatter({ getValue: () => "success" })).toContain(
        "text-success",
      );
      expect(statusColumn.formatter({ getValue: () => "error" })).toContain(
        "text-danger",
      );
    });

    it("emits copy_to_editor and hides the modal on Command cell double-click (Query)", () => {
      commandsHistoryStore.tabType = "Query";
      commandsHistoryStore.tabId = "tab-1";
      const emitSpy = vi.spyOn(emitter, "emit");
      const hideSpy = vi.fn();
      wrapper.vm.modalInstance = { hide: hideSpy };

      const snippetColumn = wrapper.vm.defaultColumns.find(
        (c) => c.field === "snippet",
      );
      snippetColumn.cellDblClick(null, { getValue: () => "select 1;" });

      expect(emitSpy).toHaveBeenCalledWith("tab-1_copy_to_editor", "select 1;");
      expect(hideSpy).toHaveBeenCalled();
    });

    it("wires the Console Command column's context menu actions", () => {
      commandsHistoryStore.tabType = "Console";
      commandsHistoryStore.tabId = "tab-1";
      wrapper.vm.table = { selectRow: vi.fn(), copyToClipboard: vi.fn() };
      const emitSpy = vi.spyOn(emitter, "emit");
      const hideSpy = vi.fn();
      wrapper.vm.modalInstance = { hide: hideSpy };
      const showModalSpy = vi.spyOn(cellDataModalStore, "showModal");

      const snippetColumn = wrapper.vm.defaultColumns.find(
        (c) => c.field === "snippet",
      );
      const cell = { getValue: () => "select 1;", getRow: () => "row-1" };

      snippetColumn.contextMenu[0].action(null, cell);
      expect(wrapper.vm.table.selectRow).toHaveBeenCalledWith("row-1");
      expect(wrapper.vm.table.copyToClipboard).toHaveBeenCalledWith("selected");

      snippetColumn.contextMenu[1].action(null, cell);
      expect(emitSpy).toHaveBeenCalledWith("tab-1_copy_to_editor", "select 1;");
      expect(hideSpy).toHaveBeenCalled();

      snippetColumn.contextMenu[2].action(null, cell);
      expect(showModalSpy).toHaveBeenCalledWith("select 1;", "sql");
    });
  });

  describe("getCommandsHistory", () => {
    beforeEach(async () => {
      axios.post.mockResolvedValue({
        data: { pages: 1, database_names: [], command_list: [] },
      });
      commandsHistoryStore.showModal("tab-1", 5, "Console");
      await flushPromises();
      vi.clearAllMocks();
    });

    it("resets currentPage to 1 when resetCurrentPage is true", async () => {
      wrapper.vm.currentPage = 3;
      axios.post.mockResolvedValueOnce({
        data: { pages: 5, database_names: [], command_list: [] },
      });

      wrapper.vm.getCommandsHistory(true);
      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith(
        "/get_commands_history/",
        expect.objectContaining({ current_page: 1 }),
      );
    });

    it("updates pages, databaseNames, and the table on success", async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          pages: 4,
          database_names: ["db1", "db2"],
          command_list: [{ start_time: "2024-01-01T00:00:00Z" }],
        },
      });
      const setDataSpy = vi.spyOn(wrapper.vm.table, "setData");
      const redrawSpy = vi.spyOn(wrapper.vm.table, "redraw");

      wrapper.vm.getCommandsHistory();
      await flushPromises();

      expect(wrapper.vm.pages).toBe(4);
      expect(wrapper.vm.databaseNames).toEqual(["db1", "db2"]);
      expect(setDataSpy).toHaveBeenCalled();
      expect(redrawSpy).toHaveBeenCalled();
    });

    it("resets currentPage to 1 when it exceeds the new page count", async () => {
      wrapper.vm.currentPage = 10;
      axios.post.mockResolvedValueOnce({
        data: { pages: 2, database_names: [], command_list: [] },
      });

      wrapper.vm.getCommandsHistory();
      await flushPromises();

      expect(wrapper.vm.currentPage).toBe(1);
    });

    it("calls handleError when the request fails", async () => {
      const error = new Error("boom");
      axios.post.mockRejectedValueOnce(error);

      wrapper.vm.getCommandsHistory();
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(error);
    });
  });

  describe("clearCommandsHistory", () => {
    it("refreshes the history on success", async () => {
      axios.post.mockResolvedValueOnce({ data: {} });
      axios.post.mockResolvedValueOnce({
        data: { pages: 1, database_names: [], command_list: [] },
      });

      wrapper.vm.clearCommandsHistory();
      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith(
        "/clear_commands_history/",
        expect.any(Object),
      );
      expect(axios.post).toHaveBeenCalledWith(
        "/get_commands_history/",
        expect.any(Object),
      );
    });

    it("calls handleError when the request fails", async () => {
      const error = new Error("boom");
      axios.post.mockRejectedValueOnce(error);

      wrapper.vm.clearCommandsHistory();
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(error);
    });
  });

  describe("pagination", () => {
    beforeEach(() => {
      wrapper.vm.getCommandsHistory = vi.fn();
    });

    it("getNextPage advances the page and re-fetches when not on the last page", () => {
      wrapper.vm.currentPage = 1;
      wrapper.vm.pages = 3;

      wrapper.vm.getNextPage();

      expect(wrapper.vm.currentPage).toBe(2);
      expect(wrapper.vm.getCommandsHistory).toHaveBeenCalled();
    });

    it("getNextPage does nothing on the last page", () => {
      wrapper.vm.currentPage = 3;
      wrapper.vm.pages = 3;

      wrapper.vm.getNextPage();

      expect(wrapper.vm.currentPage).toBe(3);
      expect(wrapper.vm.getCommandsHistory).not.toHaveBeenCalled();
    });

    it("getPreviousPage retreats the page and re-fetches when not on the first page", () => {
      wrapper.vm.currentPage = 2;

      wrapper.vm.getPreviousPage();

      expect(wrapper.vm.currentPage).toBe(1);
      expect(wrapper.vm.getCommandsHistory).toHaveBeenCalled();
    });

    it("getPreviousPage does nothing on the first page", () => {
      wrapper.vm.currentPage = 1;

      wrapper.vm.getPreviousPage();

      expect(wrapper.vm.currentPage).toBe(1);
      expect(wrapper.vm.getCommandsHistory).not.toHaveBeenCalled();
    });

    it("getFirstPage jumps to page 1 when not already there", () => {
      wrapper.vm.currentPage = 3;

      wrapper.vm.getFirstPage();

      expect(wrapper.vm.currentPage).toBe(1);
      expect(wrapper.vm.getCommandsHistory).toHaveBeenCalled();
    });

    it("getFirstPage does nothing when already on page 1", () => {
      wrapper.vm.currentPage = 1;

      wrapper.vm.getFirstPage();

      expect(wrapper.vm.getCommandsHistory).not.toHaveBeenCalled();
    });

    it("getLastPage jumps to the last page when not already there", () => {
      wrapper.vm.currentPage = 1;
      wrapper.vm.pages = 5;

      wrapper.vm.getLastPage();

      expect(wrapper.vm.currentPage).toBe(5);
      expect(wrapper.vm.getCommandsHistory).toHaveBeenCalled();
    });

    it("getLastPage does nothing when already on the last page", () => {
      wrapper.vm.currentPage = 5;
      wrapper.vm.pages = 5;

      wrapper.vm.getLastPage();

      expect(wrapper.vm.getCommandsHistory).not.toHaveBeenCalled();
    });
  });

  describe("resetToDefault", () => {
    it("resets the daterange and filters to their defaults", () => {
      wrapper.vm.startedTo = "2024-01-01T00:00:00.000Z";
      wrapper.vm.timeRangeLabel = "Custom Range";
      wrapper.vm.commandContains = "select";
      wrapper.vm.databaseFilter = "mydb";

      wrapper.vm.resetToDefault();

      expect(wrapper.vm.startedTo).toBeNull();
      expect(wrapper.vm.timeRangeLabel).toBe("Last 6 Hours");
      expect(wrapper.vm.commandContains).toBe("");
      expect(wrapper.vm.databaseFilter).toBe("");
    });
  });
});
