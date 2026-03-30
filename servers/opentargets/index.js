#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

/**
 * Open Targets MCP Server
 *
 * Provides tools to search for therapeutic targets, diseases, and drugs,
 * and retrieve associations between them using the Open Targets GraphQL API.
 * (https://api.platform.opentargets.org/api/v4/graphql)
 */

const OPENTARGETS_API_BASE = "https://api.platform.opentargets.org/api/v4/graphql";

async function queryOpenTargets(query, variables = {}) {
  const res = await fetch(OPENTARGETS_API_BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "User-Agent": "mcp-opentargets/0.1",
    },
    body: JSON.stringify({ query, variables }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${OPENTARGETS_API_BASE}`);
  return res.json();
}

// Create server instance
const server = new Server(
  {
    name: "opentargets-server",
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
        name: "search_opentargets",
        description: "Search for targets, diseases, or drugs in Open Targets. Returns hits with ID, entity type, name, and description.",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query (e.g., \"TP53\", \"breast cancer\", \"imatinib\")",
            },
            entityNames: {
              type: "array",
              items: { type: "string", enum: ["target", "disease", "drug"] },
              description: "Entity types to include in search (default: [\"target\", \"disease\", \"drug\"])",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_target_associations",
        description: "Get diseases associated with a specific target (Ensembl ID).",
        inputSchema: {
          type: "object",
          properties: {
            targetId: {
              type: "string",
              description: "Ensembl ID (e.g., \"ENSG00000141510\")",
            },
            limit: {
              type: "number",
              description: "Maximum number of associations to return (default: 10, max: 100)",
              default: 10,
            },
          },
          required: ["targetId"],
        },
      },
      {
        name: "get_disease_associations",
        description: "Get targets associated with a specific disease (EFO ID).",
        inputSchema: {
          type: "object",
          properties: {
            diseaseId: {
              type: "string",
              description: "EFO ID (e.g., \"EFO_0000311\")",
            },
            limit: {
              type: "number",
              description: "Maximum number of associations to return (default: 10, max: 100)",
              default: 10,
            },
          },
          required: ["diseaseId"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  try {
    if (name === "search_opentargets") {
      const { query: queryString, entityNames = ["target", "disease", "drug"] } = args;
      const query = `
        query Search($queryString: String!, $entityNames: [String!]) {
          search(queryString: $queryString, entityNames: $entityNames) {
            total
            hits {
              id
              entity
              name
              description
            }
          }
        }
      `;
      const data = await queryOpenTargets(query, { queryString, entityNames });
      if (data.errors) throw new Error(data.errors[0].message);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data.data.search, null, 2),
          },
        ],
      };
    }

    if (name === "get_target_associations") {
      const { targetId, limit = 10 } = args;
      const query = `
        query Target($targetId: String!, $size: Int!) {
          target(ensemblId: $targetId) {
            id
            approvedSymbol
            approvedName
            associatedDiseases(page: {index: 0, size: $size}) {
              count
              rows {
                disease {
                  id
                  name
                }
                score
              }
            }
          }
        }
      `;
      const data = await queryOpenTargets(query, { targetId, size: limit });
      if (data.errors) throw new Error(data.errors[0].message);
      if (!data.data.target) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "Target not found" }, null, 2) }],
          isError: true,
        };
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data.data.target, null, 2),
          },
        ],
      };
    }

    if (name === "get_disease_associations") {
      const { diseaseId, limit = 10 } = args;
      const query = `
        query Disease($diseaseId: String!, $size: Int!) {
          disease(efoId: $diseaseId) {
            id
            name
            associatedTargets(page: {index: 0, size: $size}) {
              count
              rows {
                target {
                  id
                  approvedSymbol
                }
                score
              }
            }
          }
        }
      `;
      const data = await queryOpenTargets(query, { diseaseId, size: limit });
      if (data.errors) throw new Error(data.errors[0].message);
      if (!data.data.disease) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "Disease not found" }, null, 2) }],
          isError: true,
        };
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data.data.disease, null, 2),
          },
        ],
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
  console.error("OpenTargets MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
