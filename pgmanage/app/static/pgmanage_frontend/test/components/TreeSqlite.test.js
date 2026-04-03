import { describe, it, expect, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import TreeSqlite from "@src/components/TreeSqlite.vue";
import { emitter } from "@src/emitter";
import { tabsStore } from "@src/stores/stores_initializer";
import { operationModes } from "@src/constants";
import {
  TemplateSelectSqlite,
  TemplateInsertSqlite,
  TemplateUpdateSqlite,
} from "@src/tree_context_functions/tree_sqlite";
import { tabSQLTemplate } from "@src/tree_context_functions/tree_postgresql";

vi.mock("@src/tree_context_functions/tree_sqlite", () => ({
  TemplateSelectSqlite: vi.fn(),
  TemplateInsertSqlite: vi.fn(),
  TemplateUpdateSqlite: vi.fn(),
}));

vi.mock("@src/tree_context_functions/tree_postgresql", () => ({
  tabSQLTemplate: vi.fn(),
}));

vi.mock("@src/emitter", () => ({
  emitter: {
    on: vi.fn(),
    emit: vi.fn(),
    all: {
      delete: vi.fn(),
    },
  },
}));

vi.mock("@src/stores/stores_initializer", () => ({
  tabsStore: {
    selectedPrimaryTab: {
      id: "primary-tab-id",
      metaData: {
        selectedDatabase: "test_db",
        selectedDBMS: "sqlite",
        secondaryTabs: [],
        selectedTab: null,
      },
    },
    createSchemaEditorTab: vi.fn(),
    createERDTab: vi.fn(),
    createDataEditorTab: vi.fn(),
    createQueryTab: vi.fn(),
  },
}));

vi.mock("@src/mixins/power_tree.js", () => ({
  default: {
    data() {
      return {
        selectedNode: null,
        templates: {
          delete: "DELETE FROM #table_name#",
          drop_table: "DROP TABLE #table_name#",
          create_column: "ALTER TABLE #table_name# ADD COLUMN col TEXT",
          create_index: "CREATE INDEX idx ON #table_name# (col)",
          reindex: "REINDEX #index_name#",
          create_trigger: "CREATE TRIGGER trg BEFORE INSERT ON #table_name#",
          alter_trigger: "ALTER TRIGGER #trigger_name# ON #table_name#",
          drop_trigger: "DROP TRIGGER #trigger_name#",
          create_view: "CREATE VIEW v_test AS SELECT 1",
          drop_view: "DROP VIEW #view_name#",
        },
        api: {
          post: vi.fn(),
        },
      };
    },
    methods: {
      doubleClickNode: vi.fn(),
      onToggle: vi.fn(),
      onContextMenu: vi.fn(),
      onClickHandler: vi.fn(),
      handleLeftSideClick: vi.fn(),
      handleLeftSideDblClick: vi.fn(),
      formatTitle(node) {
        return node.title;
      },
      getRootNode: vi.fn(() => ({
        title: "Sqlite",
        path: [0],
        children: [],
        data: { type: "server" },
      })),
      shouldUpdateNode: vi.fn(() => true),
      insertSpinnerNode: vi.fn(),
      insertNode: vi.fn(),
      removeChildNodes: vi.fn(),
      nodeOpenError: vi.fn(),
      getParentNode: vi.fn(() => ({ title: "parent_table" })),
      getParentNodeDeep: vi.fn(() => ({ title: "deep_parent_table" })),
      getFirstChildNode: vi.fn(() => ({
        title: "Columns",
        path: [0, 0],
        children: [],
      })),
      expandAndRefreshIfNeeded: vi.fn(),
      getNodeEl: vi.fn(() => ({
        scrollIntoView: vi.fn(),
      })),
      prepareDropModal: vi.fn(),
    },
  },
}));

vi.mock("@src/mixins/power_tree_drop_db_object_mixin.js", () => ({
  default: {
    methods: {},
  },
}));

describe("TreeSqlite.vue", () => {
  const mountComponent = () => {
    return mount(TreeSqlite, {
      props: {
        databaseIndex: 1,
        workspaceId: "ws-1",
      },
      global: {
        stubs: {
          PowerTree: true,
        },
      },
      shallow: true,
    });
  };

  it("renders with default root node", () => {
    const wrapper = mountComponent();

    expect(wrapper.vm.nodes).toEqual([
      {
        title: "Sqlite",
        isExpanded: false,
        isDraggable: false,
        data: {
          icon: "node node-sqlite",
          type: "server",
          contextMenu: "cm_server",
        },
      },
    ]);
  });

  it("cm_tables Create Table calls createSchemaEditorTab", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = { title: "Tables" };

    wrapper.vm.contextMenu.cm_tables[1].onClick();

    expect(tabsStore.createSchemaEditorTab).toHaveBeenCalledWith(
      wrapper.vm.selectedNode,
      operationModes.CREATE,
    );
  });

  it("cm_tables ER Diagram calls createERDTab", () => {
    const wrapper = mountComponent();

    wrapper.vm.contextMenu.cm_tables[2].onClick();

    expect(tabsStore.createERDTab).toHaveBeenCalled();
  });

  it("cm_table Query Data calls TemplateSelectSqlite", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = {
      title: "users",
      data: { raw_value: "users" },
    };

    wrapper.vm.contextMenu.cm_table[1].onClick();

    expect(TemplateSelectSqlite).toHaveBeenCalledWith("users", "t");
  });

  it("cm_table Edit Data calls createDataEditorTab", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = {
      title: "users",
      data: { raw_value: "users" },
    };

    wrapper.vm.contextMenu.cm_table[2].onClick();

    expect(tabsStore.createDataEditorTab).toHaveBeenCalledWith("users", null);
  });

  it("cm_table Alter Table calls createSchemaEditorTab with UPDATE mode", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = {
      title: "users",
      data: { raw_value: "users" },
    };

    wrapper.vm.contextMenu.cm_table[3].onClick();

    expect(tabsStore.createSchemaEditorTab).toHaveBeenCalledWith(
      wrapper.vm.selectedNode,
      operationModes.UPDATE,
    );
  });

  it("cm_table Insert template calls TemplateInsertSqlite", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = { title: "users", data: { raw_value: "users" } };

    wrapper.vm.contextMenu.cm_table[4].children[0].onClick();

    expect(TemplateInsertSqlite).toHaveBeenCalledWith("users");
  });

  it("cm_table Update template calls TemplateUpdateSqlite", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = { title: "users", data: { raw_value: "users" } };

    wrapper.vm.contextMenu.cm_table[4].children[1].onClick();

    expect(TemplateUpdateSqlite).toHaveBeenCalledWith("users");
  });

  it("cm_table Delete Records uses raw_value", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = {
      title: "users",
      data: { raw_value: "users_raw" },
    };
    wrapper.vm.templates.delete = "DELETE FROM #table_name#";

    wrapper.vm.contextMenu.cm_table[4].children[2].onClick();

    expect(tabSQLTemplate).toHaveBeenCalledWith(
      "Delete Records",
      "DELETE FROM users_raw",
    );
  });

  it("cm_table Drop Table calls prepareDropModal", () => {
    const wrapper = mountComponent();
    const prepareDropModalSpy = vi.spyOn(wrapper.vm, "prepareDropModal");

    wrapper.vm.selectedNode = {
      title: "users",
      data: { raw_value: "users_raw" },
    };
    wrapper.vm.templates.drop_table = "DROP TABLE #table_name#";

    wrapper.vm.contextMenu.cm_table[5].onClick();

    expect(prepareDropModalSpy).toHaveBeenCalledWith(
      wrapper.vm.selectedNode,
      "DROP TABLE users_raw",
    );
  });

  it("cm_view Query Data calls TemplateSelectSqlite with view type", () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = {
      title: "active_users",
      data: { raw_value: "active_users" },
    };

    wrapper.vm.contextMenu.cm_view[1].onClick();

    expect(TemplateSelectSqlite).toHaveBeenCalledWith("active_users", "v");
  });

  it("refreshTree returns early when shouldUpdateNode is false", async () => {
    const wrapper = mountComponent();
    wrapper.vm.shouldUpdateNode = vi.fn(() => false);
    const insertSpinnerNodeSpy = vi.spyOn(wrapper.vm, "insertSpinnerNode");

    await wrapper.vm.refreshTree(
      { data: { type: "server" }, children: [] },
      true,
    );

    expect(insertSpinnerNodeSpy).not.toHaveBeenCalled();
  });

  it("refreshTree routes server nodes to getTreeDetailsSqlite", async () => {
    const wrapper = mountComponent();
    wrapper.vm.getTreeDetailsSqlite = vi.fn();

    const node = { data: { type: "server" }, children: [] };
    await wrapper.vm.refreshTree(node, true);

    expect(wrapper.vm.getTreeDetailsSqlite).toHaveBeenCalledWith(node);
  });

  it("refreshTree routes table_list nodes to getTablesSqlite", async () => {
    const wrapper = mountComponent();
    wrapper.vm.getTablesSqlite = vi.fn();

    const node = { data: { type: "table_list" }, children: [] };
    await wrapper.vm.refreshTree(node, true);

    expect(wrapper.vm.getTablesSqlite).toHaveBeenCalledWith(node);
  });

  it("refreshTree routes view nodes to getViewsColumnsSqlite", async () => {
    const wrapper = mountComponent();
    wrapper.vm.getViewsColumnsSqlite = vi.fn();

    const node = { data: { type: "view" }, children: [{}] };
    await wrapper.vm.refreshTree(node, true);

    expect(wrapper.vm.getViewsColumnsSqlite).toHaveBeenCalledWith(node);
  });

  it("getProperties emits treeTabsUpdate for handled types", () => {
    const wrapper = mountComponent();
    wrapper.vm.getParentNodeDeep = vi.fn(() => ({ title: "users" }));

    wrapper.vm.getProperties({
      title: "id",
      data: { type: "table_field" },
    });

    expect(wrapper.emitted("treeTabsUpdate")).toEqual([
      [
        {
          data: {
            table: "users",
            object: "id",
            type: "table_field",
          },
          view: "/get_properties_sqlite/",
        },
      ],
    ]);
  });

  it("getProperties emits clearTabs for unsupported types", () => {
    const wrapper = mountComponent();

    wrapper.vm.getProperties({
      title: "Tables",
      data: { type: "table_list" },
    });

    expect(wrapper.emitted("clearTabs")).toEqual([[]]);
  });

  it("getTreeDetailsSqlite handles error via nodeOpenError", async () => {
    const wrapper = mountComponent();
    const error = new Error("boom");
    const node = { path: [0], children: [], data: { type: "server" } };
    const nodeOpenErrorSpy = vi.spyOn(wrapper.vm, "nodeOpenError");

    wrapper.vm.api.post.mockRejectedValue(error);

    await wrapper.vm.getTreeDetailsSqlite(node);

    expect(nodeOpenErrorSpy).toHaveBeenCalledWith(error, node);
  });

  it("getViewDefinition opens query tab with drop + definition", async () => {
    const wrapper = mountComponent();
    wrapper.vm.selectedNode = { title: "active_users" };
    wrapper.vm.templates.drop_view = "DROP VIEW #view_name#";
    wrapper.vm.api.post.mockResolvedValue({
      data: {
        data: "CREATE VIEW active_users AS SELECT * FROM users;",
      },
    });

    await wrapper.vm.getViewDefinition({ title: "active_users" });
    await flushPromises();

    expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
      "active_users",
      null,
      null,
      "DROP VIEW active_users;\nCREATE VIEW active_users AS SELECT * FROM users;",
    );
  });

  it("unmounted removes workspace emitter listeners", () => {
    const wrapper = mountComponent();

    wrapper.unmount();

    expect(emitter.all.delete).toHaveBeenCalledWith("schemaChanged_ws-1");
    expect(emitter.all.delete).toHaveBeenCalledWith("goToNode_ws-1");
  });
});
