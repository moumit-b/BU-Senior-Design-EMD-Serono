#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Helper functions for statistical calculations
function calculateStats(values) {
  const n = values.length;
  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / n;

  const sortedValues = [...values].sort((a, b) => a - b);
  const median = n % 2 === 0
    ? (sortedValues[n / 2 - 1] + sortedValues[n / 2]) / 2
    : sortedValues[Math.floor(n / 2)];

  const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / n;
  const stdDev = Math.sqrt(variance);

  const min = Math.min(...values);
  const max = Math.max(...values);

  return { n, sum, mean, median, variance, stdDev, min, max };
}

function calculateCorrelation(x, y) {
  const n = x.length;
  if (n !== y.length || n < 2) throw new Error("Arrays must have same length and at least 2 elements");

  const meanX = x.reduce((a, b) => a + b, 0) / n;
  const meanY = y.reduce((a, b) => a + b, 0) / n;

  let numerator = 0;
  let denomX = 0;
  let denomY = 0;

  for (let i = 0; i < n; i++) {
    const dx = x[i] - meanX;
    const dy = y[i] - meanY;
    numerator += dx * dy;
    denomX += dx * dx;
    denomY += dy * dy;
  }

  const correlation = numerator / Math.sqrt(denomX * denomY);
  return correlation;
}

function performRegression(x, y) {
  const n = x.length;
  if (n !== y.length) throw new Error("Arrays must have same length");

  const meanX = x.reduce((a, b) => a + b, 0) / n;
  const meanY = y.reduce((a, b) => a + b, 0) / n;

  let numerator = 0;
  let denominator = 0;

  for (let i = 0; i < n; i++) {
    numerator += (x[i] - meanX) * (y[i] - meanY);
    denominator += (x[i] - meanX) ** 2;
  }

  const slope = numerator / denominator;
  const intercept = meanY - slope * meanX;

  // Calculate R-squared
  const yPred = x.map(xi => slope * xi + intercept);
  const ssRes = y.reduce((sum, yi, i) => sum + (yi - yPred[i]) ** 2, 0);
  const ssTot = y.reduce((sum, yi) => sum + (yi - meanY) ** 2, 0);
  const rSquared = 1 - (ssRes / ssTot);

  return { slope, intercept, rSquared, equation: `y = ${slope.toFixed(4)}x + ${intercept.toFixed(4)}` };
}

// DNA/Protein sequence analysis functions
function analyzeSequence(sequence, type) {
  const seq = sequence.toUpperCase().replace(/\s/g, '');

  if (type === "DNA") {
    const length = seq.length;
    const counts = { A: 0, T: 0, G: 0, C: 0 };

    for (const base of seq) {
      if (counts.hasOwnProperty(base)) counts[base]++;
    }

    const gcContent = ((counts.G + counts.C) / length * 100).toFixed(2);
    const atContent = ((counts.A + counts.T) / length * 100).toFixed(2);

    return {
      type: "DNA",
      length,
      composition: counts,
      gcContent: `${gcContent}%`,
      atContent: `${atContent}%`,
      molecularWeight: (length * 330).toFixed(2) + " Da (approx)"
    };
  } else if (type === "PROTEIN") {
    const length = seq.length;
    const aminoAcids = {};

    for (const aa of seq) {
      aminoAcids[aa] = (aminoAcids[aa] || 0) + 1;
    }

    // Approximate molecular weight (average amino acid weight ~110 Da)
    const molecularWeight = (length * 110).toFixed(2);

    return {
      type: "Protein",
      length,
      composition: aminoAcids,
      molecularWeight: `${molecularWeight} Da (approx)`,
      uniqueAminoAcids: Object.keys(aminoAcids).length
    };
  }
}

function calculateMolecularDescriptors(properties) {
  // Calculate Lipinski's Rule of Five parameters
  const mw = properties.molecularWeight || 0;
  const logP = properties.logP || 0;
  const hbd = properties.hydrogenBondDonors || 0;
  const hba = properties.hydrogenBondAcceptors || 0;

  const lipinskiViolations = [
    mw > 500 ? "Molecular weight > 500 Da" : null,
    logP > 5 ? "LogP > 5" : null,
    hbd > 5 ? "H-bond donors > 5" : null,
    hba > 10 ? "H-bond acceptors > 10" : null
  ].filter(v => v !== null);

  const drugLike = lipinskiViolations.length <= 1;

  return {
    lipinskiRuleOfFive: {
      molecularWeight: mw,
      logP,
      hydrogenBondDonors: hbd,
      hydrogenBondAcceptors: hba,
      violations: lipinskiViolations,
      drugLike,
      summary: drugLike ? "Compound passes Lipinski's Rule of Five" : `${lipinskiViolations.length} violations detected`
    }
  };
}

// Create server instance
const server = new Server(
  {
    name: "data-analysis-server",
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
        name: "calculate_statistics",
        description: "Calculate basic statistical measures (mean, median, standard deviation, etc.) for a dataset",
        inputSchema: {
          type: "object",
          properties: {
            values: {
              type: "array",
              items: { type: "number" },
              description: "Array of numerical values to analyze",
            },
          },
          required: ["values"],
        },
      },
      {
        name: "calculate_correlation",
        description: "Calculate Pearson correlation coefficient between two datasets",
        inputSchema: {
          type: "object",
          properties: {
            x: {
              type: "array",
              items: { type: "number" },
              description: "First dataset",
            },
            y: {
              type: "array",
              items: { type: "number" },
              description: "Second dataset",
            },
          },
          required: ["x", "y"],
        },
      },
      {
        name: "perform_linear_regression",
        description: "Perform linear regression analysis and calculate R-squared value",
        inputSchema: {
          type: "object",
          properties: {
            x: {
              type: "array",
              items: { type: "number" },
              description: "Independent variable values",
            },
            y: {
              type: "array",
              items: { type: "number" },
              description: "Dependent variable values",
            },
          },
          required: ["x", "y"],
        },
      },
      {
        name: "analyze_sequence",
        description: "Analyze DNA or protein sequence composition and properties",
        inputSchema: {
          type: "object",
          properties: {
            sequence: {
              type: "string",
              description: "DNA or protein sequence",
            },
            type: {
              type: "string",
              enum: ["DNA", "PROTEIN"],
              description: "Sequence type: DNA or PROTEIN",
            },
          },
          required: ["sequence", "type"],
        },
      },
      {
        name: "calculate_molecular_descriptors",
        description: "Calculate molecular descriptors including Lipinski's Rule of Five for drug-likeness",
        inputSchema: {
          type: "object",
          properties: {
            molecularWeight: {
              type: "number",
              description: "Molecular weight in Daltons",
            },
            logP: {
              type: "number",
              description: "Partition coefficient (lipophilicity)",
            },
            hydrogenBondDonors: {
              type: "number",
              description: "Number of hydrogen bond donors",
            },
            hydrogenBondAcceptors: {
              type: "number",
              description: "Number of hydrogen bond acceptors",
            },
          },
          required: ["molecularWeight"],
        },
      },
      {
        name: "convert_units",
        description: "Convert between common scientific units (molarity, mass, volume)",
        inputSchema: {
          type: "object",
          properties: {
            value: {
              type: "number",
              description: "Value to convert",
            },
            fromUnit: {
              type: "string",
              description: "Source unit (e.g., 'mg', 'g', 'mL', 'L', 'mM', 'uM')",
            },
            toUnit: {
              type: "string",
              description: "Target unit",
            },
            molecularWeight: {
              type: "number",
              description: "Molecular weight in g/mol (required for molarity conversions)",
            },
          },
          required: ["value", "fromUnit", "toUnit"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "calculate_statistics") {
      const stats = calculateStats(args.values);

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            statistics: stats,
            dataset: args.values
          }, null, 2)
        }],
      };
    }

    if (name === "calculate_correlation") {
      const correlation = calculateCorrelation(args.x, args.y);

      let interpretation;
      const absCorr = Math.abs(correlation);
      if (absCorr > 0.9) interpretation = "Very strong correlation";
      else if (absCorr > 0.7) interpretation = "Strong correlation";
      else if (absCorr > 0.5) interpretation = "Moderate correlation";
      else if (absCorr > 0.3) interpretation = "Weak correlation";
      else interpretation = "Very weak or no correlation";

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            correlation: correlation.toFixed(4),
            interpretation,
            direction: correlation > 0 ? "Positive" : "Negative",
            n: args.x.length
          }, null, 2)
        }],
      };
    }

    if (name === "perform_linear_regression") {
      const regression = performRegression(args.x, args.y);

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            regression,
            dataPoints: args.x.length,
            interpretation: `The model explains ${(regression.rSquared * 100).toFixed(2)}% of the variance in the data`
          }, null, 2)
        }],
      };
    }

    if (name === "analyze_sequence") {
      const analysis = analyzeSequence(args.sequence, args.type);

      return {
        content: [{
          type: "text",
          text: JSON.stringify(analysis, null, 2)
        }],
      };
    }

    if (name === "calculate_molecular_descriptors") {
      const descriptors = calculateMolecularDescriptors(args);

      return {
        content: [{
          type: "text",
          text: JSON.stringify(descriptors, null, 2)
        }],
      };
    }

    if (name === "convert_units") {
      const { value, fromUnit, toUnit, molecularWeight } = args;
      let result;

      // Mass conversions
      if (fromUnit === "mg" && toUnit === "g") result = value / 1000;
      else if (fromUnit === "g" && toUnit === "mg") result = value * 1000;
      else if (fromUnit === "ug" && toUnit === "mg") result = value / 1000;
      else if (fromUnit === "mg" && toUnit === "ug") result = value * 1000;

      // Volume conversions
      else if (fromUnit === "mL" && toUnit === "L") result = value / 1000;
      else if (fromUnit === "L" && toUnit === "mL") result = value * 1000;
      else if (fromUnit === "uL" && toUnit === "mL") result = value / 1000;
      else if (fromUnit === "mL" && toUnit === "uL") result = value * 1000;

      // Molarity conversions
      else if (fromUnit === "mM" && toUnit === "uM") result = value * 1000;
      else if (fromUnit === "uM" && toUnit === "mM") result = value / 1000;
      else if (fromUnit === "M" && toUnit === "mM") result = value * 1000;
      else if (fromUnit === "mM" && toUnit === "M") result = value / 1000;

      // Mass to molarity (requires MW)
      else if ((fromUnit === "mg" || fromUnit === "g") && (toUnit === "mM" || toUnit === "uM")) {
        if (!molecularWeight) throw new Error("Molecular weight required for this conversion");
        const grams = fromUnit === "mg" ? value / 1000 : value;
        const moles = grams / molecularWeight;
        const molar = moles; // assuming 1L solution
        result = toUnit === "mM" ? molar * 1000 : molar * 1000000;
      }

      else {
        throw new Error(`Conversion from ${fromUnit} to ${toUnit} not supported`);
      }

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            original: `${value} ${fromUnit}`,
            converted: `${result.toFixed(6)} ${toUnit}`,
            conversionFactor: (result / value).toFixed(6)
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
  console.error("Data Analysis MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
