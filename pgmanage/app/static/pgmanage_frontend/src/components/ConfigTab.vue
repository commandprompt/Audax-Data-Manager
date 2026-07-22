<template>
<div class="p-2">
  <div class="row">
    <div class="form-group col">
      <form class="form" role="search" @submit.prevent>
        <label class="fw-bold mb-2" :for="`${tabId}_inputSearchSettings`">Search</label>
        <input v-model.trim="query_filter" class="form-control" :id="`${tabId}_inputSearchSettings`" name="filter"
          :disabled="v$.$invalid" placeholder="Find in settings" />
      </form>
    </div>

    <div class="form-group col-3">
      <label class="fw-bold mb-2" :for="`${tabId}_selectConf`">Category</label>
      <select class="form-select text-truncate pe-4" :id="`${tabId}_selectConfCat`" :disabled="!!query_filter || v$.$invalid" v-model="selected">
        <option v-for="(cat, index) in categories" :value="cat" :key="index">
          {{ cat }}
        </option>
      </select>
    </div>

    <div  class="col-4 d-flex">
      <div class="form-group">
        <label class="fw-bold mb-2" :for="`${tabId}_selectConf`">Config History</label>
        <select class="form-select text-truncate" :id="`${tabId}_selectConf`" v-model="selectedConf">
          <option disabled value="">Please select one</option>
          <option v-for="(config, index) in configHistory" :value="config" :key="index"
            :title="config.commit_comment">
          {{ truncateText(config, 50) }}
          </option>
        </select>
      </div>

      <div class="form-group d-flex align-items-end ps-1">
      <button class="btn btn-square btn-success me-1" :disabled="!selectedConf" @click="confirmConfig(e, true)">
        <i class="fa-solid fa-arrow-rotate-left"></i>
      </button>
      <ConfirmableButton class="btn btn-danger me-1" :disabled="!selectedConf" :callbackFunc="() => deleteOldConfig(selectedConf.id)">
        <i class="fa-solid fa-xmark"></i>
      </ConfirmableButton>
      <button type="submit" class="btn btn-success ms-3" :disabled="!hasUpdateValues || v$.$invalid"
        @click.prevent="confirmConfig">
        Apply
      </button>
    </div>
    </div>


  </div>

  <div v-if="!hasResult" class="row">
    <div class="col-12">
      <p>No results found...</p>
    </div>
  </div>

  <div v-else class="row">
    <div class="col-12">
      <div class="config-tabgroup">

        <div v-if="appliedSettings.restartPending" id="alert-configuration" class="alert alert-warning alert-dismissible" role="alert">
          <h2><i class="fa fa-warning fa-fw"></i>WARNING</h2>
          <p>Some changes are pending and PostgreSQL should be restarted:</p>
          <ul>
            <li v-for="change in appliedSettings.restartChanges" :key="change.name">
              {{ change.name }}
            </li>
          </ul>
        </div>

        <div v-if="hasAppliedValues">
          <div id="ok-configuration" class="alert alert-success alert-dismissible" role="alert">
            <button type="button" class="btn-close" aria-label="Close" @click="appliedSettings.data = ''">
            </button>
            <p class="text-center">The following changes have been applied:</p>
            <table class="table table-sm table-borderless">
              <thead>
                <tr>
                  <th width="30%">Name</th>
                  <th width="30%">Prev. value</th>
                  <th width="40%">New value</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="setting in appliedSettings.data" :key="setting.name">
                  <td>{{ setting.name }}</td>
                  <td>{{ setting.previous_setting }}</td>
                  <td>
                    <b>{{ setting.setting }}</b>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <ConfigTabGroup v-for="setting_group in currentResult" :initial-group="setting_group"
        :key="setting_group.category" @group-change="changeData" />
      </div>
    </div>
  </div>

  <!--Modal for commit messaging and returning result-->
  <div class="modal fade" :id="modalId" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header align-items-center">
          <h2 v-if="!modalRevertConfig" class="modal-title">Config Management</h2>
          <h2 v-else class="modal-title">Revert Configuration</h2>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p v-if="modalRevertConfig && !hasRevertValues">No changes to revert to.</p>
          <p v-else class="pb-2">The following changes will be applied:</p>
          <template v-if="(modalRevertConfig && hasRevertValues) || !modalRevertConfig">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th width="50%" class="border-top-0 pb-1">Name</th>
                  <th width="50%" class="border-top-0 pb-1">New value</th>
                </tr>
              </thead>
              <tbody>
  
                <template v-if="!modalRevertConfig">
                  <tr v-for="(setting_value, setting_name) in updateSettings" :key="setting_value">
                    <td>{{ setting_name }}</td>
                    <td>
                      <b>{{ setting_value.setting }}</b>
                    </td>
                  </tr>
                </template>
                <template v-else>
                  <tr v-for="(setting_value, setting_name) in configDiffData" :key="setting_value">
                    <td>{{ setting_name }}</td>
                    <td>
                      <b>{{ setting_value.setting }}</b>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
            
            <template v-if="hasUnapplicableRevertValues">
              <p class="pb-2">The following changes can not be applied due to database versions or extensions differences:</p>
              <table  class="table table-sm">
              <thead>
                <tr>
                  <th width="50%" class="border-top-0 pb-1">Name</th>
                  <th width="50%" class="border-top-0 pb-1">New value</th>
                </tr>
              </thead>
              <tbody>
                  <tr v-for="(setting_value, setting_name) in configUnapplicableDiffData" :key="setting_value">
                    <td>{{ setting_name }}</td>
                    <td>
                      <b>{{ setting_value.setting }}</b>
                    </td>
                  </tr>
              </tbody>
            </table>
            </template>
          </template>
          <div v-if="!modalRevertConfig" class="form-group">
            <label :for="`${tabId}_commit_message`" class="fw-bold mb-2">Commit Comment</label>
            <input v-model="commitComment" :id="`${tabId}_commit_message`" class="form-control"
              placeholder="Short description of your changes(optional)" />
          </div>
        </div>
        <div class="modal-footer">
          <button v-if="!modalRevertConfig" id="config_modal_button" type="button" class="btn btn-primary me-2"
            data-bs-dismiss="modal" @click="saveConfiguration">
            Save configuration
          </button>
          <button v-else id="config_modal_button" type="button" class="btn btn-primary me-2" data-bs-dismiss="modal"
            @click="revertConfig" :disabled="!hasRevertValues">
            Revert configuration
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import ConfigTabGroup from "./ConfigTabGroup.vue";
import { useVuelidate } from '@vuelidate/core'
import axios from 'axios'
import distance from 'jaro-winkler'
import moment from 'moment'
import { Modal } from "bootstrap";
import { tabsStore } from "../stores/stores_initializer";
import ConfirmableButton from "./ConfirmableButton.vue";
import { handleError } from "../logging/utils";
import { emitter } from "../emitter";

export default {
  name: "Config",
  components: {
    ConfigTabGroup,
    ConfirmableButton,
  },
  setup() {
    return {
      v$: useVuelidate()
    }
  },
  props: {
    workspaceId: String,
    databaseIndex: Number,
    tabId: String,
  },
  data() {
    return {
      data: "",
      updateSettings: {},
      selected: "",
      categories: "",
      query_filter: "",
      configHistory: "",
      selectedConf: "",
      commitComment: "",
      appliedSettings: {
        data: "",
        restartChanges: "",
        restartPending: "",
      },
      modalId: `config_modal_${this.workspaceId}_${Date.now()}`,
      modalRevertConfig: false,
      configDiffData: '',
      configUnapplicableDiffData: '',
      intervalId: ''
    };
  },
  computed: {
    currentResult() {
      if (!!this.data) {
        if (!this.query_filter) {
          return this.data.filter((item) => item.category === this.selected);
        } else {
          return this.data
            .map((element) => {
              const rows = element.rows.filter(
                (row) => {
                  let distance_name = distance(this.query_filter, row.name)
                  let distance_desc = distance(this.query_filter, row.desc)

                  return (
                    distance_desc > 0.7 ||
                    distance_name > 0.7 ||
                    row.name.toLowerCase().includes(this.query_filter.toLowerCase()) ||
                    row.desc.toLowerCase().includes(this.query_filter.toLowerCase())
                  )
                }
              );
              return { ...element, rows: rows };
            })
            .filter((element) => !!element.rows.length);
        }
      }
    },
    hasResult() {
      return !!this.currentResult?.length;
    },
    hasAppliedValues() {
      return !!this.appliedSettings.data.length;
    },
    hasUpdateValues() {
      return !!Object.keys(this.updateSettings).length;
    },
    hasRevertValues() {
      return !!Object.keys(this.configDiffData).length;
    },
    hasUnapplicableRevertValues() {
      return !!Object.keys(this.configUnapplicableDiffData).length;
    },
  },
  watch: {
    hasUpdateValues() {
      const tab = tabsStore.getSecondaryTabById(this.tabId, this.workspaceId)
      if (tab) {
        tab.metaData.hasUnsavedChanges = this.hasUpdateValues
      }
    },
  },
  mounted() {
    this.getCategories();
    this.getConfiguration();
    this.getConfigHistory();
    this.getConfigStatus();

    emitter.on(`${this.tabId}_focus_first_input`, () => {
      this.$el.querySelector('input:not([disabled]), select:not([disabled])')?.focus();
    });
  },
  unmounted() {
    emitter.all.delete(`${this.tabId}_focus_first_input`);
  },
  methods: {
    getConfiguration() {
      axios
        .post("/configuration/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
        })
        .then((response) => {
          this.data = response.data.settings;
        })
        .catch((error) => {
          this.data = "";
          handleError(error);
        });
    },
    getCategories() {
      axios
        .post("/configuration/categories/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
        })
        .then((response) => {
          this.categories = response.data.categories;
          this.selected = this.categories[0];
        })
        .catch((error) => {
          handleError(error);
        });
    },
    changeData(e) {
      const index = this.categories.indexOf(e.changedGroup.category);
      this.data[index] = e.changedGroup;
      if (e.changedSetting.setting !== e.changedSetting.reset_val)
        this.updateSettings[e.changedSetting.name] = e.changedSetting;
      else
        delete this.updateSettings[e.changedSetting.name]
    },
    saveConfiguration(event, newConfig = true) {
      axios
        .post("/save_configuration/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
          settings: this.updateSettings,
          commit_comment: this.commitComment,
          new_config: newConfig,
        })
        .then((response) => {
          this.updateSettings = {};
          this.commitComment = "";
          this.appliedSettings.data = response.data.settings;
          this.query_filter = "";
          this.getConfigHistory();
          this.getConfiguration();
          this.getConfigStatus();
        })
        .catch((error) => {
          handleError(error);
        });
    },
    getConfigHistory() {
      axios
        .post("/get_configuration_history/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
        })
        .then((response) => {
          this.configHistory = response.data.config_history.map((el) => {
            return {
              ...el,
              start_time: moment(el.start_time).format(),
            };
          });
        })
        .catch((error) => {
          handleError(error);
        });
    },
    confirmConfig(event, revert = false) {
      if (!revert) {
        this.modalRevertConfig = false
        Modal.getOrCreateInstance(`#${this.modalId}`).show()
      } else {
        this.getConfigurationDiffs()
        this.modalRevertConfig = true
        Modal.getOrCreateInstance(`#${this.modalId}`).show()
      }
    },
    revertConfig(event) {
      this.updateSettings = this.selectedConf.config_snapshot;
      this.saveConfiguration(event, false);
    },
    truncateText(input, max_length) {
      const text = `${input.start_time} - ${input.commit_comment}`;
      return text.length > max_length
        ? text.slice(0, max_length - 1) + "..."
        : text;
    },
    getConfigStatus() {
      axios
        .post("/configuration/status/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
        })
        .then((response) => {
          this.appliedSettings.restartPending = response.data.restart_pending;
          this.appliedSettings.restartChanges = response.data.restart_changes;
          if (this.appliedSettings.restartPending && !this.intervalId) {
            this.intervalId = setInterval(() => {
              this.getConfigStatus()
            }, 30000)
          }
          if (!this.appliedSettings.restartPending && !!this.intervalId) {
            clearInterval(this.intervalId)
            this.getConfiguration()
            this.getCategories()
          }
        })
        .catch((error) => {
          if (error?.response?.data?.data.includes("SSL connection has been closed unexpectedly"))
            this.getConfigStatus()
          else
          handleError(error);
        });
    },
    deleteOldConfig(config_id) {
      axios
        .delete(`/configuration/${config_id}/`)
        .then((resp) => {
          this.selectedConf = "";
          this.getConfigHistory();
        })
        .catch((error) => {
          handleError(error);
        });
    },
    getConfigurationDiffs() {
      axios
        .post("/configuration/", {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
          grouped: false,
          exclude_read_only: false
        })
        .then((response) => {
          this.configUnapplicableDiffData = {}
          let diff = Object.keys(this.selectedConf.config_snapshot).reduce((diff, key) => {
            if (!response.data.settings.hasOwnProperty(key)) {
              this.configUnapplicableDiffData[key] = this.selectedConf.config_snapshot[key]
              return diff
            }
            if (this.selectedConf.config_snapshot[key]['setting'] === response.data.settings[key]['setting']) return diff
            return {
              ...diff,
              [key]: this.selectedConf.config_snapshot[key]
            }
          }, {})
          this.configDiffData = diff
        })
        .catch((error) => {
          handleError(error);
        });
    }
  },
};
</script>

<style scoped>
  .config-tabgroup {
    height: calc(100vh - 120px);
    overflow-y: scroll;
  }
</style>
