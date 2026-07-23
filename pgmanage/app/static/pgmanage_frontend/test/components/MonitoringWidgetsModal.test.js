import { mount } from "@vue/test-utils";
import { beforeEach, describe, test, vi, expect, beforeAll } from "vitest";
import MonitoringWidgetsModal from "../../src/components/MonitoringWidgetsModal.vue";
import axios from "axios";

describe("MonitoringWidgetsModal", () => {
  let wrapper;

  beforeAll(() => {
    axios.post.mockResolvedValue({
      data: {
        data: [
          {
            id: 1,
            title: "test data",
            editable: true,
            type: "grid",
            interval: 10,
          },
        ],
      },
    });
  });

  beforeEach(() => {
    wrapper = mount(MonitoringWidgetsModal, {
      attachTo: document.body,
      props: {
        widgetsModalVisible: false,
      },
    });
  });
  test("should render MonitoringWidgetsModal component with expected elements", () => {
    expect(wrapper.html()).toContain("Monitoring Widgets");
    expect(wrapper.html()).toContain("New Widget");
  });
});
