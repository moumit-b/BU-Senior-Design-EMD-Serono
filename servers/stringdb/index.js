#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

/**
 * STRING-db MCP Server
 *
 * Provides tools to retrieve protein-protein interactions from the STRING database.
 * (https://string-db.org/cgi/help.pl?subpage=api)
 */

const STRING_API_BASE = "https://string-db.org/api/json";

async function getStringData(endpoint, params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = `${STRING_API_BASE}/${endpoint}?${query}`;
  const res = await fetch(url, {
    headers: { "User-Agent": "mcp-stringdb/0.1" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

// Create server instance
const server = new Server(
  {
    name: "stringdb-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_protein_interactions",
        description: "Get protein-protein interactions for a list of identifiers (e.g., gene symbols, UniProt IDs). Returns a list of interaction records with scores.",
        inputSchema: {
          type: "object",
          properties: {
            identifiers: {
              type: "array",
              items: { type: "string" },
              description: "List of protein identifiers (e.g., [\"TP53\", \"BRCA1\"])",
            },
            species: {
              type: "number",
              description: "Taxonomy ID (default: 9606 for Homo sapiens)",
              default: 9606,
            },
            required_score: {
              type: "number",
              description: "Minimum interaction score (0-1000, default: 400)",
              default: 400,
            },
          },
          required: ["identifiers"],
        },
      },
      {
        name: "get_interaction_partners",
        description: "Get interaction partners for a specific protein identifier. Returns a list of partners with interaction scores.",
        inputSchema: {
          type: "object",
          properties: {
            identifier: {
              type: "string",
              description: "Protein identifier (e.g., \"TP53\")",
            },
            limit: {
              type: "number",
              description: "Maximum number of partners to return (default: 10)",
              default: 10,
            },
            species: {
              type: "number",
              description: "Taxonomy ID (default: 9606 for Homo sapiens)",
              default: 9606,
            },
          },
          required: ["identifier"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  try {
    if (name === "get_protein_interactions") {
      const { identifiers, species = 9606, required_score = 400 } = args;
      const data = await getStringData("network", {
        identifiers: identifiers.join("\n"),
        species,
        required_score,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    }

    if (name === "get_interaction_partners") {
      const { identifier, limit = 10, species = 9606 } = args;
      const data = await getStringData("interaction_partners", {
        identifiers: identifier,
        limit,
        species,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ error: error.message, tool: name }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("STRING-db MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
