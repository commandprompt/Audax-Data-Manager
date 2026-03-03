import { mount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FileManager from "@src/components/FileManager.vue";
import axios from "axios";

const mockFiles = [
  {
    file_name: "test_file.txt",
    path: "./test_file.txt",
    is_directory: false,
    file_size: "10 KB",
    modified: "2024-02-01",
  },
  {
    file_name: "test_folder",
    path: "./test_folder",
    is_directory: true,
    dir_size: 2,
    modified: "2024-02-01",
  },
];

describe("FileManager.vue", () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mount(FileManager, {
      data() {
        return { selectedFile: { path: "/home/user/test_file.txt" } };
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    });
  });
  it("renders correctly", async () => {
    expect(wrapper.find(".modal-title").text()).toBe("File Manager");
  });

  it("fetches directory content on mount", async () => {
    axios.post.mockResolvedValue({
      data: { files: mockFiles, current_path: "/home/user", parent: false },
    });

    await wrapper.vm.getDirContent();
    expect(wrapper.vm.files).toEqual(mockFiles);
  });

  it("selects a file on click", async () => {
    await wrapper.setData({ files: mockFiles });
    await wrapper.vm.selectFileOrDir("test_file.txt");
    expect(wrapper.vm.selectedFile.file_name).toBe("test_file.txt");
  });

  it("changes view mode", async () => {
    // const wrapper = mount(FileManager);
    expect(wrapper.vm.currentView).toBe("grid");
    await wrapper.vm.changeView();
    expect(wrapper.vm.currentView).toBe("table");
    await wrapper.vm.changeView();
    expect(wrapper.vm.currentView).toBe("grid");
  });

  it("triggers file download", async () => {
    await wrapper.setData({ files: mockFiles });
    await wrapper.vm.selectFileOrDir("test_file.txt");

    const originalAppend = document.body.appendChild.bind(document.body);
    let capturedLink = null;

    const appendSpy = vi.spyOn(document.body, "appendChild").mockImplementation((node) => {
      if (node.tagName === "A") {
        capturedLink = node;
        vi.spyOn(node, "click").mockImplementation(() => {});
        vi.spyOn(node, "remove").mockImplementation(() => {});
      }
      return originalAppend(node);
    });

    await wrapper.vm.onDownload();

    const expectedPath = `/file_manager/download/?path=${encodeURIComponent(wrapper.vm.selectedFile.path)}`;

    expect(capturedLink).not.toBeNull();
    expect(capturedLink.href).toContain(expectedPath);
    expect(capturedLink.click).toHaveBeenCalled();
    expect(capturedLink.remove).toHaveBeenCalled();
    appendSpy.mockRestore();
  });

  it('calls openActionsModal with "addFile" when the add file button is clicked', async () => {
    const openActionsModalSpy = vi.spyOn(wrapper.vm, "openActionsModal");

    await wrapper.find('[data-testid="add-file-button"]').trigger("click");

    expect(openActionsModalSpy).toHaveBeenCalledWith("addFile");
  });

  it('calls openActionsModal with "addFolder" when the add folder button is clicked', async () => {
    const openActionsModalSpy = vi.spyOn(wrapper.vm, "openActionsModal");

    await wrapper.find('[data-testid="add-folder-button"]').trigger("click");

    expect(openActionsModalSpy).toHaveBeenCalledWith("addFolder");
  });

  it('calls openActionsModal with "delete" when delete button is clicked', async () => {
    const openActionsModalSpy = vi.spyOn(wrapper.vm, "openActionsModal");

    await wrapper.find('[data-testid="delete-file-button"]').trigger("click");

    expect(openActionsModalSpy).toHaveBeenCalledWith("delete");
  });
  it('calls openActionsModal with "rename" when rename button is clicked', async () => {
    const openActionsModalSpy = vi.spyOn(wrapper.vm, "openActionsModal");

    await wrapper.find('[data-testid="rename-button"]').trigger("click");

    expect(openActionsModalSpy).toHaveBeenCalledWith("rename");
  });

  it("calls onUpload  when the upload button is clicked", async () => {
    const onUploadSpy = vi.spyOn(wrapper.vm, "onUpload");

    await wrapper.find('[data-testid="upload-button"]').trigger("click");

    expect(onUploadSpy).toHaveBeenCalled();
  });

  it("calls onDownload when the download button is clicked", async () => {
    axios.post.mockResolvedValue({});
    const onDownloadSpy = vi.spyOn(wrapper.vm, "onDownload");

    await wrapper.find('[data-testid="download-button"]').trigger("click");

    expect(onDownloadSpy).toHaveBeenCalled();
  });

  it("calls stepBackDir when the step back dir button is clicked", async () => {
    axios.post.mockResolvedValue({
      data: { files: mockFiles, current_path: "/home/user", parent: false },
    });
    const stepBackDirSpy = vi.spyOn(wrapper.vm, "stepBackDir");

    await wrapper.find('[data-testid="step-back-dir-button"]').trigger("click");

    expect(stepBackDirSpy).toHaveBeenCalled();
  });

  it("calls refreshManager when the refresh manager button is clicked", async () => {
    const refreshManagerSpy = vi.spyOn(wrapper.vm, "refreshManager");

    await wrapper
      .find('[data-testid="refresh-manager-button"]')
      .trigger("click");

    expect(refreshManagerSpy).toHaveBeenCalled();
  });

  it("calls stepHomeDir when the step home dir button is clicked", async () => {
    const stepHomeDirSpy = vi.spyOn(wrapper.vm, "stepHomeDir");

    await wrapper.find('[data-testid="step-home-dir-button"]').trigger("click");

    expect(stepHomeDirSpy).toHaveBeenCalled();
  });
});
