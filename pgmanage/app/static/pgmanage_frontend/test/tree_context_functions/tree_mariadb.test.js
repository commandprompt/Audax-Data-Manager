import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  TemplateSelectMariadb,
  TemplateInsertMariadb,
  TemplateUpdateMariadb,
} from "@src/tree_context_functions/tree_mariadb";
import axios from "axios";
import { emitter } from "@src/emitter";
import { tabsStore } from "@src/stores/stores_initializer";
import { flushPromises } from "@vue/test-utils";
import { tabSQLTemplate } from "@src/tree_context_functions/tree_postgresql";
import { handleError } from "@src/logging/utils";

vi.mock("@src/logging/utils", () => ({
  handleError: vi.fn(),
}));
vi.mock("@src/emitter", () => ({
  emitter: {
    emit: vi.fn(),
  },
}));
vi.mock("@src/tree_context_functions/tree_postgresql", () => ({
  tabSQLTemplate: vi.fn(),
}));
vi.mock("@src/stores/stores_initializer", () => ({
  tabsStore: {
    selectedPrimaryTab: {
      metaData: {
        selectedDatabaseIndex: 1,
        selectedTab: { id: "tab-1" },
      },
      id: "primary-tab-id",
    },
    createQueryTab: vi.fn(),
  },
}));

describe("Template Functions", () => {
  const errorResponse = {
    response: {
      data: {
        data: "Error message",
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  describe("TemplateSelectMariadb", async () => {
    it("should create a query tab and emit run query event on success", async () => {
      const schema = "testSchema";
      const table = "testTable";
      const response = { data: { template: "SELECT * FROM testTable;" } };

      axios.post.mockResolvedValueOnce(response);
      tabsStore.createQueryTab.mockResolvedValueOnce({
        id: "tab-1",
      });

      TemplateSelectMariadb(schema, table);

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_select_mariadb/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table,
        schema,
      });
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "testSchema.testTable",
        null,
        null,
        response.data.template
      );
      expect(emitter.emit).toHaveBeenCalledWith("tab-1_run_query");
    });

    it("should show error toast on failure", async () => {
      const schema = "testSchema";
      const table = "testTable";

      axios.post.mockRejectedValueOnce(errorResponse);

      TemplateSelectMariadb(schema, table);
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateInsertMariadb", () => {
    it("should call tabSQLTemplate on success", async () => {
      const schema = "testSchema";
      const table = "testTable";
      const response = {
        data: { template: "INSERT INTO testTable VALUES ();" },
      };

      axios.post.mockResolvedValueOnce(response);

      TemplateInsertMariadb(schema, table);
      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_insert_mariadb/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table,
        schema,
      });
      expect(tabSQLTemplate).toHaveBeenCalledWith(
        "Insert testSchema.testTable",
        response.data.template
      );
    });

    it("should show error toast on failure", async () => {
      const schema = "testSchema";
      const table = "testTable";

      axios.post.mockRejectedValueOnce(errorResponse);

      TemplateInsertMariadb(schema, table);

      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateUpdateMariadb", () => {
    it("should call tabSQLTemplate on success", async () => {
      const schema = "testSchema";
      const table = "testTable";
      const response = { data: { template: "UPDATE testTable SET ...;" } };

      axios.post.mockResolvedValueOnce(response);

      TemplateUpdateMariadb(schema, table);

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_update_mariadb/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table,
        schema,
      });
      expect(tabSQLTemplate).toHaveBeenCalledWith(
        "Update testSchema.testTable",
        response.data.template
      );
    });

    it("should show error toast on failure", async () => {
      const schema = "testSchema";
      const table = "testTable";

      axios.post.mockRejectedValueOnce(errorResponse);

      TemplateUpdateMariadb(schema, table);

      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });
});
