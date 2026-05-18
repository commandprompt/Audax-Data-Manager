<template>
  <div class="mb-2">
    <div class="d-flex row fw-bold text-muted schema-editor__header g-0">
      <div class="col-3">
        <p class="h6">Name</p>
      </div>
      <div class="col-1">
        <p class="h6">indexType</p>
      </div>
      <div v-if="!disabledFeatures?.indexMethod" class="col-1">
        <p class="h6">Method</p>
      </div>
      <div class="col-3">
        <p class="h6">Columns</p>
      </div>
      <div v-if="!disabledFeatures?.indexPredicate" class="col">
        <p class="h6">Predicate</p>
      </div>
      <div class="col-1">
        <p class="h6">Actions</p>
      </div>
    </div>
    <div
      v-for="(index, idx) in indexes"
      :key="idx"
      :class="[
        'schema-editor__column d-flex row flex-nowrap form-group g-0',
        { 'schema-editor__column-deleted': index.deleted },
        { 'schema-editor__column-new': index.new },
        { 'schema-editor__column-dirty': index.is_dirty },
      ]"
    >
      <div class="col-3 d-flex align-items-center">
        <i
          title="Primary key"
          :class="[
            'fas fa-key action-key text-secondary ms-2',
            { invisible: !index.is_primary },
          ]"
        ></i>
        <input
          type="text"
          v-model="index.index_name"
          class="form-control mb-0 ps-2"
          placeholder="NULL"
          :disabled="disabledFeatures?.renameIndex && !index.new"
        />
      </div>

      <div class="col-1 d-flex align-items-center">
        <SearchableDropdown
          placeholder="type to search"
          :options="indexTypes"
          v-model="index.type"
          :disabled="!index.new"
        />
      </div>

      <div
        v-if="!disabledFeatures?.indexMethod"
        class="col-1 d-flex align-items-center"
      >
        <SearchableDropdown
          placeholder="type to search"
          :options="indexMethods"
          v-model="index.method"
          :disabled="!index.new || index.type == 'unique'"
        />
      </div>

      <div class="col-3">
        <SearchableDropdown
          placeholder="type to search"
          :options="columns"
          v-model="index.columns"
          :multi-select="true"
          :disabled="!index.new"
        />
      </div>

      <div
        v-if="!disabledFeatures?.indexPredicate"
        class="col d-flex align-items-center"
      >
        <input
          type="text"
          v-model="index.predicate"
          class="form-control mb-0"
          :disabled="!index.new"
        />
      </div>

      <div class="col-1 d-flex me-1 justify-content-end">
        <button
          v-if="(index.deleted && !index.new) || index.is_dirty"
          @click="revertIndex(idx)"
          type="button"
          class="btn btn-icon btn-icon-success ps-2 pe-2"
          title="Revert"
        >
          <i class="fas fa-rotate-left"></i>
        </button>

        <button
          v-if="!index.deleted && !index.is_dirty"
          @click="removeIndex(idx)"
          type="button"
          class="btn btn-icon btn-icon-danger ps-2 pe-2"
          title="Remove column"
        >
          <i class="fas fa-circle-xmark"></i>
        </button>
      </div>
    </div>
    <div class="d-flex g-0 fw-bold mt-2">
      <button @click="addIndex" class="btn btn-outline-success ms-auto">
        Add Index
      </button>
    </div>
  </div>
</template>

<script>
import SearchableDropdown from "./SearchableDropdown.vue";

export default {
  name: "SchemaEditorIndexesList",
  components: {
    SearchableDropdown,
  },
  props: {
    initialIndexes: {
      type: Array,
      default: [],
    },
    indexMethods: {
      type: Array,
      default: [],
    },
    indexTypes: {
      type: Array,
      default: [],
    },
    disabledFeatures: {
      type: Object,
      default: {},
    },
    columns: Array,
  },
  emits: ["indexes:changed"],
  data() {
    return {
      indexes: [],
    };
  },
  methods: {
    addIndex() {
      let indexName = `index_${this.indexes.length}`;
      const defaultIndex = {
        index_name: indexName,
        is_primary: false,
        columns: [],
        new: true,
        editable: true,
        method: null,
        predicate: "",
        type: "non-unique",
        is_dirty: false,
      };
      this.indexes.push(defaultIndex);
    },
    removeIndex(index) {
      if (!this.indexes[index].new) {
        this.indexes[index].deleted = true;
      } else {
        this.indexes.splice(index, 1);
      }
    },
    revertIndex(index) {
      this.indexes[index] = JSON.parse(
        JSON.stringify(this.initialIndexes[index])
      );
    },
  },
  watch: {
    initialIndexes: {
      handler(newVal, oldVal) {
        this.indexes = JSON.parse(JSON.stringify(newVal));
      },
      immediate: true,
    },
    indexes: {
      handler(newVal, oldVal) {
        this.$emit("indexes:changed", newVal);
      },
      deep: true,
    },
  },
};
</script>

<style scoped>
input[type="checkbox"].custom-checkbox:disabled {
  background-color: initial;
  border-color: rgba(118, 118, 118, 0.3);
}
</style>
