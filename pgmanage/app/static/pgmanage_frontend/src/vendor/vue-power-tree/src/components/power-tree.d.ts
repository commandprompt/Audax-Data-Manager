// @ts-ignore
import Vue from 'vue';

export interface IPowerTreeNodeModel<TDataType> {
    title: string;
    isLeaf?: boolean;
    children?: IPowerTreeNodeModel<TDataType>[];
    isExpanded?: boolean;
    isSelected?: boolean;
    isDraggable?: boolean;
    isSelectable?: boolean;
    data?: TDataType;
}
export interface IPowerTreeNode<TDataType> extends IPowerTreeNodeModel<TDataType> {
    isVisible?: boolean;
    isFirstChild: boolean;
    isLastChild: boolean;
    ind: number;
    level: number;
    path: number[];
    pathStr: string;
    children: IPowerTreeNode<TDataType>[];
}
export interface ICursorPosition<TDataType> {
    node: IPowerTreeNode<TDataType>;
    placement: 'before' | 'inside' | 'after';
}
export interface IVueData<TDataType> {
    rootCursorPosition: ICursorPosition<TDataType>;
    rootDraggingNode: IPowerTreeNode<TDataType>;
}
export default class PowerTree<TDataType> extends Vue {
    value: IPowerTreeNodeModel<TDataType>[];
    edgeSize: number;
    allowMultiselect: boolean;
    showBranches: boolean;
    level: number;
  parentInd: number;
    allowToggleBranch: boolean;
    private rootCursorPosition;
    private rootDraggingNode;
    cursorPosition: ICursorPosition<TDataType>;
    draggingNode: IPowerTreeNode<TDataType>;
    readonly nodes: IPowerTreeNode<TDataType>[];
    getNode(path: number[]): IPowerTreeNode<TDataType>;
    getFirstNode(): IPowerTreeNode<TDataType>;
    getLastNode(): IPowerTreeNode<TDataType>;
    getNextNode(path: number[], filter?: (node: IPowerTreeNode<TDataType>) => boolean): IPowerTreeNode<TDataType>;
    getPrevNode(path: number[], filter?: (node: IPowerTreeNode<TDataType>) => boolean): IPowerTreeNode<TDataType>;
    updateNode(path: number[], patch: Partial<IPowerTreeNodeModel<TDataType>>): void;
    getSelected(): IPowerTreeNode<TDataType>[];
    traverse(cb: (node: IPowerTreeNode<TDataType>, nodeModel: IPowerTreeNodeModel<TDataType>, siblings: IPowerTreeNodeModel<TDataType>[]) => boolean | void, nodeModels?: IPowerTreeNodeModel<TDataType>[], parentPath?: number[]): IPowerTreeNode<TDataType>[] | boolean;
    getNodeEl(path: number[]): HTMLElement;
    select(path: number[], addToSelection?: boolean): IPowerTreeNode<TDataType>;
    remove(paths: number[][]): void;
    insert(cursorPosition: ICursorPosition<TDataType>, nodeModel:IPowerTreeNodeModel<TDataType>): void;
}
