#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  {
    name: "playwright-server",
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
        name: "fetch_webpage",
        description: "Fetch and parse the content of a webpage",
        inputSchema: {
          type: "object",
          properties: {
            url: {
              type: "string",
              description: "URL of the webpage to fetch",
            },
            wait_for_selector: {
              type: "string",
              description: "CSS selector to wait for before returning (optional)",
            },
          },
          required: ["url"],
        },
      },
      {
        name: "extract_text",
        description: "Extract text content from a webpage",
        inputSchema: {
          type: "object",
          properties: {
            url: {
              type: "string",
              description: "URL of the webpage",
            },
            selector: {
              type: "string",
              description: "CSS selector for specific element (optional)",
            },
          },
          required: ["url"],
        },
      },
      {
        name: "get_page_metadata",
        description: "Get metadata from a webpage (title, meta tags, etc.)",
        inputSchema: {
          type: "object",
          properties: {
            url: {
              type: "string",
              description: "URL of the webpage",
            },
          },
          required: ["url"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "fetch_webpage") {
      const url = args.url;
      
      try {
        const response = await fetch(url, { 
          headers: { "User-Agent": "mcp-playwright/0.1" } 
        });
        
        if (!response.ok) {
          return {
            content: [{ type: "text", text: JSON.stringify({ error: `HTTP ${response.status}` }, null, 2) }],
          };
        }

        const html = await response.text();
        const textContent = html
          .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
          .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, "")
          .replace(/<[^>]+>/g, " ")
          .replace(/\s+/g, " ")
          .trim()
          .substring(0, 5000);

        return {
          content: [{ type: "text", text: JSON.stringify({ url, content: textContent }, null, 2) }],
        };
      } catch (fetchError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: fetchError.message }, null, 2) }],
        };
      }
    }

    if (name === "extract_text") {
      const url = args.url;
      
      try {
        const response = await fetch(url, { 
          headers: { "User-Agent": "mcp-playwright/0.1" } 
        });
        const html = await response.text();
        
        const textContent = html
          .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
          .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, "")
          .replace(/<[^>]+>/g, "\n")
          .replace(/\n\s*\n/g, "\n")
          .trim()
          .substring(0, 3000);

        return {
          content: [{ type: "text", text: JSON.stringify({ url, text: textContent }, null, 2) }],
        };
      } catch (fetchError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: fetchError.message }, null, 2) }],
        };
      }
    }

    if (name === "get_page_metadata") {
      const url = args.url;
      
      try {
        const response = await fetch(url, { 
          headers: { "User-Agent": "mcp-playwright/0.1" } 
        });
        const html = await response.text();

        const titleMatch = html.match(/<title[^>]*>([^<]*)<\/title>/i);
        const descMatch = html.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["']/i);
        const ogTitleMatch = html.match(/<meta\s+property=["']og:title["']\s+content=["']([^"']*)["']/i);
        const ogImageMatch = html.match(/<meta\s+property=["']og:image["']\s+content=["']([^"']*)["']/i);

        const metadata = {
          url: url,
          title: titleMatch ? titleMatch[1] : "",
          description: descMatch ? descMatch[1] : "",
          ogTitle: ogTitleMatch ? ogTitleMatch[1] : "",
          ogImage: ogImageMatch ? ogImageMatch[1] : "",
        };

        return {
          content: [{ type: "text", text: JSON.stringify(metadata, null, 2) }],
        };
      } catch (fetchError) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: fetchError.message }, null, 2) }],
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
  console.error("Playwright MCP server running on stdio");
}

main().catch(console.error);
