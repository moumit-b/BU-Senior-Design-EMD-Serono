#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

/**
 * medRxiv MCP Server
 *
 * Provides tools to search and retrieve medical preprints from medRxiv
 * using the public medRxiv API (https://api.medrxiv.org).
 *
 * No authentication required.
 */

const MEDRXIV_API_BASE = "https://api.medrxiv.org/details/medrxiv";

async function getJSON(url) {
  const res = await fetch(url, {
    headers: { "User-Agent": "mcp-medrxiv/0.1" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

/**
 * Fetch all pages from a medRxiv date-range endpoint.
 * The API returns max 100 results per page; `cursor` controls the offset.
 * We cap at maxResults to avoid runaway pagination.
 */
async function fetchDateRange(startDate, endDate, maxResults) {
  const collected = [];
  let cursor = 0;

  while (collected.length < maxResults) {
    const url = `${MEDRXIV_API_BASE}/${startDate}/${endDate}/${cursor}/json`;
    const data = await getJSON(url);
    const items = data?.collection || [];

    if (items.length === 0) break;

    collected.push(...items);
    cursor += items.length;

    // If fewer than 100 returned, we've hit the last page
    if (items.length < 100) break;
  }

  return collected.slice(0, maxResults);
}

// Create server instance
const server = new Server(
  {
    name: "medrxiv-server",
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
        name: "search_medrxiv_preprints",
        description:
          "Search medRxiv preprints by keyword within a date range. Returns matching preprints with title, authors, abstract, DOI, and category.",
        inputSchema: {
          type: "object",
          properties: {
            keywords: {
              type: "string",
              description:
                "Search keywords to match against title and abstract (e.g., 'mRNA vaccine efficacy')",
            },
            start_date: {
              type: "string",
              description:
                "Start date in YYYY-MM-DD format (default: 30 days ago)",
            },
            end_date: {
              type: "string",
              description:
                "End date in YYYY-MM-DD format (default: today)",
            },
            max_results: {
              type: "number",
              description:
                "Maximum number of results to return (default: 10, max: 50)",
              default: 10,
            },
          },
          required: ["keywords"],
        },
      },
      {
        name: "get_medrxiv_paper",
        description:
          "Get full metadata for a specific medRxiv preprint by DOI. Returns title, authors, abstract, category, date, and version info.",
        inputSchema: {
          type: "object",
          properties: {
            doi: {
              type: "string",
              description:
                "medRxiv DOI (e.g., '10.1101/2024.01.01.12345678')",
            },
          },
          required: ["doi"],
        },
      },
      {
        name: "get_recent_medrxiv",
        description:
          "Get the most recent medRxiv preprints, optionally filtered by category (e.g., 'epidemiology', 'infectious diseases', 'oncology').",
        inputSchema: {
          type: "object",
          properties: {
            count: {
              type: "number",
              description:
                "Number of recent preprints to retrieve (default: 10, max: 50)",
              default: 10,
            },
            category: {
              type: "string",
              description:
                "Optional category filter (e.g., 'epidemiology', 'infectious diseases', 'oncology', 'pharmacology and therapeutics')",
            },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_medrxiv_preprints") {
      const keywords = args.keywords;
      const maxResults = Math.min(args.max_results || 10, 50);

      // Default date range: last 30 days
      const now = new Date();
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      const startDate =
        args.start_date || thirtyDaysAgo.toISOString().split("T")[0];
      const endDate = args.end_date || now.toISOString().split("T")[0];

      // Fetch preprints in the date range (fetch more than needed to filter)
      const allItems = await fetchDateRange(startDate, endDate, 500);

      // Client-side keyword filtering on title + abstract
      const lowerKeywords = keywords.toLowerCase().split(/\s+/);
      const filtered = allItems.filter((item) => {
        const text = `${item.title || ""} ${item.abstract || ""}`.toLowerCase();
        return lowerKeywords.every((kw) => text.includes(kw));
      });

      const results = filtered.slice(0, maxResults).map((item) => ({
        doi: item.doi,
        title: item.title,
        authors: item.authors,
        category: item.category,
        date: item.date,
        abstract:
          item.abstract && item.abstract.length > 400
            ? item.abstract.substring(0, 400) + "..."
            : item.abstract,
        link: `https://www.medrxiv.org/content/${item.doi}`,
      }));

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                keywords,
                date_range: { start: startDate, end: endDate },
                count: results.length,
                results,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (name === "get_medrxiv_paper") {
      const doi = args.doi;
      const url = `${MEDRXIV_API_BASE}/${doi}/na/json`;
      const data = await getJSON(url);
      const items = data?.collection || [];

      if (items.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { error: "No paper found with this DOI" },
                null,
                2
              ),
            },
          ],
        };
      }

      // Return the latest version (last item in the collection)
      const paper = items[items.length - 1];

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                doi: paper.doi,
                title: paper.title,
                authors: paper.authors,
                author_corresponding: paper.author_corresponding,
                author_corresponding_institution:
                  paper.author_corresponding_institution,
                date: paper.date,
                version: paper.version,
                category: paper.category,
                abstract: paper.abstract,
                license: paper.license,
                published: paper.published,
                link: `https://www.medrxiv.org/content/${paper.doi}`,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (name === "get_recent_medrxiv") {
      const count = Math.min(args.count || 10, 50);
      const category = args.category ? args.category.toLowerCase() : null;

      // Use date range: last 7 days — fetch enough to fill count after filtering
      const now = new Date();
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      const startDate = sevenDaysAgo.toISOString().split("T")[0];
      const endDate = now.toISOString().split("T")[0];

      const fetchLimit = category ? 300 : count;
      const allItems = await fetchDateRange(startDate, endDate, fetchLimit);

      let items = allItems;
      if (category) {
        items = allItems.filter(
          (item) =>
            item.category && item.category.toLowerCase().includes(category)
        );
      }

      const results = items.slice(0, count).map((item) => ({
        doi: item.doi,
        title: item.title,
        authors: item.authors,
        category: item.category,
        date: item.date,
        abstract:
          item.abstract && item.abstract.length > 300
            ? item.abstract.substring(0, 300) + "..."
            : item.abstract,
        link: `https://www.medrxiv.org/content/${item.doi}`,
      }));

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                count: results.length,
                category_filter: category || "none",
                results,
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
          text: JSON.stringify(
            {
              error: error.message,
              tool: name,
            },
            null,
            2
          ),
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
  console.error("medRxiv MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
