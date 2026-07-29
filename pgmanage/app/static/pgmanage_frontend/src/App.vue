<template>
  <SettingsModal />
  <SideBarTabs />
  <PasswordModal />
  <MasterPasswordModal @check-completed="initialSetup" />
  <UtilityJobsJobDetail />
  <template v-if="initialized">
    <ConnectionsModal />
  </template>
  <GenericMessageModal />
  <CellDataModal />
  <FileManager />
  <UtilitiesMenu />
  <AboutModal />
  <CommandsHistoryModal />
  <template v-for="extraComp in enterpriseComps">
    <component :is="extraComp"> </component>
  </template>
</template>

<script>
import SettingsModal from "./components/SettingsModal.vue";
import SideBarTabs from "./components/SideBarTabs.vue";
import PasswordModal from "./components/PasswordModal.vue";
import MasterPasswordModal from "./components/MasterPasswordModal.vue";
import UtilityJobsJobDetail from "./components/UtilityJobsJobDetail.vue";
import ConnectionsModal from "./components/ConnectionsModal.vue";
import GenericMessageModal from "./components/GenericMessageModal.vue";
import CellDataModal from "./components/CellDataModal.vue";
import FileManager from "./components/FileManager.vue";
import UtilitiesMenu from "./components/UtilitiesMenu.vue";
import AboutModal from "./components/AboutModal.vue";
import CommandsHistoryModal from "./components/CommandsHistoryModal.vue";
import { emitter } from "./emitter";
import { startTutorial } from "./tutorial";
import { createOmnis } from "./omnis-control";
import { dbMetadataStore, settingsStore, tabsStore } from "./stores/stores_initializer";
import { default_shortcuts } from "@src/shortcuts";

export default {
  name: "PgManage",
  components: {
    SettingsModal,
    SideBarTabs,
    PasswordModal,
    MasterPasswordModal,
    UtilityJobsJobDetail,
    ConnectionsModal,
    GenericMessageModal,
    CellDataModal,
    FileManager,
    UtilitiesMenu,
    AboutModal,
    CommandsHistoryModal,
  },
  data() {
    return {
      initialized: false,
      enterpriseComps: [],
    };
  },
  computed: {
    shortcuts() {
      return settingsStore.shortcuts;
    },
  },
  mounted() {
    this.createOmnisAssistant();
    // Ask for master password
    if (master_key === "new") {
      emitter.emit("show_master_pass_prompt", true);
    } else if (master_key == "False") {
      emitter.emit("show_master_pass_prompt", false);
    } else {
      this.initialSetup();
    }

    emitter.on(
      "dbMetaRefresh",
      ({ workspace_id, database_name, database_index }) => {
        dbMetadataStore.refreshDBMeta(
          database_index,
          workspace_id,
          database_name
        );
      }
    );

    this.detectCurrentOS();
    this.createShortcutActions();
    this.ensureDefaultShortcuts();

    document.body.addEventListener("keydown", this.keyBoardShortcuts);
  },
  methods: {
    initialSetup() {
      this.initialized = true;
      v_omnis.div.style.opacity = 1;

      this.enterpriseComps = this?.enterpriseComponents ?? [];
    },
    createOmnisAssistant() {
      v_omnis = createOmnis();
      v_omnis.root = document.getElementById("app");
      v_omnis.div = document.createElement("div");
      v_omnis.div.setAttribute("id", "omnis");
      v_omnis.div.classList.add("omnis");
      v_omnis.div.style.top =
        v_omnis.root.getBoundingClientRect().height - 45 + "px";
      v_omnis.div.style.left =
        v_omnis.root.getBoundingClientRect().width - 60 + "px";
      v_omnis.div.style["z-index"] = "99999999";
      v_omnis.div.style.opacity = 0;
      v_omnis.div.innerHTML = v_omnis.template;
      document.body.appendChild(v_omnis.div);
      v_omnis.div.addEventListener("click", function () {
        startTutorial("getting_started");
      });
    },
    keyBoardShortcuts(event) {
      if (settingsStore.isPausedShortcuts) return;
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
            let action = this.shortcutActions[property];
            if (action) action(event);
          }
        }
      }
    },
    checkShortcutPressed(event, shortcutElement) {
      if ((event.ctrlKey && shortcutElement.ctrl_pressed == 0) || (!event.ctrlKey && shortcutElement.ctrl_pressed == 1))
        return false;
      if ((event.shiftKey && shortcutElement.shift_pressed == 0) || (!event.shiftKey && shortcutElement.shift_pressed == 1))
        return false;
      if ((event.altKey && shortcutElement.alt_pressed == 0) || (!event.altKey && shortcutElement.alt_pressed == 1))
        return false;
      if ((event.metaKey && shortcutElement.meta_pressed == 0) || (!event.metaKey && shortcutElement.meta_pressed == 1))
        return false;
      if (event.key.toUpperCase() == shortcutElement.shortcut_key || event.code.toUpperCase() == shortcutElement.shortcut_key)
        return true;

      return false;
    },
    ensureDefaultShortcuts() {
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
    createShortcutActions() {
      this.shortcutActions = {
        shortcut_run_query: function () {

          if (tabsStore.selectedPrimaryTab.metaData.mode === 'connection') {
            if (tabsStore.selectedPrimaryTab.metaData.selectedTab.metaData.mode === 'query') {
              emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_run_query`)
            }
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
        shortcut_focus_database_tree: function(e) {
          const tab = tabsStore.selectedPrimaryTab;
          emitter.emit(`focusTree_${tab.id}`);
        },
        shortcut_focus_selected_tab: function(e) {
          if (tabsStore.selectedPrimaryTab.metaData.mode !== 'connection') return;

          const tab = tabsStore.selectedPrimaryTab.metaData.selectedTab;
          if (!tab) return;

          emitter.emit(`${tab.id}_focus`);
        },
        shortcut_focus_data_grid: function(e) {
          if (tabsStore.selectedPrimaryTab.metaData.mode !== 'connection') return;

          const tab = tabsStore.selectedPrimaryTab.metaData.selectedTab;
          if (!tab || tab.metaData.mode !== 'query') return;

          emitter.emit(`${tab.id}_focus_secondary`);
        },
      };
    },
    detectCurrentOS() {
      if (navigator.userAgent.indexOf("Win") != -1) settingsStore.currentOS = "windows";
      if (navigator.userAgent.indexOf("Mac") != -1) settingsStore.currentOS = "macos";
      if (navigator.userAgent.indexOf("X11") != -1) settingsStore.currentOS = "linux";
      if (navigator.userAgent.indexOf("Linux") != -1) settingsStore.currentOS = "linux";
    },
  },
};
</script>
