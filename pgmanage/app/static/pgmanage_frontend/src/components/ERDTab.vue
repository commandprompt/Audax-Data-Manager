<template>
  <div ref="erdContainer">
    <div class="position-relative">
      <div class="floating-toolbar floating-toolbar--filled floating-toolbar--right-top">
        <span class="floating-toolbar__content">
          <button class="btn btn-icon-secondary" @click="resetToDefault" title="Reset to default">
            <i class="fa-solid fa-rotate-left"></i>
          </button>

          <span class="divider"></span>

          <!-- Zoom Out -->
          <button class="btn btn-icon-secondary" @click="zoomOut" title="Zoom Out">
            <i class="fas fa-search-minus"></i>
          </button>
          <!-- Zoom In -->
          <button class="btn btn-icon-secondary" @click="zoomIn" title="Zoom In">
            <i class="fas fa-search-plus"></i>
          </button>

          <button :id="`bt_fullscreen_${tabId}`" type="button"
          class="btn btn-icon-secondary" title='Fullscreen' @click="toggleFullScreen()">
              <i :class="inFullscreen ? 'fas fa-compress':'fas fa-expand'"></i>
          </button>
        </span>
      </div>
      <div class="vh-100 w-100 invisible" ref="cyContainer"></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import ShortUniqueId from 'short-unique-id'
import cytoscape from 'cytoscape';
import nodeHtmlLabel from 'cytoscape-node-html-label'
import { handleError } from '../logging/utils';
import debounce from 'lodash/debounce'
import isEmpty from 'lodash/isEmpty';


export default {
  name: "ERDTab",
  props: {
    schema: String,
    workspaceId: String,
    tabId: String,
    databaseIndex: Number,
    databaseName: String,
  },
  setup(props) {
    if (typeof cytoscape("core", "nodeHtmlLabel") === "undefined")
      nodeHtmlLabel(cytoscape);
  },
  data() {
    return {
      nodes: [],
      edges: [],
      cy: {},
      layout: {},
      instance_uid: '',
      options: {
        boxSelectionEnabled: false,
        wheelSensitivity: 0.4,
        style: [
          {
            selector: 'node',
            style: {
              "shape": "round-rectangle",
              "background-color": "#F8FAFC",
              "background-opacity": 1,
              "height": 40,
              "width": 140,
              shape: "round-rectangle",
            }
          },
          {
            selector: 'edge',
            style: {
              'curve-style': 'straight',
              'target-arrow-shape': 'triangle',
              'width': 2,
              'line-style': 'solid'
            }
          },
          {
            selector: 'edge:selected',
            style: {
              'width': 4,
              'line-color': '#F76707',
              'target-arrow-color': '#F76707',
              'source-arrow-color': '#F76707',
            }
          },
        ],
      },
      inFullscreen: false,
    };
  },
  mounted() {
    this.loadSchemaGraph()
    this.instance_uid = new ShortUniqueId({dictionary: 'alpha_upper', length: 4}).randomUUID()
  },
  updated() {
    this.$refs.cyContainer.classList.remove('invisible');
  },
  methods: {
    resetToDefault() {
      this.layout = this.cy.layout({
          name: "grid",
          padding: 50,
          spacingFactor: 0.85,
        })

        setTimeout(() => {
        this.adjustSizes()
        this.saveGraphState();
      }, 100)
    },
    loadSchemaGraph() {
      axios.post('/draw_graph/', {
        database_index: this.databaseIndex,
        workspace_id: this.workspaceId,
        schema: this.schema,
      })
      .then((response) => {
        if (response.data.layout) {
          this.jsonLayout = response.data.layout
          this.new_nodes = response.data.new_nodes
          this.new_edges = response.data.new_edges
        } else {
          this.nodes = response.data.nodes.map((node) => (
            {
              data: {
                id: node.id,
                html_id: node.id.replace(/[^a-zA-Z_.-:]+/, '_'),
                label: node.label,
                columns: node.columns.map((column) => (
                  {
                    name: column.name,
                    type: column.type,
                    cgid: column.cgid,
                    is_pk: column.is_pk,
                    is_fk: column.is_fk,
                    is_highlighted: false
                  }
                )),
                type: 'table'
              },
              position: node?.position ?? {},
              classes: 'group' + node.group
            }
          ))
  
          this.edges = response.data.edges.map((edge) => (
            {
              data: {
                source: edge.from,
                target: edge.to,
                source_col: edge.from_col,
                target_col: edge.to_col,
                label: edge.label,
                cgid: edge.cgid
              }
            }
          ))
        }
      })
      .then(() => { this.initGraph() })
      .catch((error) => {
        handleError(error);
      })
    },
    columnClass(column) {
      let classes = []
      if(column.is_pk)
        classes.push('pk-column')
      if(column.is_fk)
        classes.push('fk-column')
      if(column.is_highlighted)
        classes.push('highlighted')
      return classes.join(' ')
    },
    initGraph() {
      if (this.jsonLayout) {
        this.cy = cytoscape({
          container: this.$refs.cyContainer,
          ...this.options,
          elements: [],
        })
        this.cy.json(this.jsonLayout)

        if (this.new_nodes && this.new_nodes.length > 0) {
          const formattedNodes = this.new_nodes.map(node => ({
            group: 'nodes',
            data: {
              id: node.id,
              html_id: node.id.replace(/[^a-zA-Z_.-:]+/, '_'),
              label: node.label,
              columns: node.columns.map((column) => (
                  {
                    name: column.name,
                    type: column.type,
                    cgid: column.cgid,
                    is_pk: column.is_pk,
                    is_fk: column.is_fk,
                    is_highlighted: false
                  }
                )),
              type: 'table'
            },
            classes: 'group' + node.group
          }));
          this.cy.add(formattedNodes);
        }

        if (this.new_edges && this.new_edges.length > 0) {
          const formattedEdges = this.new_edges.map(edge => ({
            group: 'edges',
            data: {
              source: edge.from,
                target: edge.to,
                source_col: edge.from_col,
                target_col: edge.to_col,
                label: edge.label,
                cgid: edge.cgid
            }
          }));
          this.cy.add(formattedEdges);
        }
        
      } else {
        this.cy = cytoscape({
          container: this.$refs.cyContainer,
          ...this.options,
          elements: {
            selectable: true,
            grabbable: false,
            nodes: [...this.nodes],
            edges: [...this.edges]
          }
        })
        this.layout = this.cy.layout({
          name: "grid",
          padding: 50,
          spacingFactor: 0.85,
        })
        
      }
      setTimeout(() => {
        this.adjustSizes();
      }, 100);
    
      this.setupEvents();

      this.cy.nodeHtmlLabel(
        [{
          query: 'node',
          cssClass: 'erd-card',
          tpl: (function(data) {
            let coldivs = ''
            if (data.columns)
              coldivs = data.columns.map((c) => {
                let dataAttr = c.cgid ? `data-cgid="${c.cgid}"` : ''
                let colName = c.is_fk ?
                `<a ${dataAttr} href="#" class="erd-card__column_name">${c.name}</a>` :
                `<span class="erd-card__column_name">${c.name}</span>`
                return `<div ${dataAttr} class="erd-card__column ${this.columnClass(c)}">
                      ${colName}
                  <span class="erd-card__column_type">${c.type}</span>
                </div>`
              }).join('')

            return `<div class="erd-card__wrap"><div id="${this.instance_uid}-${data.html_id}">
                <h3 class="erd-card__title clipped-text" title="${data.label}">${data.label}</h3>
                ${coldivs}
            </div></div>`;
          }).bind(this)
        }],
      )

      this.$refs.cyContainer.classList.remove('invisible');
    },
    adjustSizes() {
      const padding = 2;
      this.cy.nodes().forEach((node) => {
        let el = document.querySelector(`#${this.instance_uid}-${node.data().html_id}`)
        if (el) {
          node.style('width', el.parentElement.clientWidth + padding)
          node.style('height', el.parentElement.clientHeight + padding)
        }
      })
      if (!isEmpty(this.layout)) {
        this.layout.run();
        this.cy.fit();
      }
    },
    saveGraphState() {
      const layoutData = this.cy.json(); 

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
    setupEvents() {
      this.cy.on('select unselect', 'edge', function(evt) {
        let should_highlight = evt.type == 'select'
        let {source_col, target_col} = evt.target.data()
        let edge = evt.target
        let srccols = edge.source().data('columns')
        srccols.find((c) => c.name === source_col).is_highlighted = should_highlight
        edge.source().data('columns', srccols)
        let dstcols = edge.target().data('columns')
        dstcols.find((c) => c.name === target_col).is_highlighted = should_highlight
        edge.target().data('columns', dstcols)
      });

      this.cy.on('click', 'node', function (evt) {
        if (evt.originalEvent) {
          const element = document.elementFromPoint(evt.originalEvent.clientX, evt.originalEvent.clientY);
          if(element.dataset.cgid) {
            let edge = this.cy().edges().filter(( ele ) => ele.data('cgid') === element.dataset.cgid)
            setTimeout(() => {edge.select()}, 1)
          }
        }
      });

      this.cy.on("dragfree", () => {
        this.saveGraphState();
      });

      this.cy.on('viewport', debounce(() => {
        this.saveGraphState();
      }, 500));
    },
    zoomIn() {
      if (this.cy) {
        const currentZoom = this.cy.zoom();
        this.cy.zoom({
          level: currentZoom * 1.2,
          renderedPosition: { x: this.cy.width() / 2, y: this.cy.height() / 2 }
        });
      }
    },
    zoomOut() {
      if (this.cy) {
        const currentZoom = this.cy.zoom();
        this.cy.zoom({
          level: currentZoom * 0.8,
          renderedPosition: { x: this.cy.width() / 2, y: this.cy.height() / 2 }
        });
      }
    },
    toggleFullScreen() {
      this.$refs.erdContainer.classList.toggle("omnidb__panel-view--full");
      this.inFullscreen = !this.inFullscreen;
    },
  },
};
</script>

<style scoped>

</style>