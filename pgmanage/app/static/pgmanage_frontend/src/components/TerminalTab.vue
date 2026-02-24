<template>
  <div class="container-fluid px-0">
    <div class="row">
      <div class="col">
        <div class="omnidb__txt-console">
          <div ref="console" class="custom-console"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { CanvasAddon } from '@xterm/addon-canvas';
import { settingsStore, tabsStore } from "../stores/stores_initializer";
import { createRequest, createContext } from "../long_polling";
import { queryRequestCodes, requestState } from "../constants";
import { emitter } from "../emitter";
import TabTitleUpdateMixin from "../mixins/sidebar_title_update_mixin";

export default {
  name: "TerminalTab",
  props: {
    workspaceId: String,
    databaseIndex: Number,
  },
  mixins: [TabTitleUpdateMixin],
  data() {
    return {
      term: null,
      fitAddon: null,
      lastCommand: "",
      state: "",
      clearTerminal: true,
      contextCode: undefined,
    };
  },
  mounted() {
    this.setupTerminal();
    this.setupEvents();

    settingsStore.$subscribe((mutation, state) => {
      this.term.options.theme = state.terminalTheme;
      this.term.options.fontSize = state.fontSize;
      this.fitAddon.fit();
    });

    this.subscribeToConnectionChanges(this.workspaceId, this.databaseIndex);
  },
  unmounted() {
    this.clearEvents();
  },
  methods: {
    setupTerminal() {
      this.term = new Terminal({
        fontSize: settingsStore.fontSize,
        fontFamily: "'Ubuntu Mono', monospace",
        theme: settingsStore.terminalTheme,
      });

      this.term.open(this.$refs.console);
      this.term.loadAddon(new CanvasAddon());
      this.term.onData((data) => {
        this.terminalRun(false, data);
      });

      this.fitAddon = new FitAddon();
      this.term.loadAddon(this.fitAddon);
      this.fitAddon.fit();

      this.term.focus();
      this.term.write("Starting terminal...");

      const tab = tabsStore.getPrimaryTabById(this.workspaceId);

      let context = {
        tab: tab,
        callback: this.handleResponse.bind(this),
      }

      let ctx = {
        context: context,
      }
      createContext(ctx);
      this.contextCode = ctx.code;
      tab.metaData.context = ctx;

      this.terminalRun(
        true,
        `stty rows ${this.term.rows} cols ${this.term.cols} \n`
      );
    },
    setupEvents() {
      window.addEventListener("resize", this.resizeBrowserHandler);

      emitter.on(`${this.workspaceId}_resize`, () => {
        this.$nextTick(() => {
          this.resizeBrowserHandler();
        });
      });

      emitter.on(`${this.workspaceId}_adjust_terminal_dimensions`, () => {
        this.adjustTermninalDimensions();
        this.term.focus();
      });
    },
    clearEvents() {
      window.removeEventListener("resize", this.resizeBrowserHandler);
      emitter.all.delete(`${this.workspaceId}_resize`);
      emitter.all.delete(`${this.workspaceId}_adjust_terminal_dimensions`);
    },
    terminalRun(spawn = true, query = "\r") {
      this.lastCommand = query;
      let messageData = {
        cmd: query,
        workspace_id: this.workspaceId,
        db_index: null,
        spawn: spawn,
        ssh_id: this.databaseIndex,
      };

      createRequest(queryRequestCodes.Terminal, messageData, this.contextCode);

      this.state = requestState.Executing;
    },
    handleResponse(data, context) {
      if (this.clearTerminal) {
        this.term.write("\x1b[H\x1b[2J");
        this.clearTerminal = false;
      }

      this.state = requestState.Idle;

      this.term.write(data.data.data);
    },
    resizeBrowserHandler() {
      if (this.workspaceId === tabsStore.selectedPrimaryTab.id) {
        this.fitAddon.fit();
      }
    },
    adjustTermninalDimensions() {
      this.terminalRun(
        false,
        `stty rows ${this.term.rows} cols ${this.term.cols} \n`
      );
    },
  },
};
</script>

<style scoped>
.custom-console {
  width: 100%;
  height: 100vh;
}
</style>
