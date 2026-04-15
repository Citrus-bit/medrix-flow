---
name: chart-visualization
description: This skill should be used when the user wants to visualize data. It intelligently selects the most suitable chart type from 26 available options, extracts parameters based on detailed specifications, and generates a chart image using a JavaScript script.
dependency:
  nodejs: ">=18.0.0"
---

# Chart Visualization Skill

This skill provides a comprehensive workflow for transforming data into visual charts. It handles chart selection, parameter extraction, and image generation.

## Workflow

To visualize data, follow these steps:

### 1. Intelligent Chart Selection
Analyze the user's data features to determine the most appropriate chart type. Use the following guidelines (and consult `references/` for detailed specs):

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

### 2. Parameter Extraction
Once a chart type is selected, read the corresponding file in the `references/` directory (e.g., `references/generate_line_chart.md`) to identify the required and optional fields.
Extract the data from the user's input and map it to the expected `args` format.

### 3. Chart Generation
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

### 4. Result Return
The script will output the URL of the generated chart image.
Return the following to the user:
- The image URL.
- The complete `args` (specification) used for generation.

## Reference Material
Detailed specifications for each chart type are located in the `references/` directory. Consult these files to ensure the `args` passed to the script match the expected schema.

## Quality Standards (Mandatory)

### Before Generation — Clarify Requirements
If ANY of the following are unclear, call `ask_clarification` BEFORE generating:
- What story should the chart tell? (trend, comparison, distribution, composition)
- Who is the audience? (executive summary vs. technical detail)
- Are there brand colors or style preferences?
- What is the output context? (report, dashboard, presentation slide)

### Chart Design Checklist
Apply these rules when selecting chart type and configuring `args`:

1. **Data integrity**: Never truncate Y-axis without explicit justification. Start at 0 for bar/column charts.
2. **Chart type fit**: Time series → line/area. Comparison → bar/column. Part-to-whole → pie (≤6 slices) or treemap. Distribution → histogram/boxplot/violin. Correlation → scatter.
3. **Avoid anti-patterns**: No 3D charts. No pie charts with >6 slices. No dual Y-axis without clear labeling. No chartjunk (unnecessary gridlines, decorations, borders).
4. **Color**: Max 5 colors. Use hex codes in `style.color`. Ensure color-blind safe palette (avoid red-green only encoding).
5. **Labels**: Add `title`. Include data labels for key values. Annotate anomalies or inflection points.
6. **Readability**: Font size ≥12pt for labels, ≥16pt for title. Sufficient contrast against background.

### After Generation — Self-Review
Before returning the chart to the user, verify:
- [ ] Chart type matches the data story (not just "looks nice")
- [ ] All axes are labeled with units
- [ ] Color palette is harmonious and accessible
- [ ] No misleading visual encoding (area ≠ value distortion)
- [ ] Title clearly states the insight, not just the topic

If any check fails, adjust `args` and regenerate.

## License

This `SKILL.md` is provided by [antvis/chart-visualization-skills](https://github.com/antvis/chart-visualization-skills).
Licensed under the [MIT License](https://github.com/antvis/chart-visualization-skills/blob/master/LICENSE).