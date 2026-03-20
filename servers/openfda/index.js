#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-openfda/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const server = new Server(
  {
    name: "openfda-server",
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
        name: "search_drug_approvals",
        description: "Search FDA approved drugs by name or ingredient",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Drug name or ingredient to search for",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results to return (default: 10, max: 100)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "search_adverse_events",
        description: "Search FDA adverse event reports for a specific drug",
        inputSchema: {
          type: "object",
          properties: {
            drug_name: {
              type: "string",
              description: "Drug name to search for adverse events",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10, max: 100)",
            },
          },
          required: ["drug_name"],
        },
      },
      {
        name: "search_recalls",
        description: "Search FDA recalls for medications or devices",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Drug or device name to search for recalls",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10, max: 100)",
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
    if (name === "search_drug_approvals") {
      const query = encodeURIComponent(args.query);
      const limit = Math.min(args.max_results || 10, 100);
      const url = `https://api.fda.gov/drug/ndc.json?search=proprietary_name:${query}&limit=${limit}`;

      const data = await getJSON(url);
      const results = (data.results || []).map((drug) => ({
        name: drug.proprietary_name,
        active_ingredient: drug.active_ingredients,
        dosage: drug.dosage_form,
        route: drug.route,
        strength: drug.strength,
        ndc_code: drug.product_ndc,
      }));

      return {
        content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
      };
    }

    if (name === "search_adverse_events") {
      const drug = encodeURIComponent(args.drug_name);
      const limit = Math.min(args.max_results || 10, 100);
      const url = `https://api.fda.gov/drug/event.json?search=patient.drug.openfda.brand_name:${drug}&limit=${limit}`;

      const data = await getJSON(url);
      const results = (data.results || []).map((event) => ({
        reaction: event.patient?.reaction?.[0]?.reactionmeddrapt || "Unknown",
        date: event.receivedate,
        outcome: event.patient?.reaction?.[0]?.reactionoutcome || "Unknown",
        serious: event.serious || false,
      }));

      return {
        content: [{ type: "text", text: JSON.stringify({ total: data.meta?.results?.total || 0, adverse_events: results }, null, 2) }],
      };
    }

    if (name === "search_recalls") {
      const query = encodeURIComponent(args.query);
      const limit = Math.min(args.max_results || 10, 100);
      const url = `https://api.fda.gov/drug/enforcement.json?search=openfda.brand_name:${query}&limit=${limit}`;

      const data = await getJSON(url);
      const results = (data.results || []).map((recall) => ({
        product: recall.product_description,
        reason: recall.reason_for_recall,
        date: recall.recall_initiation_date,
        classification: recall.classification,
        status: recall.status,
      }));

      return {
        content: [{ type: "text", text: JSON.stringify({ total: data.meta?.results?.total || 0, recalls: results }, null, 2) }],
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
  console.error("Open FDA MCP server running on stdio");
}

main().catch(console.error);
