import { emitter } from "../emitter";
import { tabsStore } from "../stores/stores_initializer";
import axios from "axios";
import { handleError } from "../logging/utils";

function TemplateSelectMssql(schema, table, kind) {
  axios
    .post("/template_select_mssql/", {
      database_index:
        tabsStore.selectedPrimaryTab.metaData.selectedDatabaseIndex,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      table: table,
      schema: schema,
      kind: kind,
    })
    .then((resp) => {
      let tab_name = `${tabsStore.selectedPrimaryTab.metaData.selectedDatabase}@${schema}.${table}`;
      tabsStore.createQueryTab(tab_name, null, null, resp.data.template)
      .then((tab) => {
        emitter.emit(`${tab.id}_run_query`);
      });
    })
    .catch((error) => {
      handleError(error);
    });
}

export { TemplateSelectMssql };
