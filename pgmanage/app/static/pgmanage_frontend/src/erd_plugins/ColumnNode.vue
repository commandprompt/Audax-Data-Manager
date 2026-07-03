<template>
  <div
    class="erd-card__column p-3"
    :class="{
      'pk-column': isPk,
      'fk-column': isFk,
      highlighted: Boolean(this.data?.is_highlighted),
    }"
  >
    <a class="erd-card__column_name">
      <i v-if="isPk || isFk" class="fa-solid fa-key ms-2 me-1"></i>
      {{ nodeLabel }}
    </a>

    <span v-if="data.type" class="erd-card-column__type">
      {{ data.type }}
    </span>

    <Handle
      v-if="hasRelationship"
      id="source-left"
      type="source"
      :position="leftPosition"
      :connectable="connectable"
      class="erd-card__column__handle"
    />

    <Handle
      v-if="hasRelationship"
      id="source-right"
      type="source"
      :position="rightPosition"
      :connectable="connectable"
      class="erd-card__column__handle"
    />

    <Handle
      v-if="hasRelationship"
      id="target-left"
      type="target"
      :position="leftPosition"
      :connectable="connectable"
      class="erd-card__column__handle"
    />

    <Handle
      v-if="hasRelationship"
      id="target-right"
      type="target"
      :position="rightPosition"
      :connectable="connectable"
      class="erd-card__column__handle"
    />
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
