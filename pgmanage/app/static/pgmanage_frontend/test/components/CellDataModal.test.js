import "ace-builds/src-noconflict/ace";
import { flushPromises, mount } from "@vue/test-utils";
import { describe, test, beforeEach, vi, expect, afterEach } from "vitest";
import CellDataModal from "@src/components/CellDataModal.vue";
import { useCellDataModalStore } from "@src/stores/celldata_modal";

vi.mock("bootstrap", () => ({
  Modal: {
    getOrCreateInstance: vi.fn(() => ({
      show: vi.fn(),
      hide: vi.fn(),
    })),
  },
}));

vi.mock("ace-builds/src-noconflict/ext-beautify", () => ({
  beautify: vi.fn(),
}));

describe("CellDataModal.vue", () => {
  let wrapper, cellDataModalStore;

  beforeEach(() => {
    cellDataModalStore = useCellDataModalStore();

    wrapper = mount(CellDataModal, {
      data() {
        return {
          editor: {
            setValue: vi.fn(),
            clearSelection: vi.fn(),
            getSession: vi.fn(),
            session: {
              setMode: vi.fn(),
            },
            destroy: vi.fn(),
          },
        };
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    });
  });

  afterEach(() => {
    cellDataModalStore.$reset();
  });

  test("renders modal with correct structure", () => {
    expect(wrapper.find("#cell_data_modal").exists()).toBe(true);
    expect(wrapper.find(".modal-title").text()).toBe("Show Data");
    expect(wrapper.find(".modal-body").exists()).toBe(true);
    expect(wrapper.find(".modal-footer").exists()).toBe(true);
  });

  test("shows loading spinner when showLoading is true", async () => {
    wrapper.vm.showLoading = true;
    await flushPromises();
    expect(wrapper.find(".div_loading").exists()).toBe(true);
  });

  test("hides loading spinner when showLoading is false", async () => {
    wrapper.vm.showLoading = false;
    await flushPromises();
    expect(wrapper.find(".div_loading").exists()).toBe(false);
  });

  test("renders Ace editor container", () => {
    expect(wrapper.find(".ace-editor").exists()).toBe(true);
  });

  test("renders 'View as' dropdown with options", async () => {
    cellDataModalStore.showControls = true;
    await flushPromises();
    expect(wrapper.find("select.form-select").exists()).toBe(true);
    const options = wrapper.findAll("option");
    expect(options.length).toBeGreaterThan(0);
  });

  test("updates content mode when selecting a different option", async () => {
    cellDataModalStore.showControls = true;
    await flushPromises();
    const select = wrapper.find("select.form-select");
    await select.setValue("ace/mode/sql");
    expect(wrapper.vm.contentMode).toBe("ace/mode/sql");
  });

  test("renders and toggles auto-format checkbox", async () => {
    cellDataModalStore.showControls = true;
    await flushPromises();
    const checkbox = wrapper.find("#cell_data_modal_autoformat");
    expect(checkbox.exists()).toBe(true);

    await checkbox.setChecked();
    expect(wrapper.vm.autoFormat).toBe(true);

    await checkbox.setChecked(false);
    expect(wrapper.vm.autoFormat).toBe(false);
  });

  test("calls store.hideModal when close button is clicked", async () => {
    const spy = vi.spyOn(cellDataModalStore, "hideModal");
    await wrapper.find(".btn-close").trigger("click");
    expect(spy).toHaveBeenCalled();
  });

  test("should show modal when store action is triggered", async () => {
    cellDataModalStore.showModal();
    await flushPromises();

    expect(wrapper.vm.modalInstance.show).toHaveBeenCalled();
    expect(wrapper.vm.showLoading).toBe(true);
  });

  test("should hide modal on store action", async () => {
    cellDataModalStore.showModal();
    await flushPromises();
    cellDataModalStore.hideModal();

    expect(wrapper.vm.modalInstance.hide).toHaveBeenCalled();
  });

  test("sets editor content correctly based on store values", async () => {
    cellDataModalStore.cellContent = '{"key": "value"}';
    cellDataModalStore.cellType = "json";
    wrapper.vm.setEditorContent();

    expect(wrapper.vm.editor.setValue).toHaveBeenCalledWith('{"key": "value"}');
    expect(wrapper.vm.contentMode).toBe("ace/mode/json");
  });

  test("formats content when 'Format' button is clicked", async () => {
    cellDataModalStore.showControls = true;
    await flushPromises();
    await wrapper.find('[data-testid="format-button"]').trigger("click");
    expect(wrapper.vm.editor.getSession).toHaveBeenCalled();
  });

  test("closes modal on close button click", async () => {
    wrapper.vm.setupEditor();
    const spy = vi.spyOn(cellDataModalStore, "hideModal");
    await wrapper.find('[data-testid="close-modal-button"]').trigger("click");
    expect(spy).toHaveBeenCalled();
  });

  test("calls setupEditor and setEditorContent when modal is shown", async () => {
    const setupEditorSpy = vi
      .spyOn(wrapper.vm, "setupEditor")
      .mockImplementation(() => {});
    const setEditorContentSpy = vi
      .spyOn(wrapper.vm, "setEditorContent")
      .mockImplementation(() => {});

    await wrapper.vm.$refs.cellDataModal.dispatchEvent(
      new Event("shown.bs.modal"),
    );

    expect(setupEditorSpy).toHaveBeenCalled();
    expect(setEditorContentSpy).toHaveBeenCalled();
  });

  test("calls cleanupEditor when modal is hidden", async () => {
    const cleanupEditorSpy = vi.spyOn(wrapper.vm, "cleanupEditor");

    await wrapper.vm.$refs.cellDataModal.dispatchEvent(
      new Event("hidden.bs.modal"),
    );
    expect(cleanupEditorSpy).toHaveBeenCalled();
  });

  test("formats content when autoFormat is enabled and contentMode changes", async () => {
    const formatContentSpy = vi
      .spyOn(wrapper.vm, "formatContent")
      .mockImplementation(() => {});

    wrapper.vm.autoFormat = true;
    wrapper.vm.store.visible = true;
    wrapper.vm.contentMode = "ace/mode/json";

    await flushPromises();

    expect(wrapper.vm.editor.session.setMode).toHaveBeenCalledWith(
      "ace/mode/json",
    );
    expect(formatContentSpy).toHaveBeenCalled();
  });

  test("returns correct Ace mode for JSON types", () => {
    expect(wrapper.vm.getAceMode("json")).toBe("ace/mode/json");
    expect(wrapper.vm.getAceMode("jsonb")).toBe("ace/mode/json");
  });

  test("returns correct Ace mode for XML types", () => {
    expect(wrapper.vm.getAceMode("xml")).toBe("ace/mode/xml");
    expect(wrapper.vm.getAceMode("xmltype")).toBe("ace/mode/xml");
  });

  test("returns correct Ace mode for SQL-related types", () => {
    expect(wrapper.vm.getAceMode("sql")).toBe("ace/mode/sql");
    expect(wrapper.vm.getAceMode("enum")).toBe("ace/mode/sql");
    expect(wrapper.vm.getAceMode("set")).toBe("ace/mode/sql");
    expect(wrapper.vm.getAceMode("cursor")).toBe("ace/mode/sql");
    expect(wrapper.vm.getAceMode("object")).toBe("ace/mode/sql");
  });

  test("returns plain text mode for unknown types", () => {
    expect(wrapper.vm.getAceMode("unknown_type")).toBe("ace/mode/plain_text");
    expect(wrapper.vm.getAceMode("")).toBe("ace/mode/plain_text");
    expect(wrapper.vm.getAceMode(null)).toBe("ace/mode/plain_text");
  });

  test("shows Close button in readOnly mode and hides Apply/Cancel", async () => {
    cellDataModalStore.readOnly = true;
    await flushPromises();

    expect(wrapper.find('[data-testid="close-modal-button"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="cancel-modal-button"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-testid="apply-modal-button"]').exists()).toBe(
      false,
    );
  });

  test("shows Apply/Cancel buttons in edit mode and hides Close", async () => {
    cellDataModalStore.readOnly = false;
    await flushPromises();

    expect(wrapper.find('[data-testid="close-modal-button"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-testid="cancel-modal-button"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="apply-modal-button"]').exists()).toBe(
      true,
    );
  });

  test("clicking Cancel calls store.hideModal in edit mode", async () => {
    cellDataModalStore.readOnly = false;
    await flushPromises();

    const spy = vi.spyOn(cellDataModalStore, "hideModal");
    await wrapper.find('[data-testid="cancel-modal-button"]').trigger("click");
    expect(spy).toHaveBeenCalled();
  });

  test("clicking Apply calls applyFunc with concatenated value and hides modal", async () => {
    cellDataModalStore.readOnly = false;
    cellDataModalStore.cellContent = "AAAA_BBBB";
    await flushPromises();

    wrapper.vm.loadedEndIndex = 4; // slice(4) => "_BBBB"
    wrapper.vm.editor.getValue = vi.fn(() => "ZZ");

    const applyFunc = vi.fn();
    cellDataModalStore.applyFunc = applyFunc;

    const hideSpy = vi.spyOn(cellDataModalStore, "hideModal");

    await wrapper.find('[data-testid="apply-modal-button"]').trigger("click");

    expect(applyFunc).toHaveBeenCalledWith("ZZ_BBBB");
    expect(hideSpy).toHaveBeenCalled();
  });

  test("resets loadedEndIndex to 0 when modal is hidden", async () => {
    wrapper.vm.loadedEndIndex = 123;

    await wrapper.vm.$refs.cellDataModal.dispatchEvent(
      new Event("hidden.bs.modal"),
    );

    expect(wrapper.vm.loadedEndIndex).toBe(0);
  });
});
