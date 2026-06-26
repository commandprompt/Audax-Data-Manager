import { settingsStore } from "@src/stores/stores_initializer";

let desktopHostWindow = null;

window.addEventListener("message", (event) => {
  const data = event.data || {};

  if (data.type === "pgmanage:desktop-host-ready") {
    desktopHostWindow = event.source;
  }
});

function readClipboardTextDesktop() {
  const requestId = `${Date.now()}-${Math.random()}`;

  return new Promise((resolve, reject) => {
    function onMessage(event) {
      const data = event.data || {};

      if (
        data.type !== "pgmanage:clipboard-text" ||
        data.requestId !== requestId
      ) {
        return;
      }

      window.removeEventListener("message", onMessage);

      resolve(data.text || "");
    }

    window.addEventListener("message", onMessage);

    desktopHostWindow.postMessage(
      {
        type: "pgmanage:read-clipboard-text",
        requestId,
      },
      "*",
    );
  });
}

async function readClipboardTextBrowser() {
  try {
    return await navigator.clipboard.readText();
  } catch (error) {
    return "";
  }
}

export async function readClipboardText() {
  if (settingsStore.desktopMode) {
    try {
      return await readClipboardTextDesktop();
    } catch (error) {
      return await readClipboardTextBrowser();
    }
  }

  return await readClipboardTextBrowser();
}
