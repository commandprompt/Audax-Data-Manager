import { flushPromises, mount } from "@vue/test-utils";
import SearchModal from "@src/components/SearchModal.vue";
import { emitter } from "@src/emitter";
import { dbMetadataStore } from "@src/stores/stores_initializer";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@src/stores/stores_initializer", () => ({
  tabsStore: {
    selectedPrimaryTab: { metaData: { selectedDatabase: "testdb" } },
  },
  dbMetadataStore: {
    getDbMeta: vi.fn(),
    getDatabases: vi.fn(),
  },
}));

const workspaceId = "ws-1";
const searchEvent = `${workspaceId}_show_quick_search`;

function schemaFixture() {
  return [
    {
      name: "public",
      tables: [{ name: "users" }, { name: "orders" }],
      views: [{ name: "user_stats" }],
    },
  ];
}

describe("SearchModal.vue", () => {
  let wrapper;

  const mountComponent = (props = {}) => {
    wrapper?.unmount();
    wrapper = mount(SearchModal, {
      props: {
        workspaceId,
        databaseIndex: 1,
        databaseTechnology: "postgresql",
        ...props,
      },
      // The modal teleports to the body, and the input must be in the
      // document to get focus.
      global: { stubs: { teleport: true } },
      attachTo: document.body,
    });
  };

  const openSearch = async () => {
    emitter.emit(searchEvent);
    await flushPromises();
  };

  const search = async (query) => {
    await wrapper.find("input").setValue(query);
  };

  const pressKey = async (key) => {
    await wrapper.find("input").trigger("keydown", { key });
  };

  const resultItems = () => wrapper.findAll(".search-modal__results_item");

  const resultNames = () =>
    resultItems().map((item) => item.find("div > div").text());

  const resultByName = (name) =>
    resultItems().find((item) => item.find("div > div").text() === name);

  const metaTags = (item) =>
    item.findAll(".meta-tags small").map((tag) => tag.text());

  const selectedIndex = () =>
    resultItems().findIndex((item) => item.classes("selected"));

  const isOpen = () => wrapper.find("#searchPalette").exists();

  beforeEach(() => {
    dbMetadataStore.getDbMeta.mockReturnValue(schemaFixture());
    dbMetadataStore.getDatabases.mockReturnValue(["testdb", "otherdb"]);
    mountComponent();
  });

  afterEach(() => {
    wrapper?.unmount();
    wrapper = null;
    vi.restoreAllMocks();
  });

  describe("opening and closing", () => {
    it("stays hidden until the quick search event arrives", async () => {
      expect(isOpen()).toBe(false);

      await openSearch();

      expect(isOpen()).toBe(true);
    });

    it("focuses the search input when it opens", async () => {
      await openSearch();

      expect(document.activeElement).toBe(wrapper.find("input").element);
    });

    it("closes and clears the query on Escape", async () => {
      await openSearch();
      await search("users");

      await wrapper.find("input").trigger("keyup.esc");
      expect(isOpen()).toBe(false);

      await openSearch();
      expect(wrapper.find("input").element.value).toBe("");
    });

    it("closes when the input loses focus", async () => {
      await openSearch();

      await wrapper.find("input").trigger("blur");

      expect(isOpen()).toBe(false);
    });

    it("stops listening for the quick search event after unmount", () => {
      wrapper.unmount();
      wrapper = null;

      expect(emitter.all.get(searchEvent)).toBeUndefined();
    });
  });

  describe("results", () => {
    it("shows no results until the user types", async () => {
      await openSearch();

      expect(resultItems()).toHaveLength(0);
    });

    it("finds a table", async () => {
      await openSearch();

      await search("users");

      expect(resultByName("users").find("span.text-muted").text()).toBe(
        "table"
      );
    });

    it("finds a view", async () => {
      await openSearch();

      await search("user_stats");

      expect(resultByName("user_stats").find("span.text-muted").text()).toBe(
        "view"
      );
    });

    it("finds a schema", async () => {
      await openSearch();

      await search("public");

      expect(resultByName("public").find("span.text-muted").text()).toBe(
        "schema"
      );
    });

    it("finds a database", async () => {
      await openSearch();

      await search("otherdb");

      expect(resultByName("otherdb").find("span.text-muted").text()).toBe(
        "database"
      );
    });

    it("handles a schema that has no tables and no views", async () => {
      dbMetadataStore.getDbMeta.mockReturnValue([{ name: "empty_schema" }]);
      await openSearch();

      await search("empty_schema");

      expect(resultByName("empty_schema").find("span.text-muted").text()).toBe(
        "schema"
      );
    });

    it("leaves schemas out for mysql", async () => {
      mountComponent({ databaseTechnology: "mysql" });
      await openSearch();

      await search("public");
      expect(resultByName("public")).toBeUndefined();

      await search("users");
      expect(resultByName("users")).toBeDefined();
    });

    it("keeps one entry per object when the search opens again", async () => {
      await openSearch();
      await openSearch();

      await search("users");
      expect(resultNames().filter((name) => name === "users")).toHaveLength(1);

      await search("otherdb");
      expect(resultNames().filter((name) => name === "otherdb")).toHaveLength(
        1
      );
    });
  });

  describe("meta tags", () => {
    it("shows the schema, the name and the database for a table", async () => {
      await openSearch();

      await search("users");

      expect(metaTags(resultByName("users"))).toEqual([
        "public",
        ".users",
        "@testdb",
      ]);
    });

    it("shows only the database for a schema", async () => {
      await openSearch();

      await search("public");

      expect(metaTags(resultByName("public"))).toEqual(["@testdb"]);
    });

    it("shows no meta tags for a database", async () => {
      await openSearch();

      await search("otherdb");

      expect(metaTags(resultByName("otherdb"))).toEqual([]);
    });

    it("shows the name and the database for mysql", async () => {
      mountComponent({ databaseTechnology: "mysql" });
      await openSearch();

      await search("users");

      expect(metaTags(resultByName("users"))).toEqual(["users", "@testdb"]);
    });

    it("shows no meta tags for sqlite", async () => {
      mountComponent({ databaseTechnology: "sqlite" });
      await openSearch();

      await search("users");

      expect(metaTags(resultByName("users"))).toEqual([]);
    });
  });

  describe("keyboard navigation", () => {
    it("selects the first result by default", async () => {
      await openSearch();

      await search("user");

      expect(selectedIndex()).toBe(0);
    });

    it("moves the selection down and wraps at the last result", async () => {
      await openSearch();
      await search("user");
      const count = resultItems().length;
      expect(count).toBeGreaterThan(1);

      await pressKey("ArrowDown");
      expect(selectedIndex()).toBe(1);

      for (let i = 1; i < count; i++) {
        await pressKey("ArrowDown");
      }
      expect(selectedIndex()).toBe(0);
    });

    it("moves the selection up and wraps to the last result", async () => {
      await openSearch();
      await search("user");
      const count = resultItems().length;
      expect(count).toBeGreaterThan(1);

      await pressKey("ArrowDown");
      await pressKey("ArrowUp");
      expect(selectedIndex()).toBe(0);

      await pressKey("ArrowUp");
      expect(selectedIndex()).toBe(count - 1);
    });

    it("scrolls the selected result into view", async () => {
      await openSearch();
      await search("user");
      const scrollIntoView = vi.spyOn(
        resultItems()[1].element,
        "scrollIntoView"
      );

      await pressKey("ArrowDown");

      expect(scrollIntoView).toHaveBeenCalled();
    });
  });

  describe("opening a result", () => {
    it("goes to the selected result on Enter and closes", async () => {
      await openSearch();
      await search("users");
      expect(resultNames()[0]).toBe("users");
      const emitSpy = vi.spyOn(emitter, "emit");

      await wrapper.find("input").trigger("keyup.enter");

      expect(emitSpy).toHaveBeenCalledWith(`goToNode_${workspaceId}`, {
        type: "table",
        name: "users",
        schema: "public",
        database: "testdb",
      });
      expect(isOpen()).toBe(false);
    });

    it("does nothing on Enter when there are no results", async () => {
      await openSearch();
      const emitSpy = vi.spyOn(emitter, "emit");

      await wrapper.find("input").trigger("keyup.enter");

      expect(emitSpy).not.toHaveBeenCalled();
      expect(isOpen()).toBe(true);
    });

    it("goes to a view when the user clicks it", async () => {
      await openSearch();
      await search("user_stats");
      const emitSpy = vi.spyOn(emitter, "emit");

      await resultByName("user_stats").trigger("mousedown");

      expect(emitSpy).toHaveBeenCalledWith(`goToNode_${workspaceId}`, {
        type: "view",
        name: "user_stats",
        schema: "public",
        database: "testdb",
      });
      expect(isOpen()).toBe(false);
    });

    it("goes to a schema when the user clicks it", async () => {
      await openSearch();
      await search("public");
      const emitSpy = vi.spyOn(emitter, "emit");

      await resultByName("public").trigger("mousedown");

      expect(emitSpy).toHaveBeenCalledWith(`goToNode_${workspaceId}`, {
        type: "schema",
        name: "public",
        schema: "public",
        database: "testdb",
      });
    });

    it("goes to a database when the user clicks it", async () => {
      await openSearch();
      await search("otherdb");
      const emitSpy = vi.spyOn(emitter, "emit");

      await resultByName("otherdb").trigger("mousedown");

      expect(emitSpy).toHaveBeenCalledWith(`goToNode_${workspaceId}`, {
        type: "database",
        name: "otherdb",
        database: "otherdb",
      });
    });
  });
});
