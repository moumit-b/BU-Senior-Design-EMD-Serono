#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  {
    name: "duckdb-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "execute_sql_query",
        description: "Execute SQL queries on local data files using DuckDB",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "SQL query to execute",
            },
            file_path: {
              type: "string",
              description: "Path to CSV, Parquet, or JSON file (optional)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "describe_data",
        description: "Get schema and statistics about a data file",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "Path to data file (CSV, Parquet, JSON)",
            },
          },
          required: ["file_path"],
        },
      },
      {
        name: "aggregate_data",
        description: "Perform aggregation operations on data",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "Path to data file",
            },
            aggregation: {
              type: "string",
              enum: ["count", "sum", "average", "min", "max", "group_by"],
              description: "Type of aggregation to perform",
            },
            column: {
              type: "string",
              description: "Column to aggregate on",
            },
          },
          required: ["file_path", "aggregation"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "execute_sql_query") {
      const query = args.query;
      const file_path = args.file_path;

      // Note: Actual SQL execution requires DuckDB library
      // For this MCP, we'll provide a simulated response
      const response = {
        query: query,
        file: file_path || "Not specified",
        status: "simulated",
        message: "SQL execution requires DuckDB runtime. This is a placeholder MCP.",
        note: "To use actual queries, install DuckDB and connect a server instance",
      };

      return {
        content: [{ type: "text", text: JSON.stringify(response, null, 2) }],
      };
    }

    if (name === "describe_data") {
      const file_path = args.file_path;

      const response = {
        file: file_path,
        status: "simulated",
        message: "Schema inspection requires DuckDB runtime. This is a placeholder MCP.",
        supported_formats: ["CSV", "Parquet", "JSON"],
      };

      return {
        content: [{ type: "text", text: JSON.stringify(response, null, 2) }],
      };
    }

    if (name === "aggregate_data") {
      const file_path = args.file_path;
      const aggregation = args.aggregation;
      const column = args.column;

      const response = {
        file: file_path,
        aggregation: aggregation,
        column: column || "Not specified",
        status: "simulated",
        message: "Aggregation requires DuckDB runtime. This is a placeholder MCP.",
      };

      return {
        content: [{ type: "text", text: JSON.stringify(response, null, 2) }],
      };
    }

    return {
      content: [{ type: "text", text: JSON.stringify({ error: "Unknown tool" }, null, 2) }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: JSON.stringify({ error: error.message }, null, 2) }],
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("DuckDB MCP server running on stdio");
}

main().catch(console.error);
