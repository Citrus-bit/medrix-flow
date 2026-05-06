const assert = require("assert");
const { validateSpec } = require("./generate");

function expectPass(spec) {
  assert.doesNotThrow(() => validateSpec(spec));
}

function expectFail(spec, messagePattern) {
  assert.throws(() => validateSpec(spec), messagePattern);
}

expectPass({
  tool: "generate_line_chart",
  args: {
    data: [
      { time: "2026-01", value: 10 },
      { time: "2026-02", value: 12 },
    ],
    title: "Monthly Revenue Trend",
    axisXTitle: "Month",
    axisYTitle: "Revenue (k$)",
    theme: "default",
    style: { palette: ["#1f77b4"] },
  },
  intent: {
    data_story: "trend",
    reason_for_choice: "The request asks for sequential month-over-month movement.",
    source_summary: "Derived from monthly revenue aggregates.",
    validation_notes: ["time is sequential", "value is numeric"],
  },
});

expectFail(
  {
    tool: "generate_line_chart",
    args: {
      data: [{ category: "A", value: 1 }],
      title: "Wrong Shape",
      axisXTitle: "Category",
      axisYTitle: "Value",
    },
    intent: {
      data_story: "trend",
      reason_for_choice: "Bad input example.",
      source_summary: "Synthetic example.",
      validation_notes: ["value is numeric"],
    },
  },
  /missing required field 'time'/,
);

expectFail(
  {
    tool: "generate_pie_chart",
    args: {
      data: [
        { category: "A", value: 1 },
        { category: "B", value: 1 },
        { category: "C", value: 1 },
        { category: "D", value: 1 },
        { category: "E", value: 1 },
        { category: "F", value: 1 },
        { category: "G", value: 1 },
      ],
      title: "Too Many Slices",
    },
    intent: {
      data_story: "composition",
      reason_for_choice: "Share of total example.",
      source_summary: "Synthetic example.",
      validation_notes: ["values are numeric"],
    },
  },
  /at most 6 slices/,
);

expectFail(
  {
    tool: "generate_scatter_chart",
    args: {
      data: [{ x: "high", y: 2 }],
      title: "Invalid Scatter",
      axisXTitle: "X",
      axisYTitle: "Y",
    },
    intent: {
      data_story: "relationship",
      reason_for_choice: "Correlation request.",
      source_summary: "Synthetic example.",
      validation_notes: ["y is numeric"],
    },
  },
  /field 'x' must be a finite number/,
);

expectFail(
  {
    tool: "generate_bar_chart",
    args: {
      data: [{ category: "North", value: 42 }],
      title: "Regional Sales",
      axisXTitle: "Sales",
      axisYTitle: "Region",
    },
    intent: {
      data_story: "trend",
      reason_for_choice: "Intentionally wrong story.",
      source_summary: "Synthetic example.",
      validation_notes: ["category exists", "value is numeric"],
    },
  },
  /conflicts with intent\.data_story 'trend'/,
);

console.log("chart-visualization spec validation tests passed");
