#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-pubchem/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

// Create server instance
const server = new Server(
  {
    name: "pubchem-server",
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
        name: "search_compounds_by_name",
        description: "Search PubChem CIDs by compound name (e.g., 'caffeine')",
        inputSchema: {
          type: "object",
          properties: {
            name: {
              type: "string",
              description: "Compound name to search for",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results to return (default: 5)",
              default: 5,
            },
          },
          required: ["name"],
        },
      },
      {
        name: "get_compound_properties",
        description: "Get properties for a PubChem compound by CID",
        inputSchema: {
          type: "object",
          properties: {
            cid: {
              type: "number",
              description: "PubChem Compound ID",
            },
          },
          required: ["cid"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_compounds_by_name") {
      const compoundName = args.name;
      const maxResults = args.max_results || 5;

      const url = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(
        compoundName
      )}/cids/JSON`;

      const data = await getJSON(url);
      const cids = data?.IdentifierList?.CID ?? [];

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                cids: cids.slice(0, maxResults),
                count: cids.length,
                source: "PubChem PUG REST API",
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (name === "get_compound_properties") {
      const cid = args.cid;
      const props = [
        "MolecularFormula",
        "MolecularWeight",
        "IUPACName",
        "IsomericSMILES",
        "InChI",
        "InChIKey",
      ].join(",");

      const url = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/property/${props}/JSON`;

      const data = await getJSON(url);
      const properties = data?.PropertyTable?.Properties?.[0] ?? {};

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                CID: cid,
                ...properties,
                Link: `https://pubchem.ncbi.nlm.nih.gov/compound/${cid}`,
              },
              null,
              2
            ),
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
          text: JSON.stringify({
            error: error.message,
            tool: name,
          }),
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("PubChem MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
