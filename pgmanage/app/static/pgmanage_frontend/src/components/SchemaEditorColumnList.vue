<template>
  <div class="mb-2">
    <div class="d-flex row fw-bold text-muted schema-editor__header g-0">
      <div :class="commentable ? 'col-2' : 'col-3'">
        <p class="h6">Name</p>
      </div>
      <div :class="commentable ? 'col-2' : 'col-3'">
        <p class="h6">Type</p>
      </div>
      <div :class="commentable ? 'col-2' : 'col-3'">
        <p class="h6">Default</p>
      </div>
      <div class="col-1">
        <p class="h6">Nullable</p>
      </div>
      <div class="col-1">
        <p class="h6">Primary Key</p>
      </div>
      <div v-if="commentable" class="col-3">
        <p class="h6">Comment</p>
      </div>
      <div class="col-1">
        <p class="h6">Actions</p>
      </div>
    </div>
    <div v-for="(column, index) in columns" :key="column.index"
        :class="['schema-editor__column d-flex row flex-nowrap form-group g-0',
          { 'schema-editor__column-deleted': column.deleted },
          { 'schema-editor__column-new': column.new },
          { 'schema-editor__column-dirty': column.is_dirty }]"
          >
          <div :class="commentable ? 'col-2' : 'col-3'">
              <input type="text" v-model="column.name" class="form-control mb-0" placeholder="column name..." />
          </div>

          <div :class="commentable ? 'col-2' : 'col-3'">
            <SearchableDropdown
              placeholder="type to search"
              :options="dataTypes"
              :default="{ name: 'integer' }"
              v-model="column.dataType"
              :disabled="!column.editable"
            />
          </div>

          <div :class="commentable ? 'col-2' : 'col-3'">
            <input type='text' v-model="column.defaultValue"
              class="form-control mb-0"
              @input='nullifyDefault(column)'
              :placeholder="column.defaultValue === null ? 'not set' : 'empty'"
              :disabled="!column.editable"/>
          </div>

          <div class="col-1 d-flex align-items-center">
            <input type='checkbox' class="custom-checkbox" v-model="column.nullable" :disabled="!column.editable || column.isPK"/>
          </div>

          <div class="col-1 d-flex align-items-center">
            <input type='checkbox' class="custom-checkbox" v-model="column.isPK" :disabled="disabledPrimaryKey || column.nullable"/>
          </div>

          <div v-if="commentable" :class="[this.movable(column) ? 'col': 'col-3']">
            <input v-model="column.comment" class="form-control mb-0"
            type="text"
            :placeholder="this.mode === operationModes.UPDATE ? '' : 'column comment...'" />
          </div>

          <div :class="['d-flex me-1', this.movable(column) ? 'col-auto justify-content-between': 'col justify-content-end']">
            <button v-if="column.deleted && !column.new || column.is_dirty" @click='revertColumn(index)' type="button"
              class="btn btn-icon btn-icon-success ps-2 pe-2" title="Revert">
              <i class="fas fa-rotate-left"></i>
            </button>

            <button v-if="this.movable(column)" @click='moveColumnUp(index)'
              class="btn btn-icon btn-icon-secondary ps-2 pe-2" title="Move column up" type="button">
              <i class="fas fa-circle-up"></i>
            </button>

            <button v-if="this.movable(column)" @click='moveColumnDown(index)'
              class="btn btn-icon btn-icon-secondary ps-2 pe-2" title="Move column down" type="button">
              <i class="fas fa-circle-down"></i>
            </button>

            <button v-if="!column.deleted && !column.is_dirty" @click='removeColumn(index)' type="button"
              class="btn btn-icon btn-icon-danger ps-2 pe-2" title="Remove column">
              <i class="fas fa-circle-xmark"></i>
            </button>
          </div>
    </div>
    <div class="d-flex g-0 fw-bold mt-2">
      <button @click='addColumn' class="btn btn-outline-success ms-auto">
        Add Column
      </button>
    </div>
  </div>
</template>

<script>
  import SearchableDropdown from "./SearchableDropdown.vue";
  import { operationModes } from "../constants";

  export default {
    name: 'SchemaEditorColumnList',
    data() {
      return {
        columns: [],
        value:'',
      }
    },
    created() {
      // allows for using operationModes in the template
      this.operationModes = operationModes
    },
    components: {
      SearchableDropdown
    },
    props: {
      initialColumns: {
        type: Array,
        default: []
      },
      commentable: Boolean,
      mode: operationModes,
      dataTypes: Array,
      multiPKeys: Boolean
    },
    emits: ["columns:changed"],
    computed: {
      countOfPrimaryKeys() {
        return this.columns.filter(obj => obj.isPK === true).length
      },
      disabledPrimaryKey() {
        // return this.mode === "alter" && !this.multiPKeys && this.countOfPrimaryKeys == 1
        return this.mode === operationModes.UPDATE // TODO: add support for altering Primary Keys and then fix this
      }
    },
    methods: {
      addColumn() {
        let colName = `column_${this.columns.length}`
        const defaultCol = {
          dataType: 'integer',
          name: colName,
          defaultValue: null,
          nullable: false,
          isPK: false,
          comment:null,
          new: this.mode === operationModes.UPDATE,
          editable: true,
          is_dirty: false
        }
        this.columns.push(defaultCol)
      },
      movable(column) {
        //all columns are movable when creating a new table
        if(this.mode !== operationModes.UPDATE) return true;
        if(column.new) return true;
      },
      removeColumn(index) {
        if(this.mode === operationModes.UPDATE && !this.columns[index].new) {
          this.columns[index].deleted = true;
        } else {
          this.columns.splice(index, 1)
        }
      },
      moveColumnUp(index) {
        // prevent moving newly added column above existing ones in "alter" mode
        if(index == 0) return;
        if(this.mode === operationModes.UPDATE) {
          let colAbove = this.columns[index-1]
          if(!colAbove.new) return;
        }
        let col = this.columns.splice(index, 1)[0]
        this.columns.splice(index-1, 0, col)
      },
      moveColumnDown(index) {
        if(index == this.columns.length-1) return;
        let col = this.columns.splice(index, 1)[0]
        this.columns.splice(index+1, 0, col)
      },
      nullifyDefault(column) {
        if(column.defaultValue === '') column.defaultValue = null
      },
      revertColumn(index) {
        this.columns[index] = JSON.parse(JSON.stringify(this.initialColumns[index]));
      }
    },
    watch: {
      initialColumns: {
        handler(newVal, oldVal) {
          this.columns = JSON.parse(JSON.stringify(newVal))
        },
        immediate: true
      },
      columns: {
        handler(newVal, oldVal) {

          if (!this.multiPKeys && this.countOfPrimaryKeys > 1) {
            newVal = newVal.map((obj) => {
              let isInitialPK = this.initialColumns.find(
                (initialObj) => initialObj.name === obj.name
              )?.isPK;
              return {
                ...obj,
                isPK: isInitialPK ? false : obj.isPK,
              };
            });
          }

          this.$emit("columns:changed", newVal);
        },
        deep: true,
      },
    }
  }
</script>

<style scoped>
input[type='checkbox'].custom-checkbox:disabled {
  background-color: initial;
  border-color: rgba(118, 118, 118, 0.3);
}
</style>