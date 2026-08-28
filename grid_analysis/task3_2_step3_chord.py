"""
Task 3.2: Advanced Visualizations and Insights
Step 3: Chord diagram showing power-line connections between regions
(including WAPP cross-border connections).

Produces region_chord_diagram.png — a circular diagram where arcs
connect regions, and arc thickness reflects how many lines run
between them.

Needs: pip install mpl_chord_diagram
"""

import pandas as pd
import matplotlib.pyplot as plt
from mpl_chord_diagram import chord_diagram

lines = pd.read_csv("lines_with_coords.csv")

# ---------------------------------------------------------------
# Build a region-to-region connection count.
# Uses Source Region / Destination Region (added back in
# geo_analysis.py's merge step). Undirected: A-B and B-A are the
# same connection, so we sort each pair before counting.
# ---------------------------------------------------------------
def sorted_pair(row):
    a, b = row["Source Region"], row["Destination Region"]
    return tuple(sorted([a, b]))

lines["Region Pair"] = lines.apply(sorted_pair, axis=1)

pair_counts = lines["Region Pair"].value_counts()
print("Connections between region pairs:")
print(pair_counts)

# ---------------------------------------------------------------
# Build the square matrix the chord library expects: one row/column
# per region, cell = number of lines connecting that pair.
# ---------------------------------------------------------------
all_regions = sorted(
    set(lines["Source Region"]).union(set(lines["Destination Region"]))
)

matrix = pd.DataFrame(0, index=all_regions, columns=all_regions)

for (region_a, region_b), count in pair_counts.items():
    matrix.loc[region_a, region_b] += count
    if region_a != region_b:
        matrix.loc[region_b, region_a] += count

print(f"\n{len(all_regions)} regions/nodes included (domestic + WAPP cross-border)")

# ---------------------------------------------------------------
# Render the chord diagram
# ---------------------------------------------------------------
fig = plt.figure(figsize=(10, 10))
chord_diagram(matrix.values, all_regions, fontsize=8, rotate_names=True)
plt.title("Inter-Regional Grid Connections (including WAPP)", fontsize=14, pad=20)
plt.savefig("region_chord_diagram.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: region_chord_diagram.png")