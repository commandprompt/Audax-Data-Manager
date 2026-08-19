import last from "lodash/last";
import { handleError } from "../logging/utils";
import { settingsStore } from "../stores/stores_initializer";

export default {
  methods: {
    copyTableData(data, format, columnNames) {
      let headers = [];
      let headerIndexMap = {}; // Map header titles to their original indices
      let nameCount = {}; // to track duplicates

      Object.keys(last(data)).forEach((key) => {
        const originalIndex = parseInt(key, 10);
        let header = columnNames[originalIndex];

        // Track duplicates
        if (nameCount[header]) {
          nameCount[header]++;
          header = `${header}_${nameCount[header]}`;
        } else {
          nameCount[header] = 1;
        }

        headers.push(header);
        headerIndexMap[header] = originalIndex;
      });

      if (format === "json") {
        const jsonOutput = this.generateJson(data, headers, headerIndexMap);
        this.copyToClipboard(jsonOutput);
      } else if (format === "csv") {
        const csvOutput = this.generateCsv(data, headers, headerIndexMap);
        this.copyToClipboard(csvOutput);
      } else if (format === "markdown") {
        const markdownOutput = this.generateMarkdown(
          data,
          headers,
          headerIndexMap
        );
        this.copyToClipboard(markdownOutput);
      }
    },
    copyToClipboard(text) {
      // the nwjs webview does not permit navigator.clipboard writes
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.left = "-9999px";

      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      try {
        if (!document.execCommand("copy")) {
          throw new Error("Could not copy the data to the clipboard.");
        }
      } catch (error) {
        handleError(error);
      } finally {
        textArea.remove();
      }
    },
    generateJson(data, headers, headerIndexMap) {
      const mappedData = data.map((row) => {
        const mappedRow = {};
        headers.forEach((header) => {
          const originalIndex = headerIndexMap[header];
          mappedRow[header] = row[originalIndex];
        });
        return mappedRow;
      });

      return JSON.stringify(mappedData, null, 2);
    },
    generateCsv(data, headers, headerIndexMap) {
      const csvRows = [];

      // Add header row
      csvRows.push(headers.join(settingsStore.csvDelimiter));

      data.forEach((row) => {
        const rowValues = headers.map((header) => {
          const originalIndex = headerIndexMap[header];
          return row[originalIndex] || "";
        });
        csvRows.push(rowValues.join(settingsStore.csvDelimiter));
      });

      return csvRows.join("\n");
    },
    generateMarkdown(data, headers, headerIndexMap) {
      const columnWidths = headers.map((header) => {
        const originalIndex = headerIndexMap[header];
        const maxDataLength = data.reduce(
          (max, row) =>
            Math.max(max, (row[originalIndex] || "").toString().length),
          0
        );
        return Math.max(header.length, maxDataLength);
      });

      // Helper to pad strings to a given length
      const pad = (str, length) => str.toString().padEnd(length, " ");

      const mdRows = [];

      // Add padded header row
      mdRows.push(
        `| ${headers
          .map((header, index) => pad(header, columnWidths[index]))
          .join(" | ")} |`
      );

      // Add separator row
      mdRows.push(
        `| ${columnWidths.map((width) => "-".repeat(width)).join(" | ")} |`
      );

      data.forEach((row) => {
        const rowValues = headers.map((header, index) => {
          const originalIndex = headerIndexMap[header];
          return pad(row[originalIndex] || "", columnWidths[index]);
        });
        mdRows.push(`| ${rowValues.join(" | ")} |`);
      });

      return mdRows.join("\n");
    },
  },
};
