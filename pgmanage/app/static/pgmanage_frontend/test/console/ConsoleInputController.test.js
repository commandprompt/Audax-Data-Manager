import { describe, it, expect, vi } from "vitest";
import { ConsoleInputController, QUIET_RESET } from "@src/console/ConsoleInputController.js";

function makeController(overrides = {}) {
  return new ConsoleInputController({ dialect: "postgresql", ...overrides });
}

function fakeTerminal() {
  return { write: vi.fn() };
}

function state(c) {
  return { lines: c.lines, cursorRow: c.cursorRow, cursorCol: c.cursorCol };
}

describe("ConsoleInputController", () => {
  describe("insertText", () => {
    it("inserts single-line text at the cursor", () => {
      const c = makeController();
      c.insertText("hi");
      expect(state(c)).toEqual({ lines: ["hi"], cursorRow: 0, cursorCol: 2 });
    });

    it("splits a multi-line paste across lines[]", () => {
      const c = makeController();
      c.insertText("select 1\nfrom dual");
      expect(state(c)).toEqual({ lines: ["select 1", "from dual"], cursorRow: 1, cursorCol: 9 });
    });
  });

  describe("handleData key dispatch", () => {
    function withText(text = "select foo bar") {
      const c = makeController();
      c.insertText(text);
      return c;
    }

    it.each([
      ["Home", "\x1b[H"],
      ["Home_alt", "\x1b[1~"],
      ["Ctrl+A", "\x01"],
    ])("%s moves to column 0", (label, seq) => {
      const c = withText();
      c.handleData(seq);
      expect(state(c)).toEqual({ lines: ["select foo bar"], cursorRow: 0, cursorCol: 0 });
    });

    it.each([
      ["End", "\x1b[F"],
      ["End_alt", "\x1b[4~"],
      ["Ctrl+E", "\x05"],
    ])("%s moves to end of line", (label, seq) => {
      const c = withText();
      c.handleData("\x1b[H");
      c.handleData(seq);
      expect(state(c)).toEqual({ lines: ["select foo bar"], cursorRow: 0, cursorCol: 14 });
    });

    it.each([
      ["DEL", "\x7f"],
      ["BS", "\b"],
    ])("Backspace (%s) deletes the char before the cursor", (label, seq) => {
      const c = withText();
      c.handleData(seq);
      expect(state(c)).toEqual({ lines: ["select foo ba"], cursorRow: 0, cursorCol: 13 });
    });

    it.each([
      ["Delete key", "\x1b[3~"],
      ["Ctrl+D", "\x04"],
    ])("DeleteForward (%s) deletes the char under the cursor", (label, seq) => {
      const c = withText();
      c.handleData("\x1b[H");
      c.handleData(seq);
      expect(state(c)).toEqual({ lines: ["elect foo bar"], cursorRow: 0, cursorCol: 0 });
    });

    it("ArrowLeft moves the cursor left", () => {
      const c = withText();
      c.handleData("\x1b[D");
      expect(state(c)).toEqual({ lines: ["select foo bar"], cursorRow: 0, cursorCol: 13 });
    });

    it("ArrowRight moves the cursor right", () => {
      const c = withText();
      c.handleData("\x1b[D");
      c.handleData("\x1b[C");
      expect(state(c)).toEqual({ lines: ["select foo bar"], cursorRow: 0, cursorCol: 14 });
    });

    it("Ctrl+W deletes the word behind the cursor", () => {
      const c = withText();
      c.handleData("\x17");
      expect(state(c)).toEqual({ lines: ["select foo "], cursorRow: 0, cursorCol: 11 });
    });

    it("Ctrl+U deletes to the start of the line", () => {
      const c = withText();
      c.handleData("\x15");
      expect(state(c)).toEqual({ lines: [""], cursorRow: 0, cursorCol: 0 });
    });

    it("Ctrl+K deletes to the end of the line", () => {
      const c = withText();
      c.handleData("\x1b[H");
      c.handleData("\x0b");
      expect(state(c)).toEqual({ lines: [""], cursorRow: 0, cursorCol: 0 });
    });

    it.each([
      ["Alt+B", "\x1bb"],
      ["Ctrl+Left", "\x1b[1;5D"],
    ])("%s moves one word left", (label, seq) => {
      const c = withText();
      c.handleData(seq);
      expect(state(c)).toEqual({ lines: ["select foo bar"], cursorRow: 0, cursorCol: 11 });
    });

    it.each([
      ["Alt+F", "\x1bf"],
      ["Ctrl+Right", "\x1b[1;5C"],
    ])("%s moves one word right", (label, seq) => {
      const c = withText();
      c.handleData("\x1b[H");
      c.handleData(seq);
      expect(state(c)).toEqual({ lines: ["select foo bar"], cursorRow: 0, cursorCol: 6 });
    });

    it("plain text still falls through to insertText", () => {
      const c = makeController();
      c.handleData("hi");
      expect(state(c)).toEqual({ lines: ["hi"], cursorRow: 0, cursorCol: 2 });
    });
  });

  describe("Enter", () => {
    it("an incomplete statement inserts a continuation line and returns false", () => {
      const onSubmit = vi.fn();
      const c = makeController({ onSubmit });
      c.insertText("select 1");
      const submitted = c.handleData("\r");
      expect(submitted).toBe(false);
      expect(state(c)).toEqual({ lines: ["select 1", ""], cursorRow: 1, cursorCol: 0 });
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it("a complete statement calls onSubmit with the buffer and returns true", () => {
      const onSubmit = vi.fn();
      const c = makeController({ onSubmit });
      c.insertText("select 1;");
      const submitted = c.handleData("\r");
      expect(submitted).toBe(true);
      expect(onSubmit).toHaveBeenCalledWith("select 1;");
      expect(state(c)).toEqual({ lines: [""], cursorRow: 0, cursorCol: 0 });
    });

    it("an empty/whitespace-only buffer signals QUIET_RESET (matches real psql: Enter still advances to a fresh prompt)", () => {
      const onSubmit = vi.fn();
      const c = makeController({ onSubmit });
      const result = c.handleData("\r");
      expect(result).toBe(QUIET_RESET);
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it("a bare semicolon alone signals QUIET_RESET and is cleared rather than left to leak into the next command", () => {
      const onSubmit = vi.fn();
      const c = makeController({ onSubmit });
      c.insertText(";");
      const result = c.handleData("\r");
      expect(result).toBe(QUIET_RESET);
      expect(onSubmit).not.toHaveBeenCalled();
      expect(state(c)).toEqual({ lines: [""], cursorRow: 0, cursorCol: 0 });
    });

    it("multiple bare semicolons alone signal QUIET_RESET, not a submission (bug: used to reach the backend)", () => {
      const onSubmit = vi.fn();
      const c = makeController({ onSubmit });
      c.insertText(";;;");
      const result = c.handleData("\r");
      expect(result).toBe(QUIET_RESET);
      expect(onSubmit).not.toHaveBeenCalled();
      expect(state(c)).toEqual({ lines: [""], cursorRow: 0, cursorCol: 0 });
    });
  });

  describe("history recall", () => {
    it("ArrowUp/ArrowDown walk newest-to-oldest and back, restoring the staged buffer", () => {
      const c = makeController();
      c.setPreloadedHistory(["select 1;", "select 2;"]);

      c.handleData("\x1b[A"); // up: stash "" , recall newest
      expect(c.getCurrentBuffer()).toBe("select 2;");

      c.handleData("\x1b[A"); // up: older entry
      expect(c.getCurrentBuffer()).toBe("select 1;");

      c.handleData("\x1b[A"); // up at oldest: no-op
      expect(c.getCurrentBuffer()).toBe("select 1;");

      c.handleData("\x1b[B"); // down: newer entry
      expect(c.getCurrentBuffer()).toBe("select 2;");

      c.handleData("\x1b[B"); // down past newest: restore staged buffer
      expect(c.getCurrentBuffer()).toBe("");

      c.handleData("\x1b[B"); // down with no history index: no-op
      expect(c.getCurrentBuffer()).toBe("");
    });

    it("multi-line cursor movement takes priority over history recall until at the buffer edge", () => {
      const c = makeController();
      c.setPreloadedHistory(["select 1;"]);
      c.insertText("line1\nline2\nline3");
      expect(c.cursorRow).toBe(2);

      c.handleData("\x1b[A"); // just moves up within the buffer
      expect(c.cursorRow).toBe(1);
      expect(c.getCurrentBuffer()).toBe("line1\nline2\nline3");

      c.handleData("\x1b[A"); // still within buffer
      expect(c.cursorRow).toBe(0);
      expect(c.getCurrentBuffer()).toBe("line1\nline2\nline3");

      c.handleData("\x1b[A"); // now at top row: recalls history
      expect(c.getCurrentBuffer()).toBe("select 1;");
    });
  });

  describe("setBuffer", () => {
    it("setBuffer replaces the buffer and puts the cursor at the end", () => {
      const c = makeController();
      c.setBuffer("abc\ndef");
      expect(state(c)).toEqual({ lines: ["abc", "def"], cursorRow: 1, cursorCol: 3 });
    });

    it("setBuffer resets history browsing (single-line, so ArrowUp acts on history immediately)", () => {
      const c = makeController();
      c.setPreloadedHistory(["old;"]);
      c.handleData("\x1b[A"); // start browsing history
      c.setBuffer("abc");
      // history browsing was reset: ArrowUp now stashes the new buffer as staging
      // instead of continuing to page through history from where it left off.
      c.handleData("\x1b[A");
      expect(c.getCurrentBuffer()).toBe("old;");
      c.handleData("\x1b[B"); // back down restores the staged "abc", not the pre-setBuffer value
      expect(c.getCurrentBuffer()).toBe("abc");
    });
  });

  describe("bracketed paste", () => {
    it("unwraps pasted content and inserts it as text", () => {
      const c = makeController();
      c.handleData("\x1b[200~select 1\nfrom dual\x1b[201~");
      expect(state(c)).toEqual({ lines: ["select 1", "from dual"], cursorRow: 1, cursorCol: 9 });
    });

    it("preserves line breaks in an unbracketed multi-line paste (\\r-separated, no markers)", () => {
      // xterm.js only wraps pastes in PASTE_START/PASTE_END when bracketed
      // paste mode is enabled on the terminal - otherwise it delivers the
      // raw text as one chunk with bare \r as the line separator. \r must
      // survive the control-byte strip below or every line collapses into one.
      const c = makeController();
      c.handleData("select 1\rfrom dual");
      expect(state(c)).toEqual({ lines: ["select 1", "from dual"], cursorRow: 1, cursorCol: 9 });
    });
  });

  describe("unrecognized escape sequences (Alt+Backspace regression)", () => {
    it("a bare ESC is dropped, not inserted", () => {
      const c = makeController();
      c.insertText("abc");
      c.handleData("\x1b");
      expect(state(c)).toEqual({ lines: ["abc"], cursorRow: 0, cursorCol: 3 });
    });

    it("an unrecognized ESC-prefixed sequence is dropped outright, not partially inserted", () => {
      const c = makeController();
      c.insertText("abc");
      c.handleData("\x1bZZZ");
      expect(state(c)).toEqual({ lines: ["abc"], cursorRow: 0, cursorCol: 3 });
    });
  });

  describe("onBufferChange callback", () => {
    it("fires with the current buffer text after insertText", () => {
      const seen = [];
      const c = makeController({ onBufferChange: (text) => seen.push(text) });
      c.insertText("select 1");
      expect(seen).toEqual(["select 1"]);
    });

    it("fires on other mutating operations too (backspace, history recall)", () => {
      const seen = [];
      const c = makeController({ onBufferChange: (text) => seen.push(text) });
      c.setPreloadedHistory(["select 9;"]);
      c.insertText("ab");
      c.handleData("\x7f"); // backspace
      c.handleData("\x1b[A"); // history recall
      expect(seen).toEqual(["ab", "a", "select 9;"]);
    });
  });

  describe("render", () => {
    it("batches the whole redraw into exactly one terminal.write() call", () => {
      const c = makeController();
      c.insertText("select 1\nfrom dual");
      const term = fakeTerminal();
      c.render(term);
      expect(term.write).toHaveBeenCalledTimes(1);
    });
  });

  describe("beginNewInputLine", () => {
    it("resets to an empty input line and renders exactly once", () => {
      const c = makeController();
      c.insertText("select 1");
      const term = fakeTerminal();
      c.beginNewInputLine(term);
      expect(state(c)).toEqual({ lines: [""], cursorRow: 0, cursorCol: 0 });
      expect(term.write).toHaveBeenCalledTimes(1);
    });
  });
});
