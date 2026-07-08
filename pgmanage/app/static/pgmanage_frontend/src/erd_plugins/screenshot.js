import { toPng as ElToPng } from "html-to-image";

// starting from html-to-image@1.11.12 there is a background rendering issue
// https://github.com/bubkoo/html-to-image/issues/506

const filter = (node) => {
  const exclusionClasses = ["vue-flow__background"];
  return !exclusionClasses.some((classname) =>
    node.classList?.contains(classname),
  );
};

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

  const fileName = `erd-screenshot-${Date.now()}`;

  const dataUrl = await ElToPng(el, {
    cacheBust: true,
    pixelRatio: 2,
    filter: filter,
    ...options,
  });

  if (options.shouldDownload && fileName !== "") {
    download(dataUrl, fileName);
  }

  return dataUrl;
}

export { capture };
