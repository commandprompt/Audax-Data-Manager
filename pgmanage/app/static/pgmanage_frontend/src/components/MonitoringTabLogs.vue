<template>
  <div
    v-if="loggingDisabled"
    class="alert alert-warning d-flex align-items-center justify-content-center m-4"
    role="alert"
  >
    <i class="fas fa-exclamation-triangle me-2"></i>
    <div>
      <span>Please enable logging to view the server logs.</span>
      <br />
      <span
        >More information:
        <a
          target="_blank"
          :href="`https://www.postgresql.org/docs/${serverVersion}/runtime-config-logging.html`"
        >
          Error Reporting and Logging
        </a></span
      >
    </div>
  </div>

  <div v-show="!loggingDisabled">
    <div
      ref="topToolbar"
      class="d-flex flex-row align-items-center justify-content-end p-1"
    >
      <div class="col">
        <p><span class="fw-bold">Current log:</span> {{ currentLogFile }}</p>
      </div>
      <button
        class="btn btn-ghost btn-ghost-secondary btn-w-fixed me-2"
        title="Find"
        @click="showFind()"
      >
        <i class="fas fa-magnifying-glass fa-light"></i>
      </button>
      <div>
        <div class="form-check form-switch pt-1">
          <input
            :id="`${tabId}-logs-autoscroll`"
            class="form-check-input"
            type="checkbox"
            v-model="autoScroll"
          />
          <label class="form-check-label" :for="`${tabId}-logs-autoscroll`">
            Autoscroll
          </label>
        </div>
      </div>
      <div class="col-2">
        <div class="align-items-center d-flex">
          <label class="mx-2">Format:</label>
          <select class="form-select" v-model="formatMode">
            <template v-for="(modeObj, modeName, index) in formatModes">
              <option v-if="modeObj.available" :value="modeName" :key="index">
                {{ modeObj.text }}
              </option>
            </template>
          </select>
        </div>
      </div>
    </div>
    <div class="card border-0">
      <Transition :duration="100">
        <div v-if="showLoading" class="div_loading d-block" style="z-index: 10">
          <div class="div_loading_cover"></div>
          <div class="div_loading_content">
            <div class="spinner-border spinner-size text-primary" role="status">
              <span class="sr-only">Loading...</span>
            </div>
          </div>
        </div>
      </Transition>
      <div ref="editor" class="ace-editor"></div>
    </div>
  </div>
</template>

<script>
import { settingsStore, tabsStore } from "../stores/stores_initializer";
import { handleError } from "../logging/utils";

import axios from "axios";
export default {
  name: "MonitoringTabLogs",
  props: {
    databaseIndex: Number,
    workspaceId: String,
    tabId: String,
  },
  data() {
    return {
      editor: null,
      formatModes: {},
      formatMode: "stderr",
      heightSubtract: 150,
      showLoading: true,
      loggingDisabled: false,
      autoScroll: true,
      currentLogFile: "",
      serverVersion: null,
      logOffset: null,
      intervalObject: null,
    };
  },
  computed: {
    editorHeight() {
      return `calc(100vh - ${this.heightSubtract}px)`;
    },
  },
  watch: {
    formatMode(newValue) {
      const aceMode =
        this.formatModes[newValue]?.ace_mode ?? "ace/mode/pgsql_extended";
      this.editor.session.setMode(aceMode);
      clearInterval(this.intervalObject);
      this.logOffset = null;
      this.intervalObject = null;
      this.currentLogFile = "";
      this.getLog();
    },
  },
  mounted() {
    this.setupEditor();
    this.getLogFormat();
    this.getServerVersion();

    window.addEventListener("resize", () => {
      if (
        tabsStore.selectedPrimaryTab?.metaData?.selectedTab?.id !== this.tabId
      )
        return;
      this.handleResize();
    });

    settingsStore.$onAction((action) => {
      if (action.name === "setFontSize") {
        if (
          tabsStore.selectedPrimaryTab?.metaData?.selectedTab?.id !== this.tabId
        )
          return;
        action.after(() => {
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              this.handleResize();
            });
          });
        });
      }
    });

    settingsStore.$subscribe((mutation, state) => {
      this.editor.setTheme(`ace/theme/${state.editorTheme}`);
      this.editor.setFontSize(state.fontSize);
    });

    const tabEl = document.getElementById(`${this.tabId}-logs-tab`);
    tabEl.addEventListener("shown.bs.tab", (event) => {
      this.handleResize();
      if (this.intervalObject === null) {
        this.getLog();
      }
    });
  },
  unmounted() {
    clearInterval(this.intervalObject);
    window.removeEventListener("resize", this.resizeBrowserHandler);
  },
  methods: {
    setupEditor() {
      this.editor = ace.edit(this.$refs.editor);
      this.editor.$blockScrolling = Infinity;
      this.editor.session.setMode("ace/mode/pgsql_extended");
      this.editor.setTheme(`ace/theme/${settingsStore.editorTheme}`);
      this.editor.setFontSize(settingsStore.fontSize);
      this.editor.setShowPrintMargin(false);
      this.editor.setReadOnly(true);

      this.editor.commands.bindKey("Cmd-,", null);
      this.editor.commands.bindKey("Ctrl-,", null);
      this.editor.commands.bindKey("Cmd-Delete", null);
      this.editor.commands.bindKey("Ctrl-Delete", null);
    },
    getLog(showLoading = true) {
      if (showLoading) {
        clearInterval(this.intervalObject);
        this.intervalObject = null;
        this.showLoading = true;
      }
      axios
        .post("/get_postgres_server_log/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
          log_format: this.formatMode,
          log_offset: this.logOffset,
        })
        .then((response) => {
          this.loggingDisabled = response.data.logs === null;

          if (
            !!this.currentLogFile &&
            this.currentLogFile !== response.data.current_logfile
          ) {
            this.logOffset = null;
          }

          this.currentLogFile = response.data.current_logfile;
          if (this.logOffset !== null) {
            const currentLength = this.editor.session.getLength();
            this.editor.session.insert(
              { row: currentLength, column: 0 },
              response.data.logs
            );
          } else {
            this.editor.setValue(response.data.logs);
          }
          this.editor.clearSelection();
          this.showLoading = false;
          this.logOffset = response.data.log_offset;

          this.scrollToBottom();
          if (this.intervalObject === null) {
            this.intervalObject = setInterval(() => {
              this.getLog(false);
            }, 5000);
          }
        })
        .catch((error) => {
          handleError(error);
          this.showLoading = false;
        });
    },
    getLogFormat() {
      axios
        .post("/get_postgres_server_log_formats/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
        })
        .then((resp) => {
          this.formatModes = {
            stderr: {
              ace_mode: "ace/mode/pgsql_extended",
              text: "TEXT",
              available: !!resp.data.formats?.includes("stderr"),
            },
            csvlog: {
              ace_mode: "ace/mode/xml",
              text: "CSV",
              available: !!resp.data.formats?.includes("csvlog"),
            },
            jsonlog: {
              ace_mode: "ace/mode/json",
              text: "JSON",
              available: !!resp.data.formats?.includes("jsonlog"),
            },
          };
        })
        .catch((error) => {
          handleError(error);
        });
    },
    getServerVersion() {
      axios
        .post("/get_postgresql_version/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
        })
        .then((response) => {
          this.serverVersion = response.data.version;
        })
        .catch((error) => {
          handleError(error);
        });
    },
    handleResize() {
      if (this.$refs === null || this.loggingDisabled) return;

      this.heightSubtract =
        this.$refs.topToolbar.getBoundingClientRect().bottom;
    },
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.autoScroll) {
          this.editor.renderer.scrollToLine(Number.POSITIVE_INFINITY);
        }
      });
    },
    showFind() {
      this.editor.execCommand("find");
    },
  },
};
</script>

<style scoped>
.ace-editor {
  height: v-bind(editorHeight);
}

.btn-w-fixed {
  min-width: 2.5rem;
}
</style>
