import { tabSQLTemplate } from "./tree_postgresql";
import { emitter } from "../emitter";
import { tabsStore } from "../stores/stores_initializer";
import axios from "axios";
import { handleError } from "../logging/utils";

function TemplateSelectOracle(schema, table) {
  axios
    .post("/template_select_oracle/", {
      database_index:
        tabsStore.selectedPrimaryTab.metaData.selectedDatabaseIndex,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      table: table,
      schema: schema,
    })
    .then((resp) => {
      let tab_name = `${schema}.${table}`;

      tabsStore.createQueryTab(tab_name, null, null, resp.data.template)
      .then((tab) => {
        emitter.emit(`${tab.id}_run_query`);
      });
    })
    .catch((error) => {
      handleError(error);
    });
}

function TemplateInsertOracle(schema, table) {
  axios
    .post("/template_insert_oracle/", {
      database_index:
        tabsStore.selectedPrimaryTab.metaData.selectedDatabaseIndex,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      table: table,
      schema: schema,
    })
    .then((resp) => {
      tabSQLTemplate(`Insert ${schema}.${table}`, resp.data.template);
    })
    .catch((error) => {
      handleError(error);
    });
}

function TemplateUpdateOracle(schema, table) {
  axios
    .post("/template_update_oracle/", {
      database_index:
        tabsStore.selectedPrimaryTab.metaData.selectedDatabaseIndex,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      table: table,
      schema: schema,
    })
    .then((resp) => {
      tabSQLTemplate(`Update ${schema}.${table}`, resp.data.template);
    })
    .catch((error) => {
      handleError(error);
    });
}

export { TemplateUpdateOracle, TemplateInsertOracle, TemplateSelectOracle };
