import { Tooltip } from "bootstrap";

export default {
  mounted(el) {
    new Tooltip(el, {
      boundary: "window",
      trigger: "hover",
      delay: { "show": 500, "hide": 100 }
    });
  },
  beforeUnmount(el) {
    const instance = Tooltip.getInstance(el);
    if (instance) {
      instance.dispose();
    }
  }
};