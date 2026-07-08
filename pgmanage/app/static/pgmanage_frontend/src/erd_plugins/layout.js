const COLUMN_PADDING = 5;
const TABLE_HEADER_HEIGHT = 40 + COLUMN_PADDING;
const COLUMN_HEIGHT = 24;


const DEFAULT_LAYOUT_OPTIONS = {
  padding: 50,
  spacingFactor: 0.85,
  columnsPerRow: 5,
  tableGapX: 80,
  tableGapY: 80,
};


function getNodeSize(node) {
  return {
    width: node.dimensions?.width,
    height: node.dimensions?.height,
  };
}

function getLayoutedNodes(nodes, internalNodes, options = {}) {
  const layoutOptions = {
    ...DEFAULT_LAYOUT_OPTIONS,
    ...options,
  };

  const tableNodes = nodes.filter((node) => node.type === "table");
  const tableReadNodes = internalNodes.filter((node) => node.type === "table");
  const tablePositions = {};

  const gapX = layoutOptions.tableGapX * layoutOptions.spacingFactor;
  const gapY = layoutOptions.tableGapY * layoutOptions.spacingFactor;

  let currentY = layoutOptions.padding;
  let index = 0;

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
      let internalNode = tableReadNodes[index]
      const { width, height } = getNodeSize(internalNode);
      
      tablePositions[node.id] = {
        x: currentX,
        y: currentY,
      };
      
      currentX += width + gapX;
      rowHeight = Math.max(rowHeight, height);
      index++
    });

    currentY += rowHeight + gapY;
  }

  return nodes.map((node) => {
    if (node.type !== "table") {
      return node;
    }

    return {
      ...node,
      position: tablePositions[node.id],
    };
  });
}

export {  TABLE_HEADER_HEIGHT, COLUMN_HEIGHT, getLayoutedNodes };
