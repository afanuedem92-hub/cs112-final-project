"""
Task 3.2: Advanced Visualizations and Insights
Step 4: Heatmaps for line density and maintenance-status concentration.

Produces:
  - line_density_heatmap.html
  - maintenance_status_heatmap.html
"""

import pandas as pd
import plotly.express as px

substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines_with_coords.csv")

print("Substation Status values:", substations["Status"].unique())
print("Line Status values:", lines["Status"].unique())

# ---------------------------------------------------------------
# Heatmap 1: Line density
# Sample points along each line so density reflects how much line
# infrastructure runs through an area, not just substation locations.
# ---------------------------------------------------------------
heat_points = []
for _, row in lines.iterrows():
    lat1, lon1 = row["Source Latitude"], row["Source Longitude"]
    lat2, lon2 = row["Destination Latitude"], row["Destination Longitude"]
    steps = 10
    for i in range(steps + 1):
        frac = i / steps
        heat_points.append({
            "lat": lat1 + (lat2 - lat1) * frac,
            "lon": lon1 + (lon2 - lon1) * frac,
        })

heat_df = pd.DataFrame(heat_points)

fig1 = px.density_mapbox(
    heat_df, lat="lat", lon="lon",
    radius=25,
    center={"lat": 7.9, "lon": -1.0}, zoom=5.2,
    mapbox_style="carto-positron",
    title="Line Density Heatmap",
    height=700,
)
fig1.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
fig1.write_html("line_density_heatmap.html")
print("Saved: line_density_heatmap.html")

# ---------------------------------------------------------------
# Heatmap 2: Maintenance-status concentration
# Combines substations AND lines that are NOT in a normal/active
# state, weighting the heatmap so problem areas glow brighter.
# Adjust the "not normal" filter below once you see your actual
# Status values printed above.
# ---------------------------------------------------------------
NORMAL_STATUSES = {"Active", "Operational", "In Service"}  # adjust to match your data

flagged_substations = substations[~substations["Status"].isin(NORMAL_STATUSES)]
flagged_lines = lines[~lines["Status"].isin(NORMAL_STATUSES)]

print(f"\n{len(flagged_substations)} substations flagged as non-normal status")
print(f"{len(flagged_lines)} lines flagged as non-normal status")

maint_points = []
for _, row in flagged_substations.iterrows():
    maint_points.append({"lat": row["Latitude"], "lon": row["Longitude"], "source": "substation"})
for _, row in flagged_lines.iterrows():
    lat1, lon1 = row["Source Latitude"], row["Source Longitude"]
    lat2, lon2 = row["Destination Latitude"], row["Destination Longitude"]
    for frac in [0, 0.5, 1]:
        maint_points.append({
            "lat": lat1 + (lat2 - lat1) * frac,
            "lon": lon1 + (lon2 - lon1) * frac,
            "source": "line",
        })

maint_df = pd.DataFrame(maint_points)

if len(maint_df) == 0:
    print("\nNo non-normal status records found — check NORMAL_STATUSES against "
          "the printed Status values above and adjust the set if needed.")
else:
    fig2 = px.density_mapbox(
        maint_df, lat="lat", lon="lon",
        radius=30,
        center={"lat": 7.9, "lon": -1.0}, zoom=5.2,
        mapbox_style="carto-positron",
        title="Maintenance / Fault Status Concentration",
        height=700,
        color_continuous_scale="Reds",
    )
    fig2.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    fig2.write_html("maintenance_status_heatmap.html")
    print("Saved: maintenance_status_heatmap.html")
    