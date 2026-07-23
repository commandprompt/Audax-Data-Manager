import {
  TemplateSelectMysql,
  TemplateInsertMysql,
  TemplateUpdateMysql,
} from "@src/tree_context_functions/tree_mysql";
import { tabSQLTemplate } from "@src/tree_context_functions/tree_postgresql";
import { emitter } from "@src/emitter";
import { tabsStore } from "@src/stores/stores_initializer";
import axios from "axios";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { flushPromises } from "@vue/test-utils";
import { handleError } from "@src/logging/utils";
import { mockErrorResponse } from "../helpers/fixtures.js";

vi.mock("@src/logging/utils", () => ({
  handleError: vi.fn(),
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
      },
      id: "primary-tab-id",
    },
    createQueryTab: vi.fn(),
  },
}));
vi.mock("@src/tree_context_functions/tree_postgresql", () => ({
  tabSQLTemplate: vi.fn(),
}));

describe("TemplateMysql Functions", () => {
  const errorResponse = mockErrorResponse("Error message");
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  describe("TemplateSelectMysql", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: {
          template: "SELECT * FROM table",
        },
      };
      axios.post.mockResolvedValue(response);
      tabsStore.createQueryTab.mockResolvedValueOnce({
        id: "tab-1",
      });

      TemplateSelectMysql("schema", "table");

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_select_mariadb/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
        schema: "schema",
      });
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "schema.table",
        null,
        null,
        "SELECT * FROM table"
      );
      expect(emitter.emit).toHaveBeenCalledWith("tab-1_run_query");
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateSelectMysql("schema", "table");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateInsertMysql", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: {
          template: "INSERT INTO table VALUES (...)",
        },
      };
      axios.post.mockResolvedValue(response);

      TemplateInsertMysql("schema", "table");

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_insert_mariadb/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
        schema: "schema",
      });
      expect(tabSQLTemplate).toHaveBeenCalledWith(
        "Insert schema.table",
        "INSERT INTO table VALUES (...)"
      );
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateInsertMysql("schema", "table");

      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateUpdateMysql", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: {
          template: "UPDATE table SET ...",
        },
      };
      axios.post.mockResolvedValue(response);

      TemplateUpdateMysql("schema", "table");
      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_update_mariadb/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
        schema: "schema",
      });
      expect(tabSQLTemplate).toHaveBeenCalledWith(
        "Update schema.table",
        "UPDATE table SET ..."
      );
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateUpdateMysql("schema", "table");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });
});
