<template>
  <div
    class="vue-power-tree"
    :class="{'vue-power-tree-root': isRoot }"
    v-on="{ 
      mousemove: allowDrag ? onMousemoveHandler : null, 
      mouseleave: allowDrag ? onMouseleaveHandler : null, 
      dragend: allowDrag ? (event) => onDragendHandler(null, event) : null
    }"
  >
    <div ref="nodes" class="vue-power-tree-nodes-list">
      <div
        class="vue-power-tree-node" v-for="(node, nodeInd) in nodes"
        :class="{'vue-power-tree-selected': node.isSelected }"
      >
        <div
          class="vue-power-tree-cursor vue-power-tree-cursor_before"
          @dragover.prevent
          :style="{
        'visibility': cursorPosition &&
          cursorPosition.node.pathStr === node.pathStr &&
          cursorPosition.placement === 'before' ?
          'visible' :
          'hidden',
        '--depth': depth
      }"
        >
          <!-- suggested place for node insertion  -->
        </div>

        <div
          class="vue-power-tree-node-item"
          :path="node.pathStr"
          :class="{
            'vue-power-tree-cursor-hover':
              cursorPosition &&
              cursorPosition.node.pathStr === node.pathStr,
            'vue-power-tree-cursor-inside':
              cursorPosition &&
              cursorPosition.placement === 'inside' &&
              cursorPosition.node.pathStr === node.pathStr,
            'vue-power-tree-node-is-leaf' : node.isLeaf,
            'vue-power-tree-node-is-folder' : !node.isLeaf
          }"
          :style="node.level > 1 ? { paddingLeft: 10 /* 10px base offset */ + (node.level-1) * 20 + 'px' } : {}"
        >
          <div class="vue-power-tree-branch" v-if="level && showBranches">
            <slot name="branch" :node="node">
            <span v-if="!node.isLastChild">
              {{ String.fromCharCode(0x251C) }}{{ String.fromCharCode(0x2500) }}&nbsp;
            </span>
              <span v-if="node.isLastChild">
              {{ String.fromCharCode(0x2514) }}{{ String.fromCharCode(0x2500) }}&nbsp;
            </span>
            </slot>
          </div>

          <div class="vue-power-tree-row" data-tree="row">
            <span class="vue-power-tree-toggle" v-if="!node.isLeaf" @click="onToggleHandler($event, node)">
              <slot name="toggle" :node="node">
                <span>{{ !node.isLeaf ? (node.isExpanded ? '-' : '+') : '' }}</span>
              </slot>
            </span>

            <span
              @mousedown="onNodeMousedownHandler($event, node)"
              @mouseup="onNodeMouseupHandler($event, node)"
              @contextmenu="emitNodeContextmenu(node, $event)"
              @dblclick="emitNodeDblclick(node, $event)"
              @click="emitNodeClick(node, $event)"
              @dragover="onExternalDragoverHandler(node, $event)"
              @drop="onExternalDropHandler(node, $event)"
              data-tree="title"
              class="vue-power-tree-title"
            >
              <slot name="title" :node="node">
                {{ node.title }}
              </slot>
            </span>

            <slot name="empty-node" :node="node" v-if="!node.isLeaf && node.children.length == 0 && node.isExpanded"></slot>
          </div>

          <div class="vue-power-tree-sidebar" data-tree="sidebar">
            <slot name="sidebar" :node="node"></slot>
          </div>

        </div>

        <power-tree
          v-if="node.children && node.children.length && node.isExpanded"
          :value="node.children"
          :level="node.level"
          :parentInd="nodeInd"
          :allowDrag="allowDrag"
          :allowMultiselect="allowMultiselect"
          :allowToggleBranch="allowToggleBranch"
          :edgeSize="edgeSize"
          :showBranches="showBranches"
          @dragover.prevent
        >
          <template #title="{ node }">
            <slot name="title" :node="node">{{ node.title }}</slot>
          </template>

          <template #toggle="{ node }">
            <slot name="toggle" :node="node">
            <span>
               {{ !node.isLeaf ? (node.isExpanded ? '-' : '+') : '' }}
            </span>
            </slot>
          </template>

          <template #sidebar="{ node }">
            <slot name="sidebar" :node="node"></slot>
          </template>

          <template #empty-node="{ node }">
            <slot name="empty-node" :node="node" v-if="!node.isLeaf && node.children.length === 0 && node.isExpanded">
            </slot>
          </template>

        </power-tree>

        <div
          class="vue-power-tree-cursor vue-power-tree-cursor_after"
          @dragover.prevent
          :style="{
        'visibility': cursorPosition &&
          cursorPosition.node.pathStr === node.pathStr &&
          cursorPosition.placement === 'after' ?
          'visible' :
          'hidden',
        '--depth': depth
      }"
        >
          <!-- suggested place for node insertion  -->
        </div>

      </div>

      <div v-show="isDragging" v-if="isRoot" ref="dragInfo" class="vue-power-tree-drag-info">
        <slot name="draginfo">
          Items: {{ selectionSize }}
        </slot>
      </div>

    </div>

  </div>
</template>

<script src="./power-tree.js"></script>
