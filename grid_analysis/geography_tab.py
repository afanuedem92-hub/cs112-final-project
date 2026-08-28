"""
Task 3.1: Comprehensive Dashboard — Geography Tab
Owned by: Member 3 (Visualization Specialist)

This file is written as a standalone Streamlit app so you can build
and test it independently. It also exposes render_geography_tab()
as a function, so Member 4 can import and call it inside one tab of
the shared multi-tab dashboard once everyone's pieces are ready:

    from geography_tab import render_geography_tab
    with tab_geography:
        render_geography_tab(substations, lines, utilities)

Run standalone with:
    streamlit run geography_tab.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

GHANA_REGIONS = [
    "Greater Accra", "Ashanti", "Western", "Central", "Eastern",
    "Volta", "Bono", "Northern", "Upper East", "Upper West",
]

VOLTAGE_COLORS = {
    11: "#2ca02c", 33: "#98df8a", 69: "#ffdd57",
    161: "#ff7f0e", 330: "#d62728",
}


def voltage_color(v):
    return VOLTAGE_COLORS.get(v, "#808080")


def render_geography_tab(substations: pd.DataFrame, lines: pd.DataFrame, utilities: pd.DataFrame):
    """Renders the full Geography tab into whatever container it's
    called inside (a Streamlit tab, column, or the main page)."""

    st.subheader("Geography")
    st.caption("National grid map with region, voltage, and utility filters.")

    # -----------------------------------------------------------
    # Filters (sidebar-style controls, but placed inline so they
    # work correctly even when this is embedded inside a tab)
    # -----------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        all_regions = sorted(substations["Region"].unique())
        selected_regions = st.multiselect(
            "Region", options=all_regions, default=all_regions,
            key="geo_region_filter",
        )

    with col2:
        all_voltages = sorted(substations["Voltage (kV)"].unique())
        selected_voltages = st.multiselect(
            "Voltage (kV)", options=all_voltages, default=all_voltages,
            key="geo_voltage_filter",
        )

    with col3:
        all_utilities = ["All"] + sorted(utilities["Name"].unique())
        selected_utility = st.selectbox(
            "Utility (filters lines only)", options=all_utilities,
            key="geo_utility_filter",
        )

    overlay_cols = st.columns(3)
    with overlay_cols[0]:
        show_lines = st.checkbox("Show transmission lines", value=True, key="geo_show_lines")
    with overlay_cols[1]:
        show_domestic_only = st.checkbox("Domestic regions only (hide WAPP nodes)", value=False, key="geo_domestic_only")
    with overlay_cols[2]:
        size_by_capacity = st.checkbox("Size substations by capacity", value=True, key="geo_size_by_cap")

    # -----------------------------------------------------------
    # Apply filters
    # -----------------------------------------------------------
    filtered_subs = substations[
        substations["Region"].isin(selected_regions)
        & substations["Voltage (kV)"].isin(selected_voltages)
    ].copy()

    if show_domestic_only:
        filtered_subs = filtered_subs[filtered_subs["Region"].isin(GHANA_REGIONS)]

    filtered_lines = lines[
        lines["Source Substation ID"].isin(filtered_subs["Substation ID"])
        | lines["Destination Substation ID"].isin(filtered_subs["Substation ID"])
    ].copy()

    if selected_utility != "All":
        util_id = utilities.loc[utilities["Name"] == selected_utility, "Utility ID"].iloc[0]
        filtered_lines = filtered_lines[filtered_lines["Utility ID"] == util_id]

    # -----------------------------------------------------------
    # Build the map
    # -----------------------------------------------------------
    fig = go.Figure()

    if show_lines:
        for _, row in filtered_lines.iterrows():
            fig.add_trace(go.Scattermapbox(
                lat=[row["Source Latitude"], row["Destination Latitude"]],
                lon=[row["Source Longitude"], row["Destination Longitude"]],
                mode="lines",
                line=dict(width=2, color=voltage_color(row["Voltage (kV)"])),
                hoverinfo="skip",
                showlegend=False,
            ))

    sizes = (
        filtered_subs["Capacity (MVA)"] / 25 + 6
        if size_by_capacity
        else pd.Series([10] * len(filtered_subs))
    )

    fig.add_trace(go.Scattermapbox(
        lat=filtered_subs["Latitude"],
        lon=filtered_subs["Longitude"],
        mode="markers",
        marker=dict(size=sizes, color=[voltage_color(v) for v in filtered_subs["Voltage (kV)"]]),
        text=filtered_subs.apply(
            lambda r: f"{r['Name']}<br>{r['Region']}<br>{r['Voltage (kV)']} kV, {r['Capacity (MVA)']} MVA",
            axis=1,
        ),
        hoverinfo="text",
        showlegend=False,
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": 7.9, "lon": -1.0},
        mapbox_zoom=5.2,
        height=650,
        margin=dict(r=0, t=0, l=0, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------------
    # Quick stats under the map
    # -----------------------------------------------------------
    stat_cols = st.columns(4)
    stat_cols[0].metric("Substations shown", len(filtered_subs))
    stat_cols[1].metric("Lines shown", len(filtered_lines))
    stat_cols[2].metric("Total capacity (MVA)", f"{filtered_subs['Capacity (MVA)'].sum():,.0f}")
    stat_cols[3].metric("Regions represented", filtered_subs["Region"].nunique())


# ---------------------------------------------------------------
# Standalone runner — lets you test this tab on its own before
# Member 4's dashboard shell exists.
# ---------------------------------------------------------------
if __name__ == "__main__":
    st.set_page_config(page_title="Geography Tab (standalone test)", layout="wide")

    substations = pd.read_csv("substations.csv")
    lines = pd.read_csv("lines_with_coords.csv")
    utilities = pd.read_csv("utilities.csv")

    render_geography_tab(substations, lines, utilities)