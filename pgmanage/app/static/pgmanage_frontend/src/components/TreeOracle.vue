<template>
  <PowerTree ref="tree" v-model="nodes" @nodedblclick="doubleClickNode" @toggle="onToggle"
    @nodecontextmenu="onContextMenu" :allow-multiselect="false" @nodeclick="onClickHandler" @click="handleLeftSideClick" @dblclick="handleLeftSideDblClick" tabindex="0">
    <template v-slot:toggle="{ node }">
      <i v-if="node.isExpanded" class="exp_col fas fa-chevron-down fa-sm"></i>
      <i v-if="!node.isExpanded" class="exp_col fas fa-chevron-right fa-sm"></i>
    </template>

    <template v-slot:title="{ node }">
      <span class="item-icon">
        <i :class="['icon_tree', node.data.icon]"></i>
      </span>
      <span v-if="node.data.raw_html" v-html="node.title"> </span>
      <span v-else>
        {{ formatTitle(node) }}
      </span>
    </template>
  </PowerTree>
</template>

<script>
import TreeMixin from "../mixins/power_tree.js";
import { PowerTree } from "@onekiloparsec/vue-power-tree";
import DropDbObjectMixin from "../mixins/power_tree_drop_db_object_mixin.js";
import {
  TemplateUpdateOracle,
  TemplateInsertOracle,
  TemplateSelectOracle,
} from "../tree_context_functions/tree_oracle";
import { tabSQLTemplate } from "../tree_context_functions/tree_postgresql";
import { emitter } from "../emitter";
import { tabsStore } from "../stores/stores_initializer";
import { findNode, findChild } from "../utils.js";
import { operationModes } from "../constants";

export default {
  name: "TreeOracle",
  components: {
    PowerTree,
  },
  mixins: [TreeMixin, DropDbObjectMixin],
  props: {
    databaseIndex: {
      type: Number,
      required: true,
    },
    workspaceId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      nodes: [
        {
          title: "Oracle",
          isExpanded: false,
          isDraggable: false,
          data: {
            icon: "node node-oracle",
            type: "server",
            contextMenu: "cm_server",
          },
        },
      ],
      templates: "",
      cm_server_extra: [],
    };
  },
  computed: {
    contextMenu() {
      return {
        cm_server: [this.cmRefreshObject, ...this.cm_server_extra],
        cm_database: [
          {
            label: "ER Diagram",
            icon: "fab fa-hubspot",
            onClick: () => {
              tabsStore.createERDTab(this.templates.username)
            },
          },
        ],
        cm_tables: [
          this.cmRefreshObject,
          {
            label: "Create Table",
            icon: "fas fa-plus",
            onClick: () => {
              tabsStore.createSchemaEditorTab(this.selectedNode, operationModes.CREATE)
            },
          },
        ],
        cm_table: [
          this.cmRefreshObject,
          {
            label: "Query Data",
            icon: "fas fa-search",
            onClick: () => {
              TemplateSelectOracle(
                this.templates.username,
                this.selectedNode.data.raw_value
              );
            },
          },
          {
            label: "Edit Data",
            icon: "fas fa-table",
            onClick: () => {
              tabsStore.createDataEditorTab(this.selectedNode.title, this.templates.username)
            },
          },
          {
            label: "Alter Table",
            icon: "fas fa-edit",
            onClick: () => {
              tabsStore.createSchemaEditorTab(this.selectedNode, operationModes.UPDATE)
            },
          },
          {
            label: "Templates",
            icon: "fas fa-list",
            children: [

              {
                label: "Insert Record",
                icon: "fas fa-edit",
                onClick: () => {
                  TemplateInsertOracle(
                    this.templates.username,
                    this.selectedNode.data.raw_value
                  );
                },
              },
              {
                label: "Update Records",
                icon: "fas fa-edit",
                onClick: () => {
                  TemplateUpdateOracle(
                    this.templates.username,
                    this.selectedNode.data.raw_value
                  );
                },
              },
              {
                label: "Delete Records",
                icon: "fas fa-times",
                onClick: () => {
                  tabSQLTemplate(
                    "Delete Records",
                    this.templates.delete.replace(
                      "#table_name#",
                      `${this.templates.username}.${this.selectedNode.data.raw_value}`
                    )
                  );
                },
              },
            ],
          },
          {
            label: "Drop Table",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_table.replace(
                  "#table_name#",
                  `${this.templates.username}.${this.selectedNode.data.raw_value}`
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_columns: [
          {
            label: "Create Column",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Field",
                this.templates.create_column.replace(
                  "#table_name#",
                  `${this.templates.username}.${this.getParentNode(this.selectedNode).title
                  }`
                )
              );
            },
          },
        ],
        cm_column: [
          {
            label: "Alter Column",
            icon: "fas fa-edit",
            onClick: () => {
              tabSQLTemplate(
                "Alter Column",
                this.templates.alter_column
                  .replace(
                    "#table_name#",
                    `${this.templates.username}.${this.getParentNodeDeep(this.selectedNode, 2).title
                    }`
                  )
                  .replace(/#column_name#/g, this.selectedNode.title)
              );
            },
          },
          {
            label: "Drop Column",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_column
                  .replace(
                    "#table_name#",
                    `${this.templates.username}.${this.getParentNodeDeep(this.selectedNode, 2).title
                    }`
                  )
                  .replace(/#column_name#/g, this.selectedNode.title)
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_pks: [
          this.cmRefreshObject,
          {
            label: "Create Primary Key",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Primary Key",
                this.templates.create_primarykey.replace(
                  "#table_name#",
                  `${this.templates.username}.${this.getParentNode(this.selectedNode).title
                  }`
                )
              );
            },
          },
        ],
        cm_pk: [
          this.cmRefreshObject,
          {
            label: "Drop Primary Key",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_primarykey
                  .replace(
                    "#table_name#",
                    `${this.templates.username}.${this.getParentNodeDeep(this.selectedNode, 2).title
                    }`
                  )
                  .replace("#constraint_name#", this.selectedNode.title)
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_fks: [
          this.cmRefreshObject,
          {
            label: "Create Foreign Key",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Foreign Key",
                this.templates.create_foreignkey.replace(
                  "#table_name#",
                  `${this.templates.username}.${this.getParentNode(this.selectedNode).title
                  }`
                )
              );
            },
          },
        ],
        cm_fk: [
          this.cmRefreshObject,
          {
            label: "Drop Foreign Key",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_foreignkey
                  .replace(
                    "#table_name#",
                    `${this.templates.username}.${this.getParentNodeDeep(this.selectedNode, 2).title
                    }`
                  )
                  .replace("#constraint_name#", this.selectedNode.title)
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_uniques: [
          this.cmRefreshObject,
          {
            label: "Create Unique",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Unique",
                this.templates.create_unique.replace(
                  "#table_name#",
                  `${this.templates.username}.${this.getParentNode(this.selectedNode).title
                  }`
                )
              );
            },
          },
        ],
        cm_unique: [
          this.cmRefreshObject,
          {
            label: "Drop Unique",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_unique
                  .replace(
                    "#table_name#",
                    `${this.templates.username}.${this.getParentNodeDeep(this.selectedNode, 2).title
                    }`
                  )
                  .replace("#constraint_name#", this.selectedNode.title)
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_indexes: [
          this.cmRefreshObject,
          {
            label: "Create Index",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Index",
                this.templates.create_index.replace(
                  "#table_name#",
                  `${this.templates.username}.${this.getParentNode(this.selectedNode).title
                  }`
                )
              );
            },
          },
        ],
        cm_index: [
          this.cmRefreshObject,
          {
            label: "Alter Index",
            icon: "fas fa-edit",
            onClick: () => {
              tabSQLTemplate(
                "Alter Index",
                this.templates.alter_index.replace(
                  "#index_name#",
                  `${this.templates.username}.${this.selectedNode.data.raw_value}`
                )
              );
            },
          },
          {
            label: "Drop Index",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_index.replace(
                  "#index_name#",
                  `${this.templates.username}.${this.selectedNode.data.raw_value}`
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_sequences: [
          this.cmRefreshObject,
          {
            label: "Create Sequence",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Sequence",
                this.templates.create_sequence.replace(
                  "#schema_name#",
                  this.templates.username
                )
              );
            },
          },
        ],
        cm_sequence: [
          {
            label: "Alter Sequence",
            icon: "fas fa-edit",
            onClick: () => {
              tabSQLTemplate(
                "Alter Sequence",
                this.templates.alter_sequence.replace(
                  "#sequence_name#",
                  `${this.templates.username}.${this.selectedNode.title}`
                )
              );
            },
          },
          {
            label: "Drop Sequence",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_sequence.replace(
                  "#sequence_name#",
                  `${this.templates.username}.${this.selectedNode.title}`
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_views: [
          this.cmRefreshObject,
          {
            label: "Create View",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create View",
                this.templates.create_view.replace(
                  "#schema_name#",
                  this.templates.username
                )
              );
            },
          },
        ],
        cm_view: [
          this.cmRefreshObject,
          {
            label: "Query Data",
            icon: "fas fa-search",
            onClick: () => {
              // FIX this to use TemplateSelectMariadb
              let table_name = `${this.templates.username}.${this.selectedNode.title}`;
              
              let command = `-- Querying Data\nselect t.*\nfrom ${table_name} t`

              tabsStore.createQueryTab(this.selectedNode.title, null, null, command)

              setTimeout(() => {
                emitter.emit(`${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_run_query`, command)
              }, 200)
            },
          },
          {
            label: "Edit View",
            icon: "fas fa-edit",
            onClick: () => {
              this.getViewDefinitionOracle(this.selectedNode);
            },
          },
          {
            label: "Drop View",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_view.replace(
                  "#view_name#",
                  `${this.templates.username}.${this.selectedNode.title}`
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_functions: [
          this.cmRefreshObject,
          {
            label: "Create Function",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Function",
                this.templates.create_function.replace(
                  "#schema_name#",
                  this.templates.username
                )
              );
            },
          },
        ],
        cm_function: [
          this.cmRefreshObject,
          {
            label: "Edit Function",
            icon: "fas fa-edit",
            onClick: () => {
              this.getFunctionDefinitionOracle(this.selectedNode);
            },
          },
          {
            label: "Drop Function",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_function.replace(
                  "#function_name#",
                  this.selectedNode.data.id
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_procedures: [
          this.cmRefreshObject,
          {
            label: "Create Procedure",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Procedure",
                this.templates.create_procedure.replace(
                  "#schema_name#",
                  this.templates.username
                )
              );
            },
          },
        ],
        cm_procedure: [
          this.cmRefreshObject,
          {
            label: "Edit Procedure",
            icon: "fas fa-edit",
            onClick: () => {
              this.getProcedureDefinitionOracle(this.selectedNode);
            },
          },
          {
            label: "Drop Prodecure",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_procedure.replace(
                  "#function_name#",
                  this.selectedNode.data.id
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_tablespaces: [
          this.cmRefreshObject,
          {
            label: "Create Tablespace",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate(
                "Create Tablespace",
                this.templates.create_tablespace
              );
            },
          },
        ],
        cm_tablespace: [
          {
            label: "Alter Tablespace",
            icon: "fas fa-edit",
            onClick: () => {
              tabSQLTemplate(
                "Alter Tablespace",
                this.templates.alter_tablespace.replace(
                  "#tablespace_name#",
                  this.selectedNode.title
                )
              );
            },
          },
          {
            label: "Drop Tablespace",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              let template = this.templates.drop_tablespace.replace(
                  "#tablespace_name#",
                  this.selectedNode.title
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
        cm_roles: [
          this.cmRefreshObject,
          {
            label: "Create Role",
            icon: "fas fa-plus",
            onClick: () => {
              tabSQLTemplate("Create Role", this.templates.create_role);
            },
          },
        ],
        cm_role: [
          {
            label: "Alter Role",
            icon: "fas fa-edit",
            onClick: () => {
              tabSQLTemplate(
                "Alter Role",
                this.templates.alter_role.replace(
                  "#role_name#",
                  this.selectedNode.title
                )
              );
            },
          },
          {
            label: "Drop Role",
            icon: "fas fa-times",
            divided: "up",
            onClick: () => {
              // FIXME: this does not work, we need to differentiate users and roles
              let template = this.templates.drop_role.replace(
                  "#role_name#",
                  this.selectedNode.title
                )
              this.prepareDropModal(this.selectedNode, template)
            },
          },
        ],
      };
    },
  },
  mounted() {
    this.$nextTick(() => {
      setTimeout(() => {
        this.doubleClickNode(this.getRootNode())
        let databaseNode = this.$refs.tree.getNode([0, 0])
        if (databaseNode)
          this.doubleClickNode(databaseNode)
      }, 100)
      setTimeout(() => {
        let tablesNode = this.$refs.tree.getNode([0, 0, 0])
        if (tablesNode)
          this.doubleClickNode(tablesNode)
      }, 100)
    })

    emitter.on(`schemaChanged_${this.workspaceId}`, () => {
      const tree = this.$refs.tree;
      let db_node = tree.getNextNode([0], (node) => {
        return node.data.type === "database";
      });

      let tables_node = tree.getNextNode(db_node.path, (node) => {
        return node.data.type === "table_list";
      });

      this.refreshTree(tables_node, true);
    });

    emitter.on(`goToNode_${this.workspaceId}`, async({ name, type}) => {
      const rootNode = this.getRootNode()

      // Step 1: Find  database node
      const databaseNode = findNode(rootNode, node => node.title === this.selectedDatabase && node.data.type === 'database');
      if (!databaseNode) return;

      await this.expandAndRefreshIfNeeded(databaseNode);
      const updateddatabaseNode = this.$refs.tree.getNode(databaseNode.path)

      // Step 2: Find '_list' that we need
      const containerType = `${type}_list`;
      const containerNode = findChild(updateddatabaseNode, containerType);
      if (!containerNode) return;
      await this.expandAndRefreshIfNeeded(containerNode);

      const updatedContainerNode = this.$refs.tree.getNode(containerNode.path)

      // Step 2: Find the target node
      const targetNode = findNode(updatedContainerNode, node => node.title === name && node.data.type === type);
      if (!targetNode) return;

      // Step 3: Select and scroll to it
      this.goToNodeAndSelect(targetNode);
    })
  },
  unmounted() {
    emitter.all.delete(`schemaChanged_${this.workspaceId}`);
    emitter.all.delete(`goToNode_${this.workspaceId}`);
  },
  methods: {
    async refreshTree(node, force) {
      if (!this.shouldUpdateNode(node, force)) return
      if (node.children.length == 0) this.insertSpinnerNode(node);
      if (node.data.type == "server") {
        return this.getTreeDetailsOracle(node);
      } else if (node.data.type == "database") {
        return this.getDatabaseObjectsOracle(node);
      } else if (node.data.type == "table_list") {
        return this.getTablesOracle(node);
      } else if (node.data.type == "table") {
        this.getColumnsOracle(node);
      } else if (node.data.type == "primary_key") {
        this.getPKOracle(node);
      } else if (node.data.type == "pk") {
        this.getPKColumnsOracle(node);
      } else if (node.data.type == "foreign_keys") {
        this.getFKsOracle(node);
      } else if (node.data.type == "foreign_key") {
        this.getFKsColumnsOracle(node);
      } else if (node.data.type == "uniques") {
        this.getUniquesOracle(node);
      } else if (node.data.type == "unique") {
        this.getUniquesColumnsOracle(node);
      } else if (node.data.type == "indexes") {
        this.getIndexesOracle(node);
      } else if (node.data.type == "index") {
        this.getIndexesColumnsOracle(node);
      } else if (node.data.type == "sequence_list") {
        this.getSequencesOracle(node);
      } else if (node.data.type == "view_list") {
        return this.getViewsOracle(node);
      } else if (node.data.type == "view") {
        this.getViewsColumnsOracle(node);
      } else if (node.data.type == "function_list") {
        this.getFunctionsOracle(node);
      } else if (node.data.type == "function") {
        this.getFunctionFieldsOracle(node);
      } else if (node.data.type == "procedure_list") {
        this.getProceduresOracle(node);
      } else if (node.data.type == "procedure") {
        this.getProcedureFieldsOracle(node);
      } else if (node.data.type == "tablespace_list") {
        this.getTablespacesOracle(node);
      } else if (node.data.type == "role_list") {
        this.getRolesOracle(node);
      }
    },
    getProperties(node) {
      let table;
      switch (node.data.type) {
        case "trigger":
          table = this.getParentNodeDeep(node, 2).title;
          break;
        default:
          table = null;
      }
      const handledTypes = [
        "role",
        "tablespace",
        "table",
        "sequence",
        "view",
        "mview",
        "function",
        "procedure",
        "trigger",
        "triggerfunction",
      ];

      if (handledTypes.includes(node.data.type)) {
        this.$emit("treeTabsUpdate", {
          data: {
            table: table,
            object: node.data.raw_value ?? node.title,
            type: node.data.type,
            schema: null,
          },
          view: "/get_properties_oracle/"
        })
      } else {
        this.$emit("clearTabs");
      }
    },
    async getTreeDetailsOracle(node) {
      try {
        const response = await this.api.post("/get_tree_info_oracle/")

        this.removeChildNodes(node);

        this.$refs.tree.updateNode(node.path, {
          title: response.data.formatted_version,
        });

        this.templates = response.data;

        if (response.data.superuser) {
          this.cm_server_extra = [{
            label: "Monitoring",
            icon: "fas fa-chart-line",
            children: [
              {
                label: "Sessions",
                icon: "fas fa-tasks",
                onClick: () => {
                  tabsStore.createMonitoringTab("Sessions", `
                  /*pgmanage-dash*/ 
                  select sid,
                  serial#,
                  username,
                  service_name,
                  status,
                  state,
                  osuser,
                  machine,
                  program,
                  module,
                  action,
                  type,
                  logon_time 
                  from v$session 
                  WHERE username IS NOT NULL`)
                },
              },
            ],
          }];

          this.insertNode(node, "Roles", {
            icon: "fas node-all fa-users node-user-list",
            type: "role_list",
            contextMenu: "cm_roles",
          });

          this.insertNode(node, "Tablespaces", {
            icon: "fas node-all fa-folder-open node-tablespace-list",
            type: "tablespace_list",
            contextMenu: "cm_tablespaces",
          });
        }

        this.insertNode(node, response.data.database, {
          icon: "fas node-all fa-database node-database-list",
          type: "database",
          contextMenu: "cm_database",
        });
      } catch(error) {
        this.nodeOpenError(error, node);
      }
    },
    async getDatabaseObjectsOracle(node) {
      this.removeChildNodes(node);
      return new Promise((resolve, reject) => {
        try {
          this.insertNode(node, "Procedures", {
            icon: "fas node-all fa-cog node-procedure-list",
            type: "procedure_list",
            contextMenu: "cm_procedures",
          });
    
          this.insertNode(node, "Functions", {
            icon: "fas node-all fa-cog node-function-list",
            type: "function_list",
            contextMenu: "cm_functions",
          });
    
          this.insertNode(node, "Views", {
            icon: "fas node-all fa-eye node-view-list",
            type: "view_list",
            contextMenu: "cm_views",
          });
    
          this.insertNode(node, "Sequences", {
            icon: "fas node-all fa-sort-numeric-down node-sequence-list",
            type: "sequence_list",
            contextMenu: "cm_sequences",
          });
    
          this.insertNode(node, "Tables", {
            icon: "fas node-all fa-th node-table-list",
            type: "table_list",
            contextMenu: "cm_tables",
            schema: this.templates.username,
          });
        resolve("success")
        } catch(error) {
          reject(error)
        }
      })
    },
    async getTablesOracle(node) {
      try {
        const response = await this.api.post("/get_tables_oracle/")
        this.removeChildNodes(node);

        this.$refs.tree.updateNode(node.path, {
          title: `Tables (${response.data.length})`,
        });

        let childNodes = response.data.map((el) => {
          return {
            title: el.name,
            isLeaf: false,
            isExpanded: false,
            isDraggable: false,
            data: {
              icon: "fas node-all fa-table node-table",
              type: "table",
              contextMenu: "cm_table",
              raw_value: el.name_raw,
              schema: node.data.schema,
            },
          }
        });

        this.insertNodes(node, childNodes);
      } catch(error) {
        this.nodeOpenError(error, node);
      }
    },
    getColumnsOracle(node) {
      this.api
        .post("/get_columns_oracle/", {
          table: node.data.raw_value,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          let columnsData = resp.data.map((el) => {
            return {
              title: el.column_name,
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-columns node-column",
                type: "table_field",
                contextMenu: "cm_column",
              },
              children: [
                {
                  title: `Type: ${el.data_type}`,
                  isLeaf: true,
                  isExpanded: false,
                  isDraggable: false,
                  data: {
                    icon: "fas node-all fa-ellipsis-h node-bullet",
                    schema: node.data.schema,
                  },
                },
                {
                  title: `Nullable: ${el.nullable}`,
                  isLeaf: true,
                  isExpanded: false,
                  isDraggable: false,
                  data: {
                    icon: "fas node-all fa-ellipsis-h node-bullet",
                    schema: node.data.schema,
                  },
                },
              ],
            }
          });

          let tableEntities = [
            {
              title: `Columns (${resp.data.length})`,
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-columns node-column",
                type: "column_list",
                contextMenu: "cm_columns",
              },
              children: columnsData,
            },
            {
              title: "Primary Key",
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-key node-pkey",
                type: "primary_key",
                contextMenu: "cm_pks",
              },
            },
            {
              title: "Foreign Keys",
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-key node-fkey",
                type: "foreign_keys",
                contextMenu: "cm_fks",
              },
            },
            {
              title: "Uniques",
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-key node-unique",
                type: "uniques",
                contextMenu: "cm_uniques",
              },
            },
            {
              title: "Indexes",
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-thumbtack node-index",
                type: "indexes",
                contextMenu: "cm_indexes",
                schema: node.data.schema,
              },
            },
          ];
          
          this.insertNodes(node, tableEntities);
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getPKOracle(node) {
      this.api
        .post("/get_pk_oracle/", {
          table: this.getParentNode(node).title,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          this.$refs.tree.updateNode(node.path, {
            title: `Primary Key (${resp.data.length})`,
          });

          resp.data.forEach((el) => {
            this.insertNode(node, el, {
              icon: "fas node-all fa-key node-pkey",
              type: "pk",
              contextMenu: "cm_pk",
            });
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getPKColumnsOracle(node) {
      this.api
        .post("/get_pk_columns_oracle/", {
          key: node.title,
          table: this.getParentNodeDeep(node, 2).title,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          resp.data.forEach((el) => {
            this.insertNode(
              node,
              el,
              {
                icon: "fas node-all fa-columns node-column",
              },
              true
            );
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getFKsOracle(node) {
      this.api
        .post("/get_fks_oracle/", {
          table: this.getParentNode(node).title,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          this.$refs.tree.updateNode(node.path, {
            title: `Foreign Keys (${resp.data.length})`,
          });

          let childNodes = resp.data.map((el) => {
            return {
              title: el,
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-key node-fkey",
                type: "foreign_key",
                contextMenu: "cm_fk",
              }
            }
          })

          this.insertNodes(node, childNodes);
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getFKsColumnsOracle(node) {
      this.api
        .post("/get_fks_columns_oracle/", {
          fkey: node.title,
          table: this.getParentNodeDeep(node, 2).title,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          this.insertNode(
            node,
            `${resp.data.column_name} <i class='fas node-all fa-arrow-right'></i> ${resp.data.r_column_name}`,
            {
              icon: "fas node-all fa-columns node-column",
              raw_html: true,
            },
            true
          );
          this.insertNode(
            node,
            `Update Rule: ${resp.data.update_rule}`,
            {
              icon: "fas node-all fa-ellipsis-h node-bullet",
            },
            true
          );
          this.insertNode(
            node,
            `Delete Rule: ${resp.data.delete_rule}`,
            {
              icon: "fas node-all fa-ellipsis-h node-bullet",
            },
            true
          );
          this.insertNode(
            node,
            `Referenced Table: ${resp.data.r_table_name}`,
            {
              icon: "fas node-all fa-table node-table",
            },
            true
          );
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getUniquesOracle(node) {
      this.api
        .post("/get_uniques_oracle/", {
          table: this.getParentNode(node).title,
          schema: null,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          this.$refs.tree.updateNode(node.path, {
            title: `Uniques (${resp.data.length})`,
          });

          resp.data.forEach((el) => {
            this.insertNode(node, el, {
              icon: "fas node-all fa-key node-unique",
              type: "unique",
              contextMenu: "cm_unique",
            });
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getUniquesColumnsOracle(node) {
      this.api
        .post("/get_uniques_columns_oracle/", {
          unique: node.title,
          table: this.getParentNodeDeep(node, 2).title,
          schema: null,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          resp.data.forEach((el) => {
            this.insertNode(
              node,
              el,
              {
                icon: "fas node-all fa-columns node-column",
              },
              true
            );
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getIndexesOracle(node) {
      this.api
        .post("/get_indexes_oracle/", {
          table: this.getParentNode(node).title,
          schema: null,
        })
        .then((resp) => {
          this.removeChildNodes(node);
          this.$refs.tree.updateNode(node.path, {
            title: `Indexes (${resp.data.length})`,
          });
          resp.data.forEach((el) => {
            this.insertNode(node, el.index_name, {
              icon: "fas node-all fa-thumbtack node-index",
              type: "index",
              contextMenu: "cm_index",
              unique: el.unique ? 'Unique' : "Non unique",
              raw_value: el.name_raw,
            });
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getIndexesColumnsOracle(node) {
      this.api
        .post("/get_indexes_columns_oracle/", {
          index: node.title,
          table: this.getParentNodeDeep(node, 2).title,
          schema: null,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          resp.data.forEach((el) => {
            this.insertNode(
              node,
              el,
              {
                icon: "fas node-all fa-columns node-column",
              },
              true
            );
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getSequencesOracle(node) {
      this.api
        .post("/get_sequences_oracle/")
        .then((resp) => {
          this.removeChildNodes(node);
          this.$refs.tree.updateNode(node.path, {
            title: `Sequences (${resp.data.length})`,
          });

          resp.data.forEach((el) => {
            this.insertNode(
              node,
              el.sequence_name,
              {
                icon: "fas node-all fa-sort-numeric-down node-sequence",
                type: "sequence",
                contextMenu: "cm_sequence",
              },
              true
            );
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    async getViewsOracle(node) {
      try {
        const response = await this.api.post("/get_views_oracle/")

        this.removeChildNodes(node);

        this.$refs.tree.updateNode(node.path, {
          title: `Views (${response.data.length})`,
        });

        response.data.forEach((el) => {
          this.insertNode(node, el.name, {
            icon: "fas node-all fa-eye node-view",
            type: "view",
            contextMenu: "cm_view",
          });
        });
      } catch(error) {
        this.nodeOpenError(error, node);
      }
    },
    getViewsColumnsOracle(node) {
      this.api
        .post("/get_views_columns_oracle/", {
          table: node.title,
          schema: null,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          this.insertNode(node, `Columns (${resp.data.length})`, {
            icon: "fas node-all fa-columns node-column",
          });

          const columns_node = this.getFirstChildNode(node);

          let childNodes = resp.data.map((el) => {
            return {
              title: el.column_name,
              isLeaf: false,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-columns node-column",
                type: "table_field",
              },
              children: [
                {
                  title: `Type: ${el.data_type}`,
                  isLeaf: true,
                  isExpanded: false,
                  isDraggable: false,
                  data: {
                    icon: "fas node-all fa-ellipsis-h node-bullet",
                  },
                },
              ],
            }
          });

          this.insertNodes(columns_node, childNodes);
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getViewDefinitionOracle(node) {
      this.api
        .post("/get_view_definition_oracle/", {
          view: node.title,
          schema: null,
        })
        .then((resp) => {
          tabsStore.createQueryTab(this.selectedNode.title, null, null, resp.data.data)
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getFunctionsOracle(node) {
      this.api
        .post("/get_functions_oracle/")
        .then((resp) => {
          this.removeChildNodes(node);

          this.$refs.tree.updateNode(node.path, {
            title: `Functions (${resp.data.length})`,
          });

          resp.data.forEach((el) => {
            this.insertNode(node, el.name, {
              icon: "fas node-all fa-cog node-function",
              type: "function",
              id: el.id,
              contextMenu: "cm_function",
            });
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getFunctionFieldsOracle(node) {
      this.api
        .post("/get_function_fields_oracle/", {
          function: node.data.id,
          schema: null,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          resp.data.reduceRight((_, el) => {
            if (el.type === "O") {
              this.insertNode(
                node,
                el.name,
                {
                  icon: "fas node-all fa-arrow-right node-function-field",
                },
                true
              );
            } else if (el.type === "I") {
              this.insertNode(
                node,
                el.name,
                {
                  icon: "fas node-all fa-arrow-left node-function-field",
                },
                true
              );
            } else {
              this.insertNode(
                node,
                el.name,
                {
                  icon: "fas node-all fa-exchange-alt node-function-field",
                },
                true
              );
            }
          }, null);
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getFunctionDefinitionOracle(node) {
      this.api
        .post("/get_function_definition_oracle/", {
          function: node.data.id,
        })
        .then((resp) => {
          tabsStore.createQueryTab(this.selectedNode.title, null, null, resp.data.data)
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getProceduresOracle(node) {
      this.api
        .post("/get_procedures_oracle/")
        .then((resp) => {
          this.removeChildNodes(node);

          this.$refs.tree.updateNode(node.path, {
            title: `Procedures (${resp.data.length})`,
          });

          resp.data.forEach((el) => {
            this.insertNode(node, el.name, {
              icon: "fas node-all fa-cog node-procedure",
              type: "procedure",
              contextMenu: "cm_procedure",
              id: el.id,
            });
          });
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getProcedureFieldsOracle(node) {
      this.api
        .post("/get_procedure_fields_oracle/", {
          procedure: node.data.id,
          schema: null,
        })
        .then((resp) => {
          this.removeChildNodes(node);

          resp.data.reduceRight((_, el) => {
            if (el.type === "O") {
              this.insertNode(
                node,
                el.name,
                {
                  icon: "fas node-all fa-arrow-right node-function-field",
                },
                true
              );
            } else if (el.type === "I") {
              this.insertNode(
                node,
                el.name,
                {
                  icon: "fas node-all fa-arrow-left node-function-field",
                },
                true
              );
            } else {
              this.insertNode(
                node,
                el.name,
                {
                  icon: "fas node-all fa-exchange-alt node-function-field",
                },
                true
              );
            }
          }, null);
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getProcedureDefinitionOracle(node) {
      this.api
        .post("/get_procedure_definition_oracle/", {
          procedure: node.data.id,
        })
        .then((resp) => {
          tabsStore.createQueryTab(this.selectedNode.title, null, null, resp.data.data)
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getTablespacesOracle(node) {
      this.api
        .post("/get_tablespaces_oracle/")
        .then((resp) => {
          this.removeChildNodes(node);

          this.$refs.tree.updateNode(node.path, {
            title: `Tablespaces (${resp.data.length})`,
          });

          let childNodes = resp.data.map((el) => {
            return {
              title: el.name,
              isLeaf: true,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-folder node-tablespace",
                type: "tablespace",
                contextMenu: "cm_tablespace",
              },
            }
          });

          this.insertNodes(node, childNodes);
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
    getRolesOracle(node) {
      this.api
        .post("/get_roles_oracle/")
        .then((resp) => {
          this.removeChildNodes(node);

          this.$refs.tree.updateNode(node.path, {
            title: `Roles (${resp.data.length})`,
          });

          let childNodes = resp.data.map((el) => {
            return {
              title: el.name,
              isLeaf: true,
              isExpanded: false,
              isDraggable: false,
              data: {
                icon: "fas node-all fa-user node-user",
                type: "role",
                contextMenu: "cm_role",
              },
            }
          });

          this.insertNodes(node, childNodes);
        })
        .catch((error) => {
          this.nodeOpenError(error, node);
        });
    },
  },
};
</script>
