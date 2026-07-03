const TABLE_WIDTH = 260;
const TABLE_HEADER_HEIGHT = 44;
const COLUMN_HEIGHT = 34;

const DEFAULT_LAYOUT_OPTIONS = {
  padding: 50,
  spacingFactor: 0.85,
  columnsPerRow: 5,
  tableGapX: 80,
  tableGapY: 80,
};

function getCssNumber(value, fallback) {
  if (typeof value === "number") {
    return value;
  }

  if (typeof value === "string") {
    const parsed = parseInt(value, 10);

    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }

  return fallback;
}

function getNodeSize(node) {
  return {
    width: getCssNumber(node.style?.width, TABLE_WIDTH),
    height: getCssNumber(node.style?.height, TABLE_HEADER_HEIGHT),
  };
}

function getLayoutedNodes(nodes, edges = [], options = {}) {
  const layoutOptions = {
    ...DEFAULT_LAYOUT_OPTIONS,
    ...options,
  };

  const tableNodes = nodes.filter((node) => node.type === "table");
  const tablePositions = {};

  const gapX = layoutOptions.tableGapX * layoutOptions.spacingFactor;
  const gapY = layoutOptions.tableGapY * layoutOptions.spacingFactor;

  let currentY = layoutOptions.padding;

  for (
    let rowStart = 0;
    rowStart < tableNodes.length;
    rowStart += layoutOptions.columnsPerRow
  ) {
    const rowNodes = tableNodes.slice(
      rowStart,
      rowStart + layoutOptions.columnsPerRow,
    );

    let currentX = layoutOptions.padding;
    let rowHeight = 0;

    rowNodes.forEach((node) => {
      const { width, height } = getNodeSize(node);

      tablePositions[node.id] = {
        x: currentX,
        y: currentY,
      };

      currentX += width + gapX;
      rowHeight = Math.max(rowHeight, height);
    });

    currentY += rowHeight + gapY;
  }

  return nodes.map((node) => {
    if (node.type !== "table") {
      return node;
    }

    return {
      ...node,
      position: tablePositions[node.id] || node.position,
    };
  });
}

export { TABLE_WIDTH, TABLE_HEADER_HEIGHT, COLUMN_HEIGHT, getLayoutedNodes };
