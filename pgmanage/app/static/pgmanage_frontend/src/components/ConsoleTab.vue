<template>
  <div class="console-tab">
    <div
      ref="console"
      class="omnidb__txt-console terminal-wrapper flex-grow-1"
      @contextmenu.stop.prevent="contextMenu"
    ></div>

    <div ref="tabActions" class="tab-actions py-2 d-flex align-items-center border-top ps-2">
      <button class="btn btn-square btn-secondary" title="Open File" @click="openFileManagerModal">
          <i class="fas fa-folder-open fa-light"></i>
      </button>

      <button class="btn btn-square btn-secondary" title="Clear Console" @click="clearConsole()">
        <i class="fas fa-broom fa-light"></i>
      </button>

      <button class="btn btn-square btn-secondary me-2" title="Command History" @click="showCommandsHistory()">
        <i class="fas fa-clock-rotate-left fa-light"></i>
      </button>

      <template v-if="postgresqlDialect">
        <div class="form-check form-check-inline mb-0">
          <input :id="`check_autocommit_${tabId}`" class="form-check-input" type="checkbox" v-model="autocommit" />
          <label class="form-check-label" :for="`check_autocommit_${tabId}`">Autocommit</label>
        </div>

        <TabStatusIndicator :tab-status="tabStatus" />
      </template>

      <template v-if="fetchMoreData && idleState">
        <button class="btn btn-sm btn-secondary" title="Fetch More"
          @click="consoleSQL(consoleModes.FETCH_MORE)">
          Fetch more
        </button>
        <BlockSizeSelector v-model="blockSize"/>
      </template>

      <button v-if="fetchMoreData && idleState" class="btn btn-sm btn-secondary" title="Fetch All"
        @click="consoleSQL(consoleModes.FETCH_ALL)">
        Fetch all
      </button>

      <button v-if="fetchMoreData && idleState" class="btn btn-sm btn-secondary" title="Skip Fetch"
        @click="consoleSQL(consoleModes.SKIP_FETCH)">
        Skip Fetch
      </button>

      <button v-if="openedTransaction && !executingState" class="btn btn-sm btn-primary" title="Commit">
        Commit
      </button>

      <button v-if="openedTransaction && !executingState" class="btn btn-sm btn-secondary" title="Rollback">
        Rollback
      </button>

      <CancelButton v-if="executingState && longQuery" :tab-id="tabId" :workspace-id="workspaceId"
        @cancelled="cancelConsoleTab()" />

      <p class="m-0 h6" v-if="cancelled">
        <b>Cancelled</b>
      </p>
      <p v-else-if="queryStartTime && queryDuration" class="m-0 h6 me-2">
        <b>Start time:</b> {{ queryStartTime.format() }}<br/>
        <b>Duration:</b> {{ queryDuration }}
      </p>
      <p v-else-if="queryStartTime" class="m-0 h6 me-2">
        <b>Start time:</b> {{ queryStartTime.format() }}
      </p>
    </div>
  </div>
</template>

<script>
import { markRaw } from "vue";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { CanvasAddon } from '@xterm/addon-canvas';
import axios from "axios";
import { emitter } from "../emitter";
import { flashHighlight } from "../utils";
import { showToast } from "../notification_control";
import moment from "moment";
import { createRequest } from "../long_polling";
import { settingsStore, tabsStore, messageModalStore, fileManagerStore, commandsHistoryStore } from "../stores/stores_initializer";
import TabStatusIndicator from "./TabStatusIndicator.vue";
import CancelButton from "./CancelSQLButton.vue";
import { tabStatusMap, requestState, queryRequestCodes, consoleModes } from "../constants";
import FileInputChangeMixin from '../mixins/file_input_mixin'
import BlockSizeSelector from "./BlockSizeSelector.vue";
import ContextMenu from "@imengyu/vue3-context-menu";
import { readClipboardText } from "@src/utils/clipboard";
import { handleError } from "../logging/utils.js";
import { ConsoleInputController, CLEAR_TERMINAL, QUIET_RESET } from "../console/ConsoleInputController.js";

export default {
  name: "ConsoleTab",
  components: {
    TabStatusIndicator,
    CancelButton,
    BlockSizeSelector
  },
  mixins: [FileInputChangeMixin],
  props: {
    workspaceId: String,
    tabId: String,
    consoleHelp: String,
    databaseIndex: Number,
    dialect: String,
    databaseName: String,
  },
  data() {
    return {
      consoleState: requestState.Idle,
      lastCommand: "",
      autocommit: true,
      fetchMoreData: false,
      openedTransaction: false, //TODO: implement commit/rollback functionality
      data: "",
      context: "",
      tempData: [],
      tabStatus: tabStatusMap.NOT_CONNECTED,
      queryDuration: "",
      queryStartTime: "",
      cancelled: false,
      bufferPreview: "",
      longQuery: false,
      terminal: null,
      fitAddon: null,
      inputController: null,
      blockSize: 50,
      consoleHeightSubtract: 50, //default safe value, recalculated in onResize
    };
  },
  computed: {
    executingState() {
      return this.consoleState === requestState.Executing;
    },
    idleState() {
      return this.consoleState === requestState.Idle;
    },
    postgresqlDialect() {
      return this.dialect === "postgresql";
    },
    consoleModes() {
      return consoleModes;
    },
    activeTransaction() {
      return [
        tabStatusMap.IDLE_IN_TRANSACTION,
        tabStatusMap.IDLE_IN_TRANSACTION_ABORTED,
      ].includes(this.tabStatus);
    },
    hasChanges() {
      return this.activeTransaction || this.executingState || !!this.bufferPreview
    },
    consoleHeight() {
      return `calc(100vh - ${this.consoleHeightSubtract}px)`
    }
  },
  updated() {
    if (!this.terminal) {
      this.setupTerminal()
    }

    this.updateHeightOffset()
  },
  mounted() {
    this.setupTerminal()
    if (tabsStore.selectedPrimaryTab.metaData.selectedTab.id === this.tabId) {
      requestAnimationFrame(() => {
        this.onResize();
      })
    }
    this.setupEvents();

    settingsStore.$subscribe((mutation, state) => {
      if (!this.terminal) return
      this.terminal.options.theme = state.terminalTheme;
      this.terminal.options.fontSize = state.fontSize;
    });
  },
  unmounted() {
    this.clearEvents();
  },
  methods: {
    setupTerminal() {
      // marRaw helps to avoid vue reactivity side effects on xterm objects
      this.terminal = markRaw(new Terminal({
        fontSize: settingsStore.fontSize,
        theme: settingsStore.terminalTheme,
        fontFamily: "'Ubuntu Mono', monospace",
      }));

      this.terminal.open(this.$refs.console);
      this.terminal.loadAddon(markRaw(new CanvasAddon()));
      this.terminal.onData((data) => this.onData(data));

      this.fitAddon = markRaw(new FitAddon());
      this.terminal.loadAddon(this.fitAddon);

      this.inputController = markRaw(new ConsoleInputController({
        dialect: this.dialect,
        // matches the backend's own command echo format (thread_console in
        // polling.py always prefixes output with "<database>=# "), so the
        // prompt shown while typing is consistent with what's echoed after Enter
        promptPrimary: this.databaseName ? `${this.databaseName}=# ` : undefined,
        promptContinuation: this.databaseName ? `${this.databaseName}-# ` : undefined,
        onSubmit: this.handleSubmit,
        onBufferChange: (text) => { this.bufferPreview = text; },
      }));

      this.terminal.write(this.consoleHelp);
      this.inputController.beginNewInputLine(this.terminal);
      if (tabsStore.selectedPrimaryTab.metaData.selectedTab.id === this.tabId) {
        this.terminal.focus();
      }
      this.preloadHistory();
    },
    onData(data) {
      const result = this.inputController.handleData(data);
      if (result === QUIET_RESET) {
        this.terminal.write("\r\n");
        this.inputController.beginNewInputLine(this.terminal);
      } else if (!result) {
        this.inputController.render(this.terminal);
      }
    },
    setupEvents() {
      emitter.on(`${this.tabId}_resize`, () => {
        this.onResize();
      });

      emitter.on(`${this.tabId}_check_console_status`, () => {
        if (this.consoleState === requestState.Ready) {
          this.context.tab.metaData.isReady = false;
          this.context.tab.metaData.isLoading = false;
          this.consoleState = requestState.Idle;
          this.consoleReturnRender(this.data);
        }
      });

      emitter.on(`${this.tabId}_copy_to_editor`, (content) => {
        this.inputController.setBuffer(content);
        this.inputController.render(this.terminal);
        this.terminal.focus();
      });

      emitter.on(`${this.tabId}_history_cleared`, () => {
        this.preloadHistory();
      });

      emitter.on(`${this.tabId}_focus`, () => {
        this.terminal.focus();
        flashHighlight(this.$refs.console);
      });
    },
    clearEvents() {
      emitter.all.delete(`${this.tabId}_resize`);
      emitter.all.delete(`${this.tabId}_check_console_status`);
      emitter.all.delete(`${this.tabId}_run_console`);
      emitter.all.delete(`${this.tabId}_focus`);
    },
    onResize() {
      this.updateHeightOffset();
      // wait for DOM updates after updateHeightOffset
      this.$nextTick(() => {
        requestAnimationFrame(() => {
          if (!this.fitAddon || !this.terminal) return;
          this.fitAddon.fit();
        });
      });
    },
    updateHeightOffset() {
      if (this.$refs.console) {
        this.consoleHeightSubtract = this.$refs.console.getBoundingClientRect().top;
      }
    },
    preloadHistory(databaseFilter = this.databaseName) {
      axios.post("/get_commands_history/", {
        current_page: 1,
        database_index: this.databaseIndex,
        database_filter: databaseFilter,
        command_contains: "",
        command_type: "Console",
        page_size: 300,
      }).then((resp) => {
        this.inputController.setPreloadedHistory(
          resp.data.command_list.map((c) => c.snippet).reverse()
        );
      }).catch(handleError);
    },
    handleSubmit(text) {
      if (this.terminal) this.terminal.write("\r\n");
      this.consoleSQL(consoleModes.DATA_OPERATION, text);
    },
    consoleSQL(mode = consoleModes.DATA_OPERATION, command = "") {
      let tab = tabsStore.getSelectedSecondaryTab(this.workspaceId)
      this.queryDuration = "";
      this.cancelled = false;
      this.fetchMoreData = false;
      this.longQuery = false;
      this.tempData = [];
      this.lastCommand = command;

      let message_data = {
        sql_cmd: command,
        mode: mode,
        db_index: this.databaseIndex,
        workspace_id: this.workspaceId,
        tab_id: this.tabId,
        autocommit: this.autocommit,
        block_size: this.blockSize,
        database_name: this.databaseName,
      };

      this.inputController.setLocked(true);

      this.queryStartTime = moment();

      let context = {
        tab: tab,
        database_index: this.databaseIndex,
        acked: false,
        last_command: this.lastCommand,
        mode: mode,
        callback: this.consoleReturn.bind(this),
        passwordSuccessCallback: this.passwordSuccessCallback.bind(this),
        passwordFailCalback: () => {
          emitter.emit(`${this.tabId}_cancel_query`);
        },
      };

      context.tab.metaData.context = context

      createRequest(queryRequestCodes.Console, message_data, context);

      this.consoleState = requestState.Executing;

      setTimeout(() => {
        if (this.consoleState === requestState.Executing) {
          tab.metaData.isLoading = true;
          this.longQuery = true;
        }
      }, 1000);

      this.queryInterval = setInterval((function(){
        let diff = moment().diff(this.queryStartTime)
        this.queryDuration = moment.utc(diff).format('HH:mm:ss')
      }).bind(this), 1000)

      tab.metaData.isReady = false

      this.tabStatus = tabStatusMap.RUNNING;
    },
    consoleReturn(data, context) {
      this.tempData.push(data.data.data)

      if (!this.idleState && (data.data.last_block || data.error)) {
        clearInterval(this.queryInterval);
        this.queryInterval = null;
        data.data.data = this.tempData;
        this.tempData = []
        this.inputController.setLocked(false);
        this.tabStatus = data.data.con_status;
        if (
          this.workspaceId === tabsStore.selectedPrimaryTab.id &&
          this.tabId === tabsStore.selectedPrimaryTab.metaData.selectedTab.id
        ) {
          this.context = "";
          this.data = "";
          this.consoleState = requestState.Idle;
          context.tab.metaData.isLoading = false;
          context.tab.metaData.isReady = false;
          this.consoleReturnRender(data);
        } else {
          this.consoleState = requestState.Ready;
          this.data = data;
          this.context = context;

          context.tab.metaData.isReady = true
          context.tab.metaData.isLoading = false
        }
      }
    },
    consoleReturnRender(data) {
      data.data.data.forEach((chunk) => {
        this.terminal.write(chunk);
      })
      this.terminal.write("\r\n");
      this.fetchMoreData = data.data.show_fetch_button;
      this.queryDuration = data.data.duration;

      const newActiveDatabase = data.data.active_database;
      if (newActiveDatabase && newActiveDatabase !== this.databaseName) {
        const tab = tabsStore.getSecondaryTabById(this.tabId, this.workspaceId);
        if (tab) tab.metaData.databaseName = newActiveDatabase;
        this.inputController.setPrompt(`${newActiveDatabase}=# `, `${newActiveDatabase}-# `);
        this.preloadHistory(newActiveDatabase);
      }

      if (!data.error && !!data?.data?.status && isNaN(data.data.status)) {
        let mode = ["CREATE", "DROP", "ALTER"];
        let status = data.data.status.split(" ");

        if (mode.includes(status[0])) {
          let node_type = status[1] ? `${status[1].toLowerCase()}_list` : null;

          if (!!node_type)
            emitter.emit(`refreshTreeRecursive_${this.workspaceId}`, node_type);
        }
      }

      this.inputController.beginNewInputLine(this.terminal);
    },
    contextMenu(event) {
      let option_list = [
        {
          label: "Copy",
          icon: "fas fa-copy",
          disabled: !this.terminal.hasSelection(),
          onClick: () => {
            document.execCommand("copy");
          },
        },
        {
          label: "Paste",
          icon: "fas fa-paste",
          onClick: async () => {
            const text = await readClipboardText();

            if (!text) {
              return;
            }

            this.inputController.insertText(text);
            this.inputController.render(this.terminal);
          },
        },
      ];

      ContextMenu.showContextMenu({
        theme: "pgmanage",
        x: event.x,
        y: event.y,
        zIndex: 1000,
        minWidth: 230,
        items: option_list,
      });
    },
    clearConsole() {
      this.terminal.write(CLEAR_TERMINAL);
      this.terminal.write(this.consoleHelp);
      this.inputController.beginNewInputLine(this.terminal);
    },
    cancelConsoleTab() {
      clearInterval(this.queryInterval);
      this.queryInterval = null;

      this.inputController.setLocked(false);

      this.consoleState = requestState.Idle;
      this.tabStatus = tabStatusMap.NOT_CONNECTED;

      this.cancelled = true;
    },
    passwordSuccessCallback(context) {
      emitter.emit(`${this.tabId}_cancel_query`);
      this.consoleSQL(context.mode, this.lastCommand);
    },
    showCommandsHistory() {
      commandsHistoryStore.showModal(this.tabId, this.databaseIndex, "Console");
    },
    openFileManagerModal() {
      if (!!this.bufferPreview) {
        messageModalStore.showModal(
          "Are you sure you wish to discard the current changes?",
          () => {
            fileManagerStore.showModal(true, this.handleFileInputChange);
          },
          null
        );
      } else {
        fileManagerStore.showModal(true, this.handleFileInputChange);
      }
    },
  },
  watch: {
    hasChanges() {
      const tab = tabsStore.getSecondaryTabById(this.tabId, this.workspaceId);
      if (tab) {
        tab.metaData.hasUnsavedChanges = this.hasChanges;
      }
    },
    databaseName(newVal) {
      if (!this.inputController) return;
      this.inputController.setPrompt(`${newVal}=# `, `${newVal}-# `);
    },
  }
};
</script>

<style scoped>
.console-tab {
  height: v-bind(consoleHeight);
  display: flex;
  flex-direction: column;
}

.terminal-wrapper {
  min-height: 0;
  overflow: hidden;
}

.tab-actions {
  align-items: center;
  display: flex;
  justify-content: flex-start;
  min-height: 35px;
}

.tab-actions>button {
  margin-right: 5px;
}
</style>
