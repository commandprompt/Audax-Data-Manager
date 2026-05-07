<template>
  <div class="mb-2">
    <div class="d-flex row fw-bold text-muted schema-editor__header g-0">
      <div class="col">
        <p class="h6">Name</p>
      </div>
      <div class="col-2">
        <p class="h6">Column Name</p>
      </div>
      <div v-if="hasSchema" class="col-1">
        <p class="h6">FK Schema</p>
      </div>
      <div class="col-2">
        <p class="h6">FK Table</p>
      </div>
      <div class="col-2">
        <p class="h6">FK Column</p>
      </div>
      <div v-if="!disabledFeatures?.constraints?.onUpdate" class="col-1">
        <p class="h6">On Update</p>
      </div>
      <div class="col-1">
        <p class="h6">On Delete</p>
      </div>
      <div v-if="!disabledFeatures.dropForeignKey" class="col-1">
        <p class="h6">Actions</p>
      </div>
    </div>
    <div
      v-for="(fk, idx) in foreignKeys"
      :key="idx"
      :class="[
        'schema-editor__column d-flex row flex-nowrap form-group g-0',
        { 'schema-editor__column-deleted': fk.deleted },
        { 'schema-editor__column-new': fk.new },
        { 'schema-editor__column-dirty': fk.is_dirty },
      ]"
    >
      <div class="col d-flex align-items-center">
        <input
          type="text"
          v-model="fk.constraint_name"
          class="form-control mb-0 ps-2"
          placeholder="foreign key name..."
          :disabled="!fk.new"
        />
      </div>

      <div class="col-2 d-flex align-items-center">
        <SearchableDropdown
          placeholder="column name..."
          :options="columns"
          v-model="fk.column_name"
          :disabled="!fk.new"
        />
      </div>

      <div v-if="hasSchema" class="col-1 d-flex align-items-center">
        <SearchableDropdown
          placeholder="foreign key table schema.."
          :options="schemas"
          v-model="fk.r_table_schema"
          :disabled="!fk.new"
          @change="onSchemaChange(fk)"
        />
      </div>

      <div class="col-2 d-flex align-items-center">
        <SearchableDropdown
          placeholder="foreign key table.."
          :options="getTables(fk.r_table_schema)"
          v-model="fk.r_table_name"
          :disabled="!fk.new"
          @change="onTableChange(fk)"
        />
      </div>

      <div class="col-2 d-flex align-items-center">
        <SearchableDropdown
          placeholder="foreign key column.."
          :options="getColumns(fk.r_table_schema, fk.r_table_name)"
          v-model="fk.r_column_name"
          :disabled="!fk.new"
        />
      </div>

      <div v-if="!disabledFeatures?.constraints?.onUpdate" class="col-1">
        <SearchableDropdown
          placeholder="on update ..."
          :options="foreignKeyActions"
          v-model="fk.on_update"
          :disabled="!fk.new"
        />
      </div>

      <div class="col-1 d-flex align-items-center">
        <SearchableDropdown
          placeholder="on delete ..."
          :options="foreignKeyActions"
          v-model="fk.on_delete"
          :disabled="!fk.new"
        />
      </div>

      <div
        v-if="!disabledFeatures.dropForeignKey"
        class="col-1 d-flex me-1 justify-content-end"
      >
        <button
          v-if="(fk.deleted && !fk.new) || fk.is_dirty"
          @click="revertForeignKey(idx)"
          type="button"
          class="btn btn-icon btn-icon-success ps-2 pe-2"
          title="Revert"
        >
          <i class="fas fa-rotate-left"></i>
        </button>

        <button
          v-if="!fk.deleted && !fk.is_dirty"
          @click="removeForeignKey(idx)"
          type="button"
          class="btn btn-icon btn-icon-danger ps-2 pe-2"
          title="Remove foreign key"
        >
          <i class="fas fa-circle-xmark"></i>
        </button>
      </div>
    </div>
    <div v-if="!disabledFeatures.addForeignKey" class="d-flex g-0 fw-bold mt-2">
      <button @click="addForeignKey" class="btn btn-outline-success ms-auto">
        Add Foreign Key
      </button>
    </div>
  </div>
</template>

<script>
import SearchableDropdown from "./SearchableDropdown.vue";

export default {
  name: "SchemaEditorFksList",
  components: {
    SearchableDropdown,
  },
  props: {
    initialForeignKeys: {
      type: Array,
      default: [],
    },
    disabledFeatures: {
      type: Object,
      default: {},
    },
    columns: Array,
    dbMetaData: Array,
    hasSchema: {
      type: Boolean,
      default: true,
    },
  },
  emits: ["foreign-keys:changed"],
  data() {
    return {
      foreignKeys: [],
      foreignKeyActions: [
        "NO ACTION",
        "SET NULL",
        "SET DEFAULT",
        "CASCADE",
        "RESTRICT",
      ],
      tables: [],
    };
  },
  methods: {
    addForeignKey() {
      let foreignKeyName = `fk_${this.foreignKeys.length}`;
      let defaultSchema = this.schemas.length === 1 ? this.schemas[0] : null;
      const defaultForeignKey = {
        constraint_name: foreignKeyName,
        column_name: null,
        r_table_schema: defaultSchema,
        r_table_name: null,
        r_column_name: null,
        on_update: "NO ACTION",
        on_delete: "NO ACTION",
        new: true,
        editable: true,
        is_dirty: false,
      };
      this.foreignKeys.push(defaultForeignKey);
    },
    removeForeignKey(index) {
      if (!this.foreignKeys[index].new) {
        this.foreignKeys[index].deleted = true;
      } else {
        this.foreignKeys.splice(index, 1);
      }
    },
    revertForeignKey(index) {
      this.foreignKeys[index] = JSON.parse(
        JSON.stringify(this.initialForeignKeys[index])
      );
    },
    getTables(r_table_schema) {
      let schema;
      if (this.hasSchema) {
        schema = this.dbMetaData.find(
          (schema) => schema.name === r_table_schema
        );
        if (!schema) return;
      } else {
        schema = this.dbMetaData[0] ?? null;
      }
      return schema?.tables.map((table) => table.name) ?? [];
    },
    getColumns(r_table_schema, r_table_name) {
      let schema;
      if (this.hasSchema) {
        schema = this.dbMetaData.find(
          (schema) => schema.name === r_table_schema
        );
        if (!schema) return;
      } else {
        schema = this.dbMetaData[0] ?? null;
      }

      let table = schema?.tables.find((table) => table.name === r_table_name);
      if (!table) return;

      return table.columns ?? [];
    },
    onSchemaChange(foreignKey) {
      foreignKey.r_table_name = null;
      foreignKey.r_column_name = null;
    },
    onTableChange(foreignKey) {
      foreignKey.r_column_name = null;
    },
  },
  watch: {
    initialForeignKeys: {
      handler(newVal, oldVal) {
        this.foreignKeys = JSON.parse(JSON.stringify(newVal));
      },
      immediate: true,
    },
    foreignKeys: {
      handler(newVal, oldVal) {
        this.$emit("foreign-keys:changed", newVal);
      },
      deep: true,
    },
  },
  computed: {
    schemas() {
      return this.dbMetaData.map((schema) => schema.name);
    },
  },
};
</script>
