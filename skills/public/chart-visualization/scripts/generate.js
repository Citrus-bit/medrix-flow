#!/usr/bin/env node

const fs = require("fs");

// Chart type mapping, consistent with src/utils/callTool.ts
const CHART_TYPE_MAP = {
  generate_area_chart: "area",
  generate_bar_chart: "bar",
  generate_boxplot_chart: "boxplot",
  generate_column_chart: "column",
  generate_district_map: "district-map",
  generate_dual_axes_chart: "dual-axes",
  generate_fishbone_diagram: "fishbone-diagram",
  generate_flow_diagram: "flow-diagram",
  generate_funnel_chart: "funnel",
  generate_histogram_chart: "histogram",
  generate_line_chart: "line",
  generate_liquid_chart: "liquid",
  generate_mind_map: "mind-map",
  generate_network_graph: "network-graph",
  generate_organization_chart: "organization-chart",
  generate_path_map: "path-map",
  generate_pie_chart: "pie",
  generate_pin_map: "pin-map",
  generate_radar_chart: "radar",
  generate_sankey_chart: "sankey",
  generate_scatter_chart: "scatter",
  generate_treemap_chart: "treemap",
  generate_venn_chart: "venn",
  generate_violin_chart: "violin",
  generate_word_cloud_chart: "word-cloud",
};

const REQUIRED_FIELDS = {
  generate_area_chart: ["time", "value"],
  generate_bar_chart: ["category", "value"],
  generate_boxplot_chart: ["category", "value"],
  generate_column_chart: ["category", "value"],
  generate_dual_axes_chart: ["time"],
  generate_funnel_chart: ["category", "value"],
  generate_histogram_chart: ["value"],
  generate_line_chart: ["time", "value"],
  generate_liquid_chart: ["value"],
  generate_pie_chart: ["category", "value"],
  generate_radar_chart: ["category", "value"],
  generate_sankey_chart: ["source", "target", "value"],
  generate_scatter_chart: ["x", "y"],
  generate_treemap_chart: ["category", "value"],
  generate_venn_chart: ["sets", "value"],
  generate_violin_chart: ["category", "value"],
  generate_word_cloud_chart: ["text", "value"],
};

const AXIS_BASED_TOOLS = new Set([
  "generate_area_chart",
  "generate_bar_chart",
  "generate_boxplot_chart",
  "generate_column_chart",
  "generate_dual_axes_chart",
  "generate_histogram_chart",
  "generate_line_chart",
  "generate_radar_chart",
  "generate_scatter_chart",
  "generate_violin_chart",
]);

const SUPPORTED_INTENT_STORIES = new Set([
  "trend",
  "comparison",
  "composition",
  "distribution",
  "relationship",
  "flow",
  "geography",
  "hierarchy",
]);

const TOOL_STORY_MAP = {
  generate_area_chart: "trend",
  generate_bar_chart: "comparison",
  generate_boxplot_chart: "distribution",
  generate_column_chart: "comparison",
  generate_district_map: "geography",
  generate_dual_axes_chart: "trend",
  generate_fishbone_diagram: "hierarchy",
  generate_flow_diagram: "flow",
  generate_funnel_chart: "flow",
  generate_histogram_chart: "distribution",
  generate_line_chart: "trend",
  generate_liquid_chart: "composition",
  generate_mind_map: "hierarchy",
  generate_network_graph: "relationship",
  generate_organization_chart: "hierarchy",
  generate_path_map: "geography",
  generate_pie_chart: "composition",
  generate_pin_map: "geography",
  generate_radar_chart: "comparison",
  generate_sankey_chart: "flow",
  generate_scatter_chart: "relationship",
  generate_treemap_chart: "composition",
  generate_venn_chart: "relationship",
  generate_violin_chart: "distribution",
  generate_word_cloud_chart: "comparison",
};

function isNumberLike(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function failValidation(message) {
  throw new Error(`Spec validation failed: ${message}`);
}

function ensureObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    failValidation(`${label} must be an object`);
  }
}

function validateIntent(tool, intent) {
  if (!intent) {
    return;
  }

  ensureObject(intent, "intent");

  const story = intent.data_story;
  if (!story || typeof story !== "string") {
    failValidation("intent.data_story is required when intent is provided");
  }
  if (!SUPPORTED_INTENT_STORIES.has(story)) {
    failValidation(`intent.data_story '${story}' is not supported`);
  }

  const expectedStory = TOOL_STORY_MAP[tool];
  if (expectedStory && story !== expectedStory) {
    failValidation(`tool '${tool}' conflicts with intent.data_story '${story}', expected '${expectedStory}'`);
  }

  if (!intent.reason_for_choice || typeof intent.reason_for_choice !== "string") {
    failValidation("intent.reason_for_choice is required when intent is provided");
  }
  if (!intent.source_summary || typeof intent.source_summary !== "string") {
    failValidation("intent.source_summary is required when intent is provided");
  }
  if (!Array.isArray(intent.validation_notes) || intent.validation_notes.length === 0) {
    failValidation("intent.validation_notes must be a non-empty array when intent is provided");
  }
}

function validateRowFields(tool, rows) {
  const requiredFields = REQUIRED_FIELDS[tool] || [];
  if (!requiredFields.length) {
    return;
  }

  for (const [index, row] of rows.entries()) {
    if (!row || typeof row !== "object" || Array.isArray(row)) {
      failValidation(`data row ${index} must be an object`);
    }

    for (const field of requiredFields) {
      if (!(field in row)) {
        failValidation(`data row ${index} is missing required field '${field}' for ${tool}`);
      }
    }
  }
}

function validateNumericFields(tool, rows) {
  const numericRules = {
    generate_area_chart: ["value"],
    generate_bar_chart: ["value"],
    generate_boxplot_chart: ["value"],
    generate_column_chart: ["value"],
    generate_funnel_chart: ["value"],
    generate_histogram_chart: ["value"],
    generate_line_chart: ["value"],
    generate_liquid_chart: ["value"],
    generate_pie_chart: ["value"],
    generate_radar_chart: ["value"],
    generate_sankey_chart: ["value"],
    generate_scatter_chart: ["x", "y"],
    generate_treemap_chart: ["value"],
    generate_venn_chart: ["value"],
    generate_violin_chart: ["value"],
    generate_word_cloud_chart: ["value"],
  };

  const numericFields = numericRules[tool] || [];
  for (const [index, row] of rows.entries()) {
    for (const field of numericFields) {
      if (!isNumberLike(row[field])) {
        failValidation(`data row ${index} field '${field}' must be a finite number for ${tool}`);
      }
    }
  }
}

function validateAxes(tool, args) {
  if (!AXIS_BASED_TOOLS.has(tool)) {
    return;
  }
  if (!args.axisXTitle || !args.axisYTitle) {
    failValidation(`${tool} requires both axisXTitle and axisYTitle`);
  }
}

function validatePieConstraints(tool, rows) {
  if (tool !== "generate_pie_chart") {
    return;
  }
  if (rows.length > 6) {
    failValidation("pie charts support at most 6 slices; aggregate remaining categories before generation");
  }
}

function validateArgs(tool, args) {
  ensureObject(args, "args");
  const data = args.data;
  if (!Array.isArray(data) || data.length === 0) {
    failValidation("args.data must be a non-empty array");
  }

  validateRowFields(tool, data);
  validateNumericFields(tool, data);
  validateAxes(tool, args);
  validatePieConstraints(tool, data);

  if (!args.title || typeof args.title !== "string") {
    failValidation("args.title is required");
  }
}

function validateSpec(item) {
  ensureObject(item, "spec");

  const tool = item.tool;
  if (!tool || typeof tool !== "string") {
    failValidation("spec.tool is required");
  }
  if (!CHART_TYPE_MAP[tool]) {
    failValidation(`Unknown tool '${tool}'`);
  }

  validateIntent(tool, item.intent);
  validateArgs(tool, item.args || {});
}

function getVisRequestServer() {
  return (
    process.env.VIS_REQUEST_SERVER ||
    "https://antv-studio.alipay.com/api/gpt-vis"
  );
}

function getServiceIdentifier() {
  return process.env.SERVICE_ID;
}

async function httpPost(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }

  return response.json();
}

async function generateChartUrl(chartType, options) {
  const url = getVisRequestServer();
  const payload = {
    type: chartType,
    source: "chart-visualization-creator",
    ...options,
  };

  const data = await httpPost(url, payload);

  if (!data.success) {
    throw new Error(data.errorMessage || "Unknown error");
  }

  return data.resultObj;
}

async function generateMap(tool, inputData) {
  const url = getVisRequestServer();
  const payload = {
    serviceId: getServiceIdentifier(),
    tool,
    input: inputData,
    source: "chart-visualization-creator",
  };

  const data = await httpPost(url, payload);

  if (!data.success) {
    throw new Error(data.errorMessage || "Unknown error");
  }

  return data.resultObj;
}

async function main() {
  if (process.argv.length < 3) {
    console.error("Usage: node generate.js <spec_json_or_file>");
    process.exit(1);
  }

  const specArg = process.argv[2];
  let spec;

  try {
    if (fs.existsSync(specArg)) {
      const fileContent = fs.readFileSync(specArg, "utf-8");
      spec = JSON.parse(fileContent);
    } else {
      spec = JSON.parse(specArg);
    }
  } catch (e) {
    console.error(`Error parsing spec: ${e.message}`);
    process.exit(1);
  }

  const specs = Array.isArray(spec) ? spec : [spec];

  for (const item of specs) {
    let tool;
    let args;
    let chartType;

    try {
      validateSpec(item);
      tool = item.tool;
      args = item.args || {};
      chartType = CHART_TYPE_MAP[tool];
    } catch (e) {
      console.error(e.message);
      continue;
    }

    const isMapChartTool = [
      "generate_district_map",
      "generate_path_map",
      "generate_pin_map",
    ].includes(tool);

    try {
      if (isMapChartTool) {
        const result = await generateMap(tool, args);
        if (result && result.content) {
          for (const contentItem of result.content) {
            if (contentItem.type === "text") {
              console.log(contentItem.text);
            }
          }
        } else {
          console.log(JSON.stringify(result));
        }
      } else {
        const url = await generateChartUrl(chartType, args);
        console.log(url);
      }
    } catch (e) {
      console.error(`Error generating chart for ${tool}: ${e.message}`);
    }
  }
}

if (require.main === module) {
  main().catch((err) => {
    console.error(err.message);
    process.exit(1);
  });
}

// Export functions for testing
module.exports = {
  generateChartUrl,
  generateMap,
  httpPost,
  CHART_TYPE_MAP,
  validateSpec,
};
