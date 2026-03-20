#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url, headers = {}) {
  const res = await fetch(url, { 
    headers: { 
      "User-Agent": "mcp-brave/0.1",
      ...headers 
    } 
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const server = new Server(
  {
    name: "brave-server",
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
        name: "web_search",
        description: "Search the web using Brave Search API",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10, max: 100)",
            },
            search_type: {
              type: "string",
              enum: ["web", "news"],
              description: "Type of search (default: web)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "news_search",
        description: "Search for news articles using Brave Search API",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "News search query",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10, max: 50)",
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
    if (name === "web_search") {
      const query = encodeURIComponent(args.query);
      const count = Math.min(args.max_results || 10, 100);
      
      // Brave Search API endpoint (requires API key from env)
      const apiKey = process.env.BRAVE_API_KEY;
      if (!apiKey) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "BRAVE_API_KEY environment variable not set" }, null, 2) }],
        };
      }

      const url = `https://api.search.brave.com/res/v1/web/search?q=${query}&count=${count}`;
      
      try {
        const data = await getJSON(url, { "Accept": "application/json", "X-Subscription-Token": apiKey });
        const results = (data.web?.results || []).map((result) => ({
          title: result.title,
          url: result.url,
          description: result.description,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "Web search not available", error: apiError.message }, null, 2) }],
        };
      }
    }

    if (name === "news_search") {
      const query = encodeURIComponent(args.query);
      const count = Math.min(args.max_results || 10, 50);
      
      const apiKey = process.env.BRAVE_API_KEY;
      if (!apiKey) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "BRAVE_API_KEY environment variable not set" }, null, 2) }],
        };
      }

      const url = `https://api.search.brave.com/res/v1/news/search?q=${query}&count=${count}`;
      
      try {
        const data = await getJSON(url, { "Accept": "application/json", "X-Subscription-Token": apiKey });
        const results = (data.results || []).map((result) => ({
          title: result.title,
          url: result.url,
          description: result.description,
          published: result.published,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      } catch (apiError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ message: "News search not available", error: apiError.message }, null, 2) }],
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
  console.error("Brave Search MCP server running on stdio");
}

main().catch(console.error);
