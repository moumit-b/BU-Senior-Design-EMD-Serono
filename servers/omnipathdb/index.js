#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-omnipathdb/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const server = new Server(
  {
    name: "omnipathdb-server",
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
        name: "search_protein_interactions",
        description: "Search for protein-protein interactions involving a specific protein",
        inputSchema: {
          type: "object",
          properties: {
            protein: {
              type: "string",
              description: "Protein name or UniProt ID (e.g., 'TP53', 'P04637')",
            },
            max_results: {
              type: "number",
              description: "Maximum number of interactions (default: 10, max: 100)",
            },
          },
          required: ["protein"],
        },
      },
      {
        name: "search_signaling_pathways",
        description: "Search for signaling pathways involving specific proteins",
        inputSchema: {
          type: "object",
          properties: {
            protein: {
              type: "string",
              description: "Protein name or gene symbol",
            },
            max_results: {
              type: "number",
              description: "Maximum results (default: 10)",
            },
          },
          required: ["protein"],
        },
      },
      {
        name: "search_regulatory_networks",
        description: "Search transcriptional and post-translational regulatory networks",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Protein or gene name",
            },
            direction: {
              type: "string",
              enum: ["upstream", "downstream", "both"],
              description: "Direction of regulation (default: both)",
            },
            max_results: {
              type: "number",
              description: "Maximum results (default: 10)",
            },
          },
          required: ["query"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_protein_interactions") {
      const protein = encodeURIComponent(args.protein);
      const limit = Math.min(args.max_results || 10, 100);

      const url = `https://omnipathdb.org/api/interactions?source=${protein}&target=*&limit=${limit}`;

      try {
        const data = await getJSON(url);
        const results = (data || []).map((interaction) => ({
          source: interaction.source,
          target: interaction.target,
          interaction_type: interaction.type,
          databases: interaction.sources,
          references: interaction.references,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No interactions found", query: args.protein }, null, 2) }],
        };
      }
    }

    if (name === "search_signaling_pathways") {
      const protein = encodeURIComponent(args.protein);
      const limit = Math.min(args.max_results || 10, 100);

      const url = `https://omnipathdb.org/api/pathways?proteins=${protein}&limit=${limit}`;

      try {
        const data = await getJSON(url);
        const results = (data || []).map((pathway) => ({
          pathway_name: pathway.name,
          proteins: pathway.proteins,
          description: pathway.description,
          database: pathway.database,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No pathways found", query: args.protein }, null, 2) }],
        };
      }
    }

    if (name === "search_regulatory_networks") {
      const query = encodeURIComponent(args.query);
      const direction = args.direction || "both";

      const url = `https://omnipathdb.org/api/regulatory?query=${query}&direction=${direction}`;

      try {
        const data = await getJSON(url);
        const results = (data || []).map((regulation) => ({
          source: regulation.source,
          target: regulation.target,
          effect: regulation.effect,
          type: regulation.regulation_type,
          databases: regulation.sources,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No regulatory data found", query: args.query }, null, 2) }],
        };
      }
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
  console.error("OmniPathDB MCP server running on stdio");
}

main().catch(console.error);
