import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import mixin from "@src/mixins/power_tree_drop_db_object_mixin";
import { messageModalStore } from "@src/stores/stores_initializer";
import { handleError } from "@src/logging/utils";

vi.mock("@src/stores/stores_initializer", () => ({
  messageModalStore: {
    showModal: vi.fn(),
    checkboxes: [],
  },
}));

vi.mock("@src/logging/utils", () => ({
  handleError: vi.fn(),
}));

describe("power_tree_drop_db_object_mixin", () => {
  let wrapper;
  let postMock;
  let refreshTreeMock;
  let getParentNodeMock;
  let removeNodeMock;
  let updateNodeMock;

  const mountComponent = () => {
    postMock = vi.fn();
    refreshTreeMock = vi.fn();
    getParentNodeMock = vi.fn();
    removeNodeMock = vi.fn();
    updateNodeMock = vi.fn();

    return mount({
      template: "<div><div ref='tree'></div></div>",
      mixins: [mixin],
      data() {
        return {
          api: {
            post: postMock,
          },
          getRootNode: { id: "root" },
        };
      },
      methods: {
        refreshTree: refreshTreeMock,
        getParentNode: getParentNodeMock,
        removeNode: removeNodeMock,
      },
      mounted() {
        this.$refs.tree = {
          updateNode: updateNodeMock,
        };
      },
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
    messageModalStore.checkboxes = [];
    wrapper = mountComponent();
  });

  describe("parseTemplate", () => {
    it("removes first comment line and returns options from remaining comment lines", () => {
      const src = `-- DROP TABLE
DROP TABLE public.test_table
-- CASCADE
-- RESTRICT
`;

      const result = wrapper.vm.parseTemplate(src);

      expect(result).toEqual({
        query: `DROP TABLE public.test_table
-- CASCADE
-- RESTRICT
`,
        options: ["CASCADE", "RESTRICT"],
      });
    });

    it("ignores empty lines and trims option labels", () => {
      const src = `-- first comment
DROP VIEW public.test_view

  -- CASCADE  
     
-- IF EXISTS
`;

      const result = wrapper.vm.parseTemplate(src);

      expect(result.query).toBe(`DROP VIEW public.test_view

  -- CASCADE  
     
-- IF EXISTS
`);
      expect(result.options).toEqual(["CASCADE", "IF EXISTS"]);
    });

    it("returns empty options when no option comments exist", () => {
      const src = `DROP TABLE public.test_table`;

      const result = wrapper.vm.parseTemplate(src);

      expect(result).toEqual({
        query: "DROP TABLE public.test_table",
        options: [],
      });
    });
  });

  describe("buildQueryWithOptions", () => {
    it("replaces selected options in query", () => {
      const query = `DROP TABLE public.test_table
--CASCADE
--IF EXISTS`;

      const result = wrapper.vm.buildQueryWithOptions(query, [
        "CASCADE",
        "IF EXISTS",
      ]);

      expect(result).toBe(`DROP TABLE public.test_table
CASCADE
IF EXISTS`);
    });

    it("does not replace options that are null", () => {
      const query = `DROP TABLE public.test_table
--CASCADE
--IF EXISTS`;

      const result = wrapper.vm.buildQueryWithOptions(query, ["CASCADE", null]);

      expect(result).toBe(`DROP TABLE public.test_table
CASCADE
--IF EXISTS`);
    });

    it("returns original query when options are empty", () => {
      const query = `DROP TABLE public.test_table
--CASCADE`;

      const result = wrapper.vm.buildQueryWithOptions(query, []);

      expect(result).toBe(query);
    });
  });

  describe("prepareDropModal", () => {
    it("parses template, stores node/template, and opens modal with checkboxes", () => {
      const node = {
        title: "test_table",
        data: {
          type: "table",
        },
      };

      const template = `-- DROP TABLE
DROP TABLE public.test_table
-- CASCADE
-- IF EXISTS`;

      wrapper.vm.prepareDropModal(node, template);

      expect(wrapper.vm.dropNode).toStrictEqual(node);
      expect(wrapper.vm.dropTemplate).toStrictEqual({
        query: `DROP TABLE public.test_table
-- CASCADE
-- IF EXISTS`,
        options: ["CASCADE", "IF EXISTS"],
      });

      expect(messageModalStore.showModal).toHaveBeenCalledWith(
        "Are you sure you want to drop table 'test_table'?",
        wrapper.vm.dropDbObject,
        null,
        true,
        [
          { label: "CASCADE", checked: false },
          { label: "IF EXISTS", checked: false },
        ],
      );
    });
  });

  describe("dropDbObject", () => {
    it("executes query and refreshes tree when CASCADE is selected", async () => {
      wrapper.vm.dropTemplate = {
        query: `DROP TABLE public.test_table
--CASCADE
--IF EXISTS`,
        options: ["CASCADE", "IF EXISTS"],
      };
      wrapper.vm.dropNode = {
        title: "test_table",
        path: ["root", "tables", "test_table"],
        data: { type: "table" },
      };

      messageModalStore.checkboxes = [
        { label: "CASCADE", checked: true },
        { label: "IF EXISTS", checked: false },
      ];

      postMock.mockResolvedValue({});

      wrapper.vm.dropDbObject();
      await flushPromises();

      expect(postMock).toHaveBeenCalledWith("/execute_query/", {
        query: `DROP TABLE public.test_table
CASCADE
--IF EXISTS`,
      });

      expect(refreshTreeMock).toHaveBeenCalledWith(
        wrapper.vm.getRootNode,
        true,
      );
      expect(getParentNodeMock).not.toHaveBeenCalled();
      expect(removeNodeMock).not.toHaveBeenCalled();
      expect(updateNodeMock).not.toHaveBeenCalled();
    });

    it("executes query, removes node and updates parent title when CASCADE is not selected", async () => {
      const dropNode = {
        title: "test_table",
        path: ["root", "tables", "test_table"],
        data: { type: "table" },
      };
      const parentNode = {
        title: "Tables(5)",
        path: ["root", "tables"],
        children: [{}, {}, {}, {}, {}],
      };

      wrapper.vm.dropTemplate = {
        query: `DROP TABLE public.test_table
--CASCADE
--IF EXISTS`,
        options: ["CASCADE", "IF EXISTS"],
      };
      wrapper.vm.dropNode = dropNode;

      messageModalStore.checkboxes = [
        { label: "CASCADE", checked: false },
        { label: "IF EXISTS", checked: true },
      ];

      getParentNodeMock.mockReturnValue(parentNode);
      postMock.mockResolvedValue({});

      wrapper.vm.dropDbObject();
      await flushPromises();

      expect(postMock).toHaveBeenCalledWith("/execute_query/", {
        query: `DROP TABLE public.test_table
--CASCADE
IF EXISTS`,
      });

      expect(getParentNodeMock).toHaveBeenCalledWith(dropNode);
      expect(removeNodeMock).toHaveBeenCalledWith(dropNode);
      expect(refreshTreeMock).not.toHaveBeenCalled();
    });

    it("calls handleError when request fails", async () => {
      const error = new Error("request failed");

      wrapper.vm.dropTemplate = {
        query: `DROP TABLE public.test_table
--CASCADE`,
        options: ["CASCADE"],
      };
      wrapper.vm.dropNode = {
        title: "test_table",
        path: ["root", "tables", "test_table"],
        data: { type: "table" },
      };

      messageModalStore.checkboxes = [{ label: "CASCADE", checked: true }];

      postMock.mockRejectedValue(error);

      wrapper.vm.dropDbObject();
      await flushPromises();

      expect(handleError).toHaveBeenCalledWith(error);
      expect(refreshTreeMock).not.toHaveBeenCalled();
      expect(removeNodeMock).not.toHaveBeenCalled();
      expect(updateNodeMock).not.toHaveBeenCalled();
    });
  });
});
