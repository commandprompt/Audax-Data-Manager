<template>
  <div
    class="tab-pane fade show active"
    id="settings_shortcuts"
    role="tabpanel"
    aria-labelledby="settings_shortcuts-tab"
  >
    <div
      id="div_shortcut_background_dark"
      style="display: block; visibility: hidden"
      ref="shortcutBackground"
    >

      <div style="position: absolute; top: 40%; width: 100%">
        Press key combination... (ESC to cancel)
      </div>
      <div
        v-if="hasConflicts"
        style="position: absolute; top: 50%; width: 100%"
      >
        {{ conflictText }}
      </div>
    </div>

    <div v-for="(shortcut, idx) in shortcuts" :key="idx" class="row">
      <label :for="idx" class="col-sm-7 col-form-label">{{
        shortcutLabel(shortcut)
      }}</label>
      <div class="form-group col-5 mb-2">
        <div class="d-grid">
          <button
            :id="idx"
            class="btn btn-secondary btn-sm"
            @click="startSetShortcut"
          >
            {{ buildButtonText(shortcut) }}
          </button>
        </div>
      </div>
    </div>

    <div class="text-end mt-1">
      <button class="btn btn-success" @click="$emit('saveSettings')">
        Save
      </button>
    </div>
  </div>
</template>

<script>
import { settingsStore } from "@src/stores/stores_initializer";

export default {
  name: "SettingsModalShortcutsTab",
  emits: ["recordingStatus:update", "saveSettings"],
  data() {
    return {
      shortcutButton: null,
      conflictText: "",
      hasConflicts: false,
    };
  },
  computed: {
    shortcuts() {
      return settingsStore.shortcuts;
    },
  },
  methods: {
    startSetShortcut(event) {
      settingsStore.isPausedShortcuts = true;
      this.$emit("recordingStatus:update", true);
      this.$refs.shortcutBackground.style.visibility = "visible";
      event.target.style["z-index"] = 1002;
      this.shortcutButton = event.target;

      document.body.removeEventListener("keydown", this.setShortcutEvent);
      document.body.addEventListener("keydown", this.setShortcutEvent);
    },
    setShortcutEvent(event) {
      event.preventDefault();
      event.stopPropagation();

      if (event.keyCode == 27) {
        this.finishSetShortcut();
        return;
      }

      //16 - Shift
      //17 - Ctrl
      //18 - Alt
      //91 - Meta (Windows and Mac)
      if (event.keyCode == 16 || event.keyCode == 17 || event.keyCode == 18 || event.keyCode == 91)
        return;

      // Prevent disallowed hotkeys
      if (this.isDisallowedHotkey(event)) {
        this.hasConflicts = true;
        this.conflictText = "This combination cannot be used for shortcuts";
        return;
      }

      // check for potential hotkey conflicts
      for (const [name, shortcut] of Object.entries(this.shortcuts)) {
        if (name == this.shortcutButton.id) continue;

        let keyPressed = event.key === " " ? "SPACE" : event.key.toUpperCase();

        if (
          shortcut.ctrl_pressed === event.ctrlKey &&
          shortcut.shift_pressed === event.shiftKey &&
          shortcut.alt_pressed === event.altKey &&
          shortcut.meta_pressed === event.metaKey &&
          shortcut.shortcut_key === keyPressed
        ) {
          this.hasConflicts = true;
          this.conflictText = "This combination is already used...";
          return;
        }
      }

      let shortcutElement = this.shortcuts[this.shortcutButton.id];

      if (shortcutElement) {
        shortcutElement.ctrl_pressed = event.ctrlKey;
        shortcutElement.shift_pressed = event.shiftKey;
        shortcutElement.alt_pressed = event.altKey;
        shortcutElement.meta_pressed = event.metaKey;

        if (event.code.toUpperCase() != 'SPACE')
          shortcutElement.shortcut_key = event.key.toUpperCase();
        else
          shortcutElement.shortcut_key = 'SPACE';
        this.buildButtonText(shortcutElement, this.shortcutButton);
      }

      this.finishSetShortcut();
    },
    finishSetShortcut() {
      this.shortcutButton.style["z-index"] = 0;
      this.shortcutButton = null;
      this.$refs.shortcutBackground.style.visibility = "hidden";
      this.hasConflicts = false;
      this.$emit("recordingStatus:update", false);
      document.body.removeEventListener("keydown", this.setShortcutEvent);
      settingsStore.isPausedShortcuts = false;
    },
    isDisallowedHotkey(event) {
      const key = event.key;
      const code = event.code;

      const blockedCodes = new Set([
        "Tab",
        "CapsLock",
        "ContextMenu",
        "Backspace",
        "Home",
        "End",
        "PageUp",
        "PageDown",
        "ArrowUp",
        "ArrowDown",
        "ArrowLeft",
        "ArrowRight",
      ]);

      if (blockedCodes.has(code)) {
        return true;
      }

      if (event.shiftKey && code.startsWith("Arrow")) {
        return true;
      }

      if (event.ctrlKey) {
        const ctrlBlocked = new Set(["c", "v", "z"]);
        if (ctrlBlocked.has(key)) return true;
      }

      return false;
    },
    buildButtonText(shortcut_object, button = null) {
      let text = "";
      if (shortcut_object.ctrl_pressed) text += "Ctrl+";
      if (shortcut_object.shift_pressed) text += "Shift+";
      if (shortcut_object.alt_pressed) text += "Alt+";
      if (shortcut_object.meta_pressed) text += "Meta+";
      if (!!button) button.innerHTML = text + shortcut_object.shortcut_key;
      else return text + shortcut_object.shortcut_key;
    },
    shortcutLabel(shortcut) {
      const LABEL_MAP = {
        shortcut_run_query: "Run Query",
        shortcut_run_selection: "Run Selection",
        shortcut_cancel_query: "Cancel Query",
        shortcut_indent: "Indent Code",
        shortcut_find_replace: "Find/Replace",
        shortcut_new_inner_tab: "New Tab",
        shortcut_remove_inner_tab: "Close Tab",
        shortcut_left_inner_tab: "Switch Tab Left",
        shortcut_right_inner_tab: "Switch Tab Right",
        shortcut_autocomplete: "Autocomplete",
        shortcut_explain: "Explain Query",
        shortcut_explain_analyze: "Analyze Query",
        shortcut_quick_search: "Quick Search",
        shortcut_focus_database_tree: "Focus Database Explorer",
        shortcut_focus_selected_tab: "Focus Work Area Primary",
        shortcut_focus_data_grid: "Focus Work Area Secondary",
      };
      return LABEL_MAP[shortcut.shortcut_code] || "unknown";
    },
  },
};
</script>
