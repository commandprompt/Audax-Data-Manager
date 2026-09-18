import { flushPromises, mount } from "@vue/test-utils";
import SettingsModalShortcutsTab from "@src/components/SettingsModalShortcutsTab.vue";
import { useSettingsStore } from "@src/stores/settings";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

function shortcutsFixture() {
  return {
    shortcut_run_query: {
      shortcut_code: "shortcut_run_query",
      ctrl_pressed: true,
      shift_pressed: false,
      alt_pressed: false,
      meta_pressed: false,
      shortcut_key: "R",
    },
    shortcut_indent: {
      shortcut_code: "shortcut_indent",
      ctrl_pressed: false,
      shift_pressed: true,
      alt_pressed: false,
      meta_pressed: false,
      shortcut_key: "I",
    },
  };
}

describe("SettingsModalShortcutsTab.vue", () => {
  let wrapper, settingsStore;

  const overlay = () => wrapper.find("#div_shortcut_background_dark");

  const isRecording = () => overlay().element.style.visibility === "visible";

  const shortcutButton = (name) => wrapper.find(`#${name}`);

  const startRecording = async (name) => {
    await shortcutButton(name).trigger("click");
  };

  // The component listens for keys on the body while it records.
  const pressKey = async (init) => {
    document.body.dispatchEvent(
      new KeyboardEvent("keydown", { bubbles: true, ...init })
    );
    await flushPromises();
  };

  const pressEscape = () =>
    pressKey({ key: "Escape", code: "Escape", keyCode: 27 });

  beforeEach(() => {
    settingsStore = useSettingsStore();
    settingsStore.$reset();
    settingsStore.shortcuts = shortcutsFixture();
    wrapper = mount(SettingsModalShortcutsTab, { attachTo: document.body });
  });

  afterEach(async () => {
    // An open recording keeps a listener on the body.
    if (isRecording()) await pressEscape();
    wrapper.unmount();
    settingsStore.$reset();
  });

  describe("rendering", () => {
    it("shows a row for each shortcut with its label and combination", () => {
      expect(wrapper.findAll("label").map((label) => label.text())).toEqual([
        "Run Query",
        "Indent Code",
      ]);
      expect(shortcutButton("shortcut_run_query").text()).toBe("Ctrl+R");
      expect(shortcutButton("shortcut_indent").text()).toBe("Shift+I");
    });

    it("shows every modifier in the combination", async () => {
      settingsStore.shortcuts = {
        shortcut_explain: {
          shortcut_code: "shortcut_explain",
          ctrl_pressed: true,
          shift_pressed: true,
          alt_pressed: true,
          meta_pressed: true,
          shortcut_key: "E",
        },
      };
      await flushPromises();

      expect(shortcutButton("shortcut_explain").text()).toBe(
        "Ctrl+Shift+Alt+Meta+E"
      );
    });

    it("shows unknown when the shortcut code has no label", async () => {
      settingsStore.shortcuts = {
        shortcut_odd: {
          shortcut_code: "not_in_the_label_map",
          ctrl_pressed: false,
          shift_pressed: false,
          alt_pressed: false,
          meta_pressed: false,
          shortcut_key: "Q",
        },
      };
      await flushPromises();

      expect(wrapper.find("label").text()).toBe("unknown");
    });

    it("keeps the overlay hidden before the recording starts", () => {
      expect(isRecording()).toBe(false);
    });

    it("emits saveSettings when the user clicks Save", async () => {
      await wrapper.find(".btn-success").trigger("click");

      expect(wrapper.emitted("saveSettings")).toHaveLength(1);
    });
  });

  describe("recording a shortcut", () => {
    it("shows the overlay and pauses the shortcuts when the user starts", async () => {
      await startRecording("shortcut_run_query");

      expect(isRecording()).toBe(true);
      expect(settingsStore.isPausedShortcuts).toBe(true);
      expect(wrapper.emitted("recordingStatus:update")).toEqual([[true]]);
      expect(
        String(shortcutButton("shortcut_run_query").element.style["z-index"])
      ).toBe("1002");
    });

    it("saves the pressed combination and updates the button", async () => {
      await startRecording("shortcut_run_query");

      await pressKey({ key: "j", code: "KeyJ", ctrlKey: true, altKey: true });

      expect(settingsStore.shortcuts.shortcut_run_query).toMatchObject({
        ctrl_pressed: true,
        shift_pressed: false,
        alt_pressed: true,
        meta_pressed: false,
        shortcut_key: "J",
      });
      expect(shortcutButton("shortcut_run_query").text()).toBe("Ctrl+Alt+J");
    });

    it("saves SPACE when the user presses the space bar", async () => {
      await startRecording("shortcut_run_query");

      await pressKey({ key: " ", code: "Space", ctrlKey: true });

      expect(settingsStore.shortcuts.shortcut_run_query.shortcut_key).toBe(
        "SPACE"
      );
      expect(shortcutButton("shortcut_run_query").text()).toBe("Ctrl+SPACE");
    });

    it("hides the overlay and releases the shortcuts when it completes", async () => {
      await startRecording("shortcut_run_query");

      await pressKey({ key: "j", code: "KeyJ", ctrlKey: true });

      expect(isRecording()).toBe(false);
      expect(settingsStore.isPausedShortcuts).toBe(false);
      expect(wrapper.emitted("recordingStatus:update")).toEqual([
        [true],
        [false],
      ]);
      expect(
        String(shortcutButton("shortcut_run_query").element.style["z-index"])
      ).toBe("0");
    });

    it("ignores key presses after it completes", async () => {
      await startRecording("shortcut_run_query");
      await pressKey({ key: "j", code: "KeyJ", ctrlKey: true });

      await pressKey({ key: "k", code: "KeyK", ctrlKey: true });

      expect(settingsStore.shortcuts.shortcut_run_query.shortcut_key).toBe("J");
    });

    it.each([
      ["Shift", 16],
      ["Control", 17],
      ["Alt", 18],
      ["Meta", 91],
    ])("keeps recording when the user presses %s only", async (key, keyCode) => {
      await startRecording("shortcut_run_query");

      await pressKey({ key, code: `${key}Left`, keyCode });

      expect(isRecording()).toBe(true);
      expect(settingsStore.shortcuts.shortcut_run_query.shortcut_key).toBe("R");
    });
  });

  describe("cancelling", () => {
    it("keeps the shortcut and stops the recording on Escape", async () => {
      await startRecording("shortcut_run_query");

      await pressEscape();

      expect(isRecording()).toBe(false);
      expect(settingsStore.isPausedShortcuts).toBe(false);
      expect(settingsStore.shortcuts.shortcut_run_query).toMatchObject({
        ctrl_pressed: true,
        shortcut_key: "R",
      });
      expect(wrapper.emitted("recordingStatus:update")).toEqual([
        [true],
        [false],
      ]);
    });

    it("clears the conflict message on Escape", async () => {
      await startRecording("shortcut_run_query");
      await pressKey({ key: "I", code: "KeyI", shiftKey: true });
      expect(overlay().text()).toContain("already used");

      await pressEscape();
      await startRecording("shortcut_run_query");

      expect(overlay().text()).not.toContain("already used");
    });
  });

  describe("conflicts", () => {
    it("refuses a combination that another shortcut uses", async () => {
      await startRecording("shortcut_run_query");

      await pressKey({ key: "I", code: "KeyI", shiftKey: true });

      expect(overlay().text()).toContain("This combination is already used...");
      expect(isRecording()).toBe(true);
      expect(settingsStore.shortcuts.shortcut_run_query.shortcut_key).toBe("R");
    });

    it("accepts the same combination for the same shortcut", async () => {
      await startRecording("shortcut_run_query");

      await pressKey({ key: "r", code: "KeyR", ctrlKey: true });

      expect(isRecording()).toBe(false);
      expect(settingsStore.shortcuts.shortcut_run_query).toMatchObject({
        ctrl_pressed: true,
        shortcut_key: "R",
      });
    });

    it.each([
      ["Tab", { key: "Tab", code: "Tab" }],
      ["Backspace", { key: "Backspace", code: "Backspace" }],
      ["an arrow key", { key: "ArrowUp", code: "ArrowUp" }],
      ["Ctrl+C", { key: "c", code: "KeyC", ctrlKey: true }],
      ["Ctrl+V", { key: "v", code: "KeyV", ctrlKey: true }],
      ["Ctrl+Z", { key: "z", code: "KeyZ", ctrlKey: true }],
    ])("refuses %s", async (_name, init) => {
      await startRecording("shortcut_run_query");

      await pressKey(init);

      expect(overlay().text()).toContain(
        "This combination cannot be used for shortcuts"
      );
      expect(isRecording()).toBe(true);
      expect(settingsStore.shortcuts.shortcut_run_query.shortcut_key).toBe("R");
    });
  });
});
