import { Tooltip } from "bootstrap";

export default {
  mounted() {
    this.$el.querySelectorAll('[data-bs-toggle="tooltip"]')
      .forEach(el => new Tooltip(el, {
          boundary: "window",
          trigger: "hover",
          delay: { "show": 500, "hide": 100 }
        }));
  },
  unmounted() {
    this.$el.querySelectorAll('[data-bs-toggle="tooltip"]')
      .forEach(el => {
        const instance = Tooltip.getInstance(el);
        if (instance) instance.dispose();
      });
  }
};
  