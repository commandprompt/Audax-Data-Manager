import { flushPromises, mount } from "@vue/test-utils";
import QueryEditorSearchButton from "@src/components/QueryEditorSearchButton.vue";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// A minimal Ace editor that keeps the handlers the component registers.
function createEditor() {
  const container = document.createElement("div");
  document.body.appendChild(container);

  const editor = {
    container,
    value: "",
    searchBox: null,
    handlers: {},
    commandHandlers: {},
    getValue: () => editor.value,
    execCommand: vi.fn(),
    on: vi.fn((name, handler) => {
      editor.handlers[name] = handler;
    }),
    commands: {
      on: vi.fn((name, handler) => {
        editor.commandHandlers[name] = handler;
      }),
    },
  };
  return editor;
}

describe("QueryEditorSearchButton.vue", () => {
  let wrapper, editor;

  const isHidden = () => wrapper.classes().includes("d-none");

  const initializeEditor = () => wrapper.setProps({ editorInitialized: true });

  const setEditorText = async (text) => {
    editor.value = text;
    editor.handlers.change({}, editor);
    await flushPromises();
  };

  const runCommand = (name) =>
    editor.commandHandlers.afterExec({ command: { name } }, editor);

  const openSearchBox = () => editor.handlers.findSearchBox({}, editor);

  const attachSearchBox = ({ withCloseButton = true } = {}) => {
    const element = document.createElement("div");
    if (withCloseButton) {
      element.innerHTML = '<span class="ace_searchbtn_close"></span>';
    }
    editor.searchBox = { element, active: false };
    return element;
  };

  const mouseOver = () =>
    editor.container.dispatchEvent(new MouseEvent("mouseover"));

  const mouseOut = (relatedTarget) =>
    editor.container.dispatchEvent(new MouseEvent("mouseout", { relatedTarget }));

  beforeEach(() => {
    editor = createEditor();
    wrapper = mount(QueryEditorSearchButton, {
      props: { editor, editorInitialized: false },
      attachTo: document.body,
    });
  });

  afterEach(() => {
    wrapper.unmount();
    editor.container.remove();
  });

  describe("before the editor is ready", () => {
    it("hides the button", () => {
      expect(isHidden()).toBe(true);
    });

    it("listens to nothing and leaves the button where it is", () => {
      expect(editor.on).not.toHaveBeenCalled();
      expect(editor.commands.on).not.toHaveBeenCalled();
      expect(wrapper.element.parentElement).not.toBe(editor.container);
    });
  });

  describe("when the editor becomes ready", () => {
    it("listens to the editor and moves the button into it", async () => {
      await initializeEditor();

      expect(editor.commands.on).toHaveBeenCalledWith(
        "afterExec",
        expect.any(Function)
      );
      expect(editor.on).toHaveBeenCalledWith(
        "findSearchBox",
        expect.any(Function)
      );
      expect(editor.on).toHaveBeenCalledWith("change", expect.any(Function));
      expect(wrapper.element.parentElement).toBe(editor.container);
    });
  });

  describe("editor content", () => {
    beforeEach(() => initializeEditor());

    it("shows the button when the editor has text", async () => {
      await setEditorText("SELECT 1");

      expect(isHidden()).toBe(false);
    });

    it("hides the button when the editor has only spaces", async () => {
      await setEditorText("SELECT 1");

      await setEditorText("   ");

      expect(isHidden()).toBe(true);
    });

    it("hides the button when the user removes all the text", async () => {
      await setEditorText("SELECT 1");

      await setEditorText("");

      expect(isHidden()).toBe(true);
    });
  });

  describe("search bar commands", () => {
    beforeEach(async () => {
      await initializeEditor();
      await setEditorText("SELECT 1");
    });

    it("hides the button when the find command runs", () => {
      runCommand("find");

      expect(isHidden()).toBe(true);
    });

    it("shows the button when the search bar closes", () => {
      runCommand("find");

      runCommand("closeSearchBar");

      expect(isHidden()).toBe(false);
    });

    it("keeps the button as it is for other commands", () => {
      runCommand("insertstring");

      expect(isHidden()).toBe(false);
    });
  });

  describe("the close button of the search box", () => {
    beforeEach(async () => {
      await initializeEditor();
      await setEditorText("SELECT 1");
    });

    it("shows the button when the user closes the search box", () => {
      const searchBoxElement = attachSearchBox();
      openSearchBox();
      runCommand("find");
      expect(isHidden()).toBe(true);

      searchBoxElement.querySelector("span.ace_searchbtn_close").onclick();

      expect(isHidden()).toBe(false);
    });

    it("sets the close handler only one time", () => {
      attachSearchBox();
      openSearchBox();

      const secondBox = attachSearchBox();
      openSearchBox();

      expect(secondBox.querySelector("span.ace_searchbtn_close").onclick).toBe(
        null
      );
    });

    it("does nothing when there is no search box", () => {
      expect(() => openSearchBox()).not.toThrow();
    });

    it("waits for a search box that has a close button", () => {
      attachSearchBox({ withCloseButton: false });
      openSearchBox();

      const laterBox = attachSearchBox();
      openSearchBox();

      expect(
        laterBox.querySelector("span.ace_searchbtn_close").onclick
      ).toBeInstanceOf(Function);
    });
  });

  describe("the pointer over the editor", () => {
    beforeEach(async () => {
      await initializeEditor();
      await setEditorText("SELECT 1");
    });

    it("shows the button when the pointer goes over the editor", () => {
      runCommand("find");

      mouseOver();

      expect(isHidden()).toBe(false);
    });

    it("keeps the button hidden when the editor is empty", async () => {
      await setEditorText("");

      mouseOver();

      expect(isHidden()).toBe(true);
    });

    it("keeps the button hidden when the search box is active", () => {
      attachSearchBox();
      editor.searchBox.active = true;
      runCommand("find");

      mouseOver();

      expect(isHidden()).toBe(true);
    });

    it("hides the button when the pointer leaves the editor", () => {
      const outside = document.createElement("div");
      document.body.appendChild(outside);

      mouseOut(outside);

      expect(isHidden()).toBe(true);
      outside.remove();
    });

    it("keeps the button when the pointer moves inside the editor", () => {
      const inside = document.createElement("div");
      editor.container.appendChild(inside);

      mouseOut(inside);

      expect(isHidden()).toBe(false);
    });

    it("keeps the button when the pointer moves to the editor content", () => {
      const content = document.createElement("div");
      content.classList.add("ace_content");
      document.body.appendChild(content);

      mouseOut(content);

      expect(isHidden()).toBe(false);
      content.remove();
    });
  });

  describe("clicking the button", () => {
    it("hides the button and starts the search", async () => {
      await initializeEditor();
      await setEditorText("SELECT 1");

      await wrapper.trigger("click");

      expect(editor.execCommand).toHaveBeenCalledWith("find");
      expect(isHidden()).toBe(true);
    });
  });
});
