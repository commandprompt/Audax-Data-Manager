import { emitter } from "@src/emitter";
import { tabsStore } from "@src/stores/stores_initializer";
import axios from "axios";
import {
  TemplateSelectPostgresql,
  TemplateUpdatePostgresql,
  TemplateInsertPostgresql,
  TemplateSelectFunctionPostgresql,
  TemplateCallProcedurePostgresql,
} from "@src/tree_context_functions/tree_postgresql";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { flushPromises } from "@vue/test-utils";
import { handleError } from "@src/logging/utils";


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
        selectedDatabase: "database",
      },
      id: "primary-tab-id",
    },
    createQueryTab: vi.fn(),
  },
}));

describe("TemplatePostgresql Functions", () => {
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

  describe("TemplateSelectPostgresql", () => {
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

      TemplateSelectPostgresql("schema", "table", "kind");

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_select_postgresql/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
        schema: "schema",
        kind: "kind",
      });
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "database@schema.table",
        null,
        null,
        "SELECT * FROM table"
      );
      expect(emitter.emit).toHaveBeenCalledWith("tab-1_run_query");
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateSelectPostgresql("schema", "table", "kind");

      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateInsertPostgresql", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: { template: "INSERT INTO testTable VALUES ();" },
      };
      axios.post.mockResolvedValue(response);

      TemplateInsertPostgresql("schema", "table");

      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_insert_postgresql/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
        schema: "schema",
      });
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "Insert schema.table",
        null,
        null,
        "INSERT INTO testTable VALUES ();"
      );
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateInsertPostgresql("schema", "table");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateUpdatePostgresql", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: {
          template: "UPDATE table SET ...",
        },
      };
      axios.post.mockResolvedValue(response);

      TemplateUpdatePostgresql("schema", "table");
      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith("/template_update_postgresql/", {
        database_index: 1,
        workspace_id: "primary-tab-id",
        table: "table",
        schema: "schema",
      });
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "Update schema.table",
        null,
        null,
        "UPDATE table SET ..."
      );
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateUpdatePostgresql("schema", "table");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateSelectFunctionPostgresql", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: {
          template: "SELECT * FROM function()",
        },
      };
      axios.post.mockResolvedValue(response);

      TemplateSelectFunctionPostgresql("schema", "func", "functionid");
      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith(
        "/template_select_function_postgresql/",
        {
          database_index: 1,
          workspace_id: "primary-tab-id",
          function: "func",
          functionid: "functionid",
          schema: "schema",
        }
      );
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "Select schema.func",
        null,
        null,
        "SELECT * FROM function()"
      );
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateSelectFunctionPostgresql("schema", "func", "functionid");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });

  describe("TemplateCallProcedurePostgresql", () => {
    it("should call axios.post and handle success response", async () => {
      const response = {
        data: {
          template: "CALL schema.procedure()",
        },
      };
      axios.post.mockResolvedValue(response);

      TemplateCallProcedurePostgresql("schema", "procedure", "procedureid");
      await flushPromises();

      expect(axios.post).toHaveBeenCalledWith(
        "/template_call_procedure_postgresql/",
        {
          database_index: 1,
          workspace_id: "primary-tab-id",
          procedure: "procedure",
          procedureid: "procedureid",
          schema: "schema",
        }
      );
      expect(tabsStore.createQueryTab).toHaveBeenCalledWith(
        "Call schema.procedure",
        null,
        null,
        "CALL schema.procedure()"
      );
    });

    it("should call axios.post and handle error response", async () => {
      axios.post.mockRejectedValue(errorResponse);

      TemplateSelectFunctionPostgresql("schema", "procedure", "procedureid");
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(errorResponse);
    });
  });
});
