<template>
  <div
    class="vue-flow__node-table__column_wrap"
    :class="{ 'last-column': isLast }"
  >
    <div
      class="vue-flow__node-table__column"
      :class="{
        'pk-column': isPk,
        'fk-column': isFk,
        highlighted: Boolean(this.data?.is_highlighted),
      }"
    >

      <a v-if="isFk" class="vue-flow__node-table__column_name" href="#">
        <i class="fa-solid fa-key"></i>
        <span>{{ nodeLabel }}</span>
      </a>

      <span v-else-if="isPk" class="vue-flow__node-table__column_name">
        <i class="fa-solid fa-key"></i>
        {{ nodeLabel }}
      </span>

      <span v-else class="vue-flow__node-table__column_name">
        <!-- icon placeholder -->
        <i class="fa-solid fa-key" style="visibility: hidden;" aria-hidden="true"></i>
        {{ nodeLabel }}
      </span>

      <span v-if="data.type" class="vue-flow__node-table__column_type">
        {{ data.type }}
      </span>

      <Handle
        v-if="hasRelationship"
        id="source-left"
        type="source"
        :position="leftPosition"
        :connectable="connectable"
        class="vue-flow__node-table__column__handle"
      />

      <Handle
        v-if="hasRelationship"
        id="source-right"
        type="source"
        :position="rightPosition"
        :connectable="connectable"
        class="vue-flow__node-table__column__handle"
      />

      <Handle
        v-if="hasRelationship"
        id="target-left"
        type="target"
        :position="leftPosition"
        :connectable="connectable"
        class="vue-flow__node-table__column__handle"
      />

      <Handle
        v-if="hasRelationship"
        id="target-right"
        type="target"
        :position="rightPosition"
        :connectable="connectable"
        class="vue-flow__node-table__column__handle"
      />
    </div>
  </div>

</template>

<script>
import { Handle, Position } from "@vue-flow/core";

export default {
  name: "ColumnNode",
  components: {
    Handle,
  },
  props: {
    data: {
      type: Object,
      required: true,
    },
    label: {
      type: [String, Number],
      default: "",
    },
    connectable: {
      type: Boolean,
      default: true,
    },
  },
  computed: {
    isPk() {
      return Boolean(this.data?.is_pk);
    },
    isFk() {
      return Boolean(this.data?.is_fk);
    },
    isLast() {
      return Boolean(this.data?.is_last);
    },
    nodeLabel() {
      return this.data?.label || this.label;
    },
    hasRelationship() {
      return this.isPk || this.isFk;
    },

    leftPosition() {
      return Position.Left;
    },

    rightPosition() {
      return Position.Right;
    },
  },
};
</script>
