import pandas as pd
import networkx as nx

print("Loading grid data for final contingency analysis...")
substations_df = pd.read_csv("Datasets 1/substations.csv")
lines_df = pd.read_csv("Datasets 1/lines.csv")

# Build base graph network
G = nx.Graph()
for _, row in substations_df.iterrows():
    G.add_node(row["Substation ID"], name=row["Name"])

for _, row in lines_df.iterrows():
    G.add_edge(row["Source Substation ID"], row["Destination Substation ID"])

initial_components = nx.number_connected_components(G)

print("\nRunning N-1 Contingency Failure Simulation...")
critical_failures = []
for node in G.nodes():
    sub_name = G.nodes[node]['name']
    G_test = G.copy()
    G_test.remove_node(node)
    
    # Check if removing this substation splits the network into disconnected pieces
    if nx.number_connected_components(G_test) > initial_components:
        critical_failures.append(sub_name)

print(f"\nSimulation Complete:")
print(f"- Total Substations Tested: {len(G.nodes())}")
print(f"- Critical Vulnerability Points Found: {len(critical_failures)}")

if critical_failures:
    print("\nTop Vulnerable Substations (Single Point of Failure):")
    for name in critical_failures[:3]:
        print(f"  * {name}")

print("\nFinal project analysis script completed successfully!")