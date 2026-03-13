import { describe, it, expect, vi, beforeEach } from "vitest";
import { nextTick } from "vue";
import PasswordModal from "@src/components/PasswordModal.vue";
import { Modal } from "bootstrap";
import { tabsStore } from "@src/stores/stores_initializer";
import { flushPromises, mount } from "@vue/test-utils";
import axios from "axios";

vi.mock("bootstrap", () => ({
  Modal: {
    getOrCreateInstance: vi.fn(),
  },
}));

describe("PasswordModal", () => {
  let modalShowSpy, modalHideSpy, wrapper;
  beforeEach(() => {
    modalShowSpy = vi.fn();
    modalHideSpy = vi.fn();

    Modal.getOrCreateInstance.mockReturnValue({
      show: modalShowSpy,
      hide: modalHideSpy,
    });

    wrapper = mount(PasswordModal, {
      attachTo: document.body,
    });
  });

  it("splits message into lines and renders them (messageLines computed)", async () => {
    wrapper.vm.message = "First line\n\nSecond line\n   \nThird";
    await nextTick();

    const paragraphs = wrapper.findAll("p");
    const lines = paragraphs.map((p) => p.text());

    expect(lines).toEqual(["First line", "Second line", "Third"]);
  });

  it("showModal uses Bootstrap Modal.getOrCreateInstance with static backdrop", () => {
    wrapper.vm.showModal();

    expect(Modal.getOrCreateInstance).toHaveBeenCalledWith(
      wrapper.vm.$refs.modalPassword,
      { backdrop: "static" }
    );
    expect(modalShowSpy).toHaveBeenCalled();
  });

  it("submit hides modal and calls renewPassword", async () => {
    const hideSpy = vi.fn();
    wrapper.vm.modalInstance = { hide: hideSpy };

    const renewSpy = vi
      .spyOn(wrapper.vm, "renewPassword")
      .mockResolvedValueOnce({});

    await wrapper.vm.submit();

    expect(hideSpy).toHaveBeenCalled();
    expect(renewSpy).toHaveBeenCalled();
  });

  it("cancel calls cancelCallback (if present) and sets resetToDefault", () => {
    const cancelCallback = vi.fn();
    wrapper.vm.cancelCallback = cancelCallback;
    wrapper.vm.resetToDefault = false;

    wrapper.vm.cancel();

    expect(cancelCallback).toHaveBeenCalled();
    expect(wrapper.vm.resetToDefault).toBe(true);
  });

  it("cancel from button click works", async () => {
    const cancelSpy = vi.spyOn(wrapper.vm, "cancel");

    const cancelBtn = wrapper.find("[data-testid='password-cancel-button']");
    await cancelBtn.trigger("click");

    expect(cancelSpy).toHaveBeenCalled();
  });

  it("submit is triggered by Ok button click and Enter keyup", async () => {
    const submitSpy = vi.spyOn(wrapper.vm, "submit").mockResolvedValue({});
    wrapper.vm.modalInstance = { hide: vi.fn() };

    const okBtn = wrapper.find("[data-testid='password-ok-button']")
    await okBtn.trigger("click");
    expect(submitSpy).toHaveBeenCalledTimes(1);

    const input = wrapper.find('input[type="password"]');
    await input.trigger("keyup.enter");
    expect(submitSpy).toHaveBeenCalledTimes(2);
  });

  it("renewPassword posts to backend and calls success callback on success", async () => {
    axios.post.mockResolvedValueOnce({});
    const successCallback = vi.fn();
    wrapper.vm.databaseIndex = 42;
    wrapper.vm.passwordKind = "database";
    wrapper.vm.password = "secret";
    wrapper.vm.successCallback = successCallback;

    wrapper.vm.renewPassword();
    await flushPromises();

    expect(axios.post).toHaveBeenCalledWith("/renew_password/", {
      database_index: 42,
      workspace_id: tabsStore.selectedPrimaryTab.id,
      password: "secret",
      password_kind: "database",
    });

    expect(wrapper.vm.resetToDefault).toBe(true);
    expect(successCallback).toHaveBeenCalled();
  });

  it("renewPassword sets message to error.response.data.data on error", async () => {
    axios.post.mockRejectedValue({
      response: {
        data: {
          data: "Error from backend",
        },
      },
    });

    wrapper.vm.message = "";
    wrapper.vm.renewPassword();
    await flushPromises();

    expect(wrapper.vm.message).toBe("Error from backend");
  });

  it("hidden.bs.modal reopens modal when resetToDefault is false", async () => {
    const showModalSpy = vi.spyOn(wrapper.vm, "showModal");
    wrapper.vm.resetToDefault = false;

    const el = wrapper.vm.$refs.modalPassword;
    el.dispatchEvent(new Event("hidden.bs.modal"));
    await nextTick();

    expect(showModalSpy).toHaveBeenCalled();
  });

  it("hidden.bs.modal calls resetData when resetToDefault is true", async () => {
    const resetDataSpy = vi.spyOn(wrapper.vm, "resetData");
    wrapper.vm.resetToDefault = true;

    const el = wrapper.vm.$refs.modalPassword;
    el.dispatchEvent(new Event("hidden.bs.modal"));
    await nextTick();

    expect(resetDataSpy).toHaveBeenCalled();
  });

  it("shown.bs.modal focuses the password input", async () => {
    const el = wrapper.vm.$refs.modalPassword;
    el.dispatchEvent(new Event("shown.bs.modal"));
    await nextTick();

    const input = wrapper.vm.$refs.passwordInput;
    expect(document.activeElement).toBe(input);
  });

  it("resetData clears internal state", () => {
    wrapper.vm.message = "Some message";
    wrapper.vm.successCallback = () => {};
    wrapper.vm.cancelCallback = () => {};
    wrapper.vm.databaseIndex = 1;
    wrapper.vm.passwordKind = "database";
    wrapper.vm.resetToDefault = true;

    wrapper.vm.resetData();

    expect(wrapper.vm.message).toBe("");
    expect(wrapper.vm.successCallback).toBeNull();
    expect(wrapper.vm.cancelCallback).toBeNull();
    expect(wrapper.vm.databaseIndex).toBeNull();
    expect(wrapper.vm.passwordKind).toBeNull();
    expect(wrapper.vm.resetToDefault).toBe(false);
  });
});
