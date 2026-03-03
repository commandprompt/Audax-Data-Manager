import { defineStore } from "pinia";

const useFileManagerStore = defineStore("fileManager", {
  state: () => ({
    onChange: () => {},
    dialogType: null,
    file: null,
    visible: false,
    desktopMode: null,
    title: 'File Manager'
  }),
  actions: {
    showModal(desktopMode, onChange, dialogType, title) {
      this.visible = true;
      this.desktopMode = desktopMode;
      this.onChange = onChange;
      this.dialogType = dialogType;
      this.title = title;
    },
    changeFile(file) {
      this.file = file;
    },
    hideModal() {
      this.visible = false;
      this.reset();
    },
    reset() {
      this.onChange = () => {};
      this.dialogType = null;
      this.file = null;
      this.desktopMode = null;
      this.title = 'File Manager'
    },
  },
});

export { useFileManagerStore };
