import { toRaw } from 'vue';
export default {
  name: 'power-tree',
  emits: ['update:modelValue', 'select', 'beforedrop', 'drop', 'toggle', 'nodeclick', 'nodedblclick', 'nodecontextmenu', 'externaldragover', 'externaldrop'],
  props: {
    modelValue: {
      type: Array,
      default: () => []
    },
    edgeSize: {
      type: Number,
      default: 3
    },
    showBranches: {
      type: Boolean,
      default: false
    },
    level: {
      type: Number,
      default: 0
    },
    parentInd: {
      type: Number
    },
    allowMultiselect: {
      type: Boolean,
      default: true
    },
    allowDrag: {
      type: Boolean,
      default: true
    },
    allowToggleBranch: {
      type: Boolean,
      default: true
    },
    scrollAreaHeight: {
      type: Number,
      default: 70
    },
    maxScrollSpeed: {
      type: Number,
      default: 20
    }
  },
  data () {
    return {
      rootCursorPosition: null,
      scrollIntervalId: 0,
      scrollSpeed: 0,
      lastSelectedNode: null,
      mouseIsDown: false,
      isDragging: false,
      lastMousePos: { x: 0, y: 0 },
      preventDrag: false,
      currentValue: this.modelValue,
      nodesMap: {},
      selectedNodes: []
    }
  },
  mounted () {
    if (this.isRoot) {
      document.addEventListener('mouseup', this.onDocumentMouseupHandler)
    }
    this.rebuildNodesMap();
  },
  beforeDestroy () {
    document.removeEventListener('mouseup', this.onDocumentMouseupHandler)
  },
  watch: {
    // modelValue: function (newValue) {
    //   this.currentValue = this.copy(newValue)
    // }
    
    // modelValue: {
    //   handler() {
    //     this.rebuildNodesMap();
    //   },
    //   deep: false // Optimization: Only rebuild if the array reference changes
    // }
  },
  computed: {
    cursorPosition () {
      return (this.isRoot) ? this.rootCursorPosition : this.getParent().cursorPosition
    },
    depth () {
      return this.gaps.length
    },
    nodes () {
      if (this.isRoot) {
        const nodeModels = this.copy(this.currentValue)
        return this.getNodes(nodeModels)
      }
      return this.getParent().nodes[this.parentInd].children
    },
    /**
     * gaps is using for nodes indentation
     * @returns {number[]}
     */
    gaps () {
      const gaps = []
      let i = this.level - 1
      if (!this.showBranches) i++
      while (i-- > 0) gaps.push(i)
      return gaps
    },
    isRoot () {
      return !this.level
    },
    selectionSize () {
      return this.selectedNodes.length
    },
    dragSize () {
      return this.getDraggable().length
    }
  },
  methods: {
    rebuildNodesMap() {
      console.log('rebuild')
      const map = {};
      
      // walk over the main tree structure and build a flat map of pathstr -> node
      const walk = (models, parentPath = []) => {
        models.forEach((model, index) => {
          const currentPath = [...parentPath, index];
          const pathStr = JSON.stringify(currentPath);
          
          // Store the reference to the actual object in memory
          map[pathStr] = model;
  
          // If node has children, dive deeper
          if (model.children && model.children.length > 0) {
            walk(model.children, currentPath);
          }
        });
      };
  
      walk(this.currentValue);
      this.nodesMap = map;
    },
    setCursorPosition (pos) {
      if (this.isRoot) {
        this.rootCursorPosition = pos
        return
      }
      this.getParent().setCursorPosition(pos)
    },
    getNodes (nodeModels, parentPath = [], isVisible = true) {
      const currentPath = [...parentPath, 0]; // Copy once per level of children
      const lastIdx = currentPath.length - 1;
      return nodeModels.map((nodeModel, ind) => {
        currentPath[lastIdx] = ind;
        return this.getNode(currentPath.slice(), nodeModel, nodeModels, isVisible)
      })
    },
    getNode (path, nodeModel = null, siblings = null, isVisible = null) {
      const ind = path.slice(-1)[0]

      // calculate nodeModel, siblings, isVisible fields if it is not passed as arguments
      siblings = siblings || this.getNodeSiblings(this.currentValue, path)
      nodeModel = nodeModel || (siblings && siblings[ind]) || null

      if (isVisible == null) {
        isVisible = this.isVisible(path)
      }

      if (!nodeModel) return null

      const isExpanded = nodeModel.isExpanded === void 0 ? true : !!nodeModel.isExpanded
      const isDraggable = nodeModel.isDraggable === void 0 ? true : !!nodeModel.isDraggable
      const isSelectable = nodeModel.isSelectable === void 0 ? true : !!nodeModel.isSelectable
    
      return {
        // define the all IPowerTreeNodeModel props
        title: nodeModel.title,
        isLeaf: !!nodeModel.isLeaf,
        children: nodeModel.children ? this.getNodes(nodeModel.children, path, isExpanded) : [],
        isSelected: !!nodeModel.isSelected,
        isExpanded,
        isVisible,
        isDraggable,
        isSelectable,
        data: nodeModel.data !== void 0 ? nodeModel.data : {},

        // define the all IPowerTreeNode computed props
        path: path,
        pathStr: JSON.stringify(path),
        level: path.length,
        ind,
        isFirstChild: ind === 0,
        isLastChild: ind === siblings.length - 1
      }
    },
    isVisible (path) {
      if (path.length < 2) return true
      let nodeModels = this.currentValue
      for (let i = 0; i < path.length - 1; i++) {
        let ind = path[i]
        let nodeModel = nodeModels[ind]
        let isExpanded = nodeModel.isExpanded === void 0 ? true : !!nodeModel.isExpanded
        if (!isExpanded) return false
        nodeModels = nodeModel.children
      }
      return true
    },
    emitInput (newValue) {
      this.currentValue = newValue
      this.getRoot().$emit('update:modelValue', newValue)
    },
    emitSelect (selectedNodes, event) {
      this.getRoot().$emit('select', selectedNodes, event)
    },
    emitBeforeDrop (draggingNodes, position, cancel) {
      this.getRoot().$emit('beforedrop', draggingNodes, position, cancel)
    },
    emitDrop (draggingNodes, position, event) {
      this.getRoot().$emit('drop', draggingNodes, position, event)
    },
    emitToggle (toggledNode, event) {
      this.getRoot().$emit('toggle', toggledNode, event)
    },
    emitNodeClick (node, event) {
      this.getRoot().$emit('nodeclick', node, event)
    },
    emitNodeDblclick (node, event) {
      this.getRoot().$emit('nodedblclick', node, event)
    },
    emitNodeContextmenu (node, event) {
      this.getRoot().$emit('nodecontextmenu', node, event)
    },
    onExternalDragoverHandler (node, event) {
      event.preventDefault()
      const root = this.getRoot()
      const cursorPosition = root.getCursorPositionFromCoords(event.clientX, event.clientY)
      root.setCursorPosition(cursorPosition)
      root.$emit('externaldragover', cursorPosition, event)
    },
    onExternalDropHandler (node, event) {
      const root = this.getRoot()
      const cursorPosition = root.getCursorPositionFromCoords(event.clientX, event.clientY)
      root.$emit('externaldrop', cursorPosition, event)
      this.setCursorPosition(null)
    },
    select (path, addToSelection = false, event = null) {
      // do a fast lookup via nodesMap
      const pathStr = JSON.stringify(path);
      let clickedNodeModel = this.nodesMap[pathStr];
      if (!clickedNodeModel) {
        this.rebuildNodesMap();
        
        clickedNodeModel = this.nodesMap[pathStr];
      }
      if (!clickedNodeModel) return null;
    
      const isMultiselect = event && (event.ctrlKey || event.metaKey) && this.allowMultiselect;
      const shiftKeyIsPressed = event && event.shiftKey && this.allowMultiselect;

      addToSelection = (isMultiselect || addToSelection) && this.allowMultiselect;
    
      const enableShiftSelection = shiftKeyIsPressed && this.lastSelectedNode;
      if (enableShiftSelection) {
        // shift-select is the only case when we still need traverse
        // because we need to find the visual order of nodes
        let shiftSelectionStarted = false;
        this.traverse((node, nodeModel) => {
          const isBoundary = node.pathStr === pathStr || node.pathStr === this.lastSelectedNode._pathStr;
          if (isBoundary) {
            shiftSelectionStarted = !shiftSelectionStarted;
            nodeModel.isSelected = true; // Or your specific 'isSelectable' logic
          } else if (shiftSelectionStarted) {
            nodeModel.isSelected = true;
          }
        });
        this.selectedNodes = Object.values(this.nodesMap).filter(m => m.isSelected);
      } else if (addToSelection) {
        // toggle the clicked node selection state
        clickedNodeModel.isSelected = !clickedNodeModel.isSelected;
        this.selectedNodes = Object.values(this.nodesMap).filter(m => m.isSelected);
      } else {
        // single select - remove isSelected from already selected nodes,
        // set the clicked node as selected
        this.selectedNodes.forEach(nodeModel => {
          nodeModel.isSelected = false;
        });
        clickedNodeModel.isSelected = true;
        this.selectedNodes = [clickedNodeModel]
      }
    
      this.lastSelectedNode = clickedNodeModel;
      this.emitInput(this.currentValue);
      this.emitSelect(this.selectedNodes, event);
    
      return clickedNodeModel;
    },
    onMousemoveHandler (event) {
      if (!this.isRoot) {
        this.getRoot().onMousemoveHandler(event)
        return
      }
      if (this.preventDrag) {
        return
      }

      const initialDraggingState = this.isDragging
      const isDragging =
        this.isDragging || (
          this.mouseIsDown &&
          (this.lastMousePos.x !== event.clientX || this.lastMousePos.y !== event.clientY)
        )

      const isDragStarted = initialDraggingState === false && isDragging === true

      this.lastMousePos = {
        x: event.clientX,
        y: event.clientY
      }

      if (!isDragging) return

      const $root = this.getRoot().$el
      const rootRect = $root.getBoundingClientRect()
      const $dragInfo = this.$refs.dragInfo
      const dragInfoTop = (event.clientY - rootRect.top + $root.scrollTop - ($dragInfo.style.marginBottom | 0))
      const dragInfoLeft = (event.clientX - rootRect.left)

      $dragInfo.style.top = dragInfoTop + 'px'
      $dragInfo.style.left = dragInfoLeft + 'px'

      const cursorPosition = this.getCursorPositionFromCoords(event.clientX, event.clientY)
      const destNode = cursorPosition.node
      const placement = cursorPosition.placement

      if (isDragStarted && !destNode.isSelected) {
        this.select(destNode.path, false, event)
      }

      const draggableNodes = this.getDraggable()
      if (!draggableNodes.length) {
        this.preventDrag = true
        return
      }

      this.isDragging = isDragging
      this.setCursorPosition({ node: destNode, placement })

      const scrollBottomLine = rootRect.bottom - this.scrollAreaHeight
      const scrollDownSpeed = (event.clientY - scrollBottomLine) / (rootRect.bottom - scrollBottomLine)
      const scrollTopLine = rootRect.top + this.scrollAreaHeight
      const scrollTopSpeed = (scrollTopLine - event.clientY) / (scrollTopLine - rootRect.top)

      if (scrollDownSpeed > 0) {
        this.startScroll(scrollDownSpeed)
      } else if (scrollTopSpeed > 0) {
        this.startScroll(-scrollTopSpeed)
      } else {
        this.stopScroll()
      }
    },
    getCursorPositionFromCoords (x, y) {
      const $target = document.elementFromPoint(x, y)
      const $nodeItem = $target.getAttribute('path') ? $target : this.getClosetElementWithPath($target)
      let destNode
      let placement

      if ($nodeItem) {

        if (!$nodeItem) return

        destNode = this.getNode(JSON.parse($nodeItem.getAttribute('path')))

        const nodeHeight = $nodeItem.offsetHeight
        const edgeSize = this.edgeSize
        const offsetY = y - $nodeItem.getBoundingClientRect().top

        if (destNode.isLeaf) {
          placement = offsetY >= nodeHeight / 2 ? 'after' : 'before'
        } else {
          if (offsetY <= edgeSize) {
            placement = 'before'
          } else if (offsetY >= nodeHeight - edgeSize) {
            placement = 'after'
          } else {
            placement = 'inside'
          }
        }
      } else {
        const $root = this.getRoot().$el
        const rootRect = $root.getBoundingClientRect()
        if (y > rootRect.top + (rootRect.height / 2)) {
          placement = 'after'
          destNode = this.getLastNode()
        } else {
          placement = 'before'
          destNode = this.getFirstNode()
        }
      }

      return { node: destNode, placement }
    },
    getClosetElementWithPath ($el) {
      if (!$el) return null
      if ($el.getAttribute('path')) return $el
      return this.getClosetElementWithPath($el.parentElement)
    },
    onMouseleaveHandler (event) {
      if (!this.isRoot || !this.isDragging) return
      const $root = this.getRoot().$el
      const rootRect = $root.getBoundingClientRect()
      if (event.clientY >= rootRect.bottom) {
        this.setCursorPosition({ node: this.nodes.slice(-1)[0], placement: 'after' })
      } else if (event.clientY < rootRect.top) {
        this.setCursorPosition({ node: this.getFirstNode(), placement: 'before' })
      }
    },
    getNodeEl (path) {
      this.getRoot().$el.querySelector(`[path="${JSON.stringify(path)}"]`)
    },
    getLastNode () {
      let lastNode = null
      this.traverse((node) => {
        lastNode = node
      })
      return lastNode
    },
    getFirstNode () {
      return this.getNode([0])
    },
    getNextNode (path, filter = null) {
      let resultNode = null
      this.traverse((node) => {
        if (this.comparePaths(node.path, path) < 1) {
          return
        }
        if (!filter || filter(node)) {
          resultNode = node
          return false // stop traverse
        }
      })
      return resultNode
    },
    getPrevNode (path, filter) {
      let prevNodes = []
      this.traverse((node) => {
        if (this.comparePaths(node.path, path) >= 0) {
          return false
        }
        prevNodes.push(node)
      })
      let i = prevNodes.length
      while (i--) {
        const node = prevNodes[i]
        if (!filter || filter(node)) return node
      }
      return null
    },

    /**
     * returns 1 if path1 > path2
     * returns -1 if path1 < path2
     * returns 0 if path1 == path2
     *
     * examples
     *
     * [1, 2, 3] < [1, 2, 4]
     * [1, 1, 3] < [1, 2, 3]
     * [1, 2, 3] > [1, 2, 0]
     * [1, 2, 3] > [1, 1, 3]
     * [1, 2] < [1, 2, 0]
     *
     */
    comparePaths (path1, path2) {
      for (let i = 0; i < path1.length; i++) {
        if (path2[i] === void 0) return 1
        if (path1[i] > path2[i]) return 1
        if (path1[i] < path2[i]) return -1
      }
      return path2[path1.length] === void 0 ? 0 : -1
    },
    onNodeMousedownHandler (event, node) {
      // handle only left mouse button
      if (event.button !== 0) return

      if (!this.isRoot) {
        this.getRoot().onNodeMousedownHandler(event, node)
        return
      }
      this.mouseIsDown = true
    },
    startScroll (speed) {
      const $root = this.getRoot().$el
      if (this.scrollSpeed === speed) {
        return
      } else if (this.scrollIntervalId) {
        this.stopScroll()
      }

      this.scrollSpeed = speed
      this.scrollIntervalId = setInterval(() => {
        $root.scrollTop += this.maxScrollSpeed * speed
      }, 20)
    },
    stopScroll () {
      clearInterval(this.scrollIntervalId)
      this.scrollIntervalId = 0
      this.scrollSpeed = 0
    },
    onDocumentMouseupHandler (event) {
      if (this.isDragging) this.onNodeMouseupHandler(event)
    },
    onNodeMouseupHandler (event, targetNode = null) {
      // handle only left mouse button
      if (event.button !== 0) {
        return
      }
      if (!this.isRoot) {
        this.getRoot().onNodeMouseupHandler(event, targetNode)
        return
      }

      this.mouseIsDown = false
      if (!this.isDragging && targetNode && !this.preventDrag && event.currentTarget.dataset.tree === 'title') {
        this.select(targetNode.path, false, event)
      }

      this.preventDrag = false
      if (!this.cursorPosition) {
        this.stopDrag()
        return
      }
      const draggingNodes = this.getDraggable()
      // check that nodes is possible to insert
      for (let draggingNode of draggingNodes) {
        if (draggingNode.pathStr === this.cursorPosition.node.pathStr) {
          this.stopDrag()
          return
        }

        if (this.checkNodeIsParent(draggingNode, this.cursorPosition.node)) {
          this.stopDrag()
          return
        }
      }

      const newNodes = this.copy(this.currentValue)
      const nodeModelsSubjectToInsert = []

      // find dragging model to delete
      for (let draggingNode of draggingNodes) {
        const sourceSiblings = this.getNodeSiblings(newNodes, draggingNode.path)
        const draggingNodeModel = sourceSiblings[draggingNode.ind]
        nodeModelsSubjectToInsert.push(draggingNodeModel)
      }

      // allow the drop to be cancelled
      let cancelled = false
      this.emitBeforeDrop(draggingNodes, this.cursorPosition, () => cancelled = true)
      if (cancelled) {
        this.stopDrag()
        return
      }

      const nodeModelsToInsert = []
      // mark dragging model to delete
      for (let draggingNodeModel of nodeModelsSubjectToInsert) {
        nodeModelsToInsert.push(this.copy(draggingNodeModel))
        draggingNodeModel['_markToDelete'] = true
      }

      // insert dragging nodes to the new place
      this.insertModels(this.cursorPosition, nodeModelsToInsert, newNodes)

      // delete dragging node from the old place
      this.traverseModels((nodeModel, siblings, ind) => {
        if (!nodeModel._markToDelete) return
        siblings.splice(ind, 1)
      }, newNodes)

      this.lastSelectedNode = null
      this.emitInput(newNodes)
      this.emitDrop(draggingNodes, this.cursorPosition, event)
      this.stopDrag()
    },
    onToggleHandler (event, node) {
      if (!this.allowToggleBranch) {
        return
      }
      this.updateNode(node.path, { isExpanded: !node.isExpanded })
      this.emitToggle(node, event)
      event.stopPropagation()
    },
    stopDrag () {
      this.isDragging = false
      this.mouseIsDown = false
      this.setCursorPosition(null)
      this.stopScroll()
    },
    getParent () {
      return this.$parent
    },
    getRoot () {
      if (this.isRoot) return this
      return this.getParent().getRoot()
    },
    getNodeSiblings (nodes, path) {
      if (path.length === 1) return nodes
      return this.getNodeSiblings(nodes[path[0]].children, path.slice(1))
    },
    updateNode (path, patch) {
      if (!this.isRoot) {
        this.getParent().updateNode(path, patch)
        return
      }

      const pathStr = JSON.stringify(path)
      const newNodes = this.copy(this.currentValue)
      this.traverse((node, nodeModel) => {
        if (node.pathStr !== pathStr) return
        Object.assign(nodeModel, patch)
      }, newNodes)

      this.emitInput(newNodes)
    },
    getSelected () {
      const selectedNodes = []
      this.traverse((node) => {
        if (node.isSelected) selectedNodes.push(node)
      })
      return selectedNodes
    },
    getDraggable () {
      const selectedNodes = []
      this.traverse((node) => {
        if (node.isSelected && node.isDraggable) selectedNodes.push(node)
      })
      return selectedNodes
    },
    traverse (
      cb,
      nodeModels = null,
      parentPath = []
    ) {
      if (!nodeModels) nodeModels = this.currentValue
      let shouldStop = false

      const nodes = []

      for (let nodeInd = 0; nodeInd < nodeModels.length; nodeInd++) {
        const nodeModel = nodeModels[nodeInd]
        const itemPath = parentPath.concat(nodeInd)
        // FIXME? can we resolve node in more simple way here instead of runing getnode?
        const node = this.getNode(itemPath, nodeModel, nodeModels)
        shouldStop = cb(node, nodeModel, nodeModels) === false
        nodes.push(node)

        if (shouldStop) break

        if (nodeModel.children) {
          shouldStop = this.traverse(cb, nodeModel.children, itemPath) === false
          if (shouldStop) break
        }
      }

      return !shouldStop ? nodes : false
    },
    traverseModels (cb, nodeModels) {
      let i = nodeModels.length
      while (i--) {
        const nodeModel = nodeModels[i]
        if (nodeModel.children) this.traverseModels(cb, nodeModel.children)
        cb(nodeModel, nodeModels, i)
      }
      return nodeModels
    },
    remove (paths) {
      const pathsStr = paths.map(path => JSON.stringify(path))
      const newNodes = this.copy(this.currentValue)
      this.traverse((node, nodeModel, siblings) => {
        for (const pathStr of pathsStr) {
          if (node.pathStr === pathStr) nodeModel._markToDelete = true
        }
      }, newNodes)

      this.traverseModels((nodeModel, siblings, ind) => {
        if (!nodeModel._markToDelete) return
        siblings.splice(ind, 1)
      }, newNodes)

      this.emitInput(newNodes)
    },
    insertModels (cursorPosition, nodeModels, newNodes) {
      const destNode = cursorPosition.node
      const destSiblings = this.getNodeSiblings(newNodes, destNode.path)
      const destNodeModel = destSiblings[destNode.ind]

      if (cursorPosition.placement === 'inside') {
        destNodeModel.children = destNodeModel.children || []
        destNodeModel.children.unshift(...nodeModels)
      } else {
        const insertInd = cursorPosition.placement === 'before' ?
          destNode.ind :
          destNode.ind + 1

        destSiblings.splice(insertInd, 0, ...nodeModels)
      }
    },
    insert (cursorPosition, nodeModel) {
      const nodeModels = Array.isArray(nodeModel) ? nodeModel : [nodeModel]
      const newNodes = this.copy(this.currentValue)
      this.insertModels(cursorPosition, nodeModels, newNodes)
      this.emitInput(newNodes)
    },
    checkNodeIsParent (sourceNode, destNode) {
      const destPath = destNode.path
      return JSON.stringify(destPath.slice(0, sourceNode.path.length)) === sourceNode.pathStr
    },
    // copy (entity) {
    //   return JSON.parse(JSON.stringify(entity))
    // }
    copy(entity) {
      // console.time('TreeCopyOperation');
      // const result = JSON.parse(JSON.stringify(entity));
      const result = [...entity];
      // console.timeEnd('TreeCopyOperation');
      return result;
    }
  }
}
