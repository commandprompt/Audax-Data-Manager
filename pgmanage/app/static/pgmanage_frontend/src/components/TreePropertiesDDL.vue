<template>
  <div class="omnidb__tree-tabs h-100 position-relative">
    <Transition :duration="100">
      <div v-if="showLoading" class="div_loading d-block" style="z-index: 1000">
        <div class="div_loading_cover"></div>
        <div class="div_loading_content">
          <div
            class="spinner-border text-primary"
            style="width: 4rem; height: 4rem"
            role="status"
          >
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      </div>
    </Transition>

    <button
      v-if="isVisible"
      data-testid="tree-tabs-hide-button"
      type="button"
      class="btn-icon omnidb__tree-tabs__toggler me-2"
      @click="$emit('hideTreeTabs')"
    >
      <i class="fas fa-chevron-down px-2"></i>
    </button>

    <button
      v-else
      data-testid="tree-tabs-show-button"
      type="button"
      class="btn-icon omnidb__tree-tabs__toggler me-2"
      @click="$emit('showTreeTabs')"
    >
      <i class="fas fa-chevron-up px-2"></i>
    </button>

    <div
      class="omnidb__tree-tabs__container omnidb__tab-menu--container h-100 position-relative"
    >
      <div class="omnidb__tab-menu border-bottom">
        <nav>
          <div class="nav nav-tabs">
            <a
              :id="`${workspaceId}_tree_properties_nav`"
              class="omnidb__tab-menu__link nav-item nav-link active"
              data-bs-toggle="tab"
              role="tab"
              aria-selected="true"
              ref="treePropertiesNav"
              :href="`#${workspaceId}_tree_properties`"
              :aria-controls="`${workspaceId}_tree_properties`"
              @click="$emit('showTreeTabs')"
              >Properties</a
            >
            <a
              :id="`${workspaceId}_tree_ddl_nav`"
              class="omnidb__tab-menu__link nav-item nav-link"
              data-bs-toggle="tab"
              role="tab"
              aria-selected="false"
              :href="`#${workspaceId}_tree_ddl`"
              :aria-controls="`${workspaceId}_tree_ddl`"
              @click="$emit('showTreeTabs')"
              >DDL</a
            >
          </div>
        </nav>
      </div>

      <div
        class="tab-content omnidb__tab-content h-100 pb-2"
        style="min-width: 100px"
      >
        <div
          class="tab-pane active"
          :id="`${workspaceId}_tree_properties`"
          role="tabpanel"
          :aria-labelledby="`${workspaceId}_tree_properties_nav`"
          style="height: 90%"
        >
          <div ref="tabulator" class="tabulator-custom simple pt-2"></div>
        </div>

        <div
          class="tab-pane h-100"
          :id="`${workspaceId}_tree_ddl`"
          role="tabpanel"
          :aria-labelledby="`${workspaceId}_tree_ddl_nav`"
        >
          <PreviewBox
            :database-technology="databaseTechnology"
            class="pb-3"
            style="height: 90%"
            :editor-text="ddlData"
            :show-label="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { TabulatorFull as Tabulator } from "tabulator-tables";
import PreviewBox from "./PreviewBox.vue";

export default {
  components: {
    PreviewBox,
  },
  props: {
    workspaceId: String,
    databaseTechnology: String,
    ddlData: String,
    propertiesData: Array,
    showLoading: {
      type: Boolean,
      default: false,
    },
    isVisible: Boolean,
  },
  emits: ["showTreeTabs", "hideTreeTabs"],
  data() {
    return {
      table: null,
      editor: null,
      tableBuilt: false,
    };
  },
  watch: {
    propertiesData(newValue, oldValue) {
      if (this.tableBuilt) this.table.setData(newValue);
    },
  },
  mounted() {
    this.setupTable();

    this.$refs.treePropertiesNav.addEventListener("shown.bs.tab", () => {
      this.table.redraw(true);
    });
  },
  methods: {
    setupTable() {
      this.table = new Tabulator(this.$refs.tabulator, {
        renderVertical: "basic",
        columnDefaults: {
          headerHozAlign: "left",
          headerSort: false,
        },
        height: "100%",
        data: [],
        columns: [
          {
            title: "property",
            field: "0",
            resizable: false,
          },
          {
            title: "value",
            field: "1",
            resizable: false,
          },
        ],
        layout: "fitColumns",
        selectableRows: false,
      });

      this.table.on("tableBuilt", () => {
        this.tableBuilt = true;
      });
    },
  },
};
</script>
