#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-string/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

async function getTSV(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-string/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

const server = new Server(
  {
    name: "string-server",
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
        name: "search_protein_network",
        description: "Search for protein-protein interaction network around a protein",
        inputSchema: {
          type: "object",
          properties: {
            protein: {
              type: "string",
              description: "Protein name or identifier (e.g., 'TP53', 'BRCA1')",
            },
            species: {
              type: "string",
              description: "NCBI taxon ID (e.g., '9606' for human, default: '9606')",
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
        name: "search_protein_enrichment",
        description: "Analyze functional enrichment for a set of proteins",
        inputSchema: {
          type: "object",
          properties: {
            proteins: {
              type: "array",
              items: { type: "string" },
              description: "List of protein names or identifiers",
            },
            species: {
              type: "string",
              description: "NCBI taxon ID (default: '9606' for human)",
            },
          },
          required: ["proteins"],
        },
      },
      {
        name: "get_interaction_evidence",
        description: "Get detailed evidence for interactions between two proteins",
        inputSchema: {
          type: "object",
          properties: {
            protein1: {
              type: "string",
              description: "First protein identifier",
            },
            protein2: {
              type: "string",
              description: "Second protein identifier",
            },
            species: {
              type: "string",
              description: "NCBI taxon ID (default: '9606')",
            },
          },
          required: ["protein1", "protein2"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_protein_network") {
      const protein = encodeURIComponent(args.protein);
      const species = args.species || "9606";
      const limit = Math.min(args.max_results || 10, 100);

      const url = `https://string-db.org/api/tsv/get_link?identifiers=${protein}&species=${species}&required_score=400`;

      try {
        const data = await getTSV(url);
        const lines = data.split("\n").slice(1);
        const results = lines
          .slice(0, limit)
          .filter((line) => line.trim())
          .map((line) => {
            const parts = line.split("\t");
            return {
              protein_a: parts[0],
              protein_b: parts[1],
              score: parseFloat(parts[2]),
              evidence_types: parts.slice(3),
            };
          });

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "Could not retrieve network data", query: args.protein }, null, 2) }],
        };
      }
    }

    if (name === "search_protein_enrichment") {
      const proteins = (args.proteins || []).join("%0d");
      const species = args.species || "9606";

      const url = `https://string-db.org/api/json/get_enrichment?identifiers=${proteins}&species=${species}`;

      try {
        const data = await getJSON(url);
        const results = (data || []).map((enrichment) => ({
          term: enrichment.term,
          category: enrichment.category,
          description: enrichment.description,
          pvalue: enrichment.pvalue,
          fdr: enrichment.fdr,
          genes: enrichment.inputGenes,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "Could not retrieve enrichment data", input_count: args.proteins.length }, null, 2) }],
        };
      }
    }

    if (name === "get_interaction_evidence") {
      const p1 = encodeURIComponent(args.protein1);
      const p2 = encodeURIComponent(args.protein2);
      const species = args.species || "9606";

      const url = `https://string-db.org/api/json/get_link?identifiers=${p1}|${p2}&species=${species}&required_score=0`;

      try {
        const data = await getJSON(url);
        const interaction = data[0] || {};
        const details = {
          protein_a: interaction.preferredName_A,
          protein_b: interaction.preferredName_B,
          interaction_score: interaction.score,
          neighborhood: interaction.neighborhood,
          fusion: interaction.fusion,
          cooccurence: interaction.cooccurence,
          homology: interaction.homology,
          coexpression: interaction.coexpression,
          experimental: interaction.experiments,
          database: interaction.database,
          textmining: interaction.textmining,
        };

        return {
          content: [{ type: "text", text: JSON.stringify(details, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "No interaction found between proteins" }, null, 2) }],
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
  console.error("STRING MCP server running on stdio");
}

main().catch(console.error);
