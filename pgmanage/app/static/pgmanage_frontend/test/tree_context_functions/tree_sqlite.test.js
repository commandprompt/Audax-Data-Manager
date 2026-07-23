import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";
import { handleError } from "@src/logging/utils";
import { mockErrorResponse } from "../helpers/fixtures.js";
import { emitter } from "@src/emitter";
import { tabsStore } from "@src/stores/stores_initializer";
import { flushPromises } from "@vue/test-utils";
import {
  TemplateSelectSqlite,
  TemplateInsertSqlite,
  TemplateUpdateSqlite,
} from "@src/tree_context_functions/tree_sqlite";
import { tabSQLTemplate } from "@src/tree_context_functions/tree_postgresql";

vi.mock("@src/logging/utils", () => ({
  handleError: vi.fn(),
}));
vi.mock("@src/tree_context_functions/tree_postgresql", () => ({
  tabSQLTemplate: vi.fn(),
}));
vi.mock("@src/emitter", () => ({
  emitter: {
    emit: vi.fn(),
  },
}));
vi.mock("@src/stores/stores_initializer", () => ({
  tabsStore: {
    selectedPrimaryTab: {
      metaData: {
        selectedDatabaseIndex: 1,
        selectedTab: {
          id: "tab-1",
        },
        selectedDatabase: "database",
      },
      id: "primary-tab-id",
    },
    createQueryTab: vi.fn(),
  },
}));

describe("TemplateSqlite Functions", () => {
  const errorResponse = mockErrorResponse("Error message");
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  describe("TemplateSelectSqlite", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: { template: "SELECT * FROM testTable;" },
      };
      axios.post.mockResolvedValue(response);
      tabsStore.createQueryTab.mockResolvedValueOnce({
        id: "tab-1",
      });

      TemplateSelectSqlite("table", "kind");

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_select_sqlite/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
        kind: "kind",
      });
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "table",
        null,
        null,
        response.data.template
      );
      expect(emitter.emit).toHaveBeenCalledWith("tab-1_run_query");
    });

    it("should handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateSelectSqlite("table", "kind");

      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateInsertSqlite", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: { template: "INSERT INTO testTable VALUES ();" },
      };

      axios.post.mockResolvedValue(response);

      TemplateInsertSqlite("table");

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_insert_sqlite/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
      });
      expect(tabSQLTemplate).toHaveBeenCalledTimes(1);
      expect(tabSQLTemplate).toHaveBeenCalledWith(
        "Insert table",
        response.data.template
      );
    });

    it("should handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateInsertSqlite("table");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateUpdateSqlite", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: { template: "UPDATE testTable SET column = value;" },
      };
      axios.post.mockResolvedValue(response);

      TemplateUpdateSqlite("table");

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_update_sqlite/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
      });
      expect(tabSQLTemplate).toHaveBeenCalledTimes(1);
      expect(tabSQLTemplate).toHaveBeenCalledWith(
        "Update table",
        response.data.template
      );
    });

    it("should handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateUpdateSqlite("table");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });
});
