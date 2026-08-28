"""
Task 3.2: Advanced Visualizations and Insights
Step 2: 3D network visualization.

Produces grid_network_3d.html — substations positioned by real
latitude/longitude (x/y) with voltage level giving height (z), so
higher-voltage substations visually rise above the network. Lines
connect substations in 3D space.
"""

import pandas as pd
import plotly.graph_objects as go

substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines_with_coords.csv")

# ---------------------------------------------------------------
# Height (z-axis) = voltage level. Scaled down so the map doesn't
# look absurdly tall relative to its lat/lon spread.
# ---------------------------------------------------------------
substations["z"] = substations["Voltage (kV)"] / 20

VOLTAGE_COLORS = {
    11: "#2ca02c", 33: "#98df8a", 69: "#ffdd57",
    161: "#ff7f0e", 330: "#d62728",
}
substations["color"] = substations["Voltage (kV)"].map(VOLTAGE_COLORS).fillna("#808080")

# ---------------------------------------------------------------
# Build 3D line traces (one trace per line, since each needs its
# own pair of endpoints — Plotly doesn't support per-segment 3D
# lines in a single trace the way 2D scatter does)
# ---------------------------------------------------------------
line_traces = []
for _, row in lines.iterrows():
    z_src = row["Voltage (kV)"] / 20
    z_dst = row["Voltage (kV)"] / 20
    line_traces.append(
        go.Scatter3d(
            x=[row["Source Longitude"], row["Destination Longitude"]],
            y=[row["Source Latitude"], row["Destination Latitude"]],
            z=[z_src, z_dst],
            mode="lines",
            line=dict(color="rgba(120,120,120,0.5)", width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# ---------------------------------------------------------------
# Substation nodes
# ---------------------------------------------------------------
node_trace = go.Scatter3d(
    x=substations["Longitude"],
    y=substations["Latitude"],
    z=substations["z"],
    mode="markers",
    marker=dict(
        size=substations["Capacity (MVA)"] / 40 + 4,
        color=substations["color"],
        line=dict(color="white", width=0.5),
    ),
    text=substations.apply(
        lambda r: f"{r['Name']}<br>{r['Region']}<br>{r['Voltage (kV)']} kV, {r['Capacity (MVA)']} MVA",
        axis=1,
    ),
    hoverinfo="text",
    showlegend=False,
)

fig = go.Figure(data=line_traces + [node_trace])

fig.update_layout(
    title="3D Grid Network (height = voltage level)",
    scene=dict(
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        zaxis_title="Voltage (scaled)",
    ),
    height=750,
    margin=dict(r=0, t=40, l=0, b=0),
)

fig.write_html("grid_network_3d.html")
print("Saved: grid_network_3d.html")