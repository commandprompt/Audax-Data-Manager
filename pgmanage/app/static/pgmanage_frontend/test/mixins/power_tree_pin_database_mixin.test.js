import { mount, flushPromises } from "@vue/test-utils";
import { describe, test, expect, vi, beforeEach } from "vitest";
import mixin from "@src/mixins/power_tree_pin_database_mixin";

describe("power_tree_pin_database_mixin", () => {
  let wrapper;
  let postMock;
  let updateNodeMock;
  let getParentNodeMock;
  let nodeOpenErrorMock;

  beforeEach(() => {
    postMock = vi.fn();
    updateNodeMock = vi.fn();
    getParentNodeMock = vi.fn();
    nodeOpenErrorMock = vi.fn();

    const TreeStub = {
      name: "PowerTree",
      template: "<div></div>",
      methods: {
        updateNode: updateNodeMock,
      },
    };

    wrapper = mount({
      mixins: [mixin],
      components: {
        PowerTree: TreeStub,
      },
      template: `<PowerTree ref="tree" />`,
      data() {
        return {
          api: {
            post: postMock,
          },
        };
      },
      methods: {
        getParentNode: getParentNodeMock,
        nodeOpenError: nodeOpenErrorMock,
      },
    });
  });

  test("pinDatabase pins an unpinned node and sorts parent children", async () => {
    const node = {
      title: "db_b",
      path: ["root", "db_b"],
      data: {
        pinned: false,
        someOtherField: "value",
      },
    };

    const parentNode = {
      path: ["root"],
      children: [],
    };

    const sortPinnedNodesSpy = vi.spyOn(wrapper.vm, "sortPinnedNodes");

    getParentNodeMock.mockReturnValue(parentNode);
    postMock.mockResolvedValue({});

    wrapper.vm.pinDatabase(node);
    await flushPromises();

    expect(postMock).toHaveBeenCalledWith("/pin_database/", {
      database_name: "db_b",
      pinned: true,
    });

    expect(updateNodeMock).toHaveBeenCalledWith(node.path, {
      data: {
        ...node.data,
        pinned: true,
      },
    });

    expect(getParentNodeMock).toHaveBeenCalledWith(node);
    expect(sortPinnedNodesSpy).toHaveBeenCalledWith(parentNode);
  });

  test("pinDatabase unpins a pinned node and sorts parent children", async () => {
    const node = {
      title: "db_a",
      path: ["root", "db_a"],
      data: {
        pinned: true,
      },
    };

    const parentNode = {
      path: ["root"],
      children: [],
    };

    const sortPinnedNodesSpy = vi.spyOn(wrapper.vm, "sortPinnedNodes");

    getParentNodeMock.mockReturnValue(parentNode);
    postMock.mockResolvedValue({});

    wrapper.vm.pinDatabase(node);
    await flushPromises();

    expect(postMock).toHaveBeenCalledWith("/pin_database/", {
      database_name: "db_a",
      pinned: false,
    });

    expect(updateNodeMock).toHaveBeenCalledWith(node.path, {
      data: {
        ...node.data,
        pinned: false,
      },
    });

    expect(getParentNodeMock).toHaveBeenCalledWith(node);
    expect(sortPinnedNodesSpy).toHaveBeenCalledWith(parentNode);
  });

  test("pinDatabase calls nodeOpenError when api request fails", async () => {
    const node = {
      title: "db_error",
      path: ["root", "db_error"],
      data: {
        pinned: false,
      },
    };

    const error = new Error("Request failed");
    postMock.mockRejectedValue(error);

    wrapper.vm.pinDatabase(node);
    await flushPromises();

    expect(postMock).toHaveBeenCalledWith("/pin_database/", {
      database_name: "db_error",
      pinned: true,
    });

    expect(nodeOpenErrorMock).toHaveBeenCalledWith(error, node);
    expect(updateNodeMock).not.toHaveBeenCalled();
  });

  test("sortPinnedNodes does nothing if node is null", () => {
    wrapper.vm.sortPinnedNodes(null);

    expect(updateNodeMock).not.toHaveBeenCalled();
  });

  test("sortPinnedNodes does nothing if node has no children", () => {
    const node = {
      path: ["root"],
    };

    wrapper.vm.sortPinnedNodes(node);

    expect(updateNodeMock).not.toHaveBeenCalled();
  });

  test("sortPinnedNodes does nothing if node has empty children array", () => {
    const node = {
      path: ["root"],
      children: [],
    };

    wrapper.vm.sortPinnedNodes(node);

    expect(updateNodeMock).toHaveBeenCalledWith(node.path, {
      children: [],
    });
  });

  test("sortPinnedNodes sorts pinned first, then unpinned, both alphabetically", () => {
    const node = {
      path: ["root"],
      children: [
        { title: "z_db", data: { pinned: false } },
        { title: "b_db", data: { pinned: true } },
        { title: "a_db", data: { pinned: false } },
        { title: "c_db", data: { pinned: true } },
      ],
    };

    wrapper.vm.sortPinnedNodes(node);

    expect(updateNodeMock).toHaveBeenCalledWith(node.path, {
      children: [
        { title: "b_db", data: { pinned: true } },
        { title: "c_db", data: { pinned: true } },
        { title: "a_db", data: { pinned: false } },
        { title: "z_db", data: { pinned: false } },
      ],
    });
  });

  test("sortPinnedNodes keeps only pinned nodes alphabetically sorted", () => {
    const node = {
      path: ["root"],
      children: [
        { title: "z_db", data: { pinned: true } },
        { title: "a_db", data: { pinned: true } },
      ],
    };

    wrapper.vm.sortPinnedNodes(node);

    expect(updateNodeMock).toHaveBeenCalledWith(node.path, {
      children: [
        { title: "a_db", data: { pinned: true } },
        { title: "z_db", data: { pinned: true } },
      ],
    });
  });

  test("sortPinnedNodes keeps only unpinned nodes alphabetically sorted", () => {
    const node = {
      path: ["root"],
      children: [
        { title: "z_db", data: { pinned: false } },
        { title: "a_db", data: { pinned: false } },
      ],
    };

    wrapper.vm.sortPinnedNodes(node);

    expect(updateNodeMock).toHaveBeenCalledWith(node.path, {
      children: [
        { title: "a_db", data: { pinned: false } },
        { title: "z_db", data: { pinned: false } },
      ],
    });
  });

  test("sortPinnedNodes preserves relative groups with duplicate titles across pin states", () => {
    const node = {
      path: ["root"],
      children: [
        { title: "same", data: { pinned: false } },
        { title: "same", data: { pinned: true } },
        { title: "alpha", data: { pinned: false } },
        { title: "alpha", data: { pinned: true } },
      ],
    };

    wrapper.vm.sortPinnedNodes(node);

    expect(updateNodeMock).toHaveBeenCalledWith(node.path, {
      children: [
        { title: "alpha", data: { pinned: true } },
        { title: "same", data: { pinned: true } },
        { title: "alpha", data: { pinned: false } },
        { title: "same", data: { pinned: false } },
      ],
    });
  });
});
