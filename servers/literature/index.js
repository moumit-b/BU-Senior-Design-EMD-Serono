#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-literature/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

async function getText(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-literature/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

// Create server instance
const server = new Server(
  {
    name: "literature-server",
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
        name: "search_pubmed",
        description: "Search PubMed database for research articles by keywords, returning PMIDs and basic info",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query (e.g., 'cancer immunotherapy', 'BRCA1 gene')",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results to return (default: 10, max: 100)",
              default: 10,
            },
            sort: {
              type: "string",
              description: "Sort order: 'relevance', 'date', or 'cited' (default: relevance)",
              default: "relevance",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_pubmed_abstract",
        description: "Retrieve full abstract and metadata for a PubMed article by PMID",
        inputSchema: {
          type: "object",
          properties: {
            pmid: {
              type: "string",
              description: "PubMed ID (e.g., '12345678')",
            },
          },
          required: ["pmid"],
        },
      },
      {
        name: "search_pubmed_by_author",
        description: "Search PubMed for articles by specific author name",
        inputSchema: {
          type: "object",
          properties: {
            author: {
              type: "string",
              description: "Author name (e.g., 'Smith J' or 'Smith John')",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10)",
              default: 10,
            },
          },
          required: ["author"],
        },
      },
      {
        name: "get_related_articles",
        description: "Find articles related to a given PMID based on content similarity",
        inputSchema: {
          type: "object",
          properties: {
            pmid: {
              type: "string",
              description: "PubMed ID to find related articles for",
            },
            max_results: {
              type: "number",
              description: "Maximum number of related articles (default: 5)",
              default: 5,
            },
          },
          required: ["pmid"],
        },
      },
      {
        name: "search_by_doi",
        description: "Retrieve article information using a DOI",
        inputSchema: {
          type: "object",
          properties: {
            doi: {
              type: "string",
              description: "Digital Object Identifier (e.g., '10.1038/nature12345')",
            },
          },
          required: ["doi"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_pubmed") {
      const query = encodeURIComponent(args.query);
      const maxResults = Math.min(args.max_results || 10, 100);
      const sort = args.sort || "relevance";

      const sortParam = sort === "date" ? "&sort=date" : sort === "cited" ? "&sort=pub+date" : "";

      // Step 1: Search for PMIDs
      const searchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${query}&retmax=${maxResults}&retmode=json${sortParam}`;
      const searchData = await getJSON(searchUrl);

      const pmids = searchData?.esearchresult?.idlist || [];

      if (pmids.length === 0) {
        return {
          content: [{ type: "text", text: JSON.stringify({ results: [], message: "No articles found" }, null, 2) }],
        };
      }

      // Step 2: Get summaries for found PMIDs
      const summaryUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${pmids.join(',')}&retmode=json`;
      const summaryData = await getJSON(summaryUrl);

      const results = pmids.map(pmid => {
        const article = summaryData?.result?.[pmid];
        return {
          pmid,
          title: article?.title || "N/A",
          authors: article?.authors?.slice(0, 3).map(a => a.name).join(", ") + (article?.authors?.length > 3 ? " et al." : "") || "N/A",
          journal: article?.source || "N/A",
          pubdate: article?.pubdate || "N/A",
          link: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`
        };
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify({ query: args.query, count: results.length, results }, null, 2)
        }],
      };
    }

    if (name === "get_pubmed_abstract") {
      const pmid = args.pmid;

      // Fetch full article details
      const url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmid}&retmode=xml`;
      const xmlText = await getText(url);

      // Simple XML parsing (for production, use proper XML parser)
      const titleMatch = xmlText.match(/<ArticleTitle>(.*?)<\/ArticleTitle>/s);
      const abstractMatch = xmlText.match(/<AbstractText[^>]*>(.*?)<\/AbstractText>/gs);
      const journalMatch = xmlText.match(/<Journal>.*?<Title>(.*?)<\/Title>/s);
      const pubDateMatch = xmlText.match(/<PubDate>.*?<Year>(\d{4})<\/Year>/s);

      const abstract = abstractMatch ? abstractMatch.map(m => m.replace(/<[^>]+>/g, '')).join('\n') : "Abstract not available";

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            pmid,
            title: titleMatch ? titleMatch[1] : "N/A",
            abstract,
            journal: journalMatch ? journalMatch[1] : "N/A",
            year: pubDateMatch ? pubDateMatch[1] : "N/A",
            link: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`
          }, null, 2)
        }],
      };
    }

    if (name === "search_pubmed_by_author") {
      const author = encodeURIComponent(args.author + "[Author]");
      const maxResults = args.max_results || 10;

      const searchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${author}&retmax=${maxResults}&retmode=json&sort=pub+date`;
      const searchData = await getJSON(searchUrl);

      const pmids = searchData?.esearchresult?.idlist || [];

      if (pmids.length === 0) {
        return {
          content: [{ type: "text", text: JSON.stringify({ results: [], message: "No articles found for this author" }, null, 2) }],
        };
      }

      const summaryUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${pmids.join(',')}&retmode=json`;
      const summaryData = await getJSON(summaryUrl);

      const results = pmids.map(pmid => {
        const article = summaryData?.result?.[pmid];
        return {
          pmid,
          title: article?.title || "N/A",
          journal: article?.source || "N/A",
          pubdate: article?.pubdate || "N/A",
          link: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`
        };
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify({ author: args.author, count: results.length, results }, null, 2)
        }],
      };
    }

    if (name === "get_related_articles") {
      const pmid = args.pmid;
      const maxResults = args.max_results || 5;

      const url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=pubmed&id=${pmid}&retmode=json`;
      const linkData = await getJSON(url);

      const relatedPmids = linkData?.linksets?.[0]?.linksetdbs?.find(ls => ls.linkname === "pubmed_pubmed")?.links || [];
      const limitedPmids = relatedPmids.slice(0, maxResults);

      if (limitedPmids.length === 0) {
        return {
          content: [{ type: "text", text: JSON.stringify({ results: [], message: "No related articles found" }, null, 2) }],
        };
      }

      const summaryUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${limitedPmids.join(',')}&retmode=json`;
      const summaryData = await getJSON(summaryUrl);

      const results = limitedPmids.map(relPmid => {
        const article = summaryData?.result?.[relPmid];
        return {
          pmid: relPmid,
          title: article?.title || "N/A",
          journal: article?.source || "N/A",
          pubdate: article?.pubdate || "N/A",
          link: `https://pubmed.ncbi.nlm.nih.gov/${relPmid}/`
        };
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify({ source_pmid: pmid, count: results.length, related_articles: results }, null, 2)
        }],
      };
    }

    if (name === "search_by_doi") {
      const doi = encodeURIComponent(args.doi);

      const searchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${doi}[DOI]&retmode=json`;
      const searchData = await getJSON(searchUrl);

      const pmids = searchData?.esearchresult?.idlist || [];

      if (pmids.length === 0) {
        return {
          content: [{ type: "text", text: JSON.stringify({ error: "No article found with this DOI" }, null, 2) }],
        };
      }

      const pmid = pmids[0];
      const url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmid}&retmode=xml`;
      const xmlText = await getText(url);

      const titleMatch = xmlText.match(/<ArticleTitle>(.*?)<\/ArticleTitle>/s);
      const abstractMatch = xmlText.match(/<AbstractText[^>]*>(.*?)<\/AbstractText>/gs);
      const journalMatch = xmlText.match(/<Journal>.*?<Title>(.*?)<\/Title>/s);
      const pubDateMatch = xmlText.match(/<PubDate>.*?<Year>(\d{4})<\/Year>/s);

      const abstract = abstractMatch ? abstractMatch.map(m => m.replace(/<[^>]+>/g, '')).join('\n') : "Abstract not available";

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            doi: args.doi,
            pmid,
            title: titleMatch ? titleMatch[1] : "N/A",
            abstract,
            journal: journalMatch ? journalMatch[1] : "N/A",
            year: pubDateMatch ? pubDateMatch[1] : "N/A",
            link: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`
          }, null, 2)
        }],
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          error: error.message,
          tool: name,
        }, null, 2)
      }],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Literature MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
