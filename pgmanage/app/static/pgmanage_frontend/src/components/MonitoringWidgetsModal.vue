<template>
  <div
    ref="monitoringWidgetsModal"
    class="modal fade"
    tabindex="-1"
    role="dialog"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header align-items-center">
          <h2 class="modal-title fw-bold">Monitoring Widgets</h2>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          >
          </button>
        </div>
        <div class="modal-body px-3">
          <div class="px-2" style="width: 100%; height: 400px; overflow: scroll">
            <div class="d-flex row fw-bold text-muted schema-editor__header g-0">
              <div class="col-1">
                <p class="h6">Show</p>
              </div>
              <div class="col d-flex justify-content-start ms-2">
                <p class="h6">Move</p>
              </div>
              <div class="col-5">
                <p class="h6">Title</p>
              </div>
              <div class="col-2">
                <p class="h6">Type</p>
              </div>
              <div class="col-1">
                <p class="h6">Refresh</p>
              </div>
              <div class="col d-flex justify-content-end pe-2">
                <p class="h6">Actions</p>
              </div>
            </div>

            <div
              v-for="(widget, index) in widgets" :key=index
              class="schema-editor__column d-flex row flex-nowrap form-group g-0 flex-shrink-0"
              >
              <div class="col-1 d-flex align-items-center">
                <div class="cell">
                  <div class="form-switch m-0">
                    <input
                      :checked="widget.visible"
                      @click="$emit('toggleWidget', widget, !widget.visible)"
                      type="checkbox"
                      class="form-check-input"
                      >
                    </div>
                </div>
              </div>

              <div class="col d-flex">
                <button
                  @click='$emit("moveWidgetUp", index)'
                  class="btn btn-icon btn-icon-secondary ps-2 pe-2" title="Move widget up" type="button">
                  <i class="fas fa-circle-up"></i>
                </button>

                <button
                  @click='$emit("moveWidgetDown", index)'
                  class="btn btn-icon btn-icon-secondary ps-2 pe-2" title="Move widget down" type="button">
                  <i class="fas fa-circle-down"></i>
                </button>
              </div>
              
              <div class="col-5 d-flex align-items-center">
                <div class="cell">{{ widget.title }}</div>
              </div>

              <div class="col-2 d-flex align-items-center">
                <div class="cell">{{ widget.type }}</div>
              </div>

              <div class="col-1 d-flex align-items-center">
                <div class="cell">{{ humanizeDuration(widget.interval) }}</div>
              </div>


              <div class="col d-flex me-1 justify-content-end">
                <button
                  v-if="widget.editable"
                  @click="editMonitoringWidget(widget.id)"
                  class="btn btn-icon btn-icon-secondary ps-2" title="Edit" type="button">
                  <i class="fas fa-edit"></i>
                </button>

                <button type="button"
                  v-if="widget.editable"
                  @click="deleteMonitorWidget(widget.id)"
                  class="btn btn-icon btn-icon-danger ps-2 pe-2" title="Remove">
                  <i class="fas fa-circle-xmark"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button
            @click="editMonitoringWidget()"
            class="btn btn-primary btn-sm"
          >
            New Widget
          </button>
        </div>
      </div>
    </div>
  </div>
  <MonitoringWidgetEditModal
    :workspace-id="workspaceId"
    :tab-id="tabId"
    :database-index="databaseIndex"
    :modal-visible="editModalVisible"
    :widget-id="editWidgetId"
    @modal-hide="onEditHide"
    @widget-created="onWidgetCreated"
    @widget-updated="onWidgetUpdated"
  />
</template>

<script>
import axios from "axios";
import MonitoringWidgetEditModal from "./MonitoringWidgetEditModal.vue";
import { messageModalStore } from "../stores/stores_initializer";
import { Modal } from "bootstrap";
import { handleError } from "../logging/utils";
import HumanizeDurationMixin from '../mixins/humanize_duration_mixin';

export default {
  name: "MonitoringWidgetsModal",
  components: {
    MonitoringWidgetEditModal,
  },
  props: {
    widgetsModalVisible: Boolean,
    workspaceId: String,
    tabId: String,
    databaseIndex: Number,
    widgets: Array,
  },
  mixins: [HumanizeDurationMixin],
  emits: ["modalHide", "toggleWidget", "moveWidgetUp", "moveWidgetDown", "deleteWidget", "addWidget", "updateWidget"],
  data() {
    return {
      table: null,
      editModalVisible: false,
      editWidgetId: null,
      modalInstance: null,
    };
  },
  mounted() {
    this.$refs.monitoringWidgetsModal.addEventListener("hide.bs.modal", () => {
      this.$emit("modalHide");
    });
  },
  watch: {
    widgetsModalVisible(newVal, oldVal) {
      if (newVal) {
        this.modalInstance = Modal.getOrCreateInstance(this.$refs.monitoringWidgetsModal)
        this.modalInstance.show();
      } else {
        if (!!this.table) this.table.destroy();
      }
    },
  },
  methods: {
    widgetEnabled(id) {
      return this.widgets.some(
        (widget) => widget.id === id
      )
    },
    deleteMonitorWidget(widgetId) {
      messageModalStore.showModal(
        "Are you sure you want to delete this monitor widget?",
        () => {
          axios
            .delete(`/monitoring-widgets/user-created/${widgetId}`)
            .then((resp) => {
              this.$emit("deleteWidget", widgetId)
            })
            .catch((error) => {
              handleError(error);
            });
        }
      );
    },
    editMonitoringWidget(widgetId = null) {
      this.modalInstance.hide();
      this.editModalVisible = true;
      this.editWidgetId = widgetId;
    },
    onEditHide() {
      this.editModalVisible = false;
      this.editWidgetId = null;
    },
    onWidgetCreated(widgetData) {
      this.$emit("addWidget", widgetData)
    },
    onWidgetUpdated(widgetData){
      this.$emit("updateWidget", widgetData);
    }
  },
};
</script>
