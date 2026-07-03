<template>
  <div ref="erdContainer">
    <Controls 
    :in-fullscreen="inFullscreen"
    @screenshot="doScreenshot"
    @reset="resetToDefault"
    @zoom-in="this.$refs.vueFlow.zoomIn()"
    @zoom-out="this.$refs.vueFlow.zoomOut()"
    @toggle-fullscreen="toggleFullScreen"
      />
    <VueFlow
      class="vh-100"
      ref="vueFlow"
      :node-types="nodeTypes"
      :nodes="nodes"
      :edges="edges"
      min-zoom="0.1"
      @nodes-initialized="()=> {if (!jsonLayout) this.$refs.vueFlow.fitView();}"
      @viewport-change-end="saveGraphState"
      @node-drag-stop="onNodeDragStop"
      @node-drag="scheduleRerouteEdges"
      @edge-click="onEdgeClick"
      @node-click="onNodeClick"
      @pane-click="clearErdSelection"
    >
      <Background variant="dots" />
    </VueFlow>
  </div>
</template>

<script>
import axios from 'axios'
import { handleError } from '../logging/utils';
import { VueFlow, MarkerType } from '@vue-flow/core';
import { Background } from '@vue-flow/background'
import { markRaw } from 'vue';
import { capture } from '@src/erd_plugins/screenshot';
import TableNode from '@src/erd_plugins/TableNode.vue';
import ColumnNode from '@src/erd_plugins/ColumnNode.vue';
import Controls from '@src/erd_plugins/Controls.vue';
import {
  TABLE_WIDTH,
  TABLE_HEADER_HEIGHT,
  COLUMN_HEIGHT,
  getLayoutedNodes,
} from '@src/erd_plugins/layout';

// TODO:
// 8.Crowfoot notation markers

export default {
  name: "ERDTab",
  components: {
    VueFlow,
    Background,
    Controls,
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
    };
  },
  mounted() {
    this.loadSchemaGraph()
  },
  methods: {
    doScreenshot() {
      capture(this.$refs.vueFlow.vueFlowRef, { shouldDownload: true });
    },
    resetToDefault() {
      this.nodes = getLayoutedNodes(this.$refs.vueFlow.nodes);

      this.$nextTick(() => {
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
              class: 'erd-card d-block text-center',
              style: {
                width: `${TABLE_WIDTH}px`,
                height: `${TABLE_HEADER_HEIGHT + node.columns.length * COLUMN_HEIGHT}px`,
              },
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
            
          this.edges = response.data.edges.map((edge) => this.createEdge(edge))

          this.nodes = getLayoutedNodes(
            [...tableNodes, ...columnNodes],
            this.edges,
            {
              padding: 50,
              spacingFactor: 0.85,
                columnsPerRow: 5,
            }
          )
          this.$nextTick(() => {
            this.rerouteEdgesByTableDistance();
          })
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
              style: {
                ...(node.style || {}),
                width: `${TABLE_WIDTH}px`,
                height: `${TABLE_HEADER_HEIGHT + tableData.columns.length * COLUMN_HEIGHT}px`,
              },
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
        this.rerouteEdgesByTableDistance();
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
        class: 'erd-card d-block text-center',
        style: {
          width: `${TABLE_WIDTH}px`,
          height: `${TABLE_HEADER_HEIGHT + node.columns.length * COLUMN_HEIGHT}px`,
        },
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
        style: {
          width: `${TABLE_WIDTH}px`,
          height: `${COLUMN_HEIGHT}px`,
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
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#ff0072',
        },
        markerStart: {
          type: MarkerType.ArrowClosed,
          color: '#ff0072',
        },
        data: {
          cgid: edge.cgid,
          sourceTableId: edge.from,
          targetTableId: edge.to,
        },
      }
    },
    clearErdSelection() {
      this.edges.forEach((edge) => {
        edge.selected = false;
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
      if (node.type !== "column") {
        this.clearErdSelection();
        return;
      }

      const relatedEdges = this.getRelatedEdgesForColumn(node);

      if (!relatedEdges.length) {
        this.clearErdSelection();
        return;
      }

      this.selectErdEdges(relatedEdges);
    },
    getRelatedEdgesForColumn(columnNode) {
      const columnId = columnNode.id;
      const columnCgid = columnNode.data?.cgid;

      return this.edges.filter((edge) => {
        const edgeCgid = edge?.cgid;

        return (
          edge.source === columnId ||
          edge.target === columnId ||
          Boolean(columnCgid && edgeCgid && columnCgid === edgeCgid)
        );
      });
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
        if (edge.selected !== shouldBeSelected) {
          edge.selected = shouldBeSelected;
        }
      });

      this.nodes.forEach((node) => {
        if (node.type !== "column") {
          return;
        }

        const shouldBeHighlighted = highlightedColumnIds.has(node.id);

        if (!node.data) {
          node.data = {};
        }

        if (node.data.is_highlighted !== shouldBeHighlighted) {
          node.data.is_highlighted = shouldBeHighlighted;
        }
      });
      this.edges = [...this.edges];
    },
    getCurrentFlowNodes() {
      const flowState = this.$refs.vueFlow?.toObject?.();
    
      return flowState?.nodes;
    },  
    getTableBounds(tableNode) {
      const width = parseInt(tableNode.style.width, 10);
      const height = parseInt(tableNode.style.height, 10);
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
    
      const rightToLeftDistance = Math.abs(sourceBounds.right - targetBounds.left);
      const leftToRightDistance = Math.abs(sourceBounds.left - targetBounds.right);
    
      if (rightToLeftDistance <= leftToRightDistance) {
        return {
          sourceHandle: 'source-right',
          targetHandle: 'target-left',
        };
      }
    
      return {
        sourceHandle: 'source-left',
        targetHandle: 'target-right',
      };
    },
    rerouteEdgesByTableDistance() {
      const currentNodes = this.getCurrentFlowNodes();
      let changed = false;
    
      this.edges.forEach((edge) => {
        const route = this.getBestHorizontalRoute(edge, currentNodes);
    
        if (!route) {
          return;
        }
    
        if (
          edge.sourceHandle !== route.sourceHandle ||
          edge.targetHandle !== route.targetHandle
        ) {
          edge.sourceHandle = route.sourceHandle;
          edge.targetHandle = route.targetHandle;
          changed = true;
        }
      })
    
      if (changed) {
        this.edges = [...this.edges];
      }
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
  },
};
</script>
