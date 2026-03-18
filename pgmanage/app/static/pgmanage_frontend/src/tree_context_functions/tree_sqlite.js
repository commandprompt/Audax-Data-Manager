import { tabSQLTemplate } from "./tree_postgresql";
import { emitter } from "../emitter";
import { tabsStore } from "../stores/stores_initializer";
import axios from "axios";
import { handleError } from "../logging/utils";

function TemplateSelectSqlite(table, kind) {
  axios
    .post("/template_select_sqlite/", {
      database_index:
        tabsStore.selectedPrimaryTab.metaData.selectedDatabaseIndex,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      table: table,
      kind: kind,
    })
    .then((resp) => {
      tabsStore.createQueryTab(table, null, null, resp.data.template)
      .then((tab) => {
        emitter.emit(`${tab.id}_run_query`);
      });
    })
    .catch((error) => {
      handleError(error);
    });
}

function TemplateInsertSqlite(table) {
  axios
    .post("/template_insert_sqlite/", {
      database_index:
        tabsStore.selectedPrimaryTab.metaData.selectedDatabaseIndex,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      table: table,
    })
    .then((resp) => {
      tabSQLTemplate(`Insert ${table}`, resp.data.template);
    })
    .catch((error) => {
      handleError(error);
    });
}

function TemplateUpdateSqlite(table) {
  axios
    .post("/template_update_sqlite/", {
      database_index:
        tabsStore.selectedPrimaryTab.metaData.selectedDatabaseIndex,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      table: table,
    })
    .then((resp) => {
      tabSQLTemplate(`Update ${table}`, resp.data.template);
    })
    .catch((error) => {
      handleError(error);
    });
}

export { TemplateSelectSqlite, TemplateInsertSqlite, TemplateUpdateSqlite };
