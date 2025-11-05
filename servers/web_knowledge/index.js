#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-web-knowledge/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

async function getText(url) {
  const res = await fetch(url, { headers: { "User-Agent": "mcp-web-knowledge/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

// Create server instance
const server = new Server(
  {
    name: "web-knowledge-server",
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
        name: "search_wikipedia",
        description: "Search Wikipedia for articles and get summaries",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query",
            },
            sentences: {
              type: "number",
              description: "Number of sentences in summary (default: 3)",
              default: 3,
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_wikipedia_page",
        description: "Get full content of a specific Wikipedia page by title",
        inputSchema: {
          type: "object",
          properties: {
            title: {
              type: "string",
              description: "Wikipedia page title",
            },
          },
          required: ["title"],
        },
      },
      {
        name: "search_clinical_trials",
        description: "Search ClinicalTrials.gov for clinical trials by condition, intervention, or other criteria",
        inputSchema: {
          type: "object",
          properties: {
            condition: {
              type: "string",
              description: "Disease or condition (e.g., 'breast cancer', 'diabetes')",
            },
            intervention: {
              type: "string",
              description: "Intervention/treatment being studied",
            },
            status: {
              type: "string",
              description: "Recruitment status: 'recruiting', 'completed', 'active'",
            },
            max_results: {
              type: "number",
              description: "Maximum number of results (default: 10)",
              default: 10,
            },
          },
        },
      },
      {
        name: "get_clinical_trial_details",
        description: "Get detailed information about a specific clinical trial by NCT ID",
        inputSchema: {
          type: "object",
          properties: {
            nct_id: {
              type: "string",
              description: "NCT number (e.g., 'NCT12345678')",
            },
          },
          required: ["nct_id"],
        },
      },
      {
        name: "search_patents",
        description: "Search patent databases (limited to Google Patents search)",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Patent search query",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_drugbank_info",
        description: "Get basic drug information from open sources (drug names, categories, descriptions)",
        inputSchema: {
          type: "object",
          properties: {
            drug_name: {
              type: "string",
              description: "Drug name (e.g., 'aspirin', 'metformin')",
            },
          },
          required: ["drug_name"],
        },
      },
      {
        name: "get_gene_info",
        description: "Get gene information from NCBI Gene database",
        inputSchema: {
          type: "object",
          properties: {
            gene_symbol: {
              type: "string",
              description: "Gene symbol (e.g., 'BRCA1', 'TP53')",
            },
            species: {
              type: "string",
              description: "Species (default: 'human')",
              default: "human",
            },
          },
          required: ["gene_symbol"],
        },
      },
      {
        name: "convert_identifiers",
        description: "Convert between different biomedical identifiers (Gene ID, Ensembl ID, etc.)",
        inputSchema: {
          type: "object",
          properties: {
            identifier: {
              type: "string",
              description: "Identifier to convert",
            },
            from_type: {
              type: "string",
              description: "Source type: 'gene_symbol', 'gene_id', 'ensembl', 'uniprot'",
            },
            to_type: {
              type: "string",
              description: "Target type",
            },
          },
          required: ["identifier", "from_type", "to_type"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search_wikipedia") {
      const query = encodeURIComponent(args.query);
      const sentences = args.sentences || 3;

      const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${query}`;
      const data = await getJSON(url);

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            title: data.title,
            summary: data.extract,
            url: data.content_urls?.desktop?.page,
            thumbnail: data.thumbnail?.source || null
          }, null, 2)
        }],
      };
    }

    if (name === "get_wikipedia_page") {
      const title = encodeURIComponent(args.title);

      const url = `https://en.wikipedia.org/api/rest_v1/page/html/${title}`;
      const html = await getText(url);

      // Extract text content (simplified - removes HTML tags)
      const textContent = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().substring(0, 5000);

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            title: args.title,
            content: textContent.substring(0, 2000) + "...",
            url: `https://en.wikipedia.org/wiki/${title}`,
            note: "Content truncated to 2000 characters"
          }, null, 2)
        }],
      };
    }

    if (name === "search_clinical_trials") {
      let queryParts = [];

      if (args.condition) queryParts.push(`cond=${encodeURIComponent(args.condition)}`);
      if (args.intervention) queryParts.push(`intr=${encodeURIComponent(args.intervention)}`);
      if (args.status) queryParts.push(`recrs=${args.status}`);

      const maxResults = Math.min(args.max_results || 10, 50);
      queryParts.push(`pageSize=${maxResults}`);

      const queryString = queryParts.join('&');
      const url = `https://clinicaltrials.gov/api/v2/studies?${queryString}`;

      const data = await getJSON(url);

      const studies = (data.studies || []).map(study => ({
        nctId: study.protocolSection?.identificationModule?.nctId,
        title: study.protocolSection?.identificationModule?.briefTitle,
        status: study.protocolSection?.statusModule?.overallStatus,
        condition: study.protocolSection?.conditionsModule?.conditions?.[0],
        intervention: study.protocolSection?.armsInterventionsModule?.interventions?.[0]?.name,
        phase: study.protocolSection?.designModule?.phases?.[0],
        enrollment: study.protocolSection?.designModule?.enrollmentInfo?.count,
        startDate: study.protocolSection?.statusModule?.startDateStruct?.date,
        url: `https://clinicaltrials.gov/study/${study.protocolSection?.identificationModule?.nctId}`
      }));

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            query: args,
            count: studies.length,
            trials: studies
          }, null, 2)
        }],
      };
    }

    if (name === "get_clinical_trial_details") {
      const nctId = args.nct_id;
      const url = `https://clinicaltrials.gov/api/v2/studies/${nctId}`;

      const data = await getJSON(url);
      const study = data.protocolSection;

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            nctId: study?.identificationModule?.nctId,
            title: study?.identificationModule?.officialTitle,
            briefTitle: study?.identificationModule?.briefTitle,
            status: study?.statusModule?.overallStatus,
            phase: study?.designModule?.phases,
            conditions: study?.conditionsModule?.conditions,
            interventions: study?.armsInterventionsModule?.interventions?.map(i => ({
              type: i.type,
              name: i.name,
              description: i.description
            })),
            eligibility: study?.eligibilityModule?.eligibilityCriteria?.substring(0, 500),
            enrollment: study?.designModule?.enrollmentInfo,
            locations: study?.contactsLocationsModule?.locations?.slice(0, 5).map(l => ({
              facility: l.facility,
              city: l.city,
              country: l.country
            })),
            url: `https://clinicaltrials.gov/study/${args.nct_id}`
          }, null, 2)
        }],
      };
    }

    if (name === "search_patents") {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            note: "Patent search via API requires API keys. Visit Google Patents directly:",
            url: `https://patents.google.com/?q=${encodeURIComponent(args.query)}`,
            query: args.query,
            alternatives: [
              "Use PubChem for chemical patents",
              "Use USPTO.gov for direct US patent search",
              "Use EPO (European Patent Office) for European patents"
            ]
          }, null, 2)
        }],
      };
    }

    if (name === "get_drugbank_info") {
      // Use PubChem as a proxy for basic drug information
      const drugName = encodeURIComponent(args.drug_name);
      const searchUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${drugName}/cids/JSON`;

      const searchData = await getJSON(searchUrl);
      const cid = searchData?.IdentifierList?.CID?.[0];

      if (!cid) {
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              error: "Drug not found in PubChem database",
              drug: args.drug_name
            }, null, 2)
          }],
        };
      }

      const propsUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/property/MolecularFormula,MolecularWeight,IUPACName/JSON`;
      const propsData = await getJSON(propsUrl);
      const props = propsData?.PropertyTable?.Properties?.[0];

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            drug: args.drug_name,
            cid,
            molecularFormula: props?.MolecularFormula,
            molecularWeight: props?.MolecularWeight,
            iupacName: props?.IUPACName,
            pubchemUrl: `https://pubchem.ncbi.nlm.nih.gov/compound/${cid}`
          }, null, 2)
        }],
      };
    }

    if (name === "get_gene_info") {
      const geneSymbol = args.gene_symbol;
      const species = args.species || "human";
      const taxId = species.toLowerCase() === "human" ? "9606" : "10090"; // human or mouse

      // Search for gene by symbol
      const searchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term=${encodeURIComponent(geneSymbol)}[Gene%20Name]+AND+${taxId}[Taxonomy%20ID]&retmode=json`;
      const searchData = await getJSON(searchUrl);

      const geneId = searchData?.esearchresult?.idlist?.[0];

      if (!geneId) {
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              error: "Gene not found",
              gene: geneSymbol,
              species
            }, null, 2)
          }],
        };
      }

      // Get gene summary
      const summaryUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id=${geneId}&retmode=json`;
      const summaryData = await getJSON(summaryUrl);
      const geneData = summaryData?.result?.[geneId];

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            geneId,
            symbol: geneData?.name,
            description: geneData?.description,
            chromosome: geneData?.chromosome,
            location: geneData?.maplocation,
            aliases: geneData?.otheraliases?.split(", ") || [],
            summary: geneData?.summary?.substring(0, 500) + "...",
            url: `https://www.ncbi.nlm.nih.gov/gene/${geneId}`
          }, null, 2)
        }],
      };
    }

    if (name === "convert_identifiers") {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            note: "Identifier conversion requires specialized APIs like MyGene.info or BioMart",
            suggestion: "Use MyGene.info API for comprehensive ID conversion",
            example: `https://mygene.info/v3/query?q=${args.identifier}`,
            identifier: args.identifier,
            from: args.from_type,
            to: args.to_type
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
  console.error("Web/Knowledge MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
