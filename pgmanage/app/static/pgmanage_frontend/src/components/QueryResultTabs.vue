<template>
  <div ref="resultDiv" :id="`query_result_tabs_container_${tabId}`" class="omnidb__query-result-tabs pe-2">
    <button :id="`bt_fullscreen_${tabId}`" style="position: absolute; top: 0.25rem; right: 0.5rem" type="button"
      class="btn btn-sm btn-icon btn-icon-primary pe-2" title='Fullscreen' @click="toggleFullScreen()">
      <i :class="inFullscreen ? 'fas fa-compress':'fas fa-expand'"></i>
    </button>

    <!-- DATA, MESSAGE, EXPLAIN tabs-->
    <div :id="`query_result_tabs_${tabId}`" class="h-100">
      <div class="omnidb__tab-menu ps-2">
        <div class="nav nav-tabs justi" role="tablist">
          <a ref="dataTab" class="omnidb__tab-menu__link nav-item nav-link active" :id="`nav_data_tab_${tabId}`"
          data-bs-toggle="tab" :data-bs-target="`#nav_data_${tabId}`" type="button" role="tab"
            :aria-controls="`nav_data_${tabId}`" aria-selected="true">
            <span class="omnidb__tab-menu__link-name">Data</span>
          </a>
            <a ref="messagesTab" class="omnidb__tab-menu__link nav-item nav-link" :id="`nav_messages_tab_${tabId}`"
            data-bs-toggle="tab" :data-bs-target="`#nav_messages_${tabId}`" type="button" role="tab"
              :aria-controls="`nav_messages_${tabId}`" aria-selected="true">
              <span class="omnidb__tab-menu__link-name">
                Messages
                <span v-if="noticesCount" class="badge rounded-pill badge-primary">{{ noticesCount }}</span>
              </span>
            </a>
            <a v-if="postgresqlDialect" ref="explainTab" class="nav-item nav-link omnidb__tab-menu__link" :id="`nav_explain_tab_${tabId}`"
            data-bs-toggle="tab" :data-bs-target="`#nav_explain_${tabId}`" type="button" role="tab"
              :aria-controls="`nav_explain_${tabId}`" aria-selected="false">
              <span class="omnidb__tab-menu__link-name"> Explain </span>
            </a>
        </div>
      </div>

      <div ref="tabContent" class="tab-content pb-1"> <!-- pb-1 fixes intermitent bug with handleResize-->
        <div class="tab-pane active pt-2" :id="`nav_data_${tabId}`" role="tabpanel"
          :aria-labelledby="`nav_data_tab_${tabId}`">
          <div class="result-div">
            <template v-if="exportFileName && exportDownloadName">
              The file is ready.
              <a class="text-info" :href="exportFileName" :download="exportDownloadName">Save</a>
            </template>
            <div v-show="showTable" ref="tabulator" class="tabulator-custom"></div>
          </div>
        </div>
          <div class="tab-pane" :id="`nav_messages_${tabId}`" role="tabpanel"
            :aria-labelledby="`nav_messages_tab_${tabId}`">
            <div class="messages__wrap p-2">
              <div class="result-div">
                <div class="query_info">
                {{ queryInfoText }}
              </div>
            <div v-if="errorMessage">
              <span
              class="badge rounder-pill"
              :class="noticeClass('EXCEPTION')"
              >Exception</span>
              <pre>{{ errorMessage }}</pre>
            </div>
              <div v-for="notice in notices">
                <span
                  class="badge rounded-pill"
                  :class="noticeClass(notice[0])"
                  >{{ notice[0] }}</span>
                <pre>{{ notice[1] }}</pre>
              </div>
              </div>
            </div>
          </div>
          <ExplainTabContent v-if="postgresqlDialect" :tab-id="tabId" :query="query" :plan="plan" />
      </div>
    </div>
  </div>
</template>

<script>
import ExplainTabContent from "./ExplainTabContent.vue";
import { queryModes, tabStatusMap } from "../constants";
import { emitter } from "../emitter";
import { TabulatorFull as Tabulator } from "tabulator-tables";
import { settingsStore, tabsStore, cellDataModalStore } from "../stores/stores_initializer";
import escape from 'lodash/escape';
import isNil from 'lodash/isNil';
import isEmpty from 'lodash/isEmpty';
import mean from 'lodash/mean';
import last from 'lodash/last';
import { Tab } from "bootstrap";
import dialects from './dialect-data';
import ClipboardMixin from "../mixins/table_clipboard_copy_mixin";
import ContextMenuMixin from "../mixins/tabulator_context_menu_mixin";

export default {
  components: {
    ExplainTabContent,
  },
  mixins: [ClipboardMixin, ContextMenuMixin],
  props: {
    tabId: String,
    workspaceId: String,
    editorContent: String,
    dialect: String,
    tabStatus: Number,
    resizeDiv: Boolean,
    blockSize: Number,
  },
  watch: {
    resizeDiv(newValue, oldValue) {
      if (newValue) {
        this.handleResize();
        if (this.tabulator) this.tabulator.redraw();
        this.$emit("resized");
      }
    },
  },
  emits: ["enableExplainButtons", "runExplain", "showFetchButtons", "resized"],
  data() {
    return {
      errorMessage: "",
      exportFileName: "",
      exportDownloadName: "",
      notices: [],
      queryInfoText: "",
      inFullscreen: false,
      customLayout: undefined,
      previousLayout: undefined,
      tableSettings: {
        data: [],
        placeholderHeaderFilter: "No Matching Data",
        autoResize: false,
        selectableRangeAutoFocus:false,
        selectableRange:1,
        selectableRangeColumns:true,
        selectableRangeRows:true,
        height: "100%",
        layout: "fitDataStretch",
        columnDefaults: {
          headerHozAlign: "left",
          headerSort: false,
          maxInitialWidth: 200,
        },
        clipboard: "copy",
        clipboardCopyRowRange: "range",
        clipboardCopyConfig: {
          columnHeaders: false, //do not include column headers in clipboard output
        },
      },
      query: "",
      plan: "",
      tabulator: null,
      heightSubtract: 200,
      colWidthArray: [],
      columns: [],
      colTypes: [],
      defaultColWidthArray: [],
    };
  },
  computed: {
    queryModes() {
      return queryModes;
    },
    postgresqlDialect() {
      return this.dialect === "postgresql";
    },
    noticesCount() {
      return this.notices.length;
    },
    showTable() {
      return !(
        (!!this.exportFileName && !!this.exportDownloadName) || !!this.errorMessage 
      );
    },
    resultTabHeight() {
      return `calc(100vh - ${this.heightSubtract}px)`;
    },
  },
  mounted() {
    this.handleResize();
    const DIALECT_MAP = {
        oracle: "oracledb",
        mariadb: "mysql",
        postgresql: "postgres",
    };
    let mappedDialect = DIALECT_MAP[this.dialect] || this.dialect;
    this.numericTypes = dialects[mappedDialect]?.numericTypes || [];

    if (this.dialect === "postgresql") {
      
      this.$refs.explainTab.addEventListener("shown.bs.tab", () => {
        this.$emit("enableExplainButtons");
        if (!(this.tabStatus === tabStatusMap.RUNNING))
          this.$emit("runExplain");
      });

      this.$refs.explainTab.addEventListener("hidden.bs.tab", () => {
        this.$emit("enableExplainButtons");
      });
    }

    window.addEventListener("resize", () => {
      if (
        tabsStore.selectedPrimaryTab?.metaData?.selectedTab?.id !== this.tabId
      )
        return;
      this.handleResize();
    });

    let tabulator = new Tabulator(this.$refs.tabulator, this.tableSettings);
    tabulator.on("tableBuilt", () => {
      this.tabulator = tabulator;
      document.querySelector(`#${this.tabId}_content .tabulator-range-overlay`).classList.add('invisible'); // hides cell range overlay on table initialization
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
              this.tabulator.redraw();
            });
          });
        });
      }
    });

    this.$refs.dataTab.addEventListener("shown.bs.tab", (event) => {
      this.tabulator.redraw();
    });
  },
  updated() {
    this.handleResize();
  },
  methods: {
    focus() {
      if (!this.tabulator?.getRows().length) return;
      this.tabulator.element.querySelector(".tabulator-tableholder")?.focus();
    },
    cellFormatter(cell, params, onRendered) {
      let cellVal = cell.getValue()
      if (!!cellVal && cellVal?.length > 1000) {
          let filtered = escape(cellVal.slice(0, 1000).toString().replace(/\n/g, ' ↲ '))
          return `${filtered}...`;
        }
      if (isNil(cellVal)) {
        return '<span class="text-muted">[null]</span>'
      }

      if(isEmpty(cellVal)) {
        return '<span class="text-muted">[empty]</span>'
      }

      let filtered = escape(cellVal.toString().replace(/\n/g, ' ↲ '))
      return filtered
    },
    renderResult(data, context) {
      this.clearData();
      if (data.error && context.cmd_type !== "explain") {
        this.errorMessage = data.data.message;
        Tab.getOrCreateInstance(this.$refs.messagesTab).show();
      } else {
        if (context.cmd_type === "explain") {
          this.showExplainTab(data);
        } else if (!!context.cmd_type && context.cmd_type.includes("export")) {
          this.showExport(data.data);
        } else {
          this.showDataTab(data.data, context);

          let mode = ["CREATE", "DROP", "ALTER"];
          if (!!data.data.status && isNaN(data.data.status)) {
            let status = data.data.status?.split(" ");
            if (mode.includes(status[0])) {
              let node_type = status[1]
                ? `${status[1].toLowerCase()}_list`
                : null;

              if (!!node_type) {
                emitter.emit(
                  `refreshTreeRecursive_${this.workspaceId}`,
                  node_type
                );
                emitter.emit("dbMetaRefresh", {
                  workspace_id: this.workspaceId,
                  database_name: context.tab.metaData.databaseName,
                  database_index: context.tab.metaData.databaseIndex,
                });
              }
            }
          }
        }
      }
    },
    showExplainTab(data) {
      Tab.getOrCreateInstance(this.$refs.explainTab).show()
      if (data?.error) {
        this.query = this.editorContent;
        this.plan = data.data.message;
        return;
      }

      // Adjusting data.
      let explain_text = data.data.data.join("\n");

      if (explain_text.length > 0) {
        this.query = this.editorContent;
        this.plan = explain_text;
      }
    },
    showExport(data) {
      Tab.getOrCreateInstance(this.$refs.dataTab).show()

      this.exportFileName = data.file_name;
      this.exportDownloadName = data.download_name;
    },
    showDataTab(data, context) {
      Tab.getOrCreateInstance(this.$refs.dataTab).show()

      if (data.notices.length) {
        const noticeSplitRegex = /^(\w+):\s*([\s\S]*)$/
        this.notices = data.notices.map((n) =>
          n.match(noticeSplitRegex).slice(1,3)
        );
      }

      if (
        data.data.length >= 50 && context.mode === this.queryModes.DATA_OPERATION ||
        data.data.length >= this.blockSize && context.mode === this.queryModes.FETCH_MORE
      ) {
        this.$emit("showFetchButtons", true);
      } else {
        this.$emit("showFetchButtons", false);
      }

      if (context.mode === this.queryModes.DATA_OPERATION) {
        this.showDataOperationResult(data);
      } else if (
        context.mode === this.queryModes.FETCH_MORE ||
        context.mode === this.queryModes.FETCH_ALL
      ) {
        this.fetchData(data);
      } else {
        this.queryInfoText = data.status;
      }
    },
    showDataOperationResult(data) {
      if (data.data.length === 0) {
        if (data.col_names.length === 0) {
          Tab.getOrCreateInstance(this.$refs.messagesTab).show()
          return this.queryInfoText = data.status ? data.status : "Done";
        }
      }
      this.updateTableData(data);
    },
    prepareColumns(colNames, colTypes) {
      this.colTypes = colTypes;
      this.columns = colNames.map((colName, idx) => {
        return colName === '?column?' ? `column-${idx}` : colName
      })
      let cellContextMenu = (e, cellComponent) => {
        const selectedRange = cellComponent.getTable().getRanges()[0]
        const isOneCellSelected =
          selectedRange.getBottomEdge() === selectedRange.getTopEdge() &&
          selectedRange.getRightEdge() === selectedRange.getLeftEdge();

        return [
          {
            label: '<i class="fas fa-copy"></i><span>Copy</span>',
            action: function (e, cell) {
              cell.getTable().copyToClipboard();
            },
          },
          {
            label: '<i class="fas fa-copy"></i><span>Copy as JSON</span>',
            action: () => {
              const data = last(this.tabulator.getRangesData());
              this.copyTableData(data, "json", this.columns);
            },
          },
          {
            label: '<i class="fas fa-copy"></i><span>Copy as CSV</span>',
            action: () => {
              const data = last(this.tabulator.getRangesData());
              this.copyTableData(data, "csv", this.columns);
            },
          },
          {
            label: '<i class="fas fa-copy"></i><span>Copy as Markdown</span>',
            action: () => {
              const data = last(this.tabulator.getRangesData());
              this.copyTableData(data, "markdown", this.columns);
            },
          },
          {
            label: '<i class="fas fa-edit"></i><span>View Content</span>',
            action: (e, cell) => {
              const colType = this.colTypes[cell.getColumn().getField()]
              cellDataModalStore.showModal(cell.getValue(), colType, true)
            },
            disabled: !isOneCellSelected
          },
        ];
      } 
      let columns = this.columns.map((col, idx) => {
        let formatTitle = function(col, idx) {
          if(colTypes?.length === 0 )
            return col
          return `${col}<br><span class='subscript'>${colTypes[idx]}</span>`
        }

        let colHozAlign = (function(idx) {
          return this.numericTypes.includes(colTypes?.[idx]) ? "right" : "left";
        }).bind(this)

        return {
          title: formatTitle(col, idx),
          field: idx.toString(),
          resizable: "header",
          editor: "input",
          editable: false,
          formatter: this.cellFormatter,
          contextMenu: cellContextMenu,
          hozAlign: colHozAlign(idx),
          headerDblClick: (e, column) => {
            if (
              column.getWidth() >
              this.tableSettings.columnDefaults.maxInitialWidth
            ) {
              column.setWidth(
                this.tableSettings.columnDefaults.maxInitialWidth
              );
            } else {
              column.setWidth(true);
            }
          },
          headerTooltip: 'double-click to maximize/minimize',
        };
      });

      let headerMenu = [
        {
          label:"Adaptive",
          action: () => {
            this.customLayout = 'adaptive'
            this.applyLayout()
          }
        },
        {
          label:"Compact",
          action: () => {
            this.customLayout = 'compact'
            this.applyLayout()
          }
        },{
          label:"Fit Content",
          action:() => {
            this.customLayout = 'fitcontent'
            this.applyLayout()
          }
        },{
          label:"Reset Layout",
          action:() => {
            this.customLayout = undefined;
            this.applyLayout();
          }
        },
      ]

      columns.unshift({
        formatter: "rownum",
        hozAlign: "center",
        minWidth: 55,
        frozen: true,
        headerMenu: headerMenu,
        headerMenuIcon:'<i class="actions-menu fa-solid fa-ellipsis-vertical p-2"></i>',
        headerTooltip: 'Layout'
      });
      return columns
    },
    updateTableData(data) {
      const columns = this.prepareColumns(data.col_names, data.col_types)
      this.tabulator.destroy()
      this.tableSettings.data = data.data
      this.tableSettings.columns = columns
      let tabulator = new Tabulator(this.$refs.tabulator, this.tableSettings);
      tabulator.on("renderStarted", () => {
        if (this.customLayout === undefined || this.colWidthArray.length === 0) return
        this.tabulator.getColumns().forEach((col, idx) => {
          if(idx > 0) {
            col.setWidth(this.colWidthArray[idx-1])
          }
        });
      })
      tabulator.on("tableBuilt", () => {
        this.tabulator = tabulator;
        if (this.defaultColWidthArray.length !== this.tabulator.getColumns().length) {
          this.defaultColWidthArray = this.tabulator.getColumns().map(col => col.getWidth());
        }
        if (this.customLayout !== undefined && this.colWidthArray.length !== 0) {
          
          this.tabulator.getColumns().forEach((col, idx) => {
            if(idx > 0) {
              col.setWidth(this.colWidthArray[idx-1])
            }
          });
        }
        this.addHeaderMenuOverlayElement();
      });

      tabulator.on(
        "cellDblClick",
        (e, cell) => {
          if (cell.getValue()) {
            const colType = this.colTypes[cell.getColumn().getField()];
            cellDataModalStore.showModal(cell.getValue(), colType, true);
          }
        }
      );
    },
     applyLayout() {
      this.colWidthArray = []

      this.tabulator.blockRedraw();

      this.tabulator.getColumns().forEach((col, idx) => {
        if(idx > 0) {
          if(this.customLayout == 'adaptive') {
            let widths = col.getCells().map((cell) => {return cell.getElement().scrollWidth}).filter((el) => el > 0)
            col.setWidth(mean(widths))
            this.colWidthArray.push(mean(widths))
          }

          if(this.customLayout == 'compact') {
            col.setWidth(100);
            this.colWidthArray.push(100)
          }

          if(this.customLayout == 'fitcontent') {
            col.setWidth(true);
            this.colWidthArray.push(true)
          }

          if(this.customLayout === undefined) {
            col.setWidth(this.defaultColWidthArray[idx]);
          }
        }
      });

      this.tabulator.restoreRedraw();
    },
    fetchData(data) {
      let initialData = this.tabulator.getData();
      const allData = [...initialData, ...data.data]
      let rowsToAppend = data.data.length

      // destroy and recreate tabulator instance if there is a lot of data to append
      if(rowsToAppend > 1000) {
        const scrollTop = this.tabulator.rowManager.scrollTop
        const scrollLeft = this.tabulator.rowManager.scrollLeft
        this.tableSettings.data = allData;
        this.tableSettings.columns = this.prepareColumns(data.col_names, data.col_types)

        this.tabulator.destroy()
        let tabulator = new Tabulator(this.$refs.tabulator, this.tableSettings);
        tabulator.on("tableBuilt", () => {
          this.tabulator = tabulator;
          this.applyLayout();
          this.tabulator.rowManager.element.scrollTop = scrollTop;
          this.tabulator.rowManager.scrollLeft = scrollLeft;
          this.addHeaderMenuOverlayElement();
        });

        tabulator.on(
          "cellDblClick",
          (e, cell) => {
            if (cell.getValue()) {
              const colType = this.colTypes[cell.getColumn().getField()];
              cellDataModalStore.showModal(cell.getValue(), colType, true);
            }
          }
        );
      } else {
        this.tabulator.addData(data.data);
      }


    },
    clearData() {
      this.notices = [];
      this.queryInfoText = "";
      this.exportDownloadName = "";
      this.exportFileName = "";
      this.errorMessage = "";
    },
    toggleFullScreen() {
      this.$refs.resultDiv.classList.toggle("omnidb__panel-view--full");
      this.handleResize();

      this.inFullscreen = !this.inFullscreen

      if(this.inFullscreen) {
        this.previousLayout = this.customLayout
        this.customLayout = 'adaptive'
      } else {
        this.customLayout = this.previousLayout
      }

      this.applyLayout()
    },
    handleResize() {
      if (this.$refs?.tabContent === null) return;

      this.heightSubtract = this.$refs.tabContent.getBoundingClientRect().top;
    },
    addHeaderMenuOverlayElement() {
      const targetElement = document.querySelector(`#${this.tabId}_content .tabulator-frozen-left .tabulator-header-popup-button`)

      const overlay = document.createElement("div");
      overlay.className =  "position-absolute w-100 h-100";
      overlay.style.zIndex = "1000"; 
      overlay.style.cursor = "pointer"
      overlay.style.backgroundColor = "rgba(0, 0, 0, 0)";

      targetElement.appendChild(overlay)

      targetElement.addEventListener("mousedown", (e) => {
        const { clientX, clientY } = e;

        const clickEvent = new MouseEvent("click", {
          bubbles: true,
          cancelable: true,
          clientX: clientX,
          clientY: clientY,
        });

        const targetElement = document.querySelector(`#${this.tabId}_content .tabulator-frozen-left .actions-menu`)
        
        e.stopPropagation();
        e.preventDefault();

        targetElement.dispatchEvent(clickEvent);
      });
    },
    noticeClass(notice_level){
      const NOTICE_MAP = {
        'NOTICE': 'badge-primary',
        'INFO': 'badge-secondary',
        'LOG': 'badge-secondary',
        'WARNING': 'badge-warning',
        'EXCEPTION': 'badge-danger',
        'ERROR': 'badge-danger',
      }
      return NOTICE_MAP[notice_level] || 'badge-secondary';
    }
  },
};
</script>

<style scoped>
.tab-content,
.messages__wrap {
  height: v-bind(resultTabHeight);
}

.tab-pane,
.result-div {
  height: 100%;
}

.result-div {
  overflow: auto;
}
</style>
