// Define all global stubs here
import { vi } from "vitest";
import { config } from "@vue/test-utils";

config.global.directives = {
  tooltip: {
    mounted() {},
    updated() {},
    unmounted() {},
  },
};

vi.stubGlobal("app_base_path", "test_folder");
vi.stubGlobal("v_csrf_cookie_name", "csrf_token_stub");

vi.mock("axios");

// Shared across every test that mounts a component using tabulator-tables,
// so individual test files don't each redeclare this same factory.
vi.mock("tabulator-tables", () => {
  const TabulatorFull = vi.fn();
  TabulatorFull.prototype.redraw = vi.fn();
  TabulatorFull.prototype.setData = vi.fn();
  TabulatorFull.prototype.replaceData = vi.fn();
  TabulatorFull.prototype.on = vi.fn();
  TabulatorFull.prototype.destroy = vi.fn();
  TabulatorFull.prototype.selectRow = vi.fn();
  TabulatorFull.prototype.copyToClipboard = vi.fn();
  return { TabulatorFull };
});
