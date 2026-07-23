import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { settingsStore } from "@src/stores/stores_initializer";

vi.mock("@src/stores/stores_initializer", () => ({
  settingsStore: {
    desktopMode: false,
  },
}));

function dispatchMessage(data, source) {
  window.dispatchEvent(new MessageEvent("message", { data, source }));
}

describe("clipboard.js", () => {
  let readClipboardText;
  let readTextSpy;

  beforeEach(async () => {
    // clipboard.js keeps the desktop host window reference in a module-level
    // variable set by a permanent "message" listener registered at import
    // time, so each test needs a fresh module instance to avoid leaking the
    // desktop-host-ready state into the next test.
    vi.resetModules();
    settingsStore.desktopMode = false;
    readTextSpy = vi.spyOn(navigator.clipboard, "readText");

    ({ readClipboardText } = await import("@src/utils/clipboard"));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("browser mode", () => {
    it("returns the text read from navigator.clipboard", async () => {
      readTextSpy.mockResolvedValue("copied text");

      const result = await readClipboardText();

      expect(result).toBe("copied text");
    });

    it("returns an empty string when navigator.clipboard.readText fails", async () => {
      readTextSpy.mockRejectedValue(new Error("permission denied"));

      const result = await readClipboardText();

      expect(result).toBe("");
    });
  });

  describe("desktop mode", () => {
    beforeEach(() => {
      settingsStore.desktopMode = true;
    });

    it("resolves with the text received from the desktop host", async () => {
      const hostWindow = { postMessage: vi.fn() };
      dispatchMessage({ type: "pgmanage:desktop-host-ready" }, hostWindow);

      const resultPromise = readClipboardText();

      expect(hostWindow.postMessage).toHaveBeenCalledWith(
        expect.objectContaining({ type: "pgmanage:read-clipboard-text" }),
        "*",
      );
      const { requestId } = hostWindow.postMessage.mock.calls[0][0];

      dispatchMessage({
        type: "pgmanage:clipboard-text",
        requestId,
        text: "desktop clipboard text",
      });

      await expect(resultPromise).resolves.toBe("desktop clipboard text");
    });

    it("ignores unrelated messages before resolving with the matching response", async () => {
      const hostWindow = { postMessage: vi.fn() };
      dispatchMessage({ type: "pgmanage:desktop-host-ready" }, hostWindow);

      const resultPromise = readClipboardText();
      const { requestId } = hostWindow.postMessage.mock.calls[0][0];

      dispatchMessage({ type: "some:other-message" });
      dispatchMessage({
        type: "pgmanage:clipboard-text",
        requestId: "different-request-id",
        text: "wrong response",
      });
      dispatchMessage({
        type: "pgmanage:clipboard-text",
        requestId,
        text: "correct response",
      });

      await expect(resultPromise).resolves.toBe("correct response");
    });

    it("resolves with an empty string when the desktop host sends no text", async () => {
      const hostWindow = { postMessage: vi.fn() };
      dispatchMessage({ type: "pgmanage:desktop-host-ready" }, hostWindow);

      const resultPromise = readClipboardText();
      const { requestId } = hostWindow.postMessage.mock.calls[0][0];

      dispatchMessage({ type: "pgmanage:clipboard-text", requestId });

      await expect(resultPromise).resolves.toBe("");
    });

    it("falls back to the browser clipboard when the desktop host never became ready", async () => {
      readTextSpy.mockResolvedValue("browser fallback text");

      const result = await readClipboardText();

      expect(result).toBe("browser fallback text");
    });
  });
});
