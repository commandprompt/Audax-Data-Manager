import { defineStore } from "pinia";
import axios from "axios";
import { showToast } from "../notification_control.js";
import moment from "moment";
import { Modal, Tab } from "bootstrap";
import { handleError } from "../logging/utils.js";

const useSettingsStore = defineStore("settings", {
  state: () => ({
    desktopMode: window.gv_desktopMode,
    fontSize: "",
    theme: "",
    editorTheme: "",
    terminalTheme: "",
    restoreTabs: "",
    scrollTree: "",
    binaryPaths: {},
    pigzPath: "",
    csvEncoding: "",
    csvDelimiter: "",
    dateFormat: "",
    shortcuts: {},
    currentOS: "Unknown OS",
    max_upload_size: "",
    isPausedShortcuts: false,
  }),
  actions: {
    async getSettings() {
      try {
        const response = await axios.get("/settings/");

        const userSettings = response.data.settings;
        this.$patch({
          fontSize: userSettings.font_size,
          theme: userSettings.theme,
          editorTheme: userSettings.editor_theme,
          restoreTabs: userSettings.restore_tabs,
          scrollTree: userSettings.scroll_tree,
          binaryPaths: userSettings.binary_paths,
          pigzPath: userSettings.pigz_path,
          csvEncoding: userSettings.csv_encoding,
          csvDelimiter: userSettings.csv_delimiter,
          dateFormat: !userSettings.date_format
            ? "YYYY-MM-DD, HH:mm:ss"
            : userSettings.date_format,
          max_upload_size: userSettings.max_upload_size,
        });

        this.shortcuts = Object.assign(
          {},
          this.shortcuts,
          response.data.shortcuts
        );
        moment.defaultFormat = this.dateFormat;
        document.documentElement.style.fontSize = `${this.fontSize}px`;

        return response.data;
      } catch (error) {
        handleError(error);
        return error;
      }
    },
    async saveSettings(silent = false) {
      try {
        const response = await axios.post("/settings/", {
          shortcuts: Object.values(this.shortcuts),
          current_os: this.currentOS,
          settings: {
            font_size: this.fontSize,
            theme: this.theme,
            csv_encoding: this.csvEncoding,
            csv_delimiter: this.csvDelimiter,
            binary_paths: this.binaryPaths,
            date_format: this.dateFormat,
            pigz_path: this.pigzPath,
            restore_tabs: this.restoreTabs,
            scroll_tree: this.scrollTree,
          },
        });

        moment.defaultFormat = this.dateFormat;
        if(!silent)
          showToast("success", "Configuration saved.");
        return response.data;
      } catch (error) {
        handleError(error);
        return error;
      }
    },
    setFontSize(fontSize) {
      this.fontSize = fontSize;
    },
    setTheme(theme) {
      this.theme = theme;
    },
    setEditorTheme(theme) {
      this.editorTheme = theme;
    },
    setTerminalTheme(theme) {
      this.terminalTheme = theme;
    },
    setShortcuts(shortcuts) {
      this.shortcuts = shortcuts;
    },
    setCSVEncoding(encoding) {
      this.csvEncoding = encoding;
    },
    setCSVDelimiter(delimiter) {
      this.csvDelimiter = delimiter;
    },
    setPigzPath(path) {
      this.pigzPath = path;
    },
    setDateFormat(format) {
      this.dateFormat = format;
    },
    setRestoreTabs(value) {
      this.restoreTabs = value;
    },
    setScrollTree(value) {
      this.scrollTree = value;
    },
    showModal() {
      Modal.getOrCreateInstance("#modal_settings", {
        backdrop: "static",
      }).show();
      const tab = new Tab(document.querySelector('#settings_shortcuts-tab'));
      tab.show();
    },
    setBinaryPathForVersion(versionKey, path) {
      if (!this.binaryPaths) this.binaryPaths = {};
      this.binaryPaths[versionKey] = path ? path.trim() : null;
    },
    setBinaryPaths(value) {
      this.binaryPaths = value;
    },
  },
});

export { useSettingsStore };
