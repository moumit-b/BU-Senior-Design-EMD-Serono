#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-semanticscholar/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const server = new Server(
  {
    name: "semanticscholar-server",
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
        name: "search_papers",
        description: "Search Semantic Scholar for academic papers",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query (e.g., 'machine learning', 'cancer immunotherapy')",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10, max: 100)",
            },
            sort: {
              type: "string",
              enum: ["relevance", "citation_count"],
              description: "Sort by relevance or citation count (default: relevance)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_paper_details",
        description: "Get detailed information about a specific paper by Semantic Scholar ID",
        inputSchema: {
          type: "object",
          properties: {
            paper_id: {
              type: "string",
              description: "Semantic Scholar paper ID",
            },
          },
          required: ["paper_id"],
        },
      },
      {
        name: "get_author_papers",
        description: "Get papers by a specific author",
        inputSchema: {
          type: "object",
          properties: {
            author_name: {
              type: "string",
              description: "Author name",
            },
            max_results: {
              type: "number",
              description: "Maximum number of papers (default: 10)",
            },
          },
          required: ["author_name"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_papers") {
      const query = encodeURIComponent(args.query);
      const limit = Math.min(args.max_results || 10, 100);
      const sort = args.sort || "relevance";

      const url = `https://api.semanticscholar.org/graph/v1/paper/search?query=${query}&limit=${limit}&sort=${sort === "citation_count" ? "citationCount" : "relevance"}`;

      try {
        const data = await getJSON(url);
        const results = (data.data || []).map((paper) => ({
          paper_id: paper.paperId,
          title: paper.title,
          authors: paper.authors?.map((a) => a.name) || [],
          year: paper.year,
          citation_count: paper.citationCount,
          url: paper.url,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "No papers found", query: args.query }, null, 2) }],
        };
      }
    }

    if (name === "get_paper_details") {
      const paper_id = args.paper_id;

      const url = `https://api.semanticscholar.org/graph/v1/paper/${paper_id}?fields=paperId,title,abstract,authors,year,citationCount,references,citations`;

      try {
        const data = await getJSON(url);
        const details = {
          paper_id: data.paperId,
          title: data.title,
          abstract: data.abstract,
          authors: data.authors?.map((a) => a.name) || [],
          year: data.year,
          citation_count: data.citationCount,
          references_count: data.references?.length || 0,
          citations_count: data.citations?.length || 0,
        };

        return {
          content: [{ type: "text", text: JSON.stringify(details, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "Paper not found" }, null, 2) }],
        };
      }
    }

    if (name === "get_author_papers") {
      const author_name = encodeURIComponent(args.author_name);
      const limit = Math.min(args.max_results || 10, 100);

      const url = `https://api.semanticscholar.org/graph/v1/author/search?query=${author_name}&limit=5`;

      try {
        const authorData = await getJSON(url);
        if (!authorData.data || authorData.data.length === 0) {
          return {
            content: [{ type: "text", text: JSON.stringify({ message: "Author not found" }, null, 2) }],
          };
        }

        const author_id = authorData.data[0].authorId;
        const papersUrl = `https://api.semanticscholar.org/graph/v1/author/${author_id}/papers?limit=${limit}&fields=paperId,title,year,citationCount`;
        const papersData = await getJSON(papersUrl);

        const results = (papersData.papers || []).map((paper) => ({
          paper_id: paper.paperId,
          title: paper.title,
          year: paper.year,
          citation_count: paper.citationCount,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify({ author: args.author_name, papers: results }, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "Could not retrieve author papers", error: apiError.message }, null, 2) }],
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
  console.error("Semantic Scholar MCP server running on stdio");
}

main().catch(console.error);
