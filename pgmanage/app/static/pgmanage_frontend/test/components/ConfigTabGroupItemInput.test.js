import { flushPromises, mount } from "@vue/test-utils";
import ConfigTabGroupItemInput from "@src/components/ConfigTabGroupItemInput.vue";
import { Tooltip } from "bootstrap";
import { describe, vi, it, beforeEach, afterEach, expect } from "vitest";

vi.mock("@src/stores/stores_initializer", () => ({
  tabsStore: {
    selectedPrimaryTab: {
      metaData: {
        selectedTab: {
          id: "tab-id",
        },
      },
    },
  },
}));

vi.mock("bootstrap", () => ({
  Tooltip: vi.fn(),
}));

describe("ConfigTabGroupItemInput.vue", () => {
  let wrapper;

  const mountComponent = (propsData = {}) => {
    wrapper?.unmount();
    wrapper = mount(ConfigTabGroupItemInput, {
      props: { ...propsData, index: 0 },
      shallow: true,
      // mounted() looks elements up via document.getElementById, which only
      // finds elements attached to the real document.
      attachTo: document.body,
    });
  };

  const mockSetting = {
    name: "test_setting",
    vartype: "bool", // or 'string', 'enum', etc.
    setting: "off",
    boot_val: "off",
    category: "General",
    enumvals: ["value1", "value2"],
    unit: "MB",
    min_val: "0",
    max_val: "100",
  };

  afterEach(() => {
    wrapper?.unmount();
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders boolean input correctly", () => {
    mountComponent({
      initialSetting: { ...mockSetting, setting: "on" },
    });

    const input = wrapper.find('input[type="checkbox"]');
    expect(input.exists()).toBe(true);
    expect(input.element.checked).toBe(true);
  });

  it("renders string input correctly", () => {
    mountComponent({
      initialSetting: {
        ...mockSetting,
        vartype: "string",
        setting: "some_string",
      },
    });

    const input = wrapper.find('input[type="text"]');
    expect(input.exists()).toBe(true);
    expect(input.element.value).toBe("some_string");
  });

  it("renders enum select input correctly", () => {
    mountComponent({
      initialSetting: {
        ...mockSetting,
        vartype: "enum",
        setting: "value1",
      },
    });

    const select = wrapper.find("select");
    expect(select.exists()).toBe(true);
    expect(select.element.value).toBe("value1");
    const options = select.findAll("option");
    expect(options.length).toBe(2);
    expect(options[0].element.value).toBe("value1");
    expect(options[1].element.value).toBe("value2");
  });

  it('emits "settingChange" event when input changes', async () => {
    mountComponent({ initialSetting: mockSetting });

    await wrapper.find('input[type="checkbox"]').setValue("true");

    expect(wrapper.emitted().settingChange).toBeTruthy();
    expect(wrapper.emitted().settingChange[0][0]).toEqual({
      changedSetting: {
        ...mockSetting,
        setting: "on",
      },
      index: 0,
    });
  });

  it("disables input when isReadOnly is true", () => {
    mountComponent({
      initialSetting: {
        ...mockSetting,
        is_preset_option: "True",
      },
    });

    const input = wrapper.find("input");
    expect(input.element.disabled).toBe(true);
  });

  it("displays reset button and triggers setDefault on click", async () => {
    mountComponent({
      initialSetting: {
        ...mockSetting,
        setting: "on",
      },
    });

    const resetButton = wrapper.find("button");
    expect(resetButton.exists()).toBe(true);

    await resetButton.trigger("click");
    expect(wrapper.emitted().settingChange).toBeTruthy();
    expect(wrapper.emitted().settingChange[0][0]).toEqual({
      changedSetting: {
        ...mockSetting,
        setting: "off",
      },
      index: 0,
    });
  });

  it("renders a generic input for other vartypes (e.g. integer)", () => {
    mountComponent({
      initialSetting: { ...mockSetting, vartype: "integer", setting: "50" },
    });

    const input = wrapper.find("input");
    expect(input.attributes("type")).toBeUndefined();
    expect(input.element.value).toBe("50");
  });

  describe("mounted tooltips", () => {
    it("creates a tooltip for the input, and for the reset button when it is rendered", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          setting: "on",
          boot_val: "off",
        },
      });
      await flushPromises();

      expect(Tooltip).toHaveBeenCalledTimes(2);
      expect(Tooltip).toHaveBeenCalledWith(
        wrapper.find("input").element,
        expect.objectContaining({ container: wrapper.vm.$refs.settingInput }),
      );
      expect(Tooltip).toHaveBeenCalledWith(
        wrapper.find("button").element,
        expect.objectContaining({ container: wrapper.vm.$refs.resetButton }),
      );
    });

    it("only creates the input tooltip when the reset button is not rendered", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          setting: "50",
          boot_val: "50",
        },
      });
      await flushPromises();

      expect(wrapper.find("button").exists()).toBe(false);
      expect(Tooltip).toHaveBeenCalledTimes(1);
    });
  });

  describe("validations", () => {
    it("does not require a string setting when it has no boot_val", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "string",
          setting: "",
          boot_val: "",
        },
      });

      await wrapper.vm.v$.$validate();

      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(false);
    });

    it("requires a string setting when it has a boot_val", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "string",
          setting: "",
          boot_val: "default_value",
        },
      });

      await wrapper.vm.v$.$validate();

      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(true);
    });

    // `setting` is a computed that snapshots initialSetting into a plain
    // (non-reactive) object, so v$'s $model doesn't pick up changes made by
    // mutating it after mount. Each scenario below mounts fresh instead.
    it("validates unit-based numeric settings against min/max via validNumericSetting", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          unit: "MB",
          min_val: "1",
          max_val: "10",
          setting: "5MB",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(false);

      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          unit: "MB",
          min_val: "1",
          max_val: "10",
          setting: "50MB",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(true);
    });

    it("validates octal file permission settings within min/max", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          name: "unix_socket_permissions",
          unit: "",
          min_val: "0",
          max_val: "300",
          setting: "0111",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(false);

      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          name: "unix_socket_permissions",
          unit: "",
          min_val: "0",
          max_val: "300",
          setting: "0755",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(true);
    });

    it("falls back to min/max for octal-named settings whose value isn't 4 octal digits", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          name: "unix_socket_permissions",
          unit: "",
          min_val: "0",
          max_val: "500",
          setting: "100",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(false);

      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          name: "unix_socket_permissions",
          unit: "",
          min_val: "0",
          max_val: "500",
          setting: "999",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(true);
    });

    it("validates plain numeric settings against min/max", async () => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          name: "max_connections",
          unit: "",
          min_val: "1",
          max_val: "100",
          setting: "50",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(false);

      mountComponent({
        initialSetting: {
          ...mockSetting,
          vartype: "integer",
          name: "max_connections",
          unit: "",
          min_val: "1",
          max_val: "100",
          setting: "500",
        },
      });
      await wrapper.vm.v$.$validate();
      expect(wrapper.vm.v$.setting.setting.$invalid).toBe(true);
    });
  });

  describe("formatNumber", () => {
    beforeEach(() => {
      mountComponent({ initialSetting: mockSetting });
    });

    it("converts a size value in its own unit", () => {
      expect(wrapper.vm.formatNumber("8MB", "MB")).toBe(8);
    });

    it("converts a size value across units", () => {
      expect(wrapper.vm.formatNumber("8GB", "MB")).toBe(8192);
    });

    it("divides by the factor when the configured unit itself has a number", () => {
      expect(wrapper.vm.formatNumber("8kb", "2kb")).toBe(4);
    });

    it("converts a time value in its own unit", () => {
      expect(wrapper.vm.formatNumber("500ms", "ms")).toBe(500);
    });

    it("converts a time value using a positive multiplier", () => {
      expect(wrapper.vm.formatNumber("2s", "ms")).toBe(2000);
    });

    it("converts a time value using a negative (divide) multiplier", () => {
      expect(wrapper.vm.formatNumber("2000ms", "s")).toBe(2);
    });

    it("converts between hours and days", () => {
      expect(wrapper.vm.formatNumber("2d", "h")).toBe(48);
      expect(wrapper.vm.formatNumber("48h", "d")).toBe(2);
    });

    it("converts a time value in minutes", () => {
      expect(wrapper.vm.formatNumber("30min", "min")).toBe(30);
    });

    it("falls through to NaN for a size suffix outside the known units", () => {
      expect(wrapper.vm.formatNumber("5BB")).toBeNaN();
    });

    it("falls back to a plain number when no unit suffix matches", () => {
      expect(wrapper.vm.formatNumber("42")).toBe(42);
    });
  });

  describe("validNumericSetting", () => {
    beforeEach(() => {
      mountComponent({
        initialSetting: {
          ...mockSetting,
          unit: "MB",
          min_val: "1",
          max_val: "100",
        },
      });
    });

    it("returns true for a value within range", () => {
      expect(wrapper.vm.validNumericSetting("8MB")).toBe(true);
    });

    it("returns false for a value outside range", () => {
      expect(wrapper.vm.validNumericSetting("200MB")).toBe(false);
    });

    it("returns false for a value that doesn't resolve to a number", () => {
      expect(wrapper.vm.validNumericSetting("not_a_number")).toBe(false);
    });
  });
});
