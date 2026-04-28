<template>
  <div>
    <div class="container-fluid">
      <button
        data-testid="refresh-all-widgets-button"
        class="btn btn-primary btn-sm my-2 me-2"
        @click="refreshWidgets"
      >
        <i class="fas fa-sync-alt me-2"></i>
        Refresh All
      </button>
      <button
        class="btn btn-primary btn-sm my-2"
        @click="showMonitoringWidgetsList"
      >
        Manage Widgets
      </button>

      <div class="monitoring-widgets row">
        <MonitoringWidget
          v-for="widget in visibleSortedWidgets"
          :key="widget.saved_id"
          :monitoring-widget="widget"
          :workspace-id="workspaceId"
          :tab-id="tabId"
          :database-index="databaseIndex"
          :refresh-widget="refreshWidget"
          @widget-refreshed="waitForAllAndRefreshCounter"
          @toggle-widget="toggleWidget"
          @interval-updated="updateWidgetInterval"
        />
      </div>
    </div>
    <Teleport to="body">
      <MonitoringWidgetsModal
        :widgets="sortedWidgets"
        :workspace-id="workspaceId"
        :tab-id="tabId"
        :database-index="databaseIndex"
        :widgets-modal-visible="monitoringModalVisible"
        @modal-hide="monitoringModalVisible = false"
        @toggle-widget="toggleWidget"
        @move-widget-up="moveWidgetUp"
        @move-widget-down="moveWidgetDown"
        @delete-widget="deleteWidget"
        @add-widget="addWidget"
        @update-widget="updateWidget"
      />
    </Teleport>
  </div>
</template>

<script>
import axios from "axios";
import MonitoringWidget from "./MonitoringWidget.vue";
import MonitoringWidgetsModal from "./MonitoringWidgetsModal.vue";
import { handleError } from "../logging/utils";

export default {
  name: "MonitoringDashboard",
  components: {
    MonitoringWidget,
    MonitoringWidgetsModal,
  },
  props: {
    workspaceId: String,
    tabId: String,
    databaseIndex: Number,
  },
  data() {
    return {
      widgets: [],
      refreshWidget: false,
      counter: 0,
      monitoringModalVisible: false,
    };
  },
  mounted() {
    this.getMonitoringWidgets();
  },
  methods: {
    getMonitoringWidgets() {
      axios
        .post("/monitoring-widgets", {
          workspace_id: this.workspaceId,
          database_index: this.databaseIndex,
        })
        .then((resp) => {
          this.widgets = resp.data.widgets;
        })
        .catch((error) => {
          handleError(error);
        });
    },
    refreshWidgets() {
      if (this.visibleSortedWidgets.length > 0) this.refreshWidget = true;
    },
    waitForAllAndRefreshCounter() {
      this.counter++;
      if (this.counter === this.visibleSortedWidgets.length) {
        this.refreshWidget = false;
        this.counter = 0;
      }
    },
    updateWidgetInterval({ saved_id, interval }) {
      let widget = this.widgets.find((widget) => widget.saved_id === saved_id);
      widget.interval = interval;
    },
    showMonitoringWidgetsList() {
      this.monitoringModalVisible = true;
    },
    toggleWidget(widget, visible) {
      axios
        .patch(`/monitoring-widgets/${widget.saved_id}`, {
          visible: visible,
        })
        .then(() => {
          widget.visible = visible;
        })
        .catch((error) => {
          handleError(error);
        });
    },
    moveWidgetUp(index) {
      // prevent moving newly added column above existing ones in "alter" mode
      if(index == 0) return;
      let widgetAbove = this.sortedWidgets[index-1]
      let widget = this.sortedWidgets[index]
      let posTmp = this.sortedWidgets[index].position
      widget.position = widgetAbove.position
      widgetAbove.position = posTmp
    },
    moveWidgetDown(index) {
      if(index == this.sortedWidgets.length-1) return;
      let widgetBelow = this.sortedWidgets[index+1]
      let widget = this.sortedWidgets[index]
      let posTmp = this.sortedWidgets[index].position
      widget.position = widgetBelow.position
      widgetBelow.position = posTmp
    },
    deleteWidget(widgetId) {
      let widgetIdx = this.widgets.findIndex(
        (w) => w.id === widgetId
      );
      if(widgetIdx !== -1) {
        this.widgets.splice(widgetIdx, 1)
      }
    },
    addWidget(widgetData) {
      this.widgets.push({
        id: widgetData.id,
        saved_id: widgetData.saved_id,
        title: widgetData.title,
        visible: widgetData.visible,
        position: widgetData.position,
        editable: widgetData.editable,
        type: widgetData.type,
        interval: widgetData.interval,
        plugin_name: '',
        widget_data: {}
      })
    },
    updateWidget(widgetData) {
      let widget = this.widgets.find((widget) => widget.id === widgetData.id);
      let newWidget = {...widget};
      newWidget.title = widgetData.title;
      newWidget.interval = widgetData.interval;
      newWidget.type = widgetData.type;
      this.deleteWidget(widget.id);
      this.$nextTick(() => {
        this.addWidget(newWidget);
      })
    }
  },
  computed: {
    visibleSortedWidgets() {
      return this.widgets.filter(widget => widget.visible).sort((a, b) => (a.position > b.position) ? 1 : -1)
    },
    sortedWidgets() {
      return this.widgets.sort((a, b) => (a.position > b.position) ? 1 : -1)
    }
  }
};
</script>

<style scoped>
.monitoring-widgets {
  overflow: auto;
  height: 90vh;
}
</style>
