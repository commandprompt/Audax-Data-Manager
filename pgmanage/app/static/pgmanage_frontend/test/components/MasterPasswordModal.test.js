import { mount, flushPromises } from "@vue/test-utils";
import { describe, it, expect, beforeEach, vi } from "vitest";
import MasterPasswordModal from "@src/components/MasterPasswordModal.vue";
import axios from "axios";
import { emitter } from "@src/emitter";
import { messageModalStore } from "@src/stores/stores_initializer";
import { showToast } from "@src/notification_control";
import { mockErrorResponse } from "../helpers/fixtures.js";

vi.mock("bootstrap", () => ({
  Modal: {
    getOrCreateInstance: vi.fn(() => ({
      show: vi.fn(),
      hide: vi.fn(),
    })),
  },
}));
vi.mock("@src/notification_control", () => ({
  showToast: vi.fn(),
}));
vi.mock("@src/emitter", () => ({
  emitter: {
    on: vi.fn(),
    emit: vi.fn(),
    all: new Map(),
  },
}));
vi.mock("@src/stores/stores_initializer", () => ({
  messageModalStore: {
    showModal: vi.fn(),
  },
}));

describe("MasterPasswordModal.vue", () => {
  let wrapper;

  const mountComponent = (options = {}) => {
    return mount(MasterPasswordModal, {
      attachTo: document.body,
      global: {
        stubs: { teleport: true },
      },
      ...options,
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
    wrapper = mountComponent();
  });

  it("renders Master Password modal with expected structure", () => {
    expect(wrapper.find(".modal-title").text()).toBe("Master Password");
    expect(wrapper.find("#master_password_modal").exists()).toBe(true);
  });

  it("shows new password inputs when isNewPassword=true", async () => {
    wrapper.vm.isNewPassword = true;
    await wrapper.vm.$nextTick();

    const newPassInput = wrapper.find('input[placeholder="New Password"]');
    const confirmPassInput = wrapper.find(
      'input[placeholder="Confirm Password"]'
    );
    expect(newPassInput.exists()).toBe(true);
    expect(confirmPassInput.exists()).toBe(true);
  });

  it("disables 'Set Master Password' button when passwords are empty or invalid", async () => {
    wrapper.vm.isNewPassword = true;
    await wrapper.vm.$nextTick();
    const button = wrapper.find("button.btn-success");
    expect(button.attributes("disabled")).toBeDefined();
  });

  it("calls saveMasterPass and emits success", async () => {
    wrapper.vm.isNewPassword = true;
    wrapper.vm.password = "12345678";
    wrapper.vm.passwordConfirm = "12345678";
    axios.post.mockResolvedValue({});

    await wrapper.vm.saveMasterPass();
    await flushPromises();

    expect(axios.post).toHaveBeenCalledWith("/master_password/", {
      master_password: "12345678",
    });
    expect(showToast).toHaveBeenCalledWith(
      "success",
      "Master password created."
    );
    expect(wrapper.emitted("checkCompleted")).toBeTruthy();
  });

  it("shows password input when isNewPassword=false", async () => {
    wrapper.vm.isNewPassword = false;
    await wrapper.vm.$nextTick();

    const checkInput = wrapper.find('input[placeholder="Password"]');
    expect(checkInput.exists()).toBe(true);
  });

  it("calls checkMasterPassword and hides modal on success", async () => {
    axios.post.mockResolvedValue({});
    const hideMock = vi.fn();
    wrapper.vm.modalInstance = { hide: hideMock };
    await wrapper.vm.checkMasterPassword();
    await flushPromises();

    expect(axios.post).toHaveBeenCalledWith("/master_password/", {
      master_password: wrapper.vm.checkPassword,
    });
    expect(wrapper.vm.modalInstance.hide).toHaveBeenCalled();
    expect(wrapper.emitted("checkCompleted")).toBeTruthy();
  });

  it("updates passwordMessage on failed checkMasterPassword", async () => {
    axios.post.mockRejectedValue(mockErrorResponse("Wrong password"));

    await wrapper.vm.checkMasterPassword();
    await flushPromises();
    expect(wrapper.vm.passwordMessage).toBe("Wrong password");
  });

  it("calls messageModalStore.showModal and resets password when confirmed", async () => {
    axios.post.mockResolvedValue({});
    messageModalStore.showModal.mockImplementation((_msg, onYes) => onYes());

    await wrapper.vm.resetPassword();

    expect(messageModalStore.showModal).toHaveBeenCalled();
    expect(axios.post).toHaveBeenCalledWith("/reset_master_password/");
    expect(wrapper.vm.isNewPassword).toBe(true);
  });

  it("registers emitter event listener for 'show_master_pass_prompt'", () => {
    wrapper.vm.setupEvents();
    expect(emitter.on).toHaveBeenCalledWith(
      "show_master_pass_prompt",
      expect.any(Function)
    );
  });

  it("calls showModal when show_master_pass_prompt event fires", async () => {
    const showSpy = vi.spyOn(wrapper.vm, "showModal");
    wrapper.vm.setupEvents();

    const callback = emitter.on.mock.calls[0][1];
    callback(true);

    expect(showSpy).toHaveBeenCalled();
    expect(wrapper.vm.isNewPassword).toBe(true);
  });

  it("showModal creates Bootstrap modal instance and calls show()", async () => {
    wrapper.vm.showModal();
    expect(wrapper.vm.modalInstance.show).toHaveBeenCalled();
  });

  it("returns true from isNewPasswordValid when fields are empty", () => {
    wrapper.vm.password = "";
    wrapper.vm.passwordConfirm = "";
    expect(wrapper.vm.isNewPasswordValid).toBe(true);
  });

  it("returns validation rules properly", () => {
    const validations = wrapper.vm.$options.validations();
    expect(validations.password.required).toBeDefined();
    expect(validations.password.minLength).toBeDefined();
    expect(validations.passwordConfirm.sameAs).toBeDefined();
  });
});
