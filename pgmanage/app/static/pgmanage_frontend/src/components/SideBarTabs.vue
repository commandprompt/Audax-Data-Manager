<template>
  <div
    class="omnidb__tab-menu--container omnidb__tab-menu--container--primary omnidb__tab-menu--container--menu-shown"
  >
    <div
      class="omnidb__tab-menu omnidb__tab-menu--primary omnidb__theme-bg--menu-primary d-flex flex-column justify-content-between"
    >
      <nav>
        <div class="nav nav-tabs">
          <a
            :id="tab.id"
            :class="[
              'omnidb__tab-menu__link',
              'nav-item',
              'nav-link',
              { disabled: tab.disabled, active: tab.id == selectedTab.id },
              tabColorLabelClass(tab)
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
            <span data-bs-toggle="tooltip" class="omnidb__tab-menu__link-content">
              <span
                v-if="tab.icon"
                class="omnidb__menu__btn omnidb__tab-menu__link-icon"
                v-html="tab.icon"
              >
              </span>
              <span
                v-if="tab.name.length > 11"
                class="omnidb__tab-menu__link-name"
                :data-content-start="`${splitStringInHalf(tab.name)[0]}`"
                :data-content-end="`${splitStringInHalf(tab.name)[1]}`"
              >
              </span>
              <span v-else class="omnidb__tab-menu__link-name">
                {{ tab.name }}
              </span>
            </span>
            <i
              v-if="tab.closable"
              class="fas tab-icon omnidb__tab-menu__link-close"
              :class="tab.metaData.mode == 'outer_terminal' ? 'fa-ellipsis-vertical' : 'fa-times'"
              @click.stop.prevent="tab.closeFunction($event, tab)"
            ></i>
          </a>
        </div>
      </nav>
      
      <div class="bottom-icons d-flex justify-content-evenly align-items-center">
        <span title='Smaller Font' class="bottom-icons__item"  @click="decreaseFontSize">
          <i class="fas fa-a fa-xs"></i>
        </span>
        <span title='Bigger Font' class="bottom-icons__item" @click="increaseFontSize">
          <i class="fas fa-a fa-lg"></i>
        </span>
        <span title='Change Theme' class="bottom-icons__item" @click="toggleTheme">
          <i :class="['fas fa-lg', themeIconClass]"></i>
        </span>
      </div>
    </div>

    <div class="tab-content omnidb__tab-content omnidb__tab-content--primary">
      <component
        v-for="tab in tabs"
        :key="tab.id"
        :is="tab.component"
        :id="`${tab.id}_content`"
        v-show="tab.id === selectedTab.id || tab.name === 'Snippets'"
        v-bind="getCurrentProps(tab)"
        role="tabpanel"
      ></component>
    </div>
  </div>
</template>

<script>
import { defineAsyncComponent } from "vue";
import { connectionsStore, settingsStore, tabsStore } from "../stores/stores_initializer";
import { colorLabelMap, minFontSize, maxFontSize } from "../constants";
import WelcomeScreen from "./WelcomeScreen.vue";
import SnippetPanel from "./SnippetPanel.vue";
import TabsUtils from "../mixins/tabs_utils_mixin.js";
import { splitStringInHalf } from "../utils.js";
import debounce from "lodash/debounce";

export default {
  name: "SideBarTabs",
  mixins: [TabsUtils],
  components: {
    WelcomeScreen,
    SnippetPanel,
    ConnectionTab: defineAsyncComponent(() => import("./ConnectionTab.vue")),
    TerminalTab: defineAsyncComponent(() => import("./TerminalTab.vue")),
  },
  computed: {
    tabs() {
      return tabsStore.tabs;
    },
    selectedTab() {
      return tabsStore.selectedPrimaryTab;
    },
    themeIconClass() {
      return settingsStore.theme === 'light' ? 'fa-sun' : 'fa-moon'
    }
  },
  mounted() {
    tabsStore.createConnectionsTab();
    tabsStore.createWelcomeTab();
    tabsStore.createSnippetPanel();
  },
  methods: {
    decreaseFontSize() {
      let fontSize = settingsStore.fontSize
      if(fontSize <= minFontSize)
        return
      
      settingsStore.setFontSize(--fontSize)
      this.saveSettings()
    },
    increaseFontSize () {
      let fontSize = settingsStore.fontSize
      if(fontSize >= maxFontSize)
        return
      
      settingsStore.setFontSize(++fontSize)
      this.saveSettings()
    },
    toggleTheme() {
      settingsStore.setTheme(settingsStore.theme == 'light' ? 'dark' : 'light');
      this.saveSettings()
    },
    saveSettings: debounce(() => settingsStore.saveSettings(true), 1000),
    getCurrentProps(tab) {
      const componentsProps = {
        ConnectionTab: {
          workspaceId: tab.id,
        },
        SnippetPanel: {
          workspaceId: tab.id,
        },
        TerminalTab: {
          workspaceId: tab.id,
          databaseIndex: tab?.metaData?.selectedDatabaseIndex,
        },
      };
      return componentsProps[tab.component];
    },
    tabColorLabelClass(tab) {
      let connection = connectionsStore.getConnection(tab.metaData?.selectedDatabaseIndex);
      if(connection) {
        return colorLabelMap[connection.color_label].class || ''
      }
    },
    splitStringInHalf,
  },
};
</script>

<style lang="scss" scoped>
span.omnidb__tab-menu__link-name {
  &::before,
  &::after {
    display: inline-block;
    max-width: 50%;
    overflow: hidden;
    white-space: pre;
  }

  &::before {
    content: attr(data-content-start);
    text-overflow: ellipsis;
  }

  &::after {
    content: attr(data-content-end);
    text-overflow: clip;
    direction: rtl;
  }
}
</style>
