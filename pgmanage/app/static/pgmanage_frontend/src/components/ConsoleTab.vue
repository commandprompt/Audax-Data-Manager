<template>
  <div>
  <splitpanes class="default-theme console-body" horizontal @resized="onResize">
    <pane size="80">
      <div ref="console" :id="`txt_console_${tabId}`" class="omnidb__txt-console me-2 h-100"></div>
    </pane>

    <pane size="20" class="ps-2 border-top">
      <div ref="tabActions" class="tab-actions py-2 d-flex align-items-center">
        <button class="btn btn-square btn-primary" title="Run" @click="consoleSQL(false)" :disabled="executingState">
          <i class="fas fa-play fa-light"></i>
        </button>

        <button class="btn btn-square btn-secondary" title="Open File" @click="openFileManagerModal">
            <i class="fas fa-folder-open fa-light"></i>
        </button>

        <button class="btn btn-square btn-secondary" title="Indent SQL" @click="indentSQL()">
          <i class="fas fa-indent fa-ligth"></i>
        </button>

        <button class="btn btn-square btn-secondary" title="Clear Console" @click="clearConsole()">
          <i class="fas fa-broom fa-ligth"></i>
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
            @click="consoleSQL(false, consoleModes.FETCH_MORE)">
            Fetch more
          </button>
          <BlockSizeSelector v-model="blockSize"/>
        </template>

        <button v-if="fetchMoreData && idleState" class="btn btn-sm btn-secondary" title="Fetch All"
          @click="consoleSQL(false, consoleModes.FETCH_ALL)">
          Fetch all
        </button>

        <button v-if="fetchMoreData && idleState" class="btn btn-sm btn-secondary" title="Skip Fetch"
          @click="consoleSQL(false, consoleModes.SKIP_FETCH)">
          Skip Fetch
        </button>

        <button v-if="openedTransaction && !executingState" class="btn btn-sm btn-primary" title="Run">
          Commit
        </button>

        <button v-if="openedTransaction && !executingState" class="btn btn-sm btn-secondary" title="Run">
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
        <QueryEditor ref="editor" class="editor-height me-2" :read-only="readOnlyEditor" :tab-id="tabId" :workspace-id="workspaceId" tab-mode="console"
          :dialect="dialect" @editor-change="updateEditorContent" :autocomplete="autocomplete"/>
    </pane>
  </splitpanes>
</div>
</template>

<script>
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { CanvasAddon } from '@xterm/addon-canvas';
import { Splitpanes, Pane } from "splitpanes";
import { emitter } from "../emitter";
import { showToast } from "../notification_control";
import moment from "moment";
import { createRequest } from "../long_polling";
import { settingsStore, tabsStore, connectionsStore, messageModalStore, fileManagerStore, commandsHistoryStore } from "../stores/stores_initializer";
import TabStatusIndicator from "./TabStatusIndicator.vue";
import QueryEditor from "./QueryEditor.vue";
import CancelButton from "./CancelSQLButton.vue";
import { tabStatusMap, requestState, queryRequestCodes, consoleModes } from "../constants";
import FileInputChangeMixin from '../mixins/file_input_mixin'
import BlockSizeSelector from "./BlockSizeSelector.vue";

export default {
  name: "ConsoleTab",
  components: {
    Splitpanes,
    Pane,
    TabStatusIndicator,
    QueryEditor,
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
      readOnlyEditor: false,
      editorContent: "",
      longQuery: false,
      terminal: null,
      fitAddon: null,
      blockSize: 50,
      editorHeightSubtract: 50, //default safe value, recalculated in handleResize,
      consoleHeightSubtract: 50
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
    autocomplete() {
      return connectionsStore.getConnection(this.databaseIndex).autocomplete
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
      return this.activeTransaction || this.executingState || !!this.editorContent
    },
    editorHeight() {
      return `calc(100% - ${this.editorHeightSubtract}px)`;
    },
    consoleHeight() {
      return `calc(100vh - ${this.consoleHeightSubtract}px)`
    }
  },
  updated() { 
    if (!this.terminal) {
      this.setupTerminal()
    }
    this.onResize()
  },
  mounted() {
    if (tabsStore.selectedPrimaryTab.metaData.selectedTab.id === this.tabId) {
      this.setupTerminal()
      requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              this.onResize();
            })
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
      this.terminal = new Terminal({
        fontSize: settingsStore.fontSize,
        theme: settingsStore.terminalTheme,
        fontFamily: "'Ubuntu Mono', monospace",
      });

      this.terminal.open(this.$refs.console);
      this.terminal.loadAddon(new CanvasAddon());
      this.terminal.write(this.consoleHelp);

      this.fitAddon = new FitAddon();

      this.terminal.loadAddon(this.fitAddon);
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

      emitter.on(`${this.tabId}_run_console`, (check_command) => {
        this.consoleSQL(check_command);
      });
    },
    clearEvents() {
      emitter.all.delete(`${this.tabId}_resize`);
      emitter.all.delete(`${this.tabId}_check_console_status`);
      emitter.all.delete(`${this.tabId}_run_console`);
    },
    onResize() {
      if (this.fitAddon)
        this.fitAddon.fit();
      
      this.editorHeightSubtract =
        this.$refs.tabActions.getBoundingClientRect().height;
      this.consoleHeightSubtract =
        this.$refs.console.getBoundingClientRect().top;
    },
    consoleSQL(check_command = true, mode = consoleModes.DATA_OPERATION) {
      const command = this.editorContent.trim();
      if (!check_command || command[0] === "\\") {
        if (!this.idleState) {
          showToast("info", "Tab with activity in progres.");
        } else {
          if (command === "" && mode === consoleModes.DATA_OPERATION) {
            showToast("info", "Please provide a string.");
          } else {
            let tab = tabsStore.getSelectedSecondaryTab(this.workspaceId)
            this.queryDuration = "";
            this.cancelled = false;
            this.fetchMoreData = false;
            this.longQuery = false;
            this.tempData = [];
            emitter.emit(`${this.tabId}_copy_to_editor`, "");
            this.lastCommand = command;

            let message_data = {
              sql_cmd: command,
              mode: mode,
              db_index: this.databaseIndex,
              workspace_id: this.workspaceId,
              tab_id: this.tabId,
              autocommit: this.autocommit,
              block_size: this.blockSize
            };

            this.readOnlyEditor = true;

            this.queryStartTime = moment();

            let context = {
              tab: tab,
              database_index: this.databaseIndex,
              acked: false,
              last_command: this.lastCommand,
              check_command: check_command,
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
          }
        }
      }
    },
    consoleReturn(data, context) {
      this.tempData.push(data.data.data)
      
      if (!this.idleState && (data.data.last_block || data.error)) {
        clearInterval(this.queryInterval);
        this.queryInterval = null;
        data.data.data = this.tempData;
        this.tempData = []
        this.readOnlyEditor = false;
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
        this.terminal.writeln(chunk);
      })
      this.fetchMoreData = data.data.show_fetch_button;
      this.queryDuration = data.data.duration;

      if (!data.error && !!data?.data?.status && isNaN(data.data.status)) {
        let mode = ["CREATE", "DROP", "ALTER"];
        let status = data.data.status.split(" ");

        if (mode.includes(status[0])) {
          let node_type = status[1] ? `${status[1].toLowerCase()}_list` : null;

          if (!!node_type)
            emitter.emit(`refreshTreeRecursive_${this.workspaceId}`, node_type);
        }
      }
    },
    clearConsole() {
      this.terminal.clear();
      this.terminal.write(this.consoleHelp);
    },
    indentSQL() {
      emitter.emit(`${this.tabId}_indent_sql`);
    },
    cancelConsoleTab() {
      clearInterval(this.queryInterval);
      this.queryInterval = null;

      this.readOnlyEditor = false;

      this.consoleState = requestState.Idle;
      this.tabStatus = tabStatusMap.NOT_CONNECTED;

      this.cancelled = true;
    },
    passwordSuccessCallback(context) {
      emitter.emit(`${this.tabId}_cancel_query`);

      emitter.emit(`${this.tabId}_copy_to_editor`, this.lastCommand);

      this.consoleSQL(context.check_command, context.mode);
    },
    updateEditorContent(newContent) {
      this.editorContent = newContent;
    },
    showCommandsHistory() {
      commandsHistoryStore.showModal(this.tabId, this.databaseIndex, "Console");
    },
    openFileManagerModal() {
      if (!!this.editorContent) {
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
  }
};
</script>

<style scoped>
.editor-height {
  height: v-bind(editorHeight);
}

.console-body {
  height: v-bind(consoleHeight);
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

.splitpanes .splitpanes__pane {
  transition: none;
}
</style>
