import { describe, it, expect } from "vitest";
import { isStatementComplete, isEffectivelyEmpty } from "@src/console/sql_statement_scanner.js";

describe("sql_statement_scanner", () => {
  describe("semicolon trigger", () => {
    it.each(["postgresql", "mysql", "mariadb", "sqlite"])("%s: trailing ; completes", (dialect) => {
      expect(isStatementComplete("select 1;", dialect)).toBe(true);
    });

    it("oracle: trailing ; also completes (secondary trigger alongside /)", () => {
      expect(isStatementComplete("select 1;", "oracle")).toBe(true);
    });

    it("mssql: trailing ; also completes (secondary trigger alongside GO)", () => {
      expect(isStatementComplete("select 1;", "mssql")).toBe(true);
    });

    it("no terminator at all is incomplete", () => {
      expect(isStatementComplete("select 1", "postgresql")).toBe(false);
    });

    it("a trailing comment must never manufacture a terminator on its own", () => {
      expect(isStatementComplete("select 1 -- comment", "postgresql")).toBe(false);
    });
  });

  describe("trailing comment after the semicolon (regression: previously left this incomplete)", () => {
    it("-- comment on the same line as the semicolon", () => {
      expect(isStatementComplete("select 1; -- comment", "postgresql")).toBe(true);
    });

    it("# comment on the same line (mysql)", () => {
      expect(isStatementComplete("select 1; # comment", "mysql")).toBe(true);
    });

    it("comment on its own line after the semicolon", () => {
      expect(isStatementComplete("select 1;\n-- trailing comment line", "postgresql")).toBe(true);
    });

    it("block comment between the semicolon and end of buffer", () => {
      expect(isStatementComplete("select 1; /* trailing block comment */", "postgresql")).toBe(true);
    });
  });

  describe("blocking (genuinely open) states", () => {
    it("open single quote", () => {
      expect(isStatementComplete("select 'unterminated;", "postgresql")).toBe(false);
    });

    it("open dollar-quote", () => {
      expect(
        isStatementComplete("create function f() returns void as $$\nbegin\nend;\n$$", "postgresql")
      ).toBe(false);
    });

    it("unterminated block comment", () => {
      expect(isStatementComplete("select 1; /* not closed", "postgresql")).toBe(false);
    });

    it("closed dollar-quote body containing ; and -- doesn't confuse the scanner", () => {
      const sql =
        "create function f() returns void as $$\n" +
        "begin -- not a comment marker outside body context\n" +
        "end;\n" +
        "$$ language plpgsql;";
      expect(isStatementComplete(sql, "postgresql")).toBe(true);
    });
  });

  it("unbalanced parens + trailing ; still completes (matches real psql - verified against a live instance)", () => {
    expect(isStatementComplete("select * from (select 1;", "postgresql")).toBe(true);
  });

  describe("oracle / trigger", () => {
    it("plain / on its own line", () => {
      expect(isStatementComplete("select 1\nfrom dual\n/", "oracle")).toBe(true);
    });

    it("/ followed by a trailing comment-only line", () => {
      expect(isStatementComplete("select 1\nfrom dual\n/\n-- trailing note", "oracle")).toBe(true);
    });
  });

  describe("mssql GO trigger", () => {
    it("plain GO on its own line", () => {
      expect(isStatementComplete("select 1\nGO", "mssql")).toBe(true);
    });

    it("GO with a repeat count", () => {
      expect(isStatementComplete("select 1\nGO 5", "mssql")).toBe(true);
    });

    it("GO followed by a trailing comment-only line", () => {
      expect(isStatementComplete("select 1\nGO\n-- trailing note", "mssql")).toBe(true);
    });

    it("GOTO is not mistaken for the GO marker", () => {
      expect(isStatementComplete("select 1\nGOTO", "mssql")).toBe(false);
    });
  });

  it("backslash meta-command completes immediately", () => {
    expect(isStatementComplete("\\d foo", "postgresql")).toBe(true);
  });

  it("empty/whitespace-only buffer is incomplete", () => {
    expect(isStatementComplete("   \n  ", "postgresql")).toBe(false);
  });

  it("mysql backtick identifier with doubled-backtick escaping", () => {
    expect(isStatementComplete("select `a``b` from t;", "mysql")).toBe(true);
  });

  describe("isEffectivelyEmpty (bug: a bare terminator alone shouldn't be submitted)", () => {
    it("a bare semicolon is effectively empty", () => {
      expect(isEffectivelyEmpty(";", "postgresql")).toBe(true);
    });

    it("a semicolon with a trailing comment is effectively empty", () => {
      expect(isEffectivelyEmpty("; -- oops", "postgresql")).toBe(true);
    });

    it("whitespace around a bare semicolon is effectively empty", () => {
      expect(isEffectivelyEmpty("   ;   ", "postgresql")).toBe(true);
    });

    it("multiple bare semicolons in a row are effectively empty (bug: used to reach the backend)", () => {
      expect(isEffectivelyEmpty(";;;", "postgresql")).toBe(true);
    });

    it("multiple bare semicolons separated by whitespace/newlines are effectively empty", () => {
      expect(isEffectivelyEmpty(" ; ;\n; ", "postgresql")).toBe(true);
    });

    it("a real statement followed by extra trailing semicolons is not effectively empty", () => {
      expect(isEffectivelyEmpty("select 1;;;", "postgresql")).toBe(false);
    });

    it("a truly blank buffer is effectively empty", () => {
      expect(isEffectivelyEmpty("   ", "postgresql")).toBe(true);
    });

    it("a real statement is not effectively empty", () => {
      expect(isEffectivelyEmpty("select 1;", "postgresql")).toBe(false);
    });

    it("an incomplete statement (no ;) is not effectively empty", () => {
      expect(isEffectivelyEmpty("select 1", "postgresql")).toBe(false);
    });

    it("real content before a bare ; on its own line is not effectively empty", () => {
      expect(isEffectivelyEmpty("select 1\n;", "postgresql")).toBe(false);
    });

    it("a backslash meta-command is never effectively empty", () => {
      expect(isEffectivelyEmpty("\\d foo", "postgresql")).toBe(false);
    });

    it("oracle: a bare / alone is effectively empty", () => {
      expect(isEffectivelyEmpty("/", "oracle")).toBe(true);
    });

    it("oracle: a real statement followed by / is not effectively empty", () => {
      expect(isEffectivelyEmpty("select 1\nfrom dual\n/", "oracle")).toBe(false);
    });

    it("mssql: a bare GO alone is effectively empty", () => {
      expect(isEffectivelyEmpty("GO", "mssql")).toBe(true);
    });

    it("mssql: a bare GO with a repeat count is effectively empty", () => {
      expect(isEffectivelyEmpty("GO 5", "mssql")).toBe(true);
    });

    it("mssql: a real statement followed by GO is not effectively empty", () => {
      expect(isEffectivelyEmpty("select 1\nGO", "mssql")).toBe(false);
    });
  });
});
