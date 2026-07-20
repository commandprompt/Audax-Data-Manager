<template>
  <div ref="erdContainer">

    <Transition>
      <div
        v-if="showLoading"
        class="div_loading d-block"
        :style="loadingOverlayStyle"
      >
        <div class="div_loading_cover"></div>
        <div class="div_loading_content">
          <span>Loading screenshot...</span>
          <div
            class="spinner-border spinner-size text-primary"
            role="status"
          >
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      </div>
    </Transition>
    <Controls 
    :in-fullscreen="inFullscreen"
    @screenshot="doScreenshot"
    @reset="resetToDefault"
    @zoom-in="this.$refs.vueFlow.zoomIn()"
    @zoom-out="this.$refs.vueFlow.zoomOut()"
    @toggle-fullscreen="toggleFullScreen"
      />

    <div ref="vueFlowWrap">
      <svg :style="{ position: 'absolute', top: 0, left: '-1000px' }">
        <defs>
          <marker :id="`erd-one-only-${tabId}`" viewBox="0 0 20 20" refX="18" refY="10" markerWidth="12" markerHeight="12" orient="auto-start-reverse">
            <line x1="6" y1="3" x2="6" y2="17" stroke="context-stroke" stroke-width="2" />
            <line x1="12" y1="3" x2="12" y2="17" stroke="context-stroke" stroke-width="2" />
          </marker>

          <marker :id="`erd-zero-one-${tabId}`" viewBox="0 0 20 20" refX="18" refY="10" markerWidth="12" markerHeight="12" orient="auto-start-reverse">
            <!-- fill="context-fill" lets you change the inside color via CSS if needed, or leave fill="white" for a hollow ring -->
            <circle cx="6" cy="10" r="3.5" fill="white" stroke="context-stroke" stroke-width="2" />
            <line x1="14" y1="3" x2="14" y2="17" stroke="context-stroke" stroke-width="2" />
          </marker>

          <marker :id="`erd-one-many-${tabId}`" viewBox="0 0 20 20" refX="18" refY="10" markerWidth="12" markerHeight="12" orient="auto-start-reverse">
            <line x1="4" y1="3" x2="4" y2="17" stroke="context-stroke" stroke-width="2" />
            <path d="M 10 10 L 18 3 M 10 10 L 18 17 M 4 10 L 18 10" stroke="context-stroke" stroke-width="2" stroke-linecap="round" fill="none" />
          </marker>

          <marker :id="`erd-zero-many-${tabId}`" viewBox="0 0 20 20" refX="18" refY="10" markerWidth="12" markerHeight="12" orient="auto-start-reverse">
            <circle cx="4" cy="10" r="3.5" fill="white" stroke="context-stroke" stroke-width="2" />
            <path d="M 10 10 L 18 3 M 10 10 L 18 17 M 4 10 L 18 10" stroke="context-stroke" stroke-width="2" stroke-linecap="round" fill="none" />
          </marker>
        </defs>
      </svg>

      <VueFlow
        class="vh-100"
        ref="vueFlow"
        :node-types="nodeTypes"
        :nodes="nodes"
        :edges="edges"
        :snap-to-grid="true"
        :snap-grid="[10, 10]"
        min-zoom="0.1"
        @nodes-initialized="onNodesInitialized"
        @viewport-change-end="saveGraphState"
        @node-drag-stop="onNodeDragStop"
        @node-drag="scheduleRerouteEdges"
        @edge-click="onEdgeClick"
        @node-click="onNodeClick"
        @pane-click="clearErdSelection"
      >
        <Background variant="dots" />

        <template #edge-bezierOrSmoothstep="edgeProps">
          <ErdRelationEdge v-bind="edgeProps" :tab-id="tabId"/>
        </template>
      </VueFlow>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { handleError } from '../logging/utils';
import { VueFlow, MarkerType, getConnectedEdges } from '@vue-flow/core';
import { Background } from '@vue-flow/background'
import { markRaw } from 'vue';
import { capture } from '@src/erd_plugins/screenshot';
import TableNode from '@src/erd_plugins/TableNode.vue';
import ColumnNode from '@src/erd_plugins/ColumnNode.vue';
import Controls from '@src/erd_plugins/Controls.vue';
import ErdRelationEdge from '@src/erd_plugins/ErdRelationEdge.vue';
import {
  TABLE_HEADER_HEIGHT,
  COLUMN_HEIGHT,
  getLayoutedNodes,
} from '@src/erd_plugins/layout';
import { settingsStore } from '../stores/stores_initializer';

export default {
  name: "ERDTab",
  components: {
    VueFlow,
    Background,
    Controls,
    ErdRelationEdge,
  },
  props: {
    schema: String,
    workspaceId: String,
    tabId: String,
    databaseIndex: Number,
    databaseName: String,
  },
  data() {
    return {
      nodeTypes: {
        table: markRaw(TableNode),
        column: markRaw(ColumnNode),
      },
      nodes: [],
      edges: [],
      inFullscreen: false,
      jsonLayout: false,
      rerouteFrame: null,
      showLoading: false,
      loadingOverlayTop: 0,
    };
  },
  mounted() {
    this.loadSchemaGraph();

    this.updateLoadingOverlayTop();

    settingsStore.$onAction((action) => {
      if(action.name === "setFontSize") {
        action.after(() => {
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              this.updateLoadingOverlayTop();
            })
          })
        })
      }
    })
  },
  computed: {
    loadingOverlayStyle() {
      return {
        zIndex: 10,
        top: `${this.loadingOverlayTop}px`,
      }
    },
  },
  methods: {
    onNodesInitialized() {
      if (!this.jsonLayout) {
        this.nodes = getLayoutedNodes(this.nodes, this.$refs.vueFlow.nodes,);

        this.$nextTick(() => {
          this.$refs.vueFlow.fitView();
          this.rerouteEdgesByTableDistance();
          this.applyGroupedZIndexes();
        })
      } else {
        this.$nextTick(() => {
          this.rerouteEdgesByTableDistance();
          this.applyGroupedZIndexes();
        })
      }
    },
    doScreenshot() {
      this.showLoading = true;

      requestAnimationFrame(()=> {
        requestAnimationFrame(() => {
          capture(this.$refs.vueFlowWrap, { shouldDownload: true }).then(() => this.showLoading = false)
        })
      })
    },
    resetToDefault() {
      this.nodes = getLayoutedNodes(this.nodes, this.$refs.vueFlow.nodes);

      this.$nextTick(() => {
        this.applyGroupedZIndexes();
        this.rerouteEdgesByTableDistance();
        this.$refs.vueFlow.fitView()
        this.saveGraphState();
      })
    },
    loadSchemaGraph() {
      axios.post('/draw_graph/', {
        database_index: this.databaseIndex,
        workspace_id: this.workspaceId,
        schema: this.schema,
      })
      .then((response) => {
        if (response.data.layout) {
          this.jsonLayout = true
          this.restoreVueFlowLayout(
            response.data.layout,
            response.data.new_nodes || [],
            response.data.new_edges || []
          )
        } else {
          const tableNodes = response.data.nodes.map((node, index) => (
            {
              id: node.id,
              type: 'table',
              position: { x: 0, y:0 },
              data: {
                label: node.label,
              },
            }
          ));
          const columnNodes = [];

          response.data.nodes.forEach((node) => {
            node.columns.forEach((columnNode, index) => {
              const col = this.createColumnNode(node, columnNode, index)            
              columnNodes.push(col);
            })
          })
          this.nodes = [...tableNodes, ...columnNodes]
          this.edges = response.data.edges.map((edge) => this.createEdge(edge))
        }
      })
      .catch((error) => {
        handleError(error);
      })
    },
    shortDataType(typename) {
      const TYPEMAP = {
        'character varying': 'varchar',
        'timestamp with time zone': 'timestamptz',
        'timestamp without time zone': 'timestamp',
        'time without time zone': 'time',
        'time with time zone': 'timetz',
        'character': 'char',
        'boolean': 'bool'
      }
      return TYPEMAP[typename] || typename
    },
    saveGraphState() {
      const layoutData = this.$refs.vueFlow.toObject();

      axios.post('/save_graph_state/', {
        workspace_id: this.workspaceId,
        schema: this.schema,
        database_name: this.databaseName,
        database_index: this.databaseIndex,
        layout: layoutData,
      }).catch((error) => {
        handleError(error);
      });
    },
    toggleFullScreen() {
      this.$refs.erdContainer.classList.toggle("omnidb__panel-view--full");
      this.inFullscreen = !this.inFullscreen;
    },
    restoreVueFlowLayout(layoutData, newNodesData = [], newEdgesData = []) {
      const savedNodes = layoutData.nodes || []
      const savedEdges = layoutData.edges || []
      const savedViewport = layoutData.viewport

      let nextNodes = [...savedNodes]

      const savedNodeIds = new Set(savedNodes.map((node) => node.id))
      const changedTableIds = new Set(newNodesData.map((node) => node.id))

      // If backend sends a table in new_nodes, rebuild its column nodes.
      // This handles both fully new tables and existing tables with changed columns.
      nextNodes = nextNodes.filter((node) => {
        const parentId = node.parentNode

        return !changedTableIds.has(parentId)
      })

      newNodesData.forEach((tableData) => {
        const tableAlreadyExists = savedNodeIds.has(tableData.id)

        if (tableAlreadyExists) {
          nextNodes = nextNodes.map((node) => {
            if (node.id !== tableData.id) {
              return node
            }

            return {
              ...node,
              data: {
                ...(node.data || {}),
                label: tableData.label,
              },
            }
          })
        } else {
          const tableCount = nextNodes.filter((node) => node.type === 'table').length
          const position = {x: 0, y: 0}

          nextNodes.push(this.createTableNode(tableData, position))
        }

        tableData.columns.forEach((columnNode, index) => {
          nextNodes.push(this.createColumnNode(tableData, columnNode, index))
        })
      })

      const savedEdgeIds = new Set(savedEdges.map((edge) => edge.id))

      const newEdges = newEdgesData
        .map((edge) => this.createEdge(edge))
        .filter((edge) => !savedEdgeIds.has(edge.id))

      this.nodes = nextNodes
      this.edges = [
        ...savedEdges,
        ...newEdges,
      ]

      this.$nextTick(() => {
        if (savedViewport && this.$refs.vueFlow?.setViewport) {
          this.$refs.vueFlow.setViewport(savedViewport)
        } else {
          this.$refs.vueFlow?.fitView?.({
            padding: 0.2,
          })
        }
      })
    },
    createTableNode(node, position = { x: 0, y: 0 }) {
      return {
        id: node.id,
        type: 'table',
        position,
        data: {
          label: node.label,
        },
      }
    },
    createColumnNode(tableNode, columnNode, index) {
      return {
        id: `${tableNode.id}_${columnNode.name}`,
        type: 'column',
        draggable: false,
        expandParent: true,
        parentNode: tableNode.id,
        position: {
          x: 0,
          y: TABLE_HEADER_HEIGHT + index * COLUMN_HEIGHT,
        },
        data: {
          label: columnNode.name,
          type: this.shortDataType(columnNode.type),
          cgid: columnNode.cgid,
          is_pk: columnNode.is_pk,
          is_fk: columnNode.is_fk,
          is_highlighted: false,
        },
      }
    },
    createEdge(edge) {
      return {
        id: `${edge.from}_${edge.from_col}-${edge.to}_${edge.to_col}`,
        source: `${edge.from}_${edge.from_col}`,
        target: `${edge.to}_${edge.to_col}`,
        sourceHandle: 'source-right',
        targetHandle: 'target-left',
        label: edge.label,
        cgid: edge.cgid,
        type: 'bezierOrSmoothstep',
        pathOptions: {
          offset: 30,
        },
        markerEnd: 'erd-one-only',
        markerStart: 'erd-one-many',
        data: {
          cgid: edge.cgid,
          sourceTableId: edge.from,
          targetTableId: edge.to,
        },
      }
    },
    clearErdSelection() {
      this.edges.forEach((edge) => {
        let storedEdge = this.$refs.vueFlow.findEdge(edge.id);
        storedEdge.selected = false;
        storedEdge.zIndex = 1;
      });
      this.nodes.forEach((node) => {
        node.data.is_highlighted = false;
      });
    },
    onEdgeClick({ edge }) {
      this.clearErdSelection();
      this.selectErdEdges([edge]);
    },
    onNodeClick({ node }) {
      if (node.type === 'table') {

        const edgesToSelect = [];
        this.nodes.forEach((nodeObj) => {
          if (nodeObj.parentNode == node.id) {
            this.$refs.vueFlow.updateNode(nodeObj.id, {selected: true});
            let relatedEdges = getConnectedEdges([nodeObj], this.edges);
            if (relatedEdges.length) {
              edgesToSelect.push(...relatedEdges);
              return;
            }
          }
        })
        if (!edgesToSelect.length) {
          this.clearErdSelection();
          return;
        }
        this.selectErdEdges(edgesToSelect);
      } else if (node.type === 'column') {
        const relatedEdges = getConnectedEdges([node], this.edges);
  
        if (!relatedEdges.length) {
          this.clearErdSelection();
          return;
        }
  
        this.selectErdEdges(relatedEdges);
      }
    },
    selectErdEdges(edgesToSelect) {
      const selectedEdgeKeys = new Set(edgesToSelect.map((edge) => edge.id));
      const highlightedColumnIds = new Set();

      edgesToSelect.forEach((edge) => {
        if (edge.source) {
          highlightedColumnIds.add(edge.source);
        }

        if (edge.target) {
          highlightedColumnIds.add(edge.target);
        }
      });

      this.edges.forEach((edge) => {
        const shouldBeSelected = selectedEdgeKeys.has(edge.id);
        let storedEdge = this.$refs.vueFlow.findEdge(edge.id);
        if (storedEdge.selected !== shouldBeSelected) {
          storedEdge.zIndex = 2;
          storedEdge.selected = shouldBeSelected;
        }
      });

      this.nodes.forEach((node) => {
        if (node.type !== "column") {
          return;
        }

        const shouldBeHighlighted = highlightedColumnIds.has(node.id);

        let storedNode = this.$refs.vueFlow.findNode(node.id);

        if (!storedNode.data) {
          storedNode.data = {};
        }

        if (storedNode.data.is_highlighted !== shouldBeHighlighted) {
          storedNode.data.is_highlighted = shouldBeHighlighted;
        }
      });
    }, 
    getTableBounds(tableNode) {
      const width = tableNode.dimensions.width;
      const height = tableNode.dimensions.height;
      const x = tableNode.position?.x || 0;
      const y = tableNode.position?.y || 0;
    
      return {
        left: x,
        right: x + width,
        top: y,
        bottom: y + height,
      };
    },
    getBestHorizontalRoute(edge, nodes) {
      const nodeById = new Map(nodes.map((node) => [node.id, node]));
    
      const sourceColumn = nodeById.get(edge.source);
      const targetColumn = nodeById.get(edge.target);
    
      const sourceTableId = sourceColumn.parentNode || edge.data?.sourceTableId;
    
      const targetTableId = targetColumn.parentNode || edge.data?.targetTableId;
    
      const sourceTable = nodeById.get(sourceTableId);
      const targetTable = nodeById.get(targetTableId);
    
      if (!sourceTable || !targetTable || sourceTable.id === targetTable.id) {
        return null;
      }

      const sourceBounds = this.getTableBounds(sourceTable);
      const targetBounds = this.getTableBounds(targetTable);

      let target_switch_margin = 30;

      const targetIsRightOfSource = targetBounds.left >= sourceBounds.right + target_switch_margin;
      const targetIsLeftOfSource = targetBounds.right <= sourceBounds.left - target_switch_margin;

      if (targetIsRightOfSource) {
        return {
          sourceHandle: 'source-right',
          targetHandle: 'target-left',
        };
      }

      if (targetIsLeftOfSource) {
        return {
          sourceHandle: 'source-left',
          targetHandle: 'target-right',
        };
      }
    
      const leftToLeftDistance = Math.abs(sourceBounds.left - targetBounds.left);
      const rightToRightDistance = Math.abs(sourceBounds.right - targetBounds.right);
    
       if (leftToLeftDistance <= rightToRightDistance) {
        return {
          sourceHandle: 'source-left',
          targetHandle: 'target-left',
        };
      }

      return {
        sourceHandle: 'source-right',
        targetHandle: 'target-right',
      };
    },
    rerouteEdgesByTableDistance() {
      const currentNodes = this.$refs.vueFlow.nodes;
    
      this.edges.forEach((edge) => {
        let storedEdge = this.$refs.vueFlow.findEdge(edge.id);
        const route = this.getBestHorizontalRoute(storedEdge, currentNodes);
    
        if (!route) {
          return;
        }
    
        if (
          storedEdge.sourceHandle !== route.sourceHandle ||
          storedEdge.targetHandle !== route.targetHandle
        ) {
          storedEdge.sourceHandle = route.sourceHandle;
          storedEdge.targetHandle = route.targetHandle;
        }
      })
    },
    onNodeDragStop() {
      this.rerouteEdgesByTableDistance();
      this.saveGraphState();
    },
    scheduleRerouteEdges() {
      if (this.rerouteFrame) {
        cancelAnimationFrame(this.rerouteFrame);
      }
    
      this.rerouteFrame = requestAnimationFrame(() => {
        this.rerouteEdgesByTableDistance();
        this.rerouteFrame = null;
      })
    },
    applyGroupedZIndexes() {
      const tableNodes = this.nodes.filter((node) => node.type === 'table');

      const tableZIndexById = {};

      tableNodes.forEach((tableNode, index) => {
        tableZIndexById[tableNode.id] = (index + 1) * 10;
      })

      this.nodes.forEach((node) => {
        if (node.type === 'table') {
          this.$refs.vueFlow.updateNode(node.id, {zIndex: tableZIndexById[node.id] ?? 10});
          return;
        }

        if (node.type === 'column') {
          const tableId = node.parentNode;
          const tableZIndex = tableZIndexById[tableId] ?? 10;
          this.$refs.vueFlow.updateNode(node.id, {zIndex: tableZIndex + 1});
        }
      })
    },
    updateLoadingOverlayTop() {
      const tabMenu = document.querySelector(`a[id="${this.tabId}"].nav-item`);
      this.loadingOverlayTop = tabMenu?.offsetHeight;
    },
  },
};
</script>
