import { mount } from "@vue/test-utils";
import { describe, it, expect, vi } from "vitest";
import AboutModal from "@src/components/AboutModal.vue";

vi.stubGlobal("pgmanage_version", "1.0.0");

describe("AboutModal.vue", () => {
  it("renders the modal with correct version", () => {
    const wrapper = mount(AboutModal);

    const versionElement = wrapper.find(".modal-body .col-7").element;
    expect(versionElement.textContent).toContain("1.0.0");
  });

  it("displays the correct database icons", () => {
    const wrapper = mount(AboutModal);

    const icons = wrapper.findAll(".modal-about__db img");
    expect(icons.length).toBe(6);
    expect(icons.at(0).attributes("src")).toBe(wrapper.vm.postgresqlIcon);
    expect(icons.at(1).attributes("src")).toBe(wrapper.vm.oracleIcon);
    expect(icons.at(2).attributes("src")).toBe(wrapper.vm.mysqlIcon);
    expect(icons.at(3).attributes("src")).toBe(wrapper.vm.sqliteIcon);
    expect(icons.at(4).attributes("src")).toBe(wrapper.vm.mariadbIcon);
    expect(icons.at(5).attributes("src")).toBe(wrapper.vm.mssqlIcon);
  });

  it("renders the correct supporter link", () => {
    const wrapper = mount(AboutModal);

    const supporterLink = wrapper.find('a[data-testid="supporter-link"]');
    expect(supporterLink.exists()).toBe(true);
    expect(supporterLink.text()).toContain("Command Prompt Inc");
  });

  it("renders the correct website link", () => {
    const wrapper = mount(AboutModal);

    const websiteLink = wrapper.find('a[data-testid="pgmanage-github-link"]');
    expect(websiteLink.exists()).toBe(true);
    expect(websiteLink.text()).toContain("Github");
  });
});
