<template>
  <div
    id="commands-history-modal"
    class="modal fade"
    ref="historyModal"
    tabindex="-1"
    role="dialog"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-xl" role="document">
      <div class="modal-content">
        <div class="modal-header align-items-center">
          <h2 class="modal-title fw-bold">{{ tabType }} commands history</h2>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <div class="row">
              <div class="form-group col-6 col-lg-3">
                <p class="fw-bold mb-2">Select a daterange:</p>
                <input
                  v-model="startedFrom"
                  type="text"
                  class="form-control form-control-sm d-none"
                  placeholder="Start Time"
                />
                <input
                  v-model="startedTo"
                  type="text"
                  class="form-control form-control-sm d-none"
                  placeholder="End Time"
                />
                <button
                  ref="timeRange"
                  type="button"
                  class="btn btn-outline-primary mw-100 d-flex align-items-center"
                >
                  <i class="far fa-calendar-alt"></i>
                  <span class="mx-1 clipped-text">{{ timeRangeLabel }}</span
                  ><i class="fa fa-caret-down"></i>
                </button>
              </div>

              <div class="form-group col-6 col-lg-2">
                <label class="fw-bold mb-2">Filter by database:</label>
                <select
                  v-model="databaseFilter"
                  @change="getCommandsHistory(true)"
                  class="form-select"
                  placeholder="Filter database"
                >
                  <option value="" selected>All Databases</option>
                  <option
                    v-for="(name, index) in databaseNames"
                    :key="index"
                    :value="name"
                  >
                    {{ name }}
                  </option>
                </select>
              </div>

              <div
                class="form-group col-12 col-lg-7 d-flex justify-content-lg-end align-items-end"
              >
                <div class="flex-grow-1">
                  <label class="fw-bold mb-2">Command contains:</label>
                  <input
                    v-model="commandContains"
                    @change="getCommandsHistory(true)"
                    type="text"
                    class="form-control"
                  />
                </div>

                <button
                  class="bt_execute btn btn-primary ms-1"
                  title="Refresh"
                  @click="getCommandsHistory(true)"
                >
                  <i class="fas fa-sync-alt me-1"></i>
                  Refresh
                </button>
                <ConfirmableButton
                  :confirm-text="`Confirm Clear?`"
                  :callbackFunc="clearCommandsHistory"
                  class="btn btn-danger ms-1"
                >
                  <i class="fas fa-broom me-1"></i>
                  Clear List
                </ConfirmableButton>
              </div>
            </div>
          </div>

          <div ref="daterangePicker" class="position-relative"></div>

          <div class="pagination d-flex align-items-center mb-3">
            <button class="pagination__btn me-2" @click="getFirstPage()">
              First
            </button>
            <button class="pagination__btn mx-2" @click="getPreviousPage()">
              <i class="fa-solid fa-arrow-left"></i>
              Previous
            </button>
            <div class="pagination__pages mx-3">
              <span>{{ currentPage }}</span>
              /
              <span>{{ pages }}</span>
            </div>

            <button class="pagination__btn mx-2" @click="getNextPage()">
              Next
              <i class="fa-solid fa-arrow-right"></i>
            </button>

            <button class="pagination__btn ms-2" @click="getLastPage()">
              Last
            </button>
          </div>

          <div
            id="commands_history_table"
            class="tabulator-custom"
            style="height: calc(100vh - 20rem)"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import moment from "moment";
import { TabulatorFull as Tabulator } from "tabulator-tables";
import { emitter } from "../emitter";
import ConfirmableButton from "./ConfirmableButton.vue";
import {
  cellDataModalStore,
  commandsHistoryStore,
} from "../stores/stores_initializer.js";
import { Modal } from "bootstrap";
import { handleError } from "../logging/utils.js";

export default {
  name: "CommandsHistoryModal",
  components: {
    ConfirmableButton,
  },
  data() {
    return {
      currentPage: 1,
      pages: 1,
      startedFrom: moment().subtract(6, "hour").toISOString(),
      startedTo: moment().toISOString(),
      commandContains: "",
      timeRangeLabel: "Last 6 Hours",
      databaseNames: [],
      databaseFilter: "",
      modalInstance: null,
      table: null,
    };
  },
  computed: {
    tabId() {
      return commandsHistoryStore.tabId;
    },
    tabType() {
      return commandsHistoryStore.tabType;
    },
    databaseIndex() {
      return commandsHistoryStore.databaseIndex;
    },
    defaultColumns() {
      if (this.tabType === "Query") {
        return [
          {
            title: "Start",
            field: "start_time",
          },
          {
            title: "End",
            field: "end_time",
          },
          {
            title: "Duration",
            field: "duration",
          },
          {
            title: "Status",
            field: "status",
            hozAlign: "center",
            formatter: function (cell, formatterParams, onRendered) {
              if (cell.getValue() === "success") {
                return "<i title='Success' class='fas fa-check text-success'></i>";
              } else {
                return "<i title='Error' class='fas fa-exclamation-circle text-danger'></i>";
              }
            },
          },
          {
            title: "Database",
            field: "database",
          },
          {
            title: "Command",
            field: "snippet",
            tooltip: "Double-click to copy this command to editor",
            cellDblClick: (e, cell) => {
              emitter.emit(`${this.tabId}_copy_to_editor`, cell.getValue());
              this.modalInstance.hide();
            },
            contextMenu: [
              {
                label: '<i class="fas fa-bolt"></i><span>Copy Content To Query Tab</span>',
                action: (e, cell) => {
                  emitter.emit(`${this.tabId}_copy_to_editor`, cell.getValue());
                  this.modalInstance.hide();
                },
              },
            ],
          },
        ];
      }
      return [
        {
          title: "Date",
          field: "start_time",
        },
        {
          title: "Database",
          field: "database",
        },
        {
          title: "Command",
          field: "snippet",
          tooltip: "Double-click to copy this command to editor",
          cellDblClick: (e, cell) => {
            emitter.emit(`${this.tabId}_copy_to_editor`, cell.getValue());
            this.modalInstance.hide();
          },
          contextMenu: [
            {
              label: '<i class="fas fa-copy"></i><span>Copy</span>',
              action: (e, cell) => {
                this.table.selectRow(cell.getRow());
                this.table.copyToClipboard("selected");
              },
            },
            {
              label: '<i class="fas fa-bolt"></i><span>Copy Content To Console Tab</span>',
              action: (e, cell) => {
                emitter.emit(`${this.tabId}_copy_to_editor`, cell.getValue());
                this.modalInstance.hide();
              },
            },
            {
              label: '<i class="fas fa-edit"></i><span>View Content</span>',
              action: (e, cell) => {
                cellDataModalStore.showModal(cell.getValue(), "sql");
              },
            },
          ],
        },
      ];
    },
  },
  mounted() {
    commandsHistoryStore.$onAction((action) => {
      if (action.name === "showModal") {
        action.after(() => {
          if (this.table) this.table.destroy();
          this.setupTabulator();
          this.resetToDefault();
          this.showCommandsModal();
          this.getCommandsHistory(true);
        });
      }
    });

    this.$refs.historyModal.addEventListener("shown.bs.modal", () => {
      this.setupDateRangePicker();
    });

    this.$refs.historyModal.addEventListener("hidden.bs.modal", () => {
      commandsHistoryStore.reset();
      $(this.$refs.timeRange).data("daterangepicker").remove();
    });
  },
  methods: {
    setupDateRangePicker() {
      $(this.$refs.timeRange).daterangepicker(
        {
          timePicker: true,
          startDate: moment(this.startedFrom).format(),
          endDate: moment(this.startedTo).format(),
          parentEl: this.$refs.daterangePicker,
          previewUTC: true,
          locale: {
            format: moment.defaultFormat,
          },
          ranges: {
            "Last 6 Hours": [
              moment().subtract(6, "hour").format(),
              moment().format(),
            ],
            "Last 12 Hours": [
              moment().subtract(12, "hour").format(),
              moment().format(),
            ],
            "Last 24 Hours": [
              moment().subtract(24, "hour").format(),
              moment().format(),
            ],
            "Last 7 Days": [
              moment().subtract(7, "days").startOf("day").format(),
              moment().format(),
            ],
            "Last 30 Days": [
              moment().subtract(30, "days").startOf("day").format(),
              moment().format(),
            ],
            Yesterday: [
              moment().subtract(1, "days").startOf("day").format(),
              moment().subtract(1, "days").endOf("day").format(),
            ],
            "This Month": [
              moment().startOf("month").format(),
              moment().format(),
            ],
            "Last Month": [
              moment().subtract(1, "month").startOf("month").format(),
              moment().subtract(1, "month").endOf("month").format(),
            ],
          },
        },
        (start, end, label) => {
          this.startedFrom = moment(start).toISOString();

          // Update Button Labels
          if (label === "Custom Range") {
            this.timeRangeLabel = `${start.format(
              "MM/DD/YY hh:mm A"
            )}-${end.format("MM/DD/YY hh:mm A")}`;
          } else {
            this.timeRangeLabel = label;
          }

          if (
            label === "Custom Range" ||
            label === "Yesterday" ||
            label === "Last Month"
          ) {
            this.startedTo = moment(end).toISOString();
          } else {
            this.startedTo = null;
          }
          this.getCommandsHistory(true);
        }
      );
    },
    setupTabulator() {
      this.table = new Tabulator(`#commands_history_table`, {
        placeholder: "No Data Available",
        layout: "fitDataStretch",
        width: "100%",
        clipboard: "copy",
        clipboardCopyConfig: {
          columnHeaders: false, //do not include column headers in clipboard output
        },
        clipboardCopyFormatter: function (type, output) {
          if (type == "plain") {
            return output.split("\t").pop();
          }
          return output;
        },
        columnDefaults: {
          headerHozAlign: "left",
          headerSort: false,
        },
        columns: this.defaultColumns,
      });
    },
    getCommandsHistory(resetCurrentPage = false) {
      if (resetCurrentPage) this.currentPage = 1;

      axios
        .post("/get_commands_history/", {
          command_from: this.startedFrom,
          command_to: this.startedTo,
          command_contains: this.commandContains,
          command_type: this.tabType,
          current_page: this.currentPage,
          database_filter: this.databaseFilter,
          database_index: this.databaseIndex,
        })
        .then((resp) => {
          this.pages = resp.data.pages;
          this.databaseNames = resp.data.database_names;
          if (this.currentPage > resp.data.pages) this.currentPage = 1;

          resp.data.command_list.forEach((el) => {
            el.start_time = moment(el.start_time).format();
            if (el.end_time) el.end_time = moment(el.end_time).format();
          });
          this.table.setData(resp.data.command_list);
          this.table.redraw();
        })
        .catch((error) => {
          handleError(error);
        });
    },
    clearCommandsHistory() {
      axios
        .post("/clear_commands_history/", {
          command_from: this.startedFrom,
          command_to: this.startedTo,
          command_contains: this.commandContains,
          database_filter: this.databaseFilter,
          database_index: this.databaseIndex,
          command_type: this.tabType,
        })
        .then((resp) => {
          this.getCommandsHistory(true);
          if (this.tabType === "Console") {
            emitter.emit(`${this.tabId}_history_cleared`);
          }
        })
        .catch((error) => {
          handleError(error);
        });
    },
    getNextPage() {
      if (this.currentPage < this.pages) {
        this.currentPage += 1;
        this.getCommandsHistory();
      }
    },
    getPreviousPage() {
      if (this.currentPage > 1) {
        this.currentPage -= 1;
        this.getCommandsHistory();
      }
    },
    getFirstPage() {
      if (this.currentPage !== 1) {
        this.currentPage = 1;
        this.getCommandsHistory();
      }
    },
    getLastPage() {
      if (this.currentPage !== this.pages) {
        this.currentPage = this.pages;
        this.getCommandsHistory();
      }
    },
    showCommandsModal() {
      this.modalInstance = Modal.getOrCreateInstance(this.$refs.historyModal);
      this.modalInstance.show();
    },
    resetToDefault() {
      this.startedFrom = moment().subtract(6, "hour").toISOString();
      this.startedTo = null;
      this.timeRangeLabel = "Last 6 Hours";
      this.commandContains = "";
      this.databaseFilter = "";
    },
  },
};
</script>
