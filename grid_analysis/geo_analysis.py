"""
Task 2.2: Geographic and Geospatial Analysis
Step 2-3: Load data, join coordinates onto lines, verify distances.

Adjust the column names below if your generated CSVs use slightly
different headers than the brief's schema (print(df.columns) to check).
"""

import pandas as pd
from geopy.distance import geodesic

# ---------------------------------------------------------------
# Step 2: Load and prepare the data
# ---------------------------------------------------------------

substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")

print("Substations columns:", list(substations.columns))
print("Lines columns:", list(lines.columns))
print(f"\nLoaded {len(substations)} substations and {len(lines)} lines")

# Keep only the columns we need from substations for the join,
# and rename them so we can merge twice (once for source, once for dest)
# without column-name collisions.
sub_coords = substations[["Substation ID", "Latitude", "Longitude", "Region"]]

# Join source substation coordinates
lines = lines.merge(
    sub_coords.rename(columns={
        "Substation ID": "Source Substation ID",
        "Latitude": "Source Latitude",
        "Longitude": "Source Longitude",
        "Region": "Source Region",
    }),
    on="Source Substation ID",
    how="left",
)

# Join destination substation coordinates
lines = lines.merge(
    sub_coords.rename(columns={
        "Substation ID": "Destination Substation ID",
        "Latitude": "Destination Latitude",
        "Longitude": "Destination Longitude",
        "Region": "Destination Region",
    }),
    on="Destination Substation ID",
    how="left",
)

# Sanity check: did every line find both endpoints?
missing = lines[
    lines["Source Latitude"].isna() | lines["Destination Latitude"].isna()
]
if len(missing) > 0:
    print(f"\nWARNING: {len(missing)} lines are missing endpoint coordinates:")
    print(missing[["Line ID", "Source Substation ID", "Destination Substation ID"]])
else:
    print("\nAll lines successfully matched to substation coordinates.")

# ---------------------------------------------------------------
# Step 3: Recompute and verify line distances
# ---------------------------------------------------------------

def compute_geodesic_km(row):
    src = (row["Source Latitude"], row["Source Longitude"])
    dst = (row["Destination Latitude"], row["Destination Longitude"])
    return geodesic(src, dst).km

lines["Computed Length (km)"] = lines.apply(compute_geodesic_km, axis=1)

# Compare computed distance to the dataset's own Length (km) column
lines["Length Diff (km)"] = (
    lines["Computed Length (km)"] - lines["Length (km)"]
).abs()

print("\nDistance verification summary:")
print(lines[["Length (km)", "Computed Length (km)", "Length Diff (km)"]].describe())

# Flag lines where computed vs stated length disagree by more than 5 km
# (adjust this threshold based on what you see in your own data)
discrepancies = lines[lines["Length Diff (km)"] > 5]
print(f"\n{len(discrepancies)} lines have a length discrepancy > 5km:")
print(discrepancies[["Line ID", "Length (km)", "Computed Length (km)", "Length Diff (km)"]])

# Save the enriched lines dataframe for use in later steps (density,
# clustering, mapping)
lines.to_csv("lines_with_coords.csv", index=False)
print("\nSaved enriched dataset to lines_with_coords.csv")