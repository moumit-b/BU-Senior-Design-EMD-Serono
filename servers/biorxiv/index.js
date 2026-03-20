#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-biorxiv/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const server = new Server(
  {
    name: "biorxiv-server",
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
        name: "search_biorxiv",
        description: "Search bioRxiv preprints by keywords, returning preprint metadata including DOI, title, authors, and abstract",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query (e.g., 'CRISPR gene editing', 'protein structure')",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results to return (default: 10, max: 100)",
            },
            sort: {
              type: "string",
              enum: ["relevance", "date"],
              description: "Sort results by relevance or date (default: relevance)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_biorxiv_preprint",
        description: "Get detailed information about a specific bioRxiv preprint by DOI",
        inputSchema: {
          type: "object",
          properties: {
            doi: {
              type: "string",
              description: "Digital Object Identifier (e.g., '10.1101/2024.01.15.12345678')",
            },
          },
          required: ["doi"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_biorxiv") {
      const query = encodeURIComponent(args.query);
      const max_results = Math.min(args.max_results || 10, 100);
      const sort = args.sort || "relevance";

      const url = `https://api.biorxiv.org/v1/articles?query=${query}&limit=${max_results}&sort=${sort === "date" ? "date" : "relevance"}`;

      const data = await getJSON(url);
      const results = (data.collection || []).map((article) => ({
        doi: article.doi,
        title: article.title,
        authors: article.authors,
        abstract: article.abstract,
        published: article.date,
        category: article.category,
        url: `https://www.biorxiv.org/content/${article.doi}.v${article.version}`,
      }));

      return {
        content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
      };
    }

    if (name === "get_biorxiv_preprint") {
      const doi = args.doi;
      const doiUrl = `https://api.biorxiv.org/v1/articles?doi=${encodeURIComponent(doi)}`;
      const data = await getJSON(doiUrl);

      if (!data.collection || data.collection.length === 0) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "Preprint not found" }, null, 2) }],
        };
      }

      const article = data.collection[0];
      const details = {
        doi: article.doi,
        title: article.title,
        authors: article.authors,
        abstract: article.abstract,
        published: article.date,
        category: article.category,
        keywords: article.keywords || [],
        url: `https://www.biorxiv.org/content/${article.doi}.v${article.version}`,
        versions: article.version,
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
  console.error("bioRxiv MCP server running on stdio");
}

main().catch(console.error);
