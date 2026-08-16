"""
Task 2.2: Geographic and Geospatial Analysis
Step 7: Interactive multi-layer Folium map.

Produces grid_map.html with toggleable layers:
  - All substations, colored by voltage level
  - Line-density heatmap
  - One layer per utility, showing only that utility's line network
  - All transmission lines (colored to match their substation voltage)

Run this after geo_analysis.py and geo_analysis_2.py.
"""

import pandas as pd
import folium
from folium.plugins import HeatMap

substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines_with_coords.csv")
utilities = pd.read_csv("utilities.csv")

# ---------------------------------------------------------------
# Color scale for voltage levels (low -> high)
# ---------------------------------------------------------------
VOLTAGE_COLORS = {
    11: "#2ca02c",   # green
    33: "#98df8a",   # light green
    69: "#ffdd57",   # yellow
    161: "#ff7f0e",  # orange
    330: "#d62728",  # red
}

def voltage_color(v):
    return VOLTAGE_COLORS.get(v, "#808080")  # gray fallback for unexpected values

# ---------------------------------------------------------------
# Base map, centered roughly on Ghana
# ---------------------------------------------------------------
m = folium.Map(location=[7.9, -1.0], zoom_start=6, tiles="cartodbpositron")

# ---------------------------------------------------------------
# Layer 1: All substations, colored by voltage, sized by capacity
# ---------------------------------------------------------------
substation_layer = folium.FeatureGroup(name="Substations by Voltage", show=True)

for _, row in substations.iterrows():
    radius = 4 + (row["Capacity (MVA)"] / 200)  # bigger dot = more capacity
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=radius,
        color=voltage_color(row["Voltage (kV)"]),
        fill=True,
        fill_color=voltage_color(row["Voltage (kV)"]),
        fill_opacity=0.85,
        weight=1,
        popup=folium.Popup(
            f"<b>{row['Name']}</b><br>"
            f"Region: {row['Region']}<br>"
            f"Voltage: {row['Voltage (kV)']} kV<br>"
            f"Capacity: {row['Capacity (MVA)']} MVA<br>"
            f"Status: {row['Status']}",
            max_width=250,
        ),
    ).add_to(substation_layer)

substation_layer.add_to(m)

# ---------------------------------------------------------------
# Layer 2: All transmission lines, colored by voltage
# ---------------------------------------------------------------
lines_layer = folium.FeatureGroup(name="All Transmission Lines", show=True)

for _, row in lines.iterrows():
    folium.PolyLine(
        locations=[
            [row["Source Latitude"], row["Source Longitude"]],
            [row["Destination Latitude"], row["Destination Longitude"]],
        ],
        color=voltage_color(row["Voltage (kV)"]),
        weight=2 + row["Voltage (kV)"] / 100,
        opacity=0.7,
        popup=f"{row['Source Substation']} \u2192 {row['Destination Substation']}<br>"
              f"{row['Voltage (kV)']} kV, {row['Length (km)']} km, {row['Status']}",
    ).add_to(lines_layer)

lines_layer.add_to(m)

# ---------------------------------------------------------------
# Layer 3: Line-density heatmap
# Sample points along each line (not just endpoints) so the heatmap
# reflects line density, not just substation locations.
# ---------------------------------------------------------------
heat_points = []
for _, row in lines.iterrows():
    lat1, lon1 = row["Source Latitude"], row["Source Longitude"]
    lat2, lon2 = row["Destination Latitude"], row["Destination Longitude"]
    steps = 10
    for i in range(steps + 1):
        frac = i / steps
        heat_points.append([
            lat1 + (lat2 - lat1) * frac,
            lon1 + (lon2 - lon1) * frac,
        ])

heatmap_layer = folium.FeatureGroup(name="Line Density Heatmap", show=False)
HeatMap(heat_points, radius=15, blur=20).add_to(heatmap_layer)
heatmap_layer.add_to(m)

# ---------------------------------------------------------------
# Layer 4+: One layer per utility, showing only that utility's lines
# ---------------------------------------------------------------
for _, util in utilities.iterrows():
    util_id = util["Utility ID"]
    util_name = util["Name"]
    util_lines = lines[lines["Utility ID"] == util_id]

    if len(util_lines) == 0:
        continue

    util_layer = folium.FeatureGroup(name=f"Utility: {util_name}", show=False)

    for _, row in util_lines.iterrows():
        folium.PolyLine(
            locations=[
                [row["Source Latitude"], row["Source Longitude"]],
                [row["Destination Latitude"], row["Destination Longitude"]],
            ],
            color="#1f77b4",
            weight=3,
            opacity=0.8,
            popup=f"{row['Source Substation']} \u2192 {row['Destination Substation']}",
        ).add_to(util_layer)

    util_layer.add_to(m)

# ---------------------------------------------------------------
# Layer control (lets the viewer toggle each layer on/off)
# ---------------------------------------------------------------
folium.LayerControl(collapsed=False).add_to(m)

m.save("grid_map.html")
print("Saved interactive map: grid_map.html")
print("Open it in a browser to view/toggle layers.")