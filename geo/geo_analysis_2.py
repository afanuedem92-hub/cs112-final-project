"""
Task 2.2: Geographic and Geospatial Analysis
Step 4-5: Substation density by region + distance categorization.

Run this after geo_analysis.py has produced lines_with_coords.csv.
"""

import pandas as pd
import matplotlib.pyplot as plt

substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines_with_coords.csv")

# ---------------------------------------------------------------
# Step 4: Substation density by region
# ---------------------------------------------------------------

# The 10 actual Ghanaian administrative regions in this dataset.
# Everything else in the Region column (foreign country names and
# "<Country> border" labels) is a WAPP cross-border interconnection
# point, not a domestic service region — it must be analyzed
# separately, not folded into the "underserved regions" comparison.
GHANA_REGIONS = [
    "Greater Accra", "Ashanti", "Western", "Central", "Eastern",
    "Volta", "Bono", "Northern", "Upper East", "Upper West",
]

substations["Node Type"] = substations["Region"].apply(
    lambda r: "Domestic" if r in GHANA_REGIONS else "WAPP Cross-Border"
)

domestic = substations[substations["Node Type"] == "Domestic"]
cross_border = substations[substations["Node Type"] == "WAPP Cross-Border"]

density = (
    domestic.groupby("Region")
    .agg(
        Substation_Count=("Substation ID", "count"),
        Total_Capacity_MVA=("Capacity (MVA)", "sum"),
        Avg_Voltage_kV=("Voltage (kV)", "mean"),
    )
    .sort_values("Substation_Count", ascending=False)
)

print("=== Substation Density by Region (Domestic Ghana only) ===")
print(density)
density.to_csv("substation_density_by_region.csv")

print("\n=== WAPP Cross-Border Interconnection Points ===")
print(cross_border[["Name", "Region", "Voltage (kV)", "Capacity (MVA)"]])
cross_border.to_csv("wapp_cross_border_points.csv", index=False)

# Quick bar chart for your regional analysis report (domestic only)
plt.figure(figsize=(9, 5))
density["Substation_Count"].plot(kind="bar", color="steelblue")
plt.title("Substation Count by Ghana Region (Domestic)")
plt.ylabel("Number of Substations")
plt.xlabel("Region")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("substation_density_by_region.png", dpi=150)
plt.close()
print("\nSaved chart: substation_density_by_region.png")

# Flag domestic regions with the fewest substations relative to the
# rest — a starting point for your "Geographic Gaps" writeup. Adjust
# the threshold once you've looked at the actual spread of counts.
median_count = density["Substation_Count"].median()
underserved = density[density["Substation_Count"] < median_count]
print(f"\nDomestic regions below median substation count ({median_count}):")
print(underserved[["Substation_Count"]])

# ---------------------------------------------------------------
# Step 5: Categorize line distances (short / medium / long)
# ---------------------------------------------------------------

# Using the ORIGINAL "Length (km)" column (the dataset's stated
# length), since that represents actual cable routing distance,
# not straight-line geodesic distance. Thresholds below are a
# starting point — adjust based on what you see in your data and
# say why in your report.
def categorize_length(km):
    if km < 50:
        return "Short"
    elif km < 150:
        return "Medium"
    else:
        return "Long"

lines["Distance Category"] = lines["Length (km)"].apply(categorize_length)

category_counts = lines["Distance Category"].value_counts()
print("\n=== Line Distance Categories ===")
print(category_counts)

# Does distance category vary by voltage level? (higher voltage
# lines tend to be longer, transmission-style runs)
category_by_voltage = pd.crosstab(lines["Voltage (kV)"], lines["Distance Category"])
print("\n=== Distance Category by Voltage Level ===")
print(category_by_voltage)

lines.to_csv("lines_with_coords.csv", index=False)  # re-save with new column

# Chart: distribution of line lengths, colored by category
plt.figure(figsize=(9, 5))
colors = {"Short": "seagreen", "Medium": "goldenrod", "Long": "firebrick"}
for cat, group in lines.groupby("Distance Category"):
    plt.hist(group["Length (km)"], bins=15, alpha=0.7, label=cat, color=colors[cat])
plt.title("Distribution of Line Lengths by Category")
plt.xlabel("Length (km)")
plt.ylabel("Number of Lines")
plt.legend(title="Category")
plt.tight_layout()
plt.savefig("distance_distribution.png", dpi=150)
plt.close()
print("\nSaved chart: distance_distribution.png")