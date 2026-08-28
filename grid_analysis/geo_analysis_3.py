"""
Task 2.2: Geographic and Geospatial Analysis
Step 6: Substation clustering (geographic clusters of high-capacity substations)

Uses DBSCAN with haversine distance so clustering is based on real
geographic proximity (km), not raw lat/lon numbers.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

substations = pd.read_csv("substations.csv")

# ---------------------------------------------------------------
# Define "high-capacity" — top 25% by Capacity (MVA).
# Adjust this cutoff if it gives you too few/many substations to
# say anything meaningful about.
# ---------------------------------------------------------------
capacity_threshold = substations["Capacity (MVA)"].quantile(0.75)
high_cap = substations[substations["Capacity (MVA)"] >= capacity_threshold].copy()

print(f"High-capacity threshold (75th percentile): {capacity_threshold:.1f} MVA")
print(f"{len(high_cap)} substations qualify as high-capacity\n")

# ---------------------------------------------------------------
# DBSCAN clustering using haversine distance.
# eps is the maximum distance (in km) between two points for them
# to be considered neighbors — convert to radians for haversine.
# min_samples=2 means a "cluster" needs at least 2 nearby substations.
# ---------------------------------------------------------------
EPS_KM = 60  # try adjusting this — smaller = tighter clusters
kms_per_radian = 6371.0088

coords = np.radians(high_cap[["Latitude", "Longitude"]].values)
db = DBSCAN(eps=EPS_KM / kms_per_radian, min_samples=2, metric="haversine")
high_cap["Cluster"] = db.fit_predict(coords)

# DBSCAN labels noise points (not part of any cluster) as -1
n_clusters = len(set(high_cap["Cluster"])) - (1 if -1 in high_cap["Cluster"].values else 0)
n_noise = (high_cap["Cluster"] == -1).sum()

print(f"Found {n_clusters} geographic cluster(s) of high-capacity substations")
print(f"{n_noise} high-capacity substations are geographically isolated (no nearby peers)\n")

for cluster_id in sorted(high_cap["Cluster"].unique()):
    members = high_cap[high_cap["Cluster"] == cluster_id]
    label = "Isolated (noise)" if cluster_id == -1 else f"Cluster {cluster_id}"
    print(f"--- {label} ---")
    print(members[["Name", "Region", "Capacity (MVA)", "Latitude", "Longitude"]].to_string(index=False))
    print()

high_cap.to_csv("high_capacity_clusters.csv", index=False)

# ---------------------------------------------------------------
# Visualize: scatter plot of all substations, with high-capacity
# ones colored by cluster
# ---------------------------------------------------------------
plt.figure(figsize=(8, 9))

# All substations as light background context
plt.scatter(
    substations["Longitude"], substations["Latitude"],
    c="lightgray", s=30, label="Other substations"
)

# High-capacity substations colored by cluster (noise = black)
cmap = plt.get_cmap("tab10")
for cluster_id in sorted(high_cap["Cluster"].unique()):
    members = high_cap[high_cap["Cluster"] == cluster_id]
    color = "black" if cluster_id == -1 else cmap(cluster_id % 10)
    label = "Isolated" if cluster_id == -1 else f"Cluster {cluster_id}"
    plt.scatter(
        members["Longitude"], members["Latitude"],
        c=[color], s=100, edgecolors="white", linewidths=1, label=label
    )

plt.title("Geographic Clusters of High-Capacity Substations")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.legend(loc="upper left", fontsize=8)
plt.tight_layout()
plt.savefig("substation_clustering.png", dpi=150)
plt.close()
print("Saved chart: substation_clustering.png")