"""
Task 3.2: Advanced Visualizations and Insights
Step 1: Animated map showing grid expansion by Commissioning Year.

Produces grid_growth_animation.html — open in a browser and press
play to watch substations appear over time.
"""

import pandas as pd
import plotly.express as px

substations = pd.read_csv("substations.csv")

# Make sure Commissioning Year is a clean integer/string for sorting
substations = substations.dropna(subset=["Commissioning Year"])
substations["Commissioning Year"] = substations["Commissioning Year"].astype(int)

print(f"Year range: {substations['Commissioning Year'].min()} - {substations['Commissioning Year'].max()}")
print(f"{len(substations)} substations have a commissioning year")

# ---------------------------------------------------------------
# Build a cumulative dataset: for each year shown in the animation,
# include every substation commissioned in or before that year.
# This makes the map "fill in" and stay filled, rather than showing
# only that year's substations and then going blank.
# ---------------------------------------------------------------
years = sorted(substations["Commissioning Year"].unique())

frames = []
for year in years:
    snapshot = substations[substations["Commissioning Year"] <= year].copy()
    snapshot["Animation Year"] = year
    frames.append(snapshot)

cumulative_df = pd.concat(frames, ignore_index=True)

# ---------------------------------------------------------------
# Animated scatter map
# ---------------------------------------------------------------
fig = px.scatter_mapbox(
    cumulative_df,
    lat="Latitude",
    lon="Longitude",
    color="Voltage (kV)",
    size="Capacity (MVA)",
    hover_name="Name",
    hover_data={"Region": True, "Commissioning Year": True, "Latitude": False, "Longitude": False},
    animation_frame="Animation Year",
    color_continuous_scale="YlOrRd",
    zoom=5.2,
    center={"lat": 7.9, "lon": -1.0},
    mapbox_style="carto-positron",
    title="Grid Expansion by Commissioning Year",
    height=700,
)

fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})

fig.write_html("grid_growth_animation.html")
print("Saved: grid_growth_animation.html")