#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url, body = null) {
  const options = {
    method: body ? "POST" : "GET",
    headers: {
      "User-Agent": "mcp-opentargets/0.1",
      "Content-Type": "application/json",
    },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

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

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search_gene_targets",
        description: "Search for gene targets by name or symbol",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Gene name or symbol (e.g., 'BRCA1', 'TP53')",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10, max: 100)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "search_disease_targets",
        description: "Find therapeutic targets associated with a disease",
        inputSchema: {
          type: "object",
          properties: {
            disease: {
              type: "string",
              description: "Disease name or condition",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10, max: 100)",
            },
          },
          required: ["disease"],
        },
      },
      {
        name: "get_target_disease_association",
        description: "Get association strength between a target gene and disease",
        inputSchema: {
          type: "object",
          properties: {
            gene_id: {
              type: "string",
              description: "Ensembl gene ID or gene symbol",
            },
            disease: {
              type: "string",
              description: "Disease name or DOID",
            },
          },
          required: ["gene_id", "disease"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_gene_targets") {
      const query = args.query;
      const limit = Math.min(args.max_results || 10, 100);

      const url = "https://platform-api.opentargets.org/v3/platform/search";
      const body = {
        query: query,
        size: limit,
      };

      const data = await getJSON(url, body);
      const results = (data.data || []).map((target) => ({
        gene_id: target.id,
        gene_name: target.approved_name || target.symbol,
        description: target.description,
        biotype: target.biotype,
      }));

      return {
        content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
      };
    }

    if (name === "search_disease_targets") {
      const disease = args.disease;
      const limit = Math.min(args.max_results || 10, 100);

      const url = "https://platform-api.opentargets.org/v3/platform/search";
      const body = {
        query: disease,
        size: limit,
      };

      const data = await getJSON(url, body);
      const results = (data.data || []).map((item) => ({
        id: item.id,
        name: item.name || item.symbol,
        type: item.type,
      }));

      return {
        content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
      };
    }

    if (name === "get_target_disease_association") {
      const gene_id = args.gene_id;
      const disease = args.disease;

      const url = `https://platform-api.opentargets.org/v3/platform/associations?target=${gene_id}&disease=${disease}&size=1`;
      const data = await getJSON(url);

      if (!data.associations || data.associations.length === 0) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No association found" }, null, 2) }],
        };
      }

      const assoc = data.associations[0];
      const details = {
        target: assoc.target.name,
        disease: assoc.disease.name,
        overall_association_score: assoc.association_score?.overall || 0,
        genetic_association: assoc.association_score?.genetics || 0,
        somatic_mutation: assoc.association_score?.somatic_mutation || 0,
        drugs: assoc.association_score?.drugs || 0,
      };

      return {
        content: [{ type: "text", text: JSON.stringify(details, null, 2) }],
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
  console.error("Open Targets MCP server running on stdio");
}

main().catch(console.error);
