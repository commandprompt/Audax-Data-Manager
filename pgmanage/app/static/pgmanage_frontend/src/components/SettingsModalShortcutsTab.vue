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
      <label :for="idx" class="col-sm-6 col-form-label">{{
        shortcutLabel(shortcut)
      }}</label>
      <div class="form-group col-6">
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

    <div class="text-end">
      <button class="btn btn-success" @click="$emit('saveSettings')">
        Save
      </button>
    </div>
  </div>
</template>

<script>
import { default_shortcuts } from "@src/shortcuts";
import { emitter } from "@src/emitter";
import { settingsStore, tabsStore } from "@src/stores/stores_initializer";

export default {
  name: "SettingsModalShortcutsTab",
  emits: ["recordingStatus:update", "saveSettings"],
  data() {
    return {
      shortcutObject: {
        button: null,
        actions: null,
      },
      conflictText: "",
      hasConflicts: false,
    };
  },
  computed: {
    shortcuts() {
      return settingsStore.shortcuts;
    },
  },
  mounted() {
    if (navigator.userAgent.indexOf("Win") != -1) settingsStore.currentOS = "windows";
    if (navigator.userAgent.indexOf("Mac") != -1) settingsStore.currentOS = "macos";
    if (navigator.userAgent.indexOf("X11") != -1) settingsStore.currentOS = "linux";
    if (navigator.userAgent.indexOf("Linux") != -1) settingsStore.currentOS = "linux";

    document.body.addEventListener("keydown", this.keyBoardShortcuts);

    // Shortcut actions
    this.shortcutObject.actions = {
      shortcut_run_query: function () {

        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode === 'query') {
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_run_query`)
          }
          else if (tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode === 'console')
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_run_console`, false)
          else if (tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode == 'edit')
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_query_edit`)
        }
      },
      shortcut_run_selection: function () {
        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode === 'query') {
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_run_selection`)
          }
        }
      },
      shortcut_explain: function () {

        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode === 'query') {
            if(tabsStore?.selectedPrimaryTab?.metaData?.selectedTab?.metaData?.dialect !== 'postgresql') return
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_run_explain`)
          }
        }
      },
      shortcut_explain_analyze: function () {

        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode === 'query') {
            if(tabsStore?.selectedPrimaryTab?.metaData?.selectedTab?.metaData?.dialect !== 'postgresql') return
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_run_explain_analyze`)
          }
        }
      },
      shortcut_cancel_query: function () {

        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (['query', 'console'].includes(tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode)) {
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_cancel_query`)
          }
        }
      },
      shortcut_indent: function () {

        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (['query', 'console'].includes(tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode)) {
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_indent_sql`)
          }
        }
      },
      shortcut_find_replace: function () {
        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (['query', 'console'].includes(tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode)) {
            emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_find_replace`)
          }
        }
      },
      shortcut_new_inner_tab: function () {
        if (['snippets', 'connection'].includes(tabsStore.selectedPrimaryTab.metaData.mode)) {
          let name = tabsStore.selectedPrimaryTab.metaData.selectedDatabase.replace('\\', '/').split('/').pop()
          tabsStore.createQueryTab(name)
        }
      },
      shortcut_remove_inner_tab: function () {
        if (tabsStore.selectedPrimaryTab.metaData.mode === "connection") {
          let tab = tabsStore.selectedPrimaryTab.metaData.selectedTab;
          if (tab) {
            if (tab.closeFunction && tab.closeFunction !== null) {
              tab.closeFunction(null, tab);
            } else {
              tabsStore.removeTab(tab);
            }
          }
        }
      },
      shortcut_left_inner_tab: function () {

        if (['snippets', 'connection'].includes(tabsStore.selectedPrimaryTab.metaData.mode)) {
          let secondaryTabs = tabsStore.selectedPrimaryTab.metaData.secondaryTabs;
          let selectedTab = tabsStore.selectedPrimaryTab.metaData.selectedTab
          let actualIndex = secondaryTabs.indexOf(selectedTab);

          if (actualIndex === -1) return;

          if (actualIndex === 0) {
            tabsStore.selectTab(secondaryTabs[secondaryTabs.length - 1]);
          } else {
            tabsStore.selectTab(secondaryTabs[actualIndex - 1]);
          }
        }
      },
      shortcut_right_inner_tab: function () {

        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          let secondaryTabs = tabsStore.selectedPrimaryTab.metaData.secondaryTabs;
          let selectedTab = tabsStore.selectedPrimaryTab.metaData.selectedTab
          let actualIndex = secondaryTabs.indexOf(selectedTab);

          if (actualIndex === -1) return;

          if (actualIndex === secondaryTabs.length - 1) {
            tabsStore.selectTab(secondaryTabs[0]);
          } else {
            tabsStore.selectTab(secondaryTabs[actualIndex + 1]);
          }
        }
      },
      shortcut_autocomplete: function (e) {
        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          if (['query', 'console'].includes(tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode)) {
              emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_show_autocomplete_results`, e)
            }
        }
      },
      shortcut_quick_search: function(e) {
        if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
          emitter.emit(`${tabsStore.selectedPrimaryTab.id}_show_quick_search`, e)
        }
      },
    };
    // Go over default shortcuts
    for (let default_code in default_shortcuts) {
      if (default_shortcuts.hasOwnProperty(default_code)) {
        // Find corresponding user defined
        let found = false;

        for (let user_code in this.shortcuts) {
          if (this.shortcuts.hasOwnProperty(user_code)) {
            if ((default_code == user_code) && (settingsStore.currentOS == this.shortcuts[user_code]['os'])) {
              found = true;
              break;
            }
          }
        }
        if (!found) {
          settingsStore.shortcuts[default_code] = default_shortcuts[default_code][settingsStore.currentOS]
          settingsStore.shortcuts[default_code]['shortcut_code'] = default_code
        }
      }
    }
  },
  methods: {
    startSetShortcut(event) {
      this.$emit("recordingStatus:update", true);
      this.$refs.shortcutBackground.style.visibility = "visible";
      event.target.style["z-index"] = 1002;
      this.shortcutObject.button = event.target;

      document.body.removeEventListener("keydown", this.keyBoardShortcuts);

      document.body.removeEventListener("keydown", this.setShortcutEvent);
      document.body.addEventListener("keydown", this.setShortcutEvent);
    },
    keyBoardShortcuts(event) {
      //16 - Shift
      //17 - Ctrl
      //18 - Alt
      //91 - Meta (Windows and Mac)
      //27 - Esc

      if (event.keyCode == 16 || event.keyCode == 17 || event.keyCode == 18 || event.keyCode == 91 || event.keyCode == 27)
        return;

      for (let property in this.shortcuts) {
        if (this.shortcuts.hasOwnProperty(property)) {
          let element = this.shortcuts[property];
          if (this.checkShortcutPressed(event, element)) {
            event.preventDefault();
            event.stopPropagation();
            let action = this.shortcutObject.actions[property];
            if (action) action(event);
          }
        }
      }
    },
    checkShortcutPressed(event, shortcut_element) {
      if ((event.ctrlKey && shortcut_element.ctrl_pressed == 0) || (!event.ctrlKey && shortcut_element.ctrl_pressed == 1))
        return false;
      if ((event.shiftKey && shortcut_element.shift_pressed == 0) || (!event.shiftKey && shortcut_element.shift_pressed == 1))
        return false;
      if ((event.altKey && shortcut_element.alt_pressed == 0) || (!event.altKey && shortcut_element.alt_pressed == 1))
        return false;
      if ((event.metaKey && shortcut_element.meta_pressed == 0) || (!event.metaKey && shortcut_element.meta_pressed == 1))
        return false;
      if (event.key.toUpperCase() == shortcut_element.shortcut_key || event.code.toUpperCase() == shortcut_element.shortcut_key)
        return true;

      return false;
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
      for (const [name, shortcut] of Object.entries(settingsStore.shortcuts)) {
        if (name == this.shortcutObject.button.id) continue;

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

      let shortcutElement = settingsStore.shortcuts[this.shortcutObject.button.id];

      if (shortcutElement) {
        shortcutElement.ctrl_pressed = event.ctrlKey;
        shortcutElement.shift_pressed = event.shiftKey;
        shortcutElement.alt_pressed = event.altKey;
        shortcutElement.meta_pressed = event.metaKey;

        if (event.code.toUpperCase() != 'SPACE')
          shortcutElement.shortcut_key = event.key.toUpperCase();
        else
          shortcutElement.shortcut_key = 'SPACE';
        this.buildButtonText(shortcutElement, this.shortcutObject.button);
      }

      this.finishSetShortcut();
    },
    finishSetShortcut() {
      this.shortcutObject.button.style["z-index"] = 0;
      this.shortcutObject.button = null;
      this.$refs.shortcutBackground.style.visibility = "hidden";
      this.hasConflicts = false;
      this.$emit("recordingStatus:update", false);
      document.body.removeEventListener("keydown", this.setShortcutEvent);
      document.body.addEventListener("keydown", this.keyBoardShortcuts);
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
      };
      return LABEL_MAP[shortcut.shortcut_code] || "unknown";
    },
  },
};
</script>
