<template>
  <div
    class="omnidb__tab-menu--container omnidb__tab-menu--container--secondary omnidb__tab-menu--container--menu-shown"
    :class='tabColorLabelClass'
  >
    <div
      ref="tabsBar"
      class="omnidb__tab-menu border-bottom omnidb__tab-menu--secondary omnidb__theme-bg--menu-secondary"
    >
      <nav class="d-flex align-items-center justify-content-between">
        <div class="d-flex flex-nowrap scrollable-outer">
          <div
            ref="navTabs"
            class="nav nav-tabs text-nowrap flex-nowrap scrollable-inner"
            @wheel="handleNavWheel"
            @scrollend="updateScrollOptions"
          >
            <a
              :id="tab.id"
              :class="[
                'omnidb__tab-menu__link',
                'nav-item',
                'nav-link',
                { disabled: tab.disabled, active: tab.id == selectedTab.id },
              ]"
              role="tab"
              aria-selected="false"
              :aria-controls="`${tab.id}_content`"
              :href="`#${tab.id}_content`"
              :draggable="tab.isDraggable"
              @dragend="tab.dragEndFunction($event, tab)"
              @click.prevent.stop="clickHandler($event, tab)"
              @dblclick="tab.dblClickFunction && tab.dblClickFunction(tab)"
              @contextmenu="contextMenuHandler($event, tab)"
              v-for="tab in tabs"
            >
              <span class="omnidb__tab-menu__link-content">
                <span
                  v-if="tab.icon"
                  class="omnidb__menu__btn omnidb__tab-menu__link-icon"
                  v-html="tab.icon"
                >
                </span>
                <span class="omnidb__tab-menu__link-name">
                  <span>{{ tab.name }}</span>
                  <span
                    v-if="tab.metaData.mode !== 'add'"
                    :class="{ invisible: !tab.metaData.isLoading }"
                  >
                    <i class="tab-icon node-spin"></i>
                  </span>
                  <i
                    :class="[
                      'fas',
                      'fa-check-circle',
                      'tab-icon',
                      'icon-check',
                      { 'd-none': !tab.metaData.isReady },
                    ]"
                  ></i>
                </span>
              </span>

              <i
                v-if="tab.closable"
                class="fas fa-times tab-icon omnidb__tab-menu__link-close"
                @click.stop.prevent="tab.closeFunction($event, tab)"
              ></i>
            </a>
          </div>
          <button
            data-testid="add-tab-button"
            style="width: 40px"
            class="flex-shrink-0 btn btn-icon btn-icon-primary navigation-add"
            @click="addTab"
          >
            <i class="fas fa-plus"></i>
          </button>
        </div>

        <div class="navigation-actions d-flex flex-nowrap">
          <button
            class="btn btn-icon btn-icon-secondary me-3"
            :disabled="!canScrollLeft"
            @click="handleLeftScrollClick"
          >
            <i class="fas fa-lg fa-chevron-left"></i>
          </button>
          <button
            class="btn btn-icon btn-icon-secondary me-2"
            :disabled="!canScrollRight"
            @click="handleRightScrollClick"
          >
            <i class="fas fa-lg fa-chevron-right"></i>
          </button>
        </div>
      </nav>
    </div>

    <div
      class="tab-content omnidb__tab-content omnidb__tab-content--secondary"
    >
      <component
        v-for="tab in tabs"
        :key="tab.id"
        :is="tab.component"
        :id="`${tab.id}_content`"
        v-show="tab.id === selectedTab.id"
        v-bind="getCurrentProps(tab)"
        role="tabpanel"
      ></component>
    </div>
  </div>
</template>

<script>
import { defineAsyncComponent } from "vue";
import { tabsStore, connectionsStore, settingsStore } from "../stores/stores_initializer";
import { colorLabelMap } from "../constants";
import ContextMenu from "@imengyu/vue3-context-menu";
import SnippetTab from "./SnippetTab.vue";
import TabsUtils from "../mixins/tabs_utils_mixin";
import QueryTab from "./QueryTab.vue";
import SchemaEditorTab from "./SchemaEditorTab.vue";

export default {
  name: "DatabaseTabs",
  mixins: [TabsUtils],
  components: {
    ConsoleTab: defineAsyncComponent(() => import("./ConsoleTab.vue")),
    MonitoringDashboard: defineAsyncComponent(() =>
      import("./MonitoringDashboard.vue")
    ),
    ConfigTab: defineAsyncComponent(() => import("./ConfigTab.vue")),
    BackupTab: defineAsyncComponent(() => import("./BackupTab.vue")),
    RestoreTab: defineAsyncComponent(() => import("./RestoreTab.vue")),
    ERDTab: defineAsyncComponent(() => import("./ERDTab.vue")),
    DataEditorTab: defineAsyncComponent(() => import("./DataEditorTab.vue")),
    MonitoringTab: defineAsyncComponent(() => import("./MonitoringTab.vue")),
    SchemaEditorTab,
    QueryTab,
    SnippetTab,
  },
  props: {
    workspaceId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      canScrollLeft: false,
      canScrollRight: false,
    };
  },
  computed: {
    tabs() {
      return tabsStore.getSecondaryTabs(this.workspaceId);
    },
    selectedTab() {
      return tabsStore.getSelectedSecondaryTab(this.workspaceId);
    },
    isSnippetsPanel() {
      let primaryTab = tabsStore.getPrimaryTabById(this.workspaceId);
      return primaryTab?.name === "Snippets";
    },
    tabColorLabelClass() {
      let primaryTab = tabsStore.getPrimaryTabById(this.workspaceId);
      let connection = connectionsStore.getConnection(primaryTab?.metaData?.selectedDatabaseIndex);
      if(connection) {
        return colorLabelMap[connection.color_label].class || ''
      }
    }
  },
  updated() {
    this.$nextTick(() => {
      this.updateScrollOptions();
    });
  },
  mounted() {
    if (this.isSnippetsPanel) {
      tabsStore.createSnippetTab(this.workspaceId);
    }

    tabsStore.$onAction((action) => {
      if (action.name === "addTab") {
        action.after(() => {
          if (
            (tabsStore.selectedPrimaryTab.id === this.workspaceId &&
              this.tabs.includes(this.selectedTab)) ||
            this.isSnippetsPanel
          ) {
            this.$nextTick(() => {
              let lastTab = document.getElementById(this.selectedTab.id);
              if (!!lastTab) {
                setTimeout(() => {
                  lastTab.scrollIntoView({
                    inline: "end",
                    behavior: "smooth",
                  });
                }, 100);
              }
            });
          }
        });
      }
    });

    settingsStore.$onAction((action) => {
      if (action.name === "setFontSize") {
        action.after(() => {
          // wait for transition to complete, then grab the height
          setTimeout(() => {
            let newHeight = this.$refs.tabsBar.clientHeight;
            document.documentElement.style.setProperty('--database-tabs-height', `${newHeight}px`);
          }, 350);
        });
      }
    });
  },
  methods: {
    getCurrentProps(tab) {
      const componentsProps = {
        SnippetTab: {
          tabId: tab.id,
          snippet: tab.metaData.snippetObject,
        },
        ConsoleTab: {
          workspaceId: tab.parentId,
          tabId: tab.id,
          consoleHelp: tab?.metaData?.consoleHelp,
          databaseIndex: tab?.metaData?.databaseIndex,
          dialect: tab?.metaData?.dialect,
        },
        QueryTab: {
          workspaceId: tab.parentId,
          tabId: tab.id,
          databaseIndex: tab.metaData?.databaseIndex,
          dialect: tab.metaData?.dialect,
          databaseName: tab.metaData.databaseName,
          initTabDatabaseId: tab.metaData.initTabDatabaseId,
          initialQuery: tab.metaData.initialQuery,
        },
        MonitoringDashboard: {
          workspaceId: tab.parentId,
          tabId: tab.id,
          databaseIndex: tab?.metaData?.databaseIndex,
        },
        BackupTab: {
          workspaceId: tab.parentId,
          tabId: tab.id,
          databaseIndex: tab?.metaData?.databaseIndex,
          backupType: tab.metaData.backupType,
          treeNode: tab.metaData.treeNode,
        },
        RestoreTab: {
          workspaceId: tab.parentId,
          tabId: tab.id,
          databaseIndex: tab?.metaData?.databaseIndex,
          restoreType: tab.metaData.backupType,
          treeNode: tab.metaData.treeNode,
        },
        ERDTab: {
          tabId: tab.id,
          workspaceId: tab.parentId,
          databaseIndex: tab?.metaData?.databaseIndex,
          databaseName: tab?.metaData?.databaseName,
          schema: tab.metaData?.schema,
        },
        DataEditorTab: {
          workspaceId: tab.parentId,
          tabId: tab.id,
          databaseIndex: tab?.metaData?.databaseIndex,
          table: tab.metaData.table,
          schema: tab.metaData.schema,
          dialect: tab.metaData.dialect,
        },
        SchemaEditorTab: {
          workspaceId: tab.parentId,
          tabId: tab.id,
          databaseIndex: tab?.metaData?.databaseIndex,
          databaseName: tab?.metaData?.databaseName,
          mode: tab.metaData.editMode,
          schema: tab.metaData.schema,
          table: tab.metaData.table,
          dialect: tab.metaData.dialect,
          serverVersion: tab.metaData.serverVersion,
        },
        MonitoringTab: {
          tabId: tab.id,
          workspaceId: tab.parentId,
          databaseIndex: tab?.metaData?.databaseIndex,
          dialect: tab?.metaData?.dialect,
          query: tab.metaData.query,
        },
        ConfigTab: {
          databaseIndex: tab?.metaData?.databaseIndex,
          workspaceId: tab.parentId,
          tabId: tab.id,
        },
      };
      return componentsProps[tab.component];
    },
    addTab(event) {
      if (tabsStore.getPrimaryTabById(this.workspaceId).name === "Snippets") {
        tabsStore.createSnippetTab(this.workspaceId);
      } else {
        this.showMenuNewTab(event);
      }
    },
    showMenuNewTab(e) {
      let optionList = [
        {
          label: "Query Tab",
          icon: "fas fa-search",
          onClick: () => {
            let name = tabsStore.selectedPrimaryTab.metaData.selectedDatabase
              .replace("\\", "/")
              .split("/")
              .pop();
            tabsStore.createQueryTab(name);
          },
        },
        {
          label: "Console Tab",
          icon: "fas fa-terminal",
          onClick: () => {
            tabsStore.createConsoleTab();
          },
        },
      ];

      if (
        ["postgresql", "mysql", "mariadb"].includes(
          tabsStore.selectedPrimaryTab.metaData.selectedDBMS
        )
      ) {
        optionList.push({
          label: "Monitoring Dashboard",
          icon: "fas fa-chart-line",
          onClick: () => {
            tabsStore.createMonitoringDashboardTab();
          },
        });
      }

      if (tabsStore.selectedPrimaryTab.metaData.selectedDBMS === "postgresql") {
        optionList.push({
          label: "Backends",
          icon: "fas fa-tasks",
          onClick: () => {
            tabsStore.createMonitoringTab(
              "Backends",
              '/*pgmanage-dash*/ \
              select pid as "Pid",\
              datname as "Database",\
              usename as "User",\
              application_name as "Application",\
              client_addr as "Client Addr",\
              backend_start as "Backend Start",\
              xact_start as "Transaction Start",\
              state as "State",\
              wait_event as "Wait Event",\
              backend_type as "Backend Type",\
              query as "Query" from pg_stat_activity'
            );
          },
        });
      } else if (
        ["mysql", "mariadb"].includes(
          tabsStore.selectedPrimaryTab.metaData.selectedDBMS
        )
      ) {
        optionList.push({
          label: "Process List",
          icon: "fas fa-tasks",
          onClick: () => {
            tabsStore.createMonitoringTab(
              "Process List",
              "/*pgmanage-dash*/ select * from information_schema.processlist"
            );
          },
        });
      }
      else if (
        tabsStore.selectedPrimaryTab.metaData.selectedDBMS === 'oracle'
      ) {
        optionList.push({
          label: "Sessions",
          icon: "fas fa-tasks",
          onClick: () => {
            tabsStore.createMonitoringTab(
              "Sessions",
              `/*pgmanage-dash*/ 
              select sid,
              serial#,
              username,
              service_name,
              status,
              state,
              osuser,
              machine,
              program,
              module,
              action,
              type,
              logon_time 
              from v$session 
              WHERE username IS NOT NULL`
            );
          },
        });
      }

      ContextMenu.showContextMenu({
        theme: "pgmanage",
        x: e.x,
        y: e.y,
        zIndex: 1000,
        minWidth: 230,
        items: optionList,
      });
    },
    handleNavWheel(event) {
      event.deltaY > 0
        ? this.$refs.navTabs.scrollTo({
            left: this.$refs.navTabs.scrollLeft + 150,
            behavior: "smooth",
          })
        : this.$refs.navTabs.scrollTo({
            left: this.$refs.navTabs.scrollLeft - 150,
            behavior: "smooth",
          });
    },
    handleLeftScrollClick() {
      this.$refs.navTabs.scrollTo({
        left: this.$refs.navTabs.scrollLeft - 150,
        behavior: "smooth",
      });
    },
    handleRightScrollClick() {
      this.$refs.navTabs.scrollTo({
        left: this.$refs.navTabs.scrollLeft + 150,
        behavior: "smooth",
      });
    },
    updateScrollOptions() {
      if (this.$refs.navTabs.scrollWidth > this.$refs.navTabs.clientWidth) {
        this.canScrollLeft = this.$refs.navTabs.scrollLeft === 0 ? false : true;
        if (
          this.$refs.navTabs.scrollLeft + this.$refs.navTabs.clientWidth <
          this.$refs.navTabs.scrollWidth
        ) {
          this.canScrollRight = true;
        } else {
          this.canScrollRight = false;
        }
      } else {
        this.canScrollRight = false;
        this.canScrollLeft = false;
      }
    },
  },
};
</script>

<style scoped>
.scrollable-outer {
  overflow-y: hidden;
  max-width: calc(100% - 55px);
}

.scrollable-inner {
  overflow: scroll;
  overflow-y: hidden;
  scrollbar-width: none;
}

.scrollable-inner::-webkit-scrollbar {
  display: none;
}

.navigation-add {
  padding: 0.5rem 0;
}
</style>
