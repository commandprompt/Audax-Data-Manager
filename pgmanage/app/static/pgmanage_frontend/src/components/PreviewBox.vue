<template>
  <p v-show="showLabel" class="fw-bold mb-2">{{ label }}</p>
  <div ref="editor" v-bind="$attrs"></div>

  <button
    ref="copyButton"
    title="Copy to Query Editor"
    class="btn btn-icon btn-icon-primary btn-sm m-2 d-none d-block top-0 end-0 position-absolute copy-to-editor-button"
    :disabled="isCopyButtonClicked"
    @click="copyToEditor"
  >
    <i class="fa-solid fa-edit"></i>
  </button>
</template>

<script>
import { editorModeMap, sqlFormatterDialectMap } from "../constants";
import { settingsStore, tabsStore } from "../stores/stores_initializer";
import { format } from "sql-formatter";

export default {
  props: {
    label: {
      type: String,
      default: "Preview",
    },
    showLabel: {
      type: Boolean,
      default: true,
    },
    editorText: {
      type: String,
    },
    databaseTechnology: {
      type: String,
    },
  },
  data() {
    return {
      isCopyButtonClicked: false,
      isEmpty: true,
      formatOptions: {
        tabWidth: 2,
        keywordCase: "upper",
        language:
          sqlFormatterDialectMap[this.databaseTechnology] ??
          this.databaseTechnology,
        linesBetweenQueries: 1,
      },
    };
  },
  mounted() {
    this.setupEditor();

    // ace doesn't redraw on container resize on its own
    this.resizeObserver = new ResizeObserver(() => {
      this.editor.resize();
    });
    this.resizeObserver.observe(this.$refs.editor);
  },
  beforeUnmount() {
    this.resizeObserver?.disconnect();
  },
  watch: {
    editorText(newValue, oldValue) {
      this.isEmpty = !newValue;
      if (!!newValue && this.databaseTechnology !== "postgresql") {
        newValue = format(newValue, this.formatOptions);
      }
      this.editor.setValue(newValue);
      this.editor.clearSelection();
      this.editor.moveCursorTo(0,0);
      this.isCopyButtonClicked = false;
    },
  },
  methods: {
    setupEditor() {
      let editor_mode = editorModeMap[this.databaseTechnology] || "sql";
      this.editor = ace.edit(this.$refs.editor);
      this.editor.setTheme("ace/theme/" + settingsStore.editorTheme);
      this.editor.setFontSize(Number(settingsStore.fontSize));
      this.editor.session.setMode(`ace/mode/${editor_mode}`);
      this.editor.setReadOnly(true);
      this.editor.setShowPrintMargin(false);

      this.editor.clearSelection();
      this.editor.$blockScrolling = Infinity;

      //Remove shortcuts from ace in order to avoid conflict with omnidb shortcuts
      this.editor.commands.bindKey("ctrl-space", null);
      this.editor.commands.bindKey("Cmd-,", null);
      this.editor.commands.bindKey("Ctrl-,", null);
      this.editor.commands.bindKey("Cmd-Delete", null);
      this.editor.commands.bindKey("Ctrl-Delete", null);
      this.editor.commands.bindKey("Ctrl-Up", null);
      this.editor.commands.bindKey("Ctrl-Down", null);
      this.editor.commands.bindKey("ctrl-p", null);

      settingsStore.$subscribe((mutation, state) => {
        this.editor.setTheme(`ace/theme/${state.editorTheme}`);
        this.editor.setFontSize(state.fontSize);
      });

      this.editor.setOptions({
        enableHoverLinking: true,
      });
      this.addCopyToEditorButton();
    },
    addCopyToEditorButton() {
      const copyToEditorButton = this.$refs.copyButton;

      const editorContainer = this.$refs.editor;
      editorContainer.addEventListener("mouseover", () => {
        copyToEditorButton.classList.toggle("d-none", this.isEmpty);
      });
      editorContainer.addEventListener("mouseout", () => {
        copyToEditorButton.classList.toggle("d-none", true);
      });

      editorContainer.appendChild(copyToEditorButton);
    },
    copyToEditor() {
      tabsStore.createQueryTab("Query", null, null, this.editor.getValue());
      this.isCopyButtonClicked = true;
    },
  },
};
</script>

<style scoped>
.copy-to-editor-button {
  z-index: 1000;
}
</style>
