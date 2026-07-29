import { flushPromises, mount, enableAutoUnmount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ConfigTab from "@src/components/ConfigTab.vue";
import axios from "axios";
import { tabsStore } from "@src/stores/stores_initializer";
import { handleError } from "@src/logging/utils";
import { mockErrorResponse } from "../helpers/fixtures.js";

vi.mock("@src/logging/utils", () => ({
  handleError: vi.fn(),
}));

vi.mock("@src/stores/stores_initializer", () => ({
  tabsStore: {
    getSecondaryTabById: vi.fn(),
  },
}));

enableAutoUnmount(afterEach);

describe("ConfigTab.vue", () => {
  let wrapper;
  const initialProps = {
    workspaceId: "test-workspace-id",
    databaseIndex: 0,
    tabId: "test-tab-id",
  };

  const categoriesResponse = {
    data: { categories: ["Category 1", "Category 2"] },
  };

  const settingsResponse = {
    data: {
      settings: [
        {
          category: "Category 1",
          rows: [{ name: "autovacuum", desc: "Starts the autovacuum" }],
        },
        {
          category: "Category 2",
          rows: [{ name: "temp_file_limit", desc: "Limits the total" }],
        },
      ],
    },
  };

  const configHistoryResponse = {
    data: {
      config_history: [
        { name: "Category 1", start_time: "2024-08-01T12:00:00Z" },
        { name: "Category 2", start_time: "2024-08-01T12:00:00Z" },
      ],
    },
  };

  const configStatusResponse = {
    data: {
      restart_pending: [],
      restart_changes: [],
    },
  };

  const mountComponent = (options = {}) => {
    return mount(ConfigTab, {
      props: initialProps,
      shallow: true,
      ...options,
    });
  };
  beforeEach(() => {
    vi.clearAllMocks();
    axios.post
      .mockResolvedValueOnce(categoriesResponse)
      .mockResolvedValueOnce(settingsResponse)
      .mockResolvedValueOnce(configHistoryResponse)
      .mockResolvedValueOnce(configStatusResponse);

    wrapper = mountComponent();
  });

  it("renders correctly", () => {
    expect(wrapper.exists()).toBe(true);
  });

  it("fetches categories on mount", async () => {
    await flushPromises();
    expect(axios.post).toHaveBeenCalledWith("/configuration/categories/", {
      database_index: initialProps.databaseIndex,
      workspace_id: initialProps.workspaceId,
    });
    expect(wrapper.vm.categories).toEqual(["Category 1", "Category 2"]);
    expect(wrapper.vm.selected).toBe("Category 1");
  });

  it("handles configuration save", async () => {
    wrapper.setData({
      updateSettings: { setting1: { name: "setting1", setting: "value1" } },
    });
    axios.post
      .mockResolvedValueOnce(settingsResponse)
      .mockResolvedValueOnce(configHistoryResponse)
      .mockResolvedValueOnce(settingsResponse)
      .mockResolvedValueOnce(configStatusResponse);
    await wrapper.vm.saveConfiguration();

    await flushPromises();

    expect(axios.post).toHaveBeenNthCalledWith(5, "/save_configuration/", {
      database_index: initialProps.databaseIndex,
      workspace_id: initialProps.workspaceId,
      settings: expect.objectContaining({
        setting1: expect.objectContaining({
          name: "setting1",
          setting: "value1",
        }),
      }),
      commit_comment: "",
      new_config: true,
    });
    expect(wrapper.vm.updateSettings).toEqual({});
    expect(handleError).not.toHaveBeenCalled();
  });

  it("displays error on failed configuration save", async () => {
    const errorResponse = mockErrorResponse("Failed to save configuration");
    axios.post.mockRejectedValueOnce(errorResponse);
    wrapper.setData({
      updateSettings: { setting1: { name: "setting1", setting: "value1" } },
    });

    await wrapper.vm.saveConfiguration();

    await flushPromises();

    expect(handleError).toHaveBeenCalledWith(errorResponse);
  });

  it("truncates text correctly", () => {
    const input = {
      start_time: "2024-08-09T12:00:00Z",
      commit_comment: "This is a long commit message",
    };
    const truncatedText = wrapper.vm.truncateText(input, 30);

    expect(truncatedText).toBe("2024-08-09T12:00:00Z - This i...");
  });

  it("watches for update values correctly", async () => {
    tabsStore.getSecondaryTabById.mockReturnValue({
      metaData: { hasUnsavedChanges: false },
    });
    wrapper.setData({
      updateSettings: { setting1: { name: "setting1", setting: "value1" } },
    });

    await flushPromises();

    expect(tabsStore.getSecondaryTabById).toHaveBeenCalledWith(
      initialProps.tabId,
      initialProps.workspaceId
    );
    expect(wrapper.vm.$data.updateSettings).toEqual(
      expect.objectContaining({
        setting1: { name: "setting1", setting: "value1" },
      })
    );
  });

  it("returns correct suggestions according to query_filter", () => {
    wrapper.vm.query_filter = "autovacuum";

    expect(wrapper.vm.currentResult[0]["rows"]).toContainEqual({
      name: "autovacuum",
      desc: "Starts the autovacuum",
    });
    expect(wrapper.vm.currentResult[0]["rows"]).not.toContainEqual({
      name: "temp_file_limit",
      desc: "Limits the total",
    });
  });

  it("hasRevertValues returns false if no config differs", () => {
    wrapper.setData({
      configDiffData: "",
    });

    expect(wrapper.vm.hasRevertValues).toBe(false);
  });

  it("hasRevertValues returns true if config differs", () => {
    wrapper.setData({
      configDiffData: [{ name: "max_connections", value: "100" }],
    });

    expect(wrapper.vm.hasRevertValues).toBe(true);
  });
});
