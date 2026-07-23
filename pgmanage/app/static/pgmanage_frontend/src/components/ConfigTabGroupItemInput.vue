<template>
  <div class="col-7">
    <div ref="settingInput" class="form-group mb-0">
      <div class="form-check form-switch" v-if="setting.vartype === 'bool'">
        <input class="form-check-input" type="checkbox" :id="`switch-${inputId}`" v-model="setting.setting" true-value="on" false-value="off"
          @change="changeSetting" :disabled="isReadOnly" />
        <label class="form-check-label" :for="`switch-${inputId}`"></label>
      </div>

      <select v-else-if="setting.vartype === 'enum'" class="form-select form-select-sm" :name="setting.name"
        v-model="setting.setting" @change="changeSetting" :disabled="isReadOnly">
        <option v-for="v in setting.enumvals" :value="v">{{ v }}</option>
      </select>
      <input v-else-if="setting.vartype === 'string'" data-html="true" type="text" :name="setting.name"
        :placeholder="setting.name" v-model="v$.setting.setting.$model" :id="inputId" :disabled="isReadOnly" :class="[
          'form-control',
          { 'is-invalid': v$.setting.setting.$invalid }
        ]" @input="changeSetting" />
      <input v-else data-html="true" :placeholder="setting.name" v-model="v$.setting.setting.$model" :id="inputId"
        :disabled="isReadOnly" @input="changeSetting" :class="[
          'form-control',
          { 'is-invalid': v$.setting.setting.$invalid }
        ]" />
      <div class="invalid-feedback">
        <a v-for="error of v$.setting.setting.$errors" :key="error.$uid">
          {{ error.$message }}
          <br />
        </a>
      </div>
    </div>
  </div>

  <div class="col-5 d-flex align-items-center">
    <button v-if="
      setting.setting != setting.boot_val &&
      setting.is_preset_option != 'True'
    " type="button" class="btn btn-link btn-sm" :id="buttonId" :title="`Reset to: ${setting.boot_val}`"
      ref="resetButton"
      @click.prevent="setDefault">
      <span class="fa fa-undo" aria-hidden="true"></span>
      Reset to default
    </button>
  </div>
</template>

<script>
import { useVuelidate } from '@vuelidate/core'
import { required, requiredUnless, minValue, maxValue, helpers } from '@vuelidate/validators'
import { tabsStore } from '../stores/stores_initializer';
import { Tooltip } from 'bootstrap';

export default {
  setup() {
    return {
      v$: useVuelidate({ $lazy: true })
    }
  },
  props: {
    initialSetting: {
      type: Object,
      required: true,
    },
    index: {
      type: Number,
      required: true,
    },
  },
  emits: ["settingChange"],
  data() {
    return {
      tooltipTitle: `<table class="text-start">
              <tr>
                <td>Type:</td>
                <td><b>${this.initialSetting.vartype}</b></td>
              </tr>
              <tr>
                <td>Unit:</td>
                <td><b>${this.initialSetting.unit}</b></td>
              </tr>
              <tr>
                <td>Minimum:</td>
                <td><b>${this.initialSetting.min_val}</b></td>
              </tr>
              <tr>
                <td>Maximum:</td>
                <td><b>${this.initialSetting.max_val}</b></td>
              </tr>
              </table>`,
      inputId: `${this.initialSetting.name}_${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}`,
      buttonId: `buttonResetDefault_${this.initialSetting.name}`,
    };
  },
  computed: {
    setting() {
      return Object.assign({}, this.initialSetting);
    },
    isReadOnly() {
      return this.initialSetting.is_preset_option === 'True';
    }
  },
  validations() {
    const localRules = {
      setting: {
        setting: { required: required }
      }
    }
    const filePermissionValidator = function(value) {
      const decVal = parseInt(value, 8)
      return decVal >= this.setting.min_val && decVal <= this.setting.max_val;
    }
    if (this.setting.vartype === 'string') {
      localRules.setting.setting.required = requiredUnless(() => !this.setting.boot_val)
    } else if (!!this.setting.unit) {
      localRules.setting.setting.customValidator = helpers.withMessage(
        `This field must be less than ${this.setting.max_val} or more than ${this.setting.min_val}`,
        this.validNumericSetting
      )
    } else {
      let may_be_octal = ["unix_socket_permissions", "log_file_mode", "data_directory_mode"]
      if (may_be_octal.includes(this.setting.name)) {
        const octalPattern = /^[0-7]{4}$/;
        if(octalPattern.test(this.setting.setting)) {
          localRules.setting.setting = {
            filePermissionValidator: filePermissionValidator.bind(this)
          }
        } else {
          localRules.setting.setting.minValue = minValue(this.setting.min_val)
          localRules.setting.setting.maxValue = maxValue(this.setting.max_val)
        }

        // return localRules
      } else {
        localRules.setting.setting.minValue = minValue(this.setting.min_val)
        localRules.setting.setting.maxValue = maxValue(this.setting.max_val)
      }

    }
    return localRules
  },
  mounted() {
    this.$nextTick(() => {
      const inputEl = document.getElementById(this.inputId)
      const buttonEl = document.getElementById(this.buttonId)

      if (inputEl) {
        new Tooltip(inputEl, {
          container: this.$refs.settingInput,
          sanitize: false,
          title: this.tooltipTitle,
          boundary: "window",
          html: true,
          delay: { show: 500, hide: 100 },
          trigger: 'hover'
        })
      }
      if (buttonEl) {
        new Tooltip(buttonEl, {
          container: this.$refs.resetButton,
          sanitize: false,
          boundary: "window",
          html: true,
          delay: { show: 500, hide: 100 },
          trigger: 'hover'
        })
      }
    });
  },
  methods: {
    changeSetting() {
      this.$emit("settingChange", {
        changedSetting: this.setting,
        index: this.index,
      });
    },
    setDefault() {
      this.setting.setting = this.setting.boot_val;
      this.changeSetting();
    },
    validNumericSetting(value) {
      let current_val = this.formatNumber(value, this.setting.unit)
      if (isNaN(current_val))
        return false
      if (current_val < this.setting.min_val || current_val > this.setting.max_val)
        return false
      return true
    },
    formatNumber(value, unit = null) {
      const units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "YB", "ZB"]
      const unit_regex_size = /(?<value>[0-9.]+)\s*(?<unit>[KMGBTPEYZ]?B)$/i
      let match_value_size = value.match(unit_regex_size)
      let factor = 1
      // if unit contains number, like '8kb'
      if (!!unit) {
        let match_unit = unit.match(unit_regex_size)
        if (!!match_unit) {
          factor = match_unit.groups.value
          unit = match_unit.groups.unit
        }
      }

      if (!!match_value_size) {
        let size_num = match_value_size.groups.value
        let size_unit = match_value_size.groups.unit
        let m = 0
        for (let u of units) {
          if (!!unit && unit.toLowerCase() === u.toLowerCase()) {
            m = 0
          }
          if (u.toLowerCase() === size_unit.toLowerCase()) {
            return (+size_num * (1024 ** m)) / factor
          } else {
            m += 1
          }
        }
      }

      // Valid time units are ms (milliseconds), s (seconds), min (minutes),
      // h (hours), and d (days
      const unit_regex_time = /(?<value>[0-9.]+)\s*(?<unit>us|ms|s|min|h|d)$/iy
      let match_value_time = value.match(unit_regex_time)
      let mult;
      switch (unit) {
        case "ms":
          mult = { "us": 0.001, "ms": 1, "s": 1000, "min": 60000, "h": 3600000, "d": 86400000 }
          break
        case "s":
          mult = { "ms": -1000, "s": 1, "min": 60, "h": 3600, "d": 86400 }
          break
        case "min":
          mult = { "ms": -60000, "s": -60, "min": 1, "h": 60, "d": 1440 }
          break
        case "h":
          mult = { "ms": -3600000, "s": -3600, "min": -60, "h": 1, "d": 24 }
          break
        case "d":
          mult = { "ms": -86400000, "s": -86400, "min": -1440, "h": -24, "d": 1 }
          break
        default:
          mult = { "ms": 1, "s": 1, "min": 1, "h": 1, "d": 1 }
      }

      if (!!match_value_time) {
        let time_num = match_value_time.groups.value
        let time_unit = match_value_time.groups.unit
        if (mult[time_unit] > 0)
          return time_num * mult[time_unit]
        else
          return time_num / Math.abs(mult[time_unit])
      }

      return +value
    },
  },
};
</script>