<template>
<div class="welcome pt-3 overflow-auto">
    <div class='welcome__container'>
      <div class="welcome__header mt-1 mb-4">
        <p class='mb-0'>Welcome to</p>
        <div class="welcome__logo d-flex mt-3 mb-4">
          <img :src="logoUrl" alt="">
          <img id="gears" :src="gearsUrl">

        </div>
      </div>

      <div class="welcome__main">
        <div class='row'>
            <div class='col-4 welcome__col'>
              <div class="recent-conections">
                <h2 class="mb-3">Recent Connections</h2>
                <div class="recent-conections__list d-flex flex-column">
                  <div v-for="(connection, idx) in recentConnections" :key="idx" @click="selectConnection(connection.id)"
                    :class="colorLabelMap[connection.color_label].class || ''"
                    class="recent-conections__item">
                    <div class="recent-conections__item_wrap d-flex align-items-center m-0">
                        <div class="recent-conections__item_logo me-3">
                            <div :class="['icon', 'icon-' + connection.technology]"></div>
                        </div>
                        <div class="recent-conections__item_text d-flex flex-column">
                            <p class="recent-conections__item_title d-flex align-items-center">{{ connection.alias }}</p>
                            <span class="recent-conections__item_subtitle muted-text clipped-text">{{connectionSubtitle(connection)}}</span>
                            <span class="muted-text">{{ ago(connection.last_access_date) }}</span>
                        </div>
                    </div>
                  </div>
                  <div class='muted-text' v-if="!recentConnections.length">
                      You don't have any recent connections yet...
                  </div>
                </div>
              </div>

            </div>
            <div class='col-4 welcome__col'>
              <div class="hotkeys">
                <div class="mb-3">
                  <h2 class='d-inline-block me-2 mb-0'>Hotkeys</h2>
                  <a @click="showSettings" href="#" class="links__item">
                      <i class="fas fa-tools" title="Customize"></i>
                  </a>
                </div>
                <div class='hotkeys__list'>
                  <div v-for="(shortcut, idx) in shortcuts" :key="idx" class="mb-1 hotkeys__list_item hotkey">
                      <p class='hotkey__label'>{{shortcutLabel(shortcut)}}</p>
                      <span v-for="(button, idx) in shortcutKeyNames(shortcut)" :key="idx" class='hotkey__button me-2'>
                        {{button}}
                      </span>
                  </div>
                </div>
              </div>

            </div>
            <div class='col-4'>
              <div class="welcome__col links">
                <div class="links__group links__explore d-flex flex-column">
                  <h2 class="mb-3">Explore</h2>
                  <a href='#' @click="showTutorial" class='links__item' title="Get Started">
                    <i class="fa-solid fa-circle-info me-1"></i>
                    Get Started
                  </a>
                  <a href='https://pgmanage.readthedocs.io' target='_blank' class='links__item' title="Handbook">
                    <i class="fa-solid fa-book-bookmark me-1"></i>
                    PgManage Handbook
                  </a>
                </div>

                <div class="links__group links__involved d-flex flex-column">
                  <h2 class="mb-3">Get Involved</h2>
                  <a href='https://github.com/commandprompt/pgmanage/discussions/' target='_blank' class='links__item' title="Discuss">
                    <i class="fa-solid fa-comments me-1"></i>
                    Discuss
                  </a>
                  <a href='https://github.com/commandprompt/pgmanage/issues' target='_blank' class='links__item' title="Report a Bug">
                    <i class="fa-solid fa-bug me-1"></i>
                    Report a Bug
                  </a>
                </div>
              </div>
            </div>
        </div>
      </div>
    </div>
</div>
</template>

<script>
import moment from 'moment'
import { connectionsStore, settingsStore } from '../stores/stores_initializer'
import { colorLabelMap } from "../constants";
import { startTutorial } from '../tutorial'
import { endLoading } from "../ajax_control";
import { default_shortcuts } from '../shortcuts'
import gearsUrl from '../../src/assets/images/gears.svg'
import logoUrl from '../../src/assets/images/logo.svg'


export default {
  name: "WelcomeScreen",
  computed: {
    recentConnections() {
      return connectionsStore.connections
        .filter(conn => !!conn.last_access_date)
        .sort((a, b) => (moment(a.last_access_date) > moment(b.last_access_date)) ? -1 : 1)
        .slice(0, 5)
    },
    currentOS() {
      if (navigator.userAgent.indexOf("Win") != -1) return "windows"
      if (navigator.userAgent.indexOf("Mac") != -1) return  "macos"
      if (navigator.userAgent.indexOf("X11") != -1) return  "linux"
      if (navigator.userAgent.indexOf("Linux") != -1) return  "linux"
      return "Unknown OS"
    }
  },
  data() {
    return {
        shortcuts: [],
        gearsUrl: gearsUrl,
        logoUrl: logoUrl
    };
  },
  created() {
    this.colorLabelMap = colorLabelMap;
  },
  mounted() {
    this.loadShortcuts()
    this.setupEvents()
    endLoading()
  },
  methods: {
    ago(date) {
      return moment(date).fromNow()
    },
    connectionSubtitle(connection) {
      if(connection.conn_string) return connection.conn_string
      if(connection.technology === 'sqlite') return connection.service
      if(connection.technology === 'terminal') return `${connection.tunnel.server}:${connection.tunnel.port}`
      return `${connection.server}:${connection.port}/${connection.service}`
    },
    selectConnection(conn_id) {
      connectionsStore.selectConnection(conn_id);
    },
    loadShortcuts() {
      this.shortcuts = JSON.parse(JSON.stringify(settingsStore.shortcuts))
      let shortcut_keys = Object.keys(this.shortcuts)
      Object.keys(default_shortcuts).forEach((key) => {
        if(!shortcut_keys.includes(key)) {
          this.shortcuts[key] = Object.assign({}, default_shortcuts[key][this.currentOS])
        }
      })
        // merge missing shortcuts forom default_shortcuts
    },
    shortcutKeyNames(shortcut) {
      let keys = []
      if (shortcut.ctrl_pressed)
        keys.push('Ctrl')
      if (shortcut.shift_pressed)
        keys.push('Shift')
      if (shortcut.alt_pressed)
        keys.push('Alt')
      if (shortcut.meta_pressed)
        keys.push('Meta')
      if (shortcut.shortcut_key)
        keys.push(shortcut.shortcut_key)

      return keys
    },
    shortcutLabel(shortcut) {
      const LABEL_MAP = {
        'shortcut_run_query': 'Run Query',
        'shortcut_run_selection': 'Run Selection',
        'shortcut_cancel_query': 'Cancel Query',
        'shortcut_indent': 'Indent Code',
        'shortcut_find_replace': 'Find/Replace',
        'shortcut_new_inner_tab': 'New Tab',
        'shortcut_remove_inner_tab': 'Close Tab',
        'shortcut_left_inner_tab': 'Switch Tab Left',
        'shortcut_right_inner_tab': 'Switch Tab Right',
        'shortcut_autocomplete': 'Autocomplete',
        'shortcut_explain': 'Explain Query',
        'shortcut_explain_analyze': 'Analyze Query',
        'shortcut_quick_search': 'Quick Search',
        'shortcut_focus_database_tree': "Focus into database tree",
        'shortcut_focus_selected_tab': "Focus into selected tab",
        'shortcut_focus_data_grid': "Focus into data grid",
      };
      return LABEL_MAP[shortcut.shortcut_code] || 'unknown'
    },
    showSettings() {
      settingsStore.showModal()
    },
    showTutorial() {
      startTutorial('getting_started')
    },
    setupEvents() {
      settingsStore.$onAction((action) => {
        if ( action.name === 'saveSettings') {
          action.after(() => {
            this.loadShortcuts();
          })
        }
      })
    },
  },
};
</script>