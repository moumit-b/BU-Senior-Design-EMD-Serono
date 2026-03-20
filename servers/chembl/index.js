#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-chembl/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const server = new Server(
  {
    name: "chembl-server",
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
        name: "search_compounds",
        description: "Search ChEMBL compounds by name or SMILES",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Compound name or SMILES string",
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
        name: "search_targets",
        description: "Search ChEMBL drug targets by name or gene symbol",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Target name or gene symbol",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_bioactivity",
        description: "Get bioactivity data for compound-target interactions",
        inputSchema: {
          type: "object",
          properties: {
            compound_id: {
              type: "string",
              description: "ChEMBL compound ID",
            },
            target_id: {
              type: "string",
              description: "ChEMBL target ID",
            },
          },
          required: ["compound_id", "target_id"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_compounds") {
      const query = encodeURIComponent(args.query);
      const limit = Math.min(args.max_results || 10, 100);

      const url = `https://www.ebi.ac.uk/chembl/api/data/compounds?name__icontains=${query}&limit=${limit}&format=json`;

      try {
        const data = await getJSON(url);
        const results = (data.results || []).map((compound) => ({
          chembl_id: compound.molecule_chembl_id,
          name: compound.pref_name,
          smiles: compound.canonical_smiles,
          molecular_weight: compound.molecular_weight,
          logp: compound.logp,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No compounds found", query: args.query }, null, 2) }],
        };
      }
    }

    if (name === "search_targets") {
      const query = encodeURIComponent(args.query);
      const limit = Math.min(args.max_results || 10, 100);

      const url = `https://www.ebi.ac.uk/chembl/api/data/targets?pref_name__icontains=${query}&limit=${limit}&format=json`;

      try {
        const data = await getJSON(url);
        const results = (data.results || []).map((target) => ({
          chembl_id: target.target_chembl_id,
          name: target.pref_name,
          organism: target.organism,
          type: target.target_type,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No targets found", query: args.query }, null, 2) }],
        };
      }
    }

    if (name === "get_bioactivity") {
      const compound_id = args.compound_id;
      const target_id = args.target_id;

      const url = `https://www.ebi.ac.uk/chembl/api/data/activities?molecule_chembl_id=${compound_id}&target_chembl_id=${target_id}&limit=10&format=json`;

      try {
        const data = await getJSON(url);
        const results = (data.results || []).map((activity) => ({
          activity_id: activity.activity_id,
          assay_type: activity.assay_type,
          standard_type: activity.standard_type,
          standard_value: activity.standard_value,
          standard_units: activity.standard_units,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify({ total: data.meta?.result_count || 0, activities: results }, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No bioactivity data found" }, null, 2) }],
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
  console.error("ChEMBL MCP server running on stdio");
}

main().catch(console.error);
