import { isStatementComplete, isEffectivelyEmpty } from "./sql_statement_scanner.js";

// Named ANSI/VT escape sequences and control codes, instead of scattered literals.
const ESC = "\x1b";

const CR = "\r";
const CRLF = "\r\n";
const CURSOR_HOME = `${ESC}[H`;
const ERASE_TO_END_OF_SCREEN = `${ESC}[0J`;
const ERASE_SCREEN = `${ESC}[2J`;
const ERASE_SCROLLBACK = `${ESC}[3J`;
const CURSOR_UP = (n) => `${ESC}[${n}A`;
const CURSOR_FORWARD = (n) => `${ESC}[${n}C`;

// Full hard reset. Not `terminal.clear()` - that keeps the current line,
// leaving stale content out of sync with our cursor tracking.
export const CLEAR_TERMINAL = CURSOR_HOME + ERASE_SCREEN + ERASE_SCROLLBACK;

// Bracketed-paste markers xterm.js wraps pasted text in.
const PASTE_START = `${ESC}[200~`;
const PASTE_END = `${ESC}[201~`;

// handleData/handleEnter return this instead of false when Enter is pressed
// on an effectively-empty buffer - like real psql/sqlite3, it still advances
// to a fresh prompt line rather than submitting or silently doing nothing.
export const QUIET_RESET = Symbol("QUIET_RESET");

// Keystroke sequences recognized from the terminal's input event.
const KEY = {
  BACKSPACE_DEL: "\x7f",
  BACKSPACE_BS: "\b",
  DELETE: `${ESC}[3~`,
  ARROW_LEFT: `${ESC}[D`,
  ARROW_RIGHT: `${ESC}[C`,
  ARROW_UP: `${ESC}[A`,
  ARROW_DOWN: `${ESC}[B`,
  HOME: CURSOR_HOME,
  HOME_ALT: `${ESC}[1~`,
  CTRL_A: "\x01",
  END: `${ESC}[F`,
  END_ALT: `${ESC}[4~`,
  CTRL_E: "\x05",
  CTRL_D: "\x04",
  CTRL_W: "\x17",
  CTRL_U: "\x15",
  CTRL_K: "\x0b",
  ALT_B: `${ESC}b`,
  CTRL_LEFT: `${ESC}[1;5D`,
  ALT_F: `${ESC}f`,
  CTRL_RIGHT: `${ESC}[1;5C`,
};

const KEY_HANDLERS = {
  [KEY.BACKSPACE_DEL]: "backspace",
  [KEY.BACKSPACE_BS]: "backspace",
  [KEY.DELETE]: "deleteForward",
  [KEY.ARROW_LEFT]: "moveLeft",
  [KEY.ARROW_RIGHT]: "moveRight",
  [KEY.ARROW_UP]: "historyUp",
  [KEY.ARROW_DOWN]: "historyDown",
  [KEY.HOME]: "moveHome",
  [KEY.HOME_ALT]: "moveHome",
  [KEY.CTRL_A]: "moveHome",
  [KEY.END]: "moveEnd",
  [KEY.END_ALT]: "moveEnd",
  [KEY.CTRL_E]: "moveEnd",
  [KEY.CTRL_D]: "deleteForward",
  [KEY.CTRL_W]: "deleteWordBackward",
  [KEY.CTRL_U]: "deleteToLineStart",
  [KEY.CTRL_K]: "deleteToLineEnd",
  [KEY.ALT_B]: "moveWordLeft",
  [KEY.CTRL_LEFT]: "moveWordLeft",
  [KEY.ALT_F]: "moveWordRight",
  [KEY.CTRL_RIGHT]: "moveWordRight",
};

// Drives the console input region (buffer/cursor/history, VT parsing, redraw).
// Cursor row is tracked in JS, not read from the terminal, since write() is async.
// Assumes one line per screen row - no wrap-width tracking.
export class ConsoleInputController {
  constructor({ dialect, promptPrimary = "=# ", promptContinuation = "-# ", onSubmit, onBufferChange } = {}) {
    this.dialect = dialect;
    this.promptPrimary = promptPrimary;
    this.promptContinuation = promptContinuation;
    this.onSubmit = onSubmit;
    this.onBufferChange = onBufferChange;

    this.lines = [""];
    this.cursorRow = 0;
    this.cursorCol = 0;
    this.history = [];
    this.historyIndex = null;
    this.stagingBuffer = null;
    this.locked = false;
    this._cursorRowOffset = 0;
  }

  setLocked(locked) {
    this.locked = locked;
  }

  setPreloadedHistory(snippets) {
    this.history = snippets.slice();
    this.historyIndex = null;
    this.stagingBuffer = null;
  }

  getCurrentBuffer() {
    return this.lines.join("\n");
  }

  setBuffer(text) {
    this.historyIndex = null;
    this.stagingBuffer = null;
    this.setBufferLines(text);
  }

  insertText(rawText) {
    const text = rawText.replace(/\t/g, "    ");
    const parts = text.split(/\r\n|\r|\n/);
    const line = this.lines[this.cursorRow];
    const before = line.slice(0, this.cursorCol);
    const after = line.slice(this.cursorCol);

    if (parts.length === 1) {
      this.lines[this.cursorRow] = before + parts[0] + after;
      this.cursorCol = before.length + parts[0].length;
    } else {
      const newLines = [before + parts[0], ...parts.slice(1, -1), parts[parts.length - 1] + after];
      this.lines.splice(this.cursorRow, 1, ...newLines);
      this.cursorRow += parts.length - 1;
      this.cursorCol = parts[parts.length - 1].length;
    }
    this.notifyBufferChange();
  }

  // Returns true if a command was submitted (caller should skip render() -
  // onSubmit handles advancing the terminal), QUIET_RESET if Enter hit an
  // effectively-empty buffer (caller should advance a line and start fresh
  // without submitting), or false otherwise (caller should render in place).
  handleData(data) {
    if (this.locked) return false;

    // Enter returns its own result rather than a hardcoded false, so it's
    // handled separately from KEY_HANDLERS.
    if (data === CR) return this.handleEnter();

    const handlerName = KEY_HANDLERS[data];
    if (handlerName) {
      this[handlerName]();
      return false;
    }

    let text = data;
    if (text.startsWith(PASTE_START) && text.endsWith(PASTE_END)) {
      text = text.slice(PASTE_START.length, -PASTE_END.length);
    } else if (text.startsWith(ESC)) {
      // Unrecognized ESC sequence (e.g. some Alt+Backspace variants) - drop
      // it instead of leaking a stray fragment into the buffer.
      return false;
    }
    // Strip stray control bytes, but keep \r (0x0d) - unbracketed multi-line
    // pastes deliver line breaks as bare \r, which insertText splits on.
    text = text.replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, "");
    if (text) this.insertText(text);
    return false;
  }

  // Redraws the input region in one write() call - splitting across multiple
  // writes let xterm.js paint an intermediate frame, flashing the cursor.
  render(terminal) {
    let out = "";
    if (this._cursorRowOffset > 0) {
      out += CURSOR_UP(this._cursorRowOffset);
    }
    out += CR + ERASE_TO_END_OF_SCREEN;

    for (let i = 0; i < this.lines.length; i++) {
      if (i > 0) out += CRLF;
      out += (i === 0 ? this.promptPrimary : this.promptContinuation) + this.lines[i];
    }

    const rowsUp = (this.lines.length - 1) - this.cursorRow;
    if (rowsUp > 0) out += CURSOR_UP(rowsUp);
    const prefixLen = this.cursorRow === 0 ? this.promptPrimary.length : this.promptContinuation.length;
    const col = prefixLen + this.cursorCol;
    out += col > 0 ? CR + CURSOR_FORWARD(col) : CR;

    terminal.write(out);
    this._cursorRowOffset = this.cursorRow;
  }

  // Resets to a fresh input line anchored at the terminal's current position.
  beginNewInputLine(terminal) {
    this._cursorRowOffset = 0;
    this.lines = [""];
    this.cursorRow = 0;
    this.cursorCol = 0;
    this.render(terminal);
  }

  handleEnter() {
    const bufferText = this.getCurrentBuffer();
    if (isEffectivelyEmpty(bufferText, this.dialect)) {
      this.lines = [""];
      this.cursorRow = 0;
      this.cursorCol = 0;
      this.notifyBufferChange();
      return QUIET_RESET;
    }

    if (!isStatementComplete(bufferText, this.dialect)) {
      const line = this.lines[this.cursorRow];
      const before = line.slice(0, this.cursorCol);
      const after = line.slice(this.cursorCol);
      this.lines.splice(this.cursorRow, 1, before, after);
      this.cursorRow += 1;
      this.cursorCol = 0;
      this.notifyBufferChange();
      return false;
    }

    this.commitSubmit(bufferText);
    return true;
  }

  commitSubmit(submitText) {
    this.history.push(submitText);
    this.historyIndex = null;
    this.stagingBuffer = null;
    this.lines = [""];
    this.cursorRow = 0;
    this.cursorCol = 0;
    this.notifyBufferChange();
    this.onSubmit?.(submitText);
  }

  backspace() {
    if (this.cursorCol > 0) {
      const line = this.lines[this.cursorRow];
      this.lines[this.cursorRow] = line.slice(0, this.cursorCol - 1) + line.slice(this.cursorCol);
      this.cursorCol -= 1;
      this.notifyBufferChange();
    } else if (this.cursorRow > 0) {
      const prevLine = this.lines[this.cursorRow - 1];
      const curLine = this.lines[this.cursorRow];
      this.lines.splice(this.cursorRow - 1, 2, prevLine + curLine);
      this.cursorRow -= 1;
      this.cursorCol = prevLine.length;
      this.notifyBufferChange();
    }
  }

  deleteForward() {
    const line = this.lines[this.cursorRow];
    if (this.cursorCol < line.length) {
      this.lines[this.cursorRow] = line.slice(0, this.cursorCol) + line.slice(this.cursorCol + 1);
      this.notifyBufferChange();
    } else if (this.cursorRow < this.lines.length - 1) {
      const nextLine = this.lines[this.cursorRow + 1];
      this.lines.splice(this.cursorRow, 2, line + nextLine);
      this.notifyBufferChange();
    }
  }

  moveLeft() {
    if (this.cursorCol > 0) {
      this.cursorCol -= 1;
    } else if (this.cursorRow > 0) {
      this.cursorRow -= 1;
      this.cursorCol = this.lines[this.cursorRow].length;
    }
  }

  moveRight() {
    const line = this.lines[this.cursorRow];
    if (this.cursorCol < line.length) {
      this.cursorCol += 1;
    } else if (this.cursorRow < this.lines.length - 1) {
      this.cursorRow += 1;
      this.cursorCol = 0;
    }
  }

  moveHome() {
    this.cursorCol = 0;
  }

  moveEnd() {
    this.cursorCol = this.lines[this.cursorRow].length;
  }

  // Word-boundary helpers scoped to the current line only (matches readline behavior).
  wordBackwardCol() {
    const line = this.lines[this.cursorRow];
    let i = this.cursorCol;
    while (i > 0 && /\s/.test(line[i - 1])) i--;
    while (i > 0 && !/\s/.test(line[i - 1])) i--;
    return i;
  }

  wordForwardCol() {
    const line = this.lines[this.cursorRow];
    const len = line.length;
    let i = this.cursorCol;
    while (i < len && /\s/.test(line[i])) i++;
    while (i < len && !/\s/.test(line[i])) i++;
    return i;
  }

  moveWordLeft() {
    this.cursorCol = this.wordBackwardCol();
  }

  moveWordRight() {
    this.cursorCol = this.wordForwardCol();
  }

  deleteWordBackward() {
    const line = this.lines[this.cursorRow];
    const start = this.wordBackwardCol();
    if (start === this.cursorCol) return;
    this.lines[this.cursorRow] = line.slice(0, start) + line.slice(this.cursorCol);
    this.cursorCol = start;
    this.notifyBufferChange();
  }

  deleteToLineStart() {
    const line = this.lines[this.cursorRow];
    if (this.cursorCol === 0) return;
    this.lines[this.cursorRow] = line.slice(this.cursorCol);
    this.cursorCol = 0;
    this.notifyBufferChange();
  }

  deleteToLineEnd() {
    const line = this.lines[this.cursorRow];
    if (this.cursorCol >= line.length) return;
    this.lines[this.cursorRow] = line.slice(0, this.cursorCol);
    this.notifyBufferChange();
  }

  historyUp() {
    if (this.cursorRow > 0) {
      this.cursorRow -= 1;
      this.cursorCol = Math.min(this.cursorCol, this.lines[this.cursorRow].length);
      return;
    }
    if (this.historyIndex === null) {
      if (this.history.length === 0) return;
      this.stagingBuffer = this.getCurrentBuffer();
      this.historyIndex = this.history.length - 1;
      this.loadHistoryEntry();
    } else if (this.historyIndex > 0) {
      this.historyIndex -= 1;
      this.loadHistoryEntry();
    }
  }

  historyDown() {
    if (this.cursorRow < this.lines.length - 1) {
      this.cursorRow += 1;
      this.cursorCol = Math.min(this.cursorCol, this.lines[this.cursorRow].length);
      return;
    }
    if (this.historyIndex === null) return;
    if (this.historyIndex < this.history.length - 1) {
      this.historyIndex += 1;
      this.loadHistoryEntry();
    } else {
      this.historyIndex = null;
      this.setBufferLines(this.stagingBuffer ?? "");
      this.stagingBuffer = null;
    }
  }

  loadHistoryEntry() {
    this.setBufferLines(this.history[this.historyIndex]);
  }

  setBufferLines(text) {
    this.lines = text.length ? text.split("\n") : [""];
    this.cursorRow = this.lines.length - 1;
    this.cursorCol = this.lines[this.cursorRow].length;
    this.notifyBufferChange();
  }

  notifyBufferChange() {
    this.onBufferChange?.(this.getCurrentBuffer());
  }
}
