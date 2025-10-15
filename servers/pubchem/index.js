// Minimal PubChem MCP server (stdio transport).
// Requires: Node 18+ (global fetch), @modelcontextprotocol/sdk
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Utility: safe fetch wrapper
async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-pubchem-demo/0.1" }});
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return await res.json();
}

const server = new Server(
  {
    name: "pubchem-local",
    version: "0.1.0"
  },
  {
    // Tool 1: search by compound name -> list of CIDs
    tools: [
      {
        name: "search_compounds_by_name",
        description: "Search PubChem CIDs by compound name",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Compound common name (e.g., 'caffeine')" },
            max_results: { type: "number", description: "Max CIDs to return", default: 5 }
          },
          required: ["name"]
        },
        handler: async ({ name, max_results = 5 }) => {
          const url = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(name)}/cids/JSON`;
          const data = await getJSON(url);
          const cids = data?.IdentifierList?.CID ?? [];
          return {
            cids: cids.slice(0, max_results),
            provenance: { source: "PubChem PUG REST", url }
          };
        }
      },

      // Tool 2: properties by CID
      {
        name: "get_compound_properties",
        description: "Fetch identifiers/properties for a PubChem CID",
        inputSchema: {
          type: "object",
          properties: {
            cid: { type: "number", description: "PubChem Compound ID" }
          },
          required: ["cid"]
        },
        handler: async ({ cid }) => {
          const props = [
            "MolecularFormula",
            "MolecularWeight",
            "IUPACName",
            "IsomericSMILES",
            "InChI",
            "InChIKey"
          ].join(",");

          const url = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/property/${props}/JSON`;
          const data = await getJSON(url);
          const p = data?.PropertyTable?.Properties?.[0] ?? null;

          return {
            cid,
            properties: p || {},
            link: `https://pubchem.ncbi.nlm.nih.gov/compound/${cid}`,
            provenance: { source: "PubChem PUG REST", url }
          };
        }
      }
    ]
  }
);

// Start the stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("[pubchem-local] MCP server ready on stdio");
