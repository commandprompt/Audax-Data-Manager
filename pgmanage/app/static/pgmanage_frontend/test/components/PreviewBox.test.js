import { mount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import PreviewBox from "@src/components/PreviewBox.vue";

vi.mock("sql-formatter", () => ({ format: vi.fn((text) => text) }));

vi.mock("@src/stores/stores_initializer", () => ({
  settingsStore: {
    editorTheme: "omnidb",
    fontSize: 12,
    $subscribe: vi.fn(),
  },
  tabsStore: {
    createQueryTab: vi.fn(),
  },
}));

const aceMockEditor = {
  setTheme: vi.fn(),
  setFontSize: vi.fn(),
  setReadOnly: vi.fn(),
  setShowPrintMargin: vi.fn(),
  setValue: vi.fn(),
  clearSelection: vi.fn(),
  moveCursorTo: vi.fn(),
  resize: vi.fn(),
  commands: { bindKey: vi.fn() },
  setOptions: vi.fn(),
  getValue: vi.fn(() => "SELECT 1;"),
  session: { setMode: vi.fn() },
};

global.ace = { edit: vi.fn(() => aceMockEditor) };

describe("PreviewBox.vue", () => {
  let wrapper;

  beforeEach(() => {
    vi.clearAllMocks();
    wrapper = mount(PreviewBox, {
      props: { editorText: "", databaseTechnology: "postgresql" },
    });
  });

  it("initializes the ace editor on mount", () => {
    expect(global.ace.edit).toHaveBeenCalled();
    expect(aceMockEditor.setReadOnly).toHaveBeenCalledWith(true);
  });

  it("updates the editor value when editorText changes", async () => {
    await wrapper.setProps({ editorText: "SELECT * FROM test;" });
    expect(aceMockEditor.setValue).toHaveBeenCalledWith("SELECT * FROM test;");
  });

});
