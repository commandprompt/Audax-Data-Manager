import findLastIndex from "lodash/findLastIndex";

const STATE = {
  NORMAL: "NORMAL",
  SINGLE_QUOTE: "SINGLE_QUOTE",
  DOUBLE_QUOTE: "DOUBLE_QUOTE",
  BACKTICK: "BACKTICK",
  DOLLAR_QUOTE: "DOLLAR_QUOTE",
  LINE_COMMENT: "LINE_COMMENT",
  BLOCK_COMMENT: "BLOCK_COMMENT",
};

// Scans for quote/comment state and builds a comment-stripped copy of the
// text (mirrors pgcli's strip_comments) so a trailing comment can't hide a
// terminator. Block comments are treated as non-nested (simplification).
function scanBuffer(text, dialect) {
  const isMySQLFamily = dialect === "mysql" || dialect === "mariadb";
  let state = STATE.NORMAL;
  let dollarTag = null;
  let codeText = "";

  for (let i = 0; i < text.length; i++) {
    const start = i;
    const c = text[i];
    const next = text[i + 1];
    let skipAppend = false;

    switch (state) {
      case STATE.NORMAL:
        if (c === "'") {
          state = STATE.SINGLE_QUOTE;
        } else if (c === '"') {
          state = STATE.DOUBLE_QUOTE;
        } else if (c === "`" && isMySQLFamily) {
          state = STATE.BACKTICK;
        } else if (c === "-" && next === "-") {
          state = STATE.LINE_COMMENT;
          i++;
          skipAppend = true;
        } else if (c === "#" && isMySQLFamily) {
          state = STATE.LINE_COMMENT;
          skipAppend = true;
        } else if (c === "/" && next === "*") {
          state = STATE.BLOCK_COMMENT;
          i++;
          skipAppend = true;
        } else if (c === "$" && dialect === "postgresql") {
          const match = /^\$([A-Za-z_]\w*)?\$/.exec(text.slice(i));
          if (match) {
            dollarTag = match[0];
            state = STATE.DOLLAR_QUOTE;
            i += match[0].length - 1;
          }
        }
        break;

      case STATE.SINGLE_QUOTE:
        if (c === "'" && next === "'") {
          i++;
        } else if (c === "\\" && isMySQLFamily) {
          i++;
        } else if (c === "'") {
          state = STATE.NORMAL;
        }
        break;

      case STATE.DOUBLE_QUOTE:
        if (c === '"' && next === '"') {
          i++;
        } else if (c === "\\" && isMySQLFamily) {
          i++;
        } else if (c === '"') {
          state = STATE.NORMAL;
        }
        break;

      case STATE.BACKTICK:
        if (c === "`" && next === "`") {
          i++;
        } else if (c === "`") {
          state = STATE.NORMAL;
        }
        break;

      case STATE.DOLLAR_QUOTE:
        if (text.startsWith(dollarTag, i)) {
          i += dollarTag.length - 1;
          state = STATE.NORMAL;
          dollarTag = null;
        }
        break;

      case STATE.LINE_COMMENT:
        skipAppend = true;
        if (c === "\n") {
          state = STATE.NORMAL;
          codeText += "\n";
        }
        break;

      case STATE.BLOCK_COMMENT:
        skipAppend = true;
        if (c === "\n") {
          codeText += "\n";
        } else if (c === "*" && next === "/") {
          state = STATE.NORMAL;
          i++;
        }
        break;
    }

    if (!skipAppend) {
      codeText += text.slice(start, i + 1);
    }
  }

  return { state, codeText };
}

// Last non-blank line of the comment-stripped text (ignores trailing comment-only lines).
function lastCodeLine(codeText) {
  const codeLines = codeText.split("\n");
  const idx = findLastIndex(codeLines, (line) => line.trim() !== "");
  return { idx, line: idx >= 0 ? codeLines[idx].trim() : "" };
}

// Backslash meta-commands (\d, \c, etc.) are complete the moment they're typed.
const isMetaCommand = (text) => text.trimStart()[0] === "\\";

// oracle's bare "/" and mssql's bare "GO[ n]" terminator lines.
function isBareTerminatorLine(line, dialect) {
  if (dialect === "oracle") return line === "/";
  if (dialect === "mssql") return /^go(\s+\d+)?$/i.test(line);
  return false;
}

// Whether Enter should submit or continue - mimics each DB's own CLI (psql/mysql/sqlplus/sqlcmd).
export function isStatementComplete(bufferText, dialect) {
  const trimmed = bufferText.trimEnd();

  if (trimmed === "") {
    return false;
  }

  if (isMetaCommand(trimmed)) {
    return true;
  }

  const { state: endState, codeText } = scanBuffer(trimmed, dialect);
  // A trailing line comment isn't "open" like an unclosed quote/block-comment -
  // Enter always ends the current line, which closes a line comment too.
  if (endState !== STATE.NORMAL && endState !== STATE.LINE_COMMENT) {
    return false;
  }

  // Comment-stripped from here on, so e.g. "select 1; -- note" isn't hidden by the comment.
  if (codeText.trimEnd().endsWith(";")) {
    return true;
  }

  const { line } = lastCodeLine(codeText);
  return isBareTerminatorLine(line, dialect);
}

// Whether bufferText has no real SQL to submit - blank, comments only, or
// just bare terminators (";", ";;;", oracle "/", mssql "GO") with nothing else.
// isStatementComplete would call these "complete" (a bare ";" does end a
// statement), but there's nothing worth sending to the backend for them.
export function isEffectivelyEmpty(bufferText, dialect) {
  const trimmed = bufferText.trimEnd();
  if (trimmed === "") {
    return true;
  }
  if (isMetaCommand(trimmed)) {
    return false;
  }

  const { codeText } = scanBuffer(trimmed, dialect);
  // Any number of bare terminators (";", ";;;", "; ; ;") is still nothing to run.
  if (codeText.replace(/;/g, "").trim() === "") {
    return true;
  }

  let body = codeText.trimEnd();
  if (body.endsWith(";")) {
    body = body.slice(0, -1);
  }

  const lines = body.split("\n");
  const { idx, line } = lastCodeLine(body);
  if (isBareTerminatorLine(line, dialect)) {
    return !lines.some((l, i) => i !== idx && l.trim() !== "");
  }

  return body.trim() === "";
}
