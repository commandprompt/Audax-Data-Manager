<template>
  <div
    :id="`${workspaceId}_panel_snippet`"
    :class="[
      'snippets',
      { 'snippets--slide-in': isVisible },
    ]"
  >
    <button
      type="button"
      class="snippets__toggler"
      @click="togglePanel"
    >
      <i :class="[
        'fas',
        isVisible ? 'fa-chevron-down': 'fa-chevron-up'
      ]"></i>
    </button>

    <div class="container-fluid h-100 position-relative g-0">
      <div :id="`${workspaceId}_snippet_div_layout_grid`" class="row h-100">
        <splitpanes class="default-theme">
          <pane min-size="18" size="25">
            <div class="snippets__left h-100 border-end">
              <div class="snippets__tree">
                <TreeSnippets
                  :workspace-id="workspaceId"
                  @tree-updated="getAllSnippets"
                />
              </div>
            </div>
          </pane>
          <pane min-size="2">
            <div
              class="snippets__right pt-0 h-100 position-relative"
            >
              <div class="row">
                <DatabaseTabs :id="`${workspaceId}`" class="w-100" :workspace-id="workspaceId" />
              </div>
            </div>
          </pane>
        </splitpanes>
      </div>
    </div>
  </div>
</template>

<script>
import { Splitpanes, Pane } from "splitpanes";
import { emitter } from "../emitter";
import DatabaseTabs from "./DatabaseTabs.vue";
import TreeSnippets from "./TreeSnippets.vue";
import axios from "axios";
import { snippetsStore } from "../stores/stores_initializer";
import { showToast } from "../notification_control";
import { handleError } from "../logging/utils";

export default {
  components: {
    DatabaseTabs,
    Splitpanes,
    Pane,
    TreeSnippets,
  },
  data() {
    return {
      isVisible: false,
    };
  },
  props: {
    workspaceId: String,
  },
  mounted() {
    this.getAllSnippets();
    this.setupEvents();
  },
  unmounted() {
    this.clearEvents();
  },
  methods: {
    togglePanel() {
      document.querySelectorAll('.omnidb__panel-view--full').forEach(element => {
        element.classList.remove('omnidb__panel-view--full');
      });
      this.isVisible = !this.isVisible;
    },
    hidePanel() {
      this.isVisible = false;
    },
    getAllSnippets() {
      axios
        .get("/get_all_snippets/")
        .then((resp) => {
          snippetsStore.$patch({
            files: resp.data.files,
            folders: resp.data.folders,
          });
        })
        .catch((error) => {
          handleError(error);
        });
    },
    setupEvents() {
      emitter.on("toggle_snippet_panel", () => {
        this.togglePanel();
      });

      emitter.on("hide_snippet_panel", () => {
        this.hidePanel();
      });

      emitter.on("get_all_snippets", () => {
        this.getAllSnippets();
      });
      emitter.on(
        "save_snippet_text_confirm",
        ({ saveObject, text, callback }) => {
          this.saveSnippetTextConfirm(saveObject, text, callback);
        }
      );
    },
    clearEvents() {
      emitter.all.delete("toggle_snippet_panel");
      emitter.all.delete("get_all_snippets");
      emitter.all.delete("save_snippet_text_confirm");
      emitter.all.delete("hide_snippet_panel");
    },
    saveSnippetTextConfirm(save_object, text, callback) {
      axios
        .post("/save_snippet_text/", {
          id: save_object.id,
          parent_id: save_object.parent,
          name: save_object.name,
          text: text,
        })
        .then((resp) => {
          emitter.emit("refresh_snippet_tree", resp.data.parent);

          if (callback != null) {
            const snippetObject = {
              text: text, ...resp.data
            };

            callback(snippetObject);
          }

          showToast("success", "Snippet saved.");

          this.getAllSnippets();
        })
        .catch((error) => {
          handleError(error);
        });
    },
  },
};
</script>
