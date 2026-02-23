import { defineStore } from "pinia";

const useCellDataModalStore = defineStore("cellDataModal", {
  state: () => ({
    visible: false,
    cellContent: null,
    cellType: null,
    showControls: false,
    readOnly: true,
    applyFunc: () => {}
  }),
  actions: {
    showModal(cellContent, cellType, showControls, readOnly, applyFunc) {
      this.cellContent = cellContent;
      this.cellType = cellType;
      this.visible = true;
      this.showControls = showControls ?? false;
      this.readOnly = readOnly ?? true;
      this.applyFunc = applyFunc
    },
    hideModal() {
      this.visible = false;
      this.cellContent = null;
      this.cellType = null;
      this.readOnly = true;
    },
  },
});

export { useCellDataModalStore };
