<template>
  <Teleport to="body">
    <div
      id="cell_data_modal"
      ref="cellDataModal"
      class="modal fade"
      aria-hidden="true"
      role="dialog"
      tabindex="-1"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header align-items-center">
            <h2 class="modal-title font-weight-bold">Show Data</h2>
            <button
              type="button"
              class="btn-close"
              aria-label="Close"
              @click="store.hideModal()"
            ></button>
          </div>
          <div class="modal-body">
            <Transition :duration="100">
              <div
                v-if="showLoading"
                class="div_loading d-block"
                style="z-index: 10"
              >
                <div class="div_loading_cover"></div>
                <div class="div_loading_content">
                  <div
                    class="spinner-border spinner-size text-primary"
                    role="status"
                  >
                    <span class="sr-only">Loading...</span>
                  </div>
                </div>
              </div>
            </Transition>
            <div ref="editor" class="ace-editor"></div>
          </div>
          <div
            class="modal-footer"
            :class="{ 'justify-content-between': store.showControls }"
          >
            <div v-if="store.showControls" class="row">
              <div class="col-auto align-content-center">
                <span class="fw-bold"> View as </span>
              </div>
              <div class="col-auto">
                <select class="form-select" v-model="contentMode">
                  <option
                    v-for="(modePath, modeName, index) in contentModes"
                    :value="modePath"
                    :key="index"
                  >
                    {{ modeName }}
                  </option>
                </select>
              </div>
              <div v-if="readOnly" class="col-auto form-check align-content-center">
                <input
                  id="cell_data_modal_autoformat"
                  type="checkbox"
                  class="form-check-input"
                  v-model="autoFormat"
                />
                <label for="cell_data_modal_autoformat" class="form-check-label"
                  >Autoformat</label
                >
              </div>
              <div class="col-auto">
                <button
                  data-testid="format-button"
                  class="btn btn-sm btn-primary"
                  @click="formatContent"
                >
                  Format
                </button>
              </div>
            </div>
            <button
              v-if="readOnly"
              data-testid="close-modal-button"
              type="button"
              class="btn btn-secondary"
              @click="store.hideModal()"
            >
              Close
            </button>
            <div v-else>
              <button
                data-testid="cancel-modal-button"
                type="button"
                class="btn btn-secondary me-1"
                @click="store.hideModal()"
              >
                Cancel
              </button>
              <button
                data-testid="apply-modal-button"
                type="button"
                class="btn btn-success"
                @click="onApply"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { beautify } from "ace-builds/src-noconflict/ext-beautify";
import {
  settingsStore,
  cellDataModalStore,
} from "../stores/stores_initializer";
import { Modal } from "bootstrap";

const chunkSize = 100000;

export default {
  name: "CellDataModal",
  data() {
    return {
      editor: null,
      modalInstance: null,
      contentModes: {
        TEXT: "ace/mode/plain_text",
        JSON: "ace/mode/json",
        HTML: "ace/mode/xml",
        SQL: "ace/mode/sql",
      },
      contentMode: "ace/mode/plain_text",
      autoFormat: true,
      showLoading: true,
      loadedEndIndex: 0,
    };
  },
  computed: {
    store() {
      return cellDataModalStore;
    },
    readOnly() {
      return this.store.readOnly;
    },
  },
  mounted() {
    this.modalInstance = Modal.getOrCreateInstance(this.$refs.cellDataModal, {
      backdrop: "static",
    });

    this.$refs.cellDataModal.addEventListener("shown.bs.modal", (event) => {
      this.setupEditor();
      this.setEditorContent();
    });

    this.$refs.cellDataModal.addEventListener("hidden.bs.modal", () => {
      this.cleanupEditor();
      this.loadedEndIndex = 0;
    });

    cellDataModalStore.$onAction((action) => {
      if (action.name === "showModal") {
        action.after(() => {
          this.showLoading = true;
          if (!this.readOnly) this.autoFormat = false;
          this.modalInstance.show();
        });
      }

      if (action.name === "hideModal") {
        this.modalInstance.hide();
      }
    });
  },
  watch: {
    contentMode(newValue) {
      if (!this.store.visible || !this.editor) return;
      this.editor.session.setMode(newValue);
      if (this.autoFormat) {
        this.formatContent();
      }
    },
  },
  methods: {
    setupEditor() {
      this.editor = ace.edit(this.$refs.editor);
      this.editor.$blockScrolling = Infinity;
      this.editor.setTheme(`ace/theme/${settingsStore.editorTheme}`);
      this.editor.setFontSize(settingsStore.fontSize);
      this.editor.setShowPrintMargin(false);
      this.editor.setReadOnly(this.readOnly);

      this.editor.commands.bindKey("Cmd-,", null);
      this.editor.commands.bindKey("Ctrl-,", null);
      this.editor.commands.bindKey("Cmd-Delete", null);
      this.editor.commands.bindKey("Ctrl-Delete", null);
      this.editor.getSession().on("changeScrollTop", this.onEditorScroll);
    },
    onEditorScroll() {
      const scrollTop = this.editor.renderer.scrollTop;
      const scrollHeight = this.editor.renderer.scrollBarV.scrollHeight;
      const clientHeight = this.editor.renderer.$size.scrollerHeight;

      const nearBottom = scrollTop + clientHeight >= scrollHeight - 100;

      if (nearBottom) {
        this.appendNextChunk();
      }
    },
    appendNextChunk() {
      if (!this.store.cellContent || this.store.cellContent.length === 0)
        return;

      let cellContent = this.store.cellContent;

      const nextChunk = cellContent.slice(this.loadedEndIndex, this.loadedEndIndex + chunkSize);
      this.loadedEndIndex += nextChunk.length;

      if (nextChunk) {
        const currentLength = this.editor.session.getLength();
        this.editor.session.insert(
          { row: currentLength, column: 0 },
          nextChunk
        );
        this.formatContent();
        this.editor.resize(); // updates scroll position if it wasn't updated
      }
    },
    setEditorContent() {
      let cellContent = this.store.cellContent || "";
      if (cellContent) cellContent = this.store.cellContent.toString();
      const cellType = this.store.cellType || "default";
      const cellContentToAdd = cellContent.slice(0, chunkSize);
      this.loadedEndIndex = cellContentToAdd.length;
      this.editor.setValue(cellContentToAdd);

      this.contentMode = this.getAceMode(cellType);
      this.editor.clearSelection();
      this.showLoading = false;
    },
    getAceMode(cellType) {
      switch (cellType) {
        case "json":
        case "jsonb":
          return "ace/mode/json";
        case "xml":
        case "xmltype":
          return "ace/mode/xml";
        case "sql":
        case "enum":
        case "set":
        case "cursor":
        case "object":
          return "ace/mode/sql";
        default:
          return "ace/mode/plain_text";
      }
    },
    formatContent() {
      beautify(this.editor.getSession());
    },
    cleanupEditor() {
      this.editor.setValue("");
      this.contentMode = this.contentModes.TEXT;
      // erase leftover css classes left after editor destruction
      this.$refs.editor.classList.remove("ace-omnidb", "ace-omnidb_dark");
      this.editor.destroy();
    },
    onApply() {
      const currentEditorValue = this.editor.getValue();
      const newValue = currentEditorValue + (this.store.cellContent?.slice(this.loadedEndIndex) ?? "");
      this.store.applyFunc(newValue);
      this.store.hideModal();
    },
  },
};
</script>

<style scoped>
.modal-dialog {
  width: 1200px;
  max-width: 90vw;
}

.ace-editor {
  height: 70vh;
}

.modal-body {
  white-space: pre-line;
}
</style>
