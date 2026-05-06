---
name: chart-visualization
description: Use this skill whenever the user wants a chart, graph, plot, dashboard visual, or asks to visualize structured numbers, trends, comparisons, proportions, distributions, correlations, rankings, or flows. This skill must also trigger when the user describes a reporting need in natural language without explicitly saying "chart". It converts the request into a validated chart specification, checks that the chosen chart type actually matches the data story, and only then generates the visual.
dependency:
  nodejs: ">=18.0.0"
---

# Chart Visualization Skill

This skill provides a comprehensive workflow for transforming data into visual charts. It handles chart selection, parameter extraction, and image generation.

## Workflow

To visualize data, follow these steps:

### 1. Normalize the Request Into a Chart Brief
Before choosing any chart, reduce the user's request into a brief with these fields:

```json
{
  "goal": "What decision or comparison the chart should support",
  "audience": "executive | analytical | operational | academic | unknown",
  "data_story": "trend | comparison | composition | distribution | relationship | flow | geography | hierarchy",
  "source_data_state": "explicit data provided | partially described | no data",
  "must_show": ["metrics or categories that must appear"],
  "constraints": ["units, time grain, brand colors, report context, etc."]
}
```

If any of these are ambiguous enough to affect chart correctness, call `ask_clarification` before generating.

### 2. Ground the Data Before Chart Selection

- If the user uploaded CSV/XLSX or described tabular data, use `data-analysis` first to inspect schema and derive the exact rows/columns for charting.
- If the request contains only prose and no reliable numbers, do **not** invent plausible values just to make a chart. Ask for the missing data or clearly state that you can only produce a conceptual mock chart.
- Always produce a clean `data` array before generation. The final chart spec must be reproducible from that array alone.

### 3. Intelligent Chart Selection
Analyze the grounded data and the chart brief to determine the most appropriate chart type. Use the following guidelines (and consult `references/` for detailed specs):

- **Time Series**: Use `generate_line_chart` (trends) or `generate_area_chart` (accumulated trends). Use `generate_dual_axes_chart` for two different scales.
- **Comparisons**: Use `generate_bar_chart` (categorical) or `generate_column_chart`. Use `generate_histogram_chart` for frequency distributions.
- **Part-to-Whole**: Use `generate_pie_chart` or `generate_treemap_chart` (hierarchical).
- **Relationships & Flow**: Use `generate_scatter_chart` (correlation), `generate_sankey_chart` (flow), or `generate_venn_chart` (overlap).
- **Maps**: Use `generate_district_map` (regions), `generate_pin_map` (points), or `generate_path_map` (routes).
- **Hierarchies & Trees**: Use `generate_organization_chart` or `generate_mind_map`.
- **Specialized**:
    - `generate_radar_chart`: Multi-dimensional comparison.
    - `generate_funnel_chart`: Process stages.
    - `generate_liquid_chart`: Percentage/Progress.
    - `generate_word_cloud_chart`: Text frequency.
    - `generate_boxplot_chart` or `generate_violin_chart`: Statistical distribution.
    - `generate_network_graph`: Complex node-edge relationships.
    - `generate_fishbone_diagram`: Cause-effect analysis.
    - `generate_flow_diagram`: Process flow.
    - `generate_spreadsheet`: Tabular data or pivot tables for structured data display and cross-tabulation.

### 4. Parameter Extraction
Once a chart type is selected, read the corresponding file in the `references/` directory (e.g., `references/generate_line_chart.md`) to identify the required and optional fields.
Extract the data from the user's input and map it to the expected `args` format.

### 5. Build a Validated Chart Spec
Before running the generator, create a chart spec with this structure:

```json
{
  "tool": "generate_chart_type_name",
  "args": {
    "data": [],
    "title": "",
    "theme": "default",
    "style": {},
    "axisXTitle": "",
    "axisYTitle": ""
  },
  "intent": {
    "data_story": "trend",
    "reason_for_choice": "Line chart fits sequential time-based change.",
    "source_summary": "Derived from monthly revenue totals grouped from Orders table.",
    "validation_notes": [
      "x field is temporal",
      "y field is numeric",
      "title matches metric and grain"
    ]
  }
}
```

Rules:
- `intent.data_story` must agree with the selected chart type.
- `intent.reason_for_choice` must explain why this chart is a better fit than obvious alternatives.
- `intent.source_summary` must say where the plotted data came from.
- `intent.validation_notes` must explicitly mention the key field checks you performed.

### 6. Validate Before Generation
Do not call `generate.js` until these checks are true:

- The selected chart type matches the requested story.
- Required fields for that chart type exist in every row.
- Numeric fields are actually numeric.
- Axis titles or labels are present for charts that use axes.
- Pie charts use 6 slices or fewer, or you aggregated a remainder bucket.
- Bar/column charts do not imply a misleading truncated scale.
- Titles describe the takeaway or exact metric, not a vague topic label.

If any check fails, revise the spec or ask for clarification instead of generating a wrong chart.

### 7. Chart Generation
Invoke the `scripts/generate.js` script with a JSON payload.

**Payload Format:**
```json
{
  "tool": "generate_chart_type_name",
  "args": {
    "data": [...],
    "title": "...",
    "theme": "...",
    "style": { ... }
  }
}
```

**Execution Command:**
```bash
node ./scripts/generate.js '<payload_json>'
```

### 8. Result Return
The script will output the URL of the generated chart image.
Return the following to the user:
- The image URL.
- The complete validated spec used for generation.
- A one-paragraph explanation of why this chart type was chosen.

## Reference Material
Detailed specifications for each chart type are located in the `references/` directory. Consult these files to ensure the `args` passed to the script match the expected schema.

## Color Palettes & Presets

### Professional Color Palettes
Read `references/color_palettes.json` for 12 pre-built professional palettes. Select a palette that matches the audience and context:
- **business-blue**: Corporate reports, dashboards
- **tech-vibrant**: SaaS products, startup pitches
- **medical-clinical**: Healthcare, clinical data
- **nature-earth**: Sustainability, environmental data
- **accessible-high-contrast**: Public-facing, accessibility-critical
- **categorical-distinct**: Multi-series comparisons (colorblind-safe)
- **dark-mode**: Dark dashboards, monitoring

Usage: Pass the palette's `colors` array directly as `style.palette` in the chart args.

### Chart Presets
Read `references/chart_presets.json` for 5 scenario presets with recommended chart types, styles, and guidelines:
- **executive-dashboard**: KPI charts for executives
- **technical-report**: Detailed charts for engineering teams
- **marketing-report**: Engaging charts for growth metrics
- **financial-analysis**: Conservative charts for financial data
- **dark-dashboard**: Dark-themed monitoring charts

Usage: Use the preset's `style` object as a starting point for your chart configuration.

## Quality Standards (Mandatory)

### Before Generation — Clarify Requirements
If ANY of the following are unclear, call `ask_clarification` BEFORE generating:
- What story should the chart tell? (trend, comparison, distribution, composition)
- Who is the audience? (executive summary vs. technical detail)
- Are there brand colors or style preferences?
- What is the output context? (report, dashboard, presentation slide)
- What exact fields or numbers should be plotted?

### Chart Design Checklist
Apply these rules when selecting chart type and configuring `args`:

1. **Data integrity**: Never truncate Y-axis without explicit justification. Start at 0 for bar/column charts. Never fabricate missing quantitative data.
2. **Chart type fit**: Time series → line/area. Comparison → bar/column. Part-to-whole → pie (≤6 slices) or treemap. Distribution → histogram/boxplot/violin. Correlation → scatter.
3. **Avoid anti-patterns**: No 3D charts. No pie charts with >6 slices. No dual Y-axis without clear labeling. No chartjunk (unnecessary gridlines, decorations, borders).
4. **Color**: Max 5 colors. Use hex codes in `style.color`. Ensure color-blind safe palette (avoid red-green only encoding).
5. **Labels**: Add `title`. Include data labels for key values. Annotate anomalies or inflection points. Axis-based charts must include axis titles unless the meaning is already explicit in the rendered labels.
6. **Readability**: Font size ≥12pt for labels, ≥16pt for title. Sufficient contrast against background.

### After Generation — Self-Review
Before returning the chart to the user, verify:
- [ ] Chart type matches the data story (not just "looks nice")
- [ ] The plotted fields match the user's requested metric/category/time grain
- [ ] All axes are labeled with units
- [ ] Color palette is harmonious and accessible
- [ ] No misleading visual encoding (area ≠ value distortion)
- [ ] Title clearly states the insight, not just the topic

If any check fails, adjust `args` and regenerate.

## License

This `SKILL.md` is provided by [antvis/chart-visualization-skills](https://github.com/antvis/chart-visualization-skills).
Licensed under the [MIT License](https://github.com/antvis/chart-visualization-skills/blob/master/LICENSE).
