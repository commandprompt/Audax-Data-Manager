import { mount, flushPromises } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import WorkspaceTab from "@src/components/WorkspaceTab.vue";
import axios from "axios";
import { emitter } from "@src/emitter";
import { handleError } from "@src/logging/utils";
import { useConnectionsStore } from "@src/stores/connections";
import { useTabsStore } from "@src/stores/tabs";

vi.mock("bootstrap", () => ({
  Tooltip: vi.fn(),
}));

vi.mock("@src/logging/utils", () => ({
  handleError: vi.fn(),
}));

const connectionMock = {
  autocomplete: true,
  id: 1,
  technology: "postgresql",
  service: "testdb",
  color_label: 1,
};

describe("WorkspaceTab.vue", () => {
  let wrapper, connectionsStore, tabsStore, connTab;

  beforeAll(() => {
    connectionsStore = useConnectionsStore();
    tabsStore = useTabsStore();
    connTab = tabsStore.addTab({ name: "TestConnection" });
    tabsStore.selectTab(connTab);
    connTab.metaData.selectedDatabaseIndex = 1;
    connTab.metaData.selectedDBMS = "postgresql";
    connTab.metaData.selectedDatabase = "testdb";
    connectionsStore.$patch({
      connections: [connectionMock],
    });
  });

  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();

    axios.post.mockResolvedValueOnce({});

    wrapper = mount(WorkspaceTab, {
      props: { workspaceId: connTab.id },
      shallow: true,
    });
  });

  it("renders correctly", () => {
    expect(wrapper.find('[data-testid="connection-tab"]').exists()).toBe(true);
    expect(wrapper.vm.workspaceTab.metaData.selectedDatabase).toBe("testdb");
  });

  it("truncates SQLite databaseName correctly", () => {
    wrapper.vm.workspaceTab.metaData.selectedDBMS = "sqlite";
    wrapper.vm.workspaceTab.metaData.selectedDatabase = "averylongfilename.db";
    expect(wrapper.vm.databaseName.length).toBeLessThanOrEqual(13);
  });

  it("reflects autocompleteStatus changes in store", () => {
    let conn = connectionsStore.getConnection(connectionMock.id);
    expect(wrapper.vm.autocompleteStatus).toBe(true);
    conn.autocomplete = false;
    expect(wrapper.vm.autocompleteStatus).toBe(false);
  });

  it("calls emitConnectionSave correctly", () => {
    const emitterSaveSpy = vi.spyOn(emitter, "emit");
    wrapper.vm.emitConnectionSave();
    expect(emitterSaveSpy).toHaveBeenCalledWith(
      "connection-save",
      expect.any(Object),
    );
  });

  it("clearTreeTabsData resets ddl and properties", () => {
    wrapper.vm.ddlData = "ddl";
    wrapper.vm.propertiesData = [{ x: 1 }];
    wrapper.vm.clearTreeTabsData();
    expect(wrapper.vm.ddlData).toBe("");
    expect(wrapper.vm.propertiesData).toEqual([]);
  });

  it("showQuickSearch emits proper event", () => {
    const emittershowQuickSearchSpy = vi.spyOn(emitter, "emit");
    wrapper.vm.showQuickSearch("click");
    expect(emittershowQuickSearchSpy).toHaveBeenCalledWith(
      `${connTab.id}_show_quick_search`,
      "click",
    );
  });

  it("handles axios error via handleError", async () => {
    axios.post.mockRejectedValue({});

    await wrapper.vm.changeDatabase(2);
    await flushPromises();

    expect(handleError).toHaveBeenCalled();
  });

  it("sets loading state, updates data, clears timeout", async () => {
    wrapper.vm.treeTabsPaneSize = 5;
    axios.post.mockResolvedValue({ data: { properties: [1], ddl: "ddl" } });
    const params = { view: "/view", data: {} };

    wrapper.vm.getProperties(params);

    await vi.advanceTimersByTimeAsync(200);

    await flushPromises();

    expect(wrapper.vm.ddlData).toBe("ddl");
    expect(wrapper.vm.propertiesData).toEqual([1]);
    expect(wrapper.vm.showTreeTabsLoading).toBe(false);
  });

  it("handles password timeout in getProperties", async () => {
    wrapper.vm.treeTabsPaneSize = 5;
    const emitterShowPasswordSpy = vi.spyOn(emitter, "emit");
    const err = { response: { data: { password_timeout: true, data: "msg" } } };
    axios.post.mockRejectedValue(err);
    wrapper.vm.getProperties({ view: "/v", data: {} });

    await vi.advanceTimersByTimeAsync(200);

    await flushPromises();
    expect(emitterShowPasswordSpy).toHaveBeenCalledWith(
      "show_password_prompt",
      expect.any(Object),
    );
  });

  it("calls handleError for other errors", async () => {
    axios.post.mockRejectedValue({ response: { data: {} } });
    await wrapper.vm.getProperties({ view: "/v", data: {} });
    expect(handleError).toHaveBeenCalled();
  });

  it("computes correct tree component by technology", async () => {
    const map = {
      postgresql: "TreePostgresql",
      sqlite: "TreeSqlite",
      mysql: "TreeMysql",
      mariadb: "TreeMariaDB",
      oracle: "TreeOracle",
      mssql: "TreeMssql",
    };
    for (const [tech, comp] of Object.entries(map)) {
      wrapper.vm.workspaceTab.metaData.selectedDBMS = tech;
      expect(wrapper.vm.treeComponent).toBe(comp);
    }
  });

  it("shows tree tabs pane and calls getProperties when previous tab data exists", async () => {
    const getPropertiesSpy = vi
      .spyOn(wrapper.vm, "getProperties")
      .mockResolvedValue();

    wrapper.vm.treeTabsPaneSize = 2;
    wrapper.vm.lastTreeTabsPaneSize = 35;
    wrapper.vm.lastTreeTabsView = "/v";
    wrapper.vm.lastTreeTabsData = { id: 1 };

    await wrapper.vm.showTreeTabPane();

    expect(wrapper.vm.treeTabsPaneSize).toBe(35);
    expect(getPropertiesSpy).toHaveBeenCalledWith({
      data: { id: 1 },
      view: "/v",
    });
  });

  it("hides tree tabs pane and stores last size", () => {
    wrapper.vm.treeTabsPaneSize = 40;

    wrapper.vm.hideTreeTabpane();

    expect(wrapper.vm.treeTabsPaneSize).toBe(2);
    expect(wrapper.vm.lastTreeTabsPaneSize).toBe(40);
  });

  it("handles database tree resize and collapses small tree tabs pane size", () => {
    wrapper.vm.lastTreeTabsPaneSize = 40;

    wrapper.vm.handleDatabaseTreeResize([{ size: 95 }, { size: 4 }]);

    expect(wrapper.vm.treeTabsPaneSize).toBe(2);
    expect(wrapper.vm.lastTreeTabsPaneSize).toBe(40);
  });

  it("handles database tree resize and stores visible tree tabs pane size", () => {
    wrapper.vm.handleDatabaseTreeResize([{ size: 70 }, { size: 30 }]);

    expect(wrapper.vm.treeTabsPaneSize).toBe(30);
    expect(wrapper.vm.lastTreeTabsPaneSize).toBe(30);
  });
});
