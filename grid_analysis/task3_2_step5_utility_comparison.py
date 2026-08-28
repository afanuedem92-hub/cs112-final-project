"""
Task 3.2: Advanced Visualizations and Insights
Step 5: Comparative charts for utility infrastructure footprints.

Note: only lines.csv has a Utility ID (substations aren't tied to a
single utility in this dataset), so utility footprint is measured
through each utility's line network.

Produces utility_comparison.html (interactive Plotly bar charts).
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

utilities = pd.read_csv("utilities.csv")
lines = pd.read_csv("lines_with_coords.csv")

GHANA_REGIONS = {
    "Greater Accra", "Ashanti", "Western", "Central", "Eastern",
    "Volta", "Bono", "Northern", "Upper East", "Upper West",
}

def is_wapp(region):
    return region not in GHANA_REGIONS

lines["Touches WAPP"] = lines["Source Region"].apply(is_wapp) | lines["Destination Region"].apply(is_wapp)

# ---------------------------------------------------------------
# Build per-utility summary stats
# ---------------------------------------------------------------
summary_rows = []
for _, util in utilities.iterrows():
    util_id = util["Utility ID"]
    util_lines = lines[lines["Utility ID"] == util_id]

    regions_touched = set(util_lines["Source Region"]).union(set(util_lines["Destination Region"]))

    summary_rows.append({
        "Utility": util["Name"],
        "Line Count": len(util_lines),
        "Total Length (km)": util_lines["Length (km)"].sum(),
        "Avg Line Length (km)": util_lines["Length (km)"].mean() if len(util_lines) else 0,
        "Total Line Capacity (MVA)": util_lines["Capacity (MVA)"].sum(),
        "Regions Touched": len(regions_touched),
        "WAPP Connections": util_lines["Touches WAPP"].sum(),
    })

summary = pd.DataFrame(summary_rows)
print(summary.to_string(index=False))
summary.to_csv("utility_comparison_summary.csv", index=False)

# ---------------------------------------------------------------
# Build a 2x2 comparative chart grid
# ---------------------------------------------------------------
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Line Count by Utility",
        "Total Line Capacity (MVA)",
        "Regions Touched",
        "WAPP Cross-Border Connections",
    ),
)

fig.add_trace(go.Bar(x=summary["Utility"], y=summary["Line Count"], marker_color="steelblue"), row=1, col=1)
fig.add_trace(go.Bar(x=summary["Utility"], y=summary["Total Line Capacity (MVA)"], marker_color="darkorange"), row=1, col=2)
fig.add_trace(go.Bar(x=summary["Utility"], y=summary["Regions Touched"], marker_color="seagreen"), row=2, col=1)
fig.add_trace(go.Bar(x=summary["Utility"], y=summary["WAPP Connections"], marker_color="firebrick"), row=2, col=2)

fig.update_layout(
    title_text="Utility Infrastructure Footprint Comparison",
    height=800,
    showlegend=False,
)

fig.write_html("utility_comparison.html")
print("\nSaved: utility_comparison.html")
print("Saved: utility_comparison_summary.csv")