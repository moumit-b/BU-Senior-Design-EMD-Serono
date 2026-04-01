#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

/**
 * bioRxiv MCP Server
 *
 * Provides tools to search and retrieve biological preprints from bioRxiv
 * using the public bioRxiv API (https://api.biorxiv.org).
 *
 * No authentication required.
 */

const BIORXIV_API_BASE = "https://api.biorxiv.org/details/biorxiv";

async function getJSON(url) {
  const res = await fetch(url, {
    headers: { "User-Agent": "mcp-biorxiv/0.1" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

/**
 * Fetch all pages from a bioRxiv date-range endpoint.
 * The API returns max 100 results per page; `cursor` controls the offset.
 * We cap at maxResults to avoid runaway pagination.
 */
async function fetchDateRange(startDate, endDate, maxResults) {
  const collected = [];
  let cursor = 0;

  while (collected.length < maxResults) {
    const url = `${BIORXIV_API_BASE}/${startDate}/${endDate}/${cursor}/json`;
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
    name: "biorxiv-server",
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
        name: "search_biorxiv_preprints",
        description:
          "Search bioRxiv preprints by keyword within a date range. Returns matching preprints with title, authors, abstract, DOI, and category.",
        inputSchema: {
          type: "object",
          properties: {
            keywords: {
              type: "string",
              description:
                "Search keywords to match against title and abstract (e.g., 'CRISPR gene editing')",
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
        name: "get_biorxiv_paper",
        description:
          "Get full metadata for a specific bioRxiv preprint by DOI. Returns title, authors, abstract, category, date, and version info.",
        inputSchema: {
          type: "object",
          properties: {
            doi: {
              type: "string",
              description:
                "bioRxiv DOI (e.g., '10.1101/2024.01.01.12345678')",
            },
          },
          required: ["doi"],
        },
      },
      {
        name: "get_recent_biorxiv",
        description:
          "Get the most recent bioRxiv preprints, optionally filtered by category (e.g., 'genetics', 'neuroscience', 'bioinformatics').",
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
                "Optional category filter (e.g., 'biochemistry', 'cell biology', 'genetics', 'neuroscience', 'bioinformatics')",
            },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  try {
    if (name === "search_biorxiv_preprints") {
      const keywords = (args.keywords || "").trim();
      if (!keywords) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "keywords parameter is required and must not be blank" }, null, 2) }],
          isError: true,
        };
      }
      const maxResults = Math.min(args.max_results || 10, 50);

      // Default date range: last 30 days
      const now = new Date();
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      const startDate =
        args.start_date || thirtyDaysAgo.toISOString().split("T")[0];
      const endDate = args.end_date || now.toISOString().split("T")[0];

      // Fetch preprints in date range — scale fetch limit to maxResults
      const fetchLimit = Math.min(maxResults * 10, 500);
      const allItems = await fetchDateRange(startDate, endDate, fetchLimit);

      // Client-side keyword filtering on title + abstract
      const lowerKeywords = keywords.toLowerCase().split(/\s+/).filter(Boolean);
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
        link: `https://www.biorxiv.org/content/${item.doi}`,
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

    if (name === "get_biorxiv_paper") {
      const doi = args.doi;

      if (typeof doi !== "string" || doi.trim() === "") {
        return {
          isError: true,
          content: [
            {
              type: "text",
              text:
                'Missing required "doi" argument. Please provide a non-empty DOI.',
            },
          ],
        };
      }
      const encodedDoi = encodeURIComponent(doi);
      const url = `${BIORXIV_API_BASE}/${encodedDoi}/na/json`;
      const data = await getJSON(url);
      const items = data?.collection || [];

      if (items.length === 0) {
        return {
          isError: true,
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { error: "No paper found with this DOI", doi },
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
                link: `https://www.biorxiv.org/content/${paper.doi}`,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (name === "get_recent_biorxiv") {
      const count = Math.max(1, Math.min(Math.floor(Number(args.count) || 10), 50));
      const category = args.category ? args.category.toLowerCase() : null;

      // Use date range: last 7 days
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
        link: `https://www.biorxiv.org/content/${item.doi}`,
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
  console.error("bioRxiv MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
