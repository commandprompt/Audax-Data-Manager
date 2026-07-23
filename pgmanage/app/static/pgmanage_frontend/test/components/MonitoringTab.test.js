import { flushPromises, mount } from "@vue/test-utils";
import { test, describe, beforeEach, vi, expect } from "vitest";
import MonitoringTab from "@src/components/MonitoringTab.vue";

import axios from "axios";

describe("MonitoringTab", () => {
  let monTabWrapper;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.restoreAllMocks();
    axios.delete.mockResolvedValue("Deleted");
    axios.post
      .mockResolvedValue({ data: { data: [{ name: "1234" }] } })
      .mockResolvedValueOnce({ data: { data: [{ name: "1234" }] } });
    monTabWrapper = mount(MonitoringTab, {
      props: {
        workspaceId: "workspaceId",
      },
      shallow: true,
    });
  });

  test("should render MonitoringTab component with expected elements", () => {
    expect(monTabWrapper.html()).toContain("Refresh");
    expect(monTabWrapper.html()).toContain("Pause");
    expect(monTabWrapper.html()).toContain("refresh-menu__link");
  });

  test("should refresh grid data on 'Refresh' button click", async () => {
    const refreshWidgetsSpy = vi.spyOn(monTabWrapper.vm, "refreshMonitoring");

    await monTabWrapper
      .get('[data-testid="monitoring-refresh-button"]')
      .trigger("click");

    expect(refreshWidgetsSpy).toBeCalledTimes(1);
  });

  test("should change refresh interval when different refresh option is clicked", async () => {
    await monTabWrapper
      .get('[data-testid="refresh-option-300"]')
      .trigger("click");
    expect(monTabWrapper.vm.monitoringInterval).toBe(300);
  });

  test("should pause refresh when pause button is is clicked", async () => {
    const pauseSpy = vi.spyOn(monTabWrapper.vm, "pauseMonitoring");
    await monTabWrapper
      .get('[data-testid="monitoring-pause-button"]')
      .trigger("click");
    expect(pauseSpy).toBeCalledTimes(1);
  });

  test("should resume refresh when play button is is clicked", async () => {
    const playSpy = vi.spyOn(monTabWrapper.vm, "playMonitoring");
    await monTabWrapper
      .get('[data-testid="monitoring-pause-button"]')
      .trigger("click");
    await monTabWrapper
      .get('[data-testid="monitoring-play-button"]')
      .trigger("click");
    expect(playSpy).toBeCalledTimes(1);
  });

  test("refreshMonitoring should set up a timer", async () => {
    const setIntervalSpy = vi.spyOn(global, "setTimeout");
    monTabWrapper.vm.refreshMonitoring();

    await flushPromises();

    expect(setIntervalSpy).toHaveBeenCalledWith(
      expect.any(Function),
      monTabWrapper.vm.monitoringInterval * 1000
    );
  });

  test("pauseMonitoring should clear interval", async () => {
    monTabWrapper.vm.refreshMonitoring();
    await flushPromises();

    const clearSpy = vi.spyOn(global, "clearTimeout");
    expect(monTabWrapper.vm.timeoutObject).not.toBeNull();
    await monTabWrapper.vm.pauseMonitoring();
    expect(clearSpy).toHaveBeenCalledWith(monTabWrapper.vm.timeoutObject);
  });

  test("playMonitoring should set isActive to true", async () => {
    monTabWrapper.vm.isActive = false;
    await monTabWrapper.vm.playMonitoring();
    expect(monTabWrapper.vm.isActive).toBe(true);
  });

  test("pauseMonitoring should set isActive to false", async () => {
    monTabWrapper.vm.isActive = true;
    await monTabWrapper.vm.pauseMonitoring();
    expect(monTabWrapper.vm.isActive).toBe(false);
  });

  test("should show Processes and Logs subtabs only for postgresql dialect", () => {
    expect(
      monTabWrapper.find('button[data-testid="backends-tab-button"]').exists()
    ).toBeFalsy();
    expect(
      monTabWrapper.find('button[data-testid="logs-tab-button"]').exists()
    ).toBeFalsy();

    monTabWrapper.unmount();

    let postgresMonTab = mount(MonitoringTab, {
      props: {
        workspaceId: "workspaceId",
        dialect: "postgresql",
      },
      shallow: true,
    });

    expect(
      postgresMonTab.find('button[data-testid="logs-tab-button"]').exists()
    ).toBeTruthy();
  });
});
