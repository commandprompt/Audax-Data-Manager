<template>
  <div class="dropdown dropdown-searchable" v-if="options">

    <!-- Dropdown Input -->
    <input class="dropdown-searchable__input form-control pe-4"
      :name="name"
      @focus="showOptions()"
      @blur="exit()"
      @keyup.up="keyMonitor"
      @keyup.down="keyMonitor"
      @keyup.enter="onEnter"
      v-model="searchFilter"
      :disabled="disabled"
      :placeholder="placeholder"
      autocomplete="off"
      ref="input" />

    <!-- Dropdown Menu -->
    <div class="dropdown-searchable__content"
      v-show="optionsShown">
      <div
        ref="dropdownItems"
        :data-testid="`dropdown-searchable-item-${index}`"
        class="dropdown-searchable__content_item"
        @mousedown="toggleOption(option)"
        @mouseover="highlightedIndex = index"
        v-for="(option, index) in filteredOptions"
        :key="index"
        :class="{ 'selected': isSelected(option) , 'highlighted': index === highlightedIndex}"
        >
            {{  option }}
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'Dropdown',
    template: 'Dropdown',
    props: {
      name: {
        type: String,
        required: false,
        default: 'dropdown',
        note: 'Input name'
      },
      options: {
        type: Array,
        required: true,
        default: [],
        note: 'Options of dropdown. An array of options',
      },
      placeholder: {
        type: String,
        required: false,
        default: 'Please select an option',
        note: 'Placeholder of dropdown'
      },
      disabled: {
        type: Boolean,
        required: false,
        default: false,
        note: 'Disable the dropdown'
      },
      maxItem: {
        type: Number,
        required: false,
        default: 30,
        note: 'Max items showing'
      },
      modelValue: {
        default: null
      },
      multiSelect: {
        type: Boolean,
        default: false
      }
    },
    emits: ['update:modelValue', 'change'],
    data() {
      return {
        selected: this.multiSelect ? [] : null,
        optionsShown: false,
        searchFilter: this.modelValue,
        highlightedIndex: -1
      }
    },
    computed: {
      filteredOptions() {
        const filtered = [];
        // const regOption = new RegExp(this.searchFilter, 'ig');
        for (const option of this.options) {
          // if (this.searchFilter.length < 1 || option.name.match(regOption)){
          if (this.searchFilter?.length < 1 || option?.includes(this.searchFilter)){
            if (filtered.length < this.maxItem) filtered.push(option);
          }
        }
        return filtered;
      }
    },
    methods: {
      addOption(option) {
        if (this.multiSelect) {
          const index = this.selected.findIndex(selectedOption => selectedOption === option);
          if (index === -1) {
            this.selected.push(option);
          }
        }
      },
      toggleOption(option) {
        if (this.multiSelect) {
          const index = this.selected.findIndex(selectedOption => selectedOption === option);
          if (index === -1) {
            this.selected.push(option);
          } else {
            this.selected.splice(index, 1);
          }
          this.$emit('update:modelValue', this.selected);
        } else {
          this.selected = option;
          this.$emit('update:modelValue', this.selected);
          this.optionsShown = false;
          this.searchFilter = this.selected;
        }
        this.$emit('change', this.selected);
        this.highlightedIndex = -1;
      },
      showOptions(){
        if (!this.disabled) {
          // THIS resets onblur
          this.searchFilter = '';
          this.optionsShown = true;
          this.highlightedIndex = -1;
        }
      },
      exit() {
        if (!this.selected && this.searchFilter.length > 0) {
          this.selected = this.searchFilter
        } else {
          this.searchFilter = this.selected;
        }
        this.$emit('update:modelValue', this.selected);
        this.optionsShown = false;
        this.highlightedIndex = -1;
      },
      onEnter() {
        if (this.highlightedIndex == -1 && this.filteredOptions[0]) {
          this.toggleOption(this.filteredOptions[0]);
        } else if (this.filteredOptions.length === 0 && this.multiSelect) {
          let options = this.searchFilter.split(',');
          options.forEach((option) => {
            this.addOption(option.trim())
          });
          this.$emit('update:modelValue', this.selected);
        } else if (this.highlightedIndex >= 0) {
          this.toggleOption(this.filteredOptions[this.highlightedIndex]);
        } 
      },
      keyMonitor: function(event) {
        if (event.key === "ArrowDown") {
          if (this.highlightedIndex < this.filteredOptions.length - 1) {
            this.highlightedIndex++;
          } else {
            this.highlightedIndex = 0;
          }
        } else if (event.key === "ArrowUp") {
          if (this.highlightedIndex > 0) {
            this.highlightedIndex--;
          } else {
            this.highlightedIndex = this.filteredOptions.length - 1;
          }
        }
        this.scrollToHighlighted();
      },
      scrollToHighlighted() {
        this.$nextTick(() => {
          const highlightedEl = this.$refs.dropdownItems?.[this.highlightedIndex];
          if (highlightedEl) {
            highlightedEl.scrollIntoView({ block: "nearest", behavior: "instant" });
          }
        });
      },
      isSelected(option) {
        if (this.multiSelect) {
          return this.selected.some(selectedOption => selectedOption === option);
        } else {
          return this.selected && this.selected === option;
        }
      },
    },
    watch: {
      searchFilter(newVal) {
        if (this.filteredOptions.length === 0 && !this.multiSelect) {
          this.selected = null;
        } else if (this.selected !== newVal) {
          this.optionsShown = true;
        }
      },
      modelValue: {
        handler(newVal) {
          if (this.multiSelect) {
            this.selected = this.options.filter(option => newVal?.includes(option));
          } else {
            this.selected = this.options.find(option => option === newVal) || newVal;
          }
          this.searchFilter = this.selected;
        },
        immediate: true
      },
    }
  };
</script>