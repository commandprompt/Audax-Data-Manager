import { toPng as ElToPng } from "html-to-image";

function patchVueFlowEdgesForExport(root) {
  // Hide Vue Flow's invisible edge hitboxes. They are only needed for mouse
  // interaction and can be rendered incorrectly by html-to-image.

  const cleanups = [];

  function setAttr(el, name, value) {
    const oldValue = el.getAttribute(name);

    el.setAttribute(name, value);

    cleanups.push(() => {
      if (oldValue === null) {
        el.removeAttribute(name);
      } else {
        el.setAttribute(name, oldValue);
      }
    });
  }

  function setStyle(el, name, value) {
    const oldValue = el.style.getPropertyValue(name);
    const oldPriority = el.style.getPropertyPriority(name);

    el.style.setProperty(name, value, "important");

    cleanups.push(() => {
      if (oldValue) {
        el.style.setProperty(name, oldValue, oldPriority);
      } else {
        el.style.removeProperty(name);
      }
    });
  }

  root.querySelectorAll(".vue-flow__edge-interaction").forEach((path) => {
    setStyle(path, "display", "none");
    setAttr(path, "stroke", "none");
    setAttr(path, "stroke-width", "0");
    setAttr(path, "fill", "none");
  });

  root.querySelectorAll(".vue-flow__edge-path").forEach((path) => {
    const computed = window.getComputedStyle(path);

    const stroke =
      computed.stroke && computed.stroke !== "none"
        ? computed.stroke
        : path.getAttribute("stroke") || "#ff0072";

    const strokeWidth =
      computed.strokeWidth && computed.strokeWidth !== "0px"
        ? computed.strokeWidth
        : path.getAttribute("stroke-width") || "1";

    setAttr(path, "fill", "none");
    setAttr(path, "stroke", stroke);
    setAttr(path, "stroke-width", strokeWidth);
    setAttr(path, "stroke-linecap", computed.strokeLinecap || "round");
    setAttr(path, "stroke-linejoin", computed.strokeLinejoin || "round");

    setStyle(path, "fill", "none");
    setStyle(path, "stroke", stroke);
    setStyle(path, "stroke-width", strokeWidth);
  });

  return () => {
    cleanups.reverse().forEach((cleanup) => cleanup());
  };
}

function download(dataUrl, fileName) {
  const link = document.createElement("a");

  link.download = `${fileName}.png`;
  link.href = dataUrl;
  link.click();
}

async function capture(el, options = {}) {
  if (!el) {
    return null;
  }

  const fileName = `vue-flow-screenshot-${Date.now()}`;

  // The returned cleanup function
  // restores the original DOM after the screenshot is generated.
  const cleanup = patchVueFlowEdgesForExport(el);

  try {
    const dataUrl = await ElToPng(el, {
      cacheBust: true,
      pixelRatio: 2,
      ...options,
    });

    if (options.shouldDownload && fileName !== "") {
      download(dataUrl, fileName);
    }

    return dataUrl;
  } finally {
    cleanup();
  }
}

export { capture };
