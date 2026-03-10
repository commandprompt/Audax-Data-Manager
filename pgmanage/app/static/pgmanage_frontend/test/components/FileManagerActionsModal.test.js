import { mount, flushPromises } from "@vue/test-utils";
import FileManagerActionsModal from "@src/components/FileManagerActionsModal.vue";
import axios from "axios";
import { describe, beforeEach, it, expect } from "vitest";

describe("FileManagerActionsModal.vue", () => {
  let wrapper;

  const fileMock = {
    file_name: "test.txt",
    path: "/test.txt",
    is_directory: false,
  };

  beforeEach(() => {
    wrapper = mount(FileManagerActionsModal, {
      props: {
        action: "rename",
        file: fileMock,
        currentPath: "/test-folder",
      },
    });
  });

  it("renders correct modal title based on action", async () => {
    await wrapper.setProps({ action: "addFolder" });
    expect(wrapper.find(".modal-title").text()).toBe("New folder");

    await wrapper.setProps({ action: "addFile" });
    expect(wrapper.find(".modal-title").text()).toBe("New file");

    await wrapper.setProps({ action: "delete" });
    expect(wrapper.find(".modal-title").text()).toBe("Delete File");

    await wrapper.setProps({ action: "rename" });
    expect(wrapper.find(".modal-title").text()).toBe("Rename");
  });

  it("displays correct file icon and name", async () => {
    await wrapper.setProps({ action: "delete" });
    expect(wrapper.find("i.fa-file").exists()).toBe(true);
    expect(wrapper.find('[data-testid="delete-file-name"]').text()).toBe(fileMock.file_name);
  });

  it("emits actionDone event on successful rename", async () => {
    axios.post.mockResolvedValueOnce({ data: {} });

    const input = wrapper.find("input");
    await input.setValue("new_name.txt");

    await wrapper.find("button.btn-primary").trigger("click");
    await flushPromises();

    expect(wrapper.emitted("actionDone")).toBeTruthy();
    expect(wrapper.emitted("actionDone")[0]).toEqual([
      expect.any(Object),
      "new_name.txt",
    ]);
  });

  it("emits actionDone event on successful create", async () => {
    axios.post.mockResolvedValueOnce({ data: {} });

    await wrapper.setProps({ action: "addFile" });

    const input = wrapper.find("input");
    await input.setValue("new_file.txt");

    await wrapper.find("button.btn-primary").trigger("click");
    await flushPromises();

    expect(axios.post).toHaveBeenCalledWith("/file_manager/create/", {
      path: "/test-folder",
      name: "new_file.txt",
      type: "file",
    });

    expect(wrapper.emitted("actionDone")).toBeTruthy();
    expect(wrapper.emitted("actionDone")[0]).toEqual([
      expect.any(Object),
      "new_file.txt",
    ]);
  });

  it("emits actionDone event on successful delete", async () => {
    axios.post.mockResolvedValueOnce({ data: {} });

    await wrapper.setProps({ action: "delete" });
    await wrapper.find("button.btn-danger").trigger("click");
    await flushPromises();

    expect(axios.post).toHaveBeenCalledWith("/file_manager/delete/", {
      path: "/test.txt",
    });

    expect(wrapper.emitted("actionDone")).toBeTruthy();
  });

  it("clears input field when modal is hidden", async () => {
    const input = wrapper.find("input");
    await input.setValue("temp_name.txt");

    wrapper.vm.$refs.fileManagerActionsModal.dispatchEvent(
      new Event("hidden.bs.modal")
    );
    await flushPromises();

    expect(wrapper.vm.name).toBe("");
  });

  it("handles API errors and displays toast on failure", async () => {
    const errorMsg = "Something went wrong";
    axios.post.mockRejectedValueOnce({
      response: { data: { data: errorMsg } },
    });

    const input = wrapper.find("input");
    await input.setValue("fail_name.txt");

    await wrapper.find("button.btn-primary").trigger("click");
    await flushPromises();

    expect(axios.post).toHaveBeenCalled();
    expect(wrapper.vm.name).toBe("fail_name.txt");
  });
});
