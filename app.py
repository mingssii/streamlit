import streamlit as st
import pandas as pd
import pydeck as pdk
import networkx as nx
import plotly.express as px
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

# Load data
universities = pd.read_csv("universities_mock.csv")
references = pd.read_csv("references_mock.csv")

# Build the network graph
G = nx.from_pandas_edgelist(
    references,
    source="source_id",
    target="target_id",
    edge_attr="weight"
)

# Add node attributes
for _, row in universities.iterrows():
    nx.set_node_attributes(G, {
        row["id"]: {
            "name": row["name"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "research_count": row["research_count"],
            "importance": row["importance"],
        }
    })

# Network Analysis
def calculate_centralities(G):
    return {
        "Degree Centrality": nx.degree_centrality(G),
        "Betweenness Centrality": nx.betweenness_centrality(G),
        "Closeness Centrality": nx.closeness_centrality(G),
        "PageRank": nx.pagerank(G),
    }

# 3D Visualization with Pydeck
def create_3d_globe_view(universities, references):
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=universities,
        get_position=["longitude", "latitude"],
        get_radius="importance * 20000",
        get_fill_color=[0, 102, 255, 150],
    )

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=references.merge(universities, left_on="source_id", right_on="id").merge(
            universities, left_on="target_id", right_on="id", suffixes=("_source", "_target")
        ),
        get_source_position=["longitude_source", "latitude_source"],
        get_target_position=["longitude_target", "latitude_target"],
        get_width="weight * 0.5",
        get_source_color=[255, 69, 0, 120],
        get_target_color=[50, 205, 50, 120],
    )

    view_state = pdk.ViewState(latitude=0, longitude=0, zoom=1, pitch=45)

    return pdk.Deck(
        layers=[scatter_layer, arc_layer],
        initial_view_state=view_state,
        tooltip={"html": "<b>{name}</b><br>Research Count: {research_count}"},
    )

# 2D Visualization with Folium
def create_2d_map_view(universities, references):
    map_2d = folium.Map(location=[0, 0], zoom_start=2)

    # Add universities as markers
    for _, row in universities.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=row["importance"] * 5,  # Reduced scaling factor
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.6,
            popup=folium.Popup(f"<b>{row['name']}</b><br>Research Count: {row['research_count']}", max_width=200),
        ).add_to(map_2d)

    # Add references as lines
    for _, row in references.iterrows():
        source = universities[universities["id"] == row["source_id"]].iloc[0]
        target = universities[universities["id"] == row["target_id"]].iloc[0]
        folium.PolyLine(
            locations=[
                [source["latitude"], source["longitude"]],
                [target["latitude"], target["longitude"]],
            ],
            color="orange",
            weight=row["weight"] * 0.5,
            opacity=0.6,
        ).add_to(map_2d)

    return map_2d

# 3D Realistic Globe Visualization with Plotly
def create_realistic_globe_view(universities, references):
    fig = px.scatter_geo(
        universities,
        lat="latitude",
        lon="longitude",
        text="name",
        size="importance",
        size_max=15,
        color="research_count",
        color_continuous_scale="Plasma",
    )
    fig.update_geos(
        projection_type="orthographic",  # Use orthographic projection for a realistic globe
        showcountries=True,
        showcoastlines=True,
        showland=True,
        landcolor="lightgray",
        oceancolor="lightblue",
        showocean=True,
    )
    
    # Add arcs for connections
    for _, row in references.iterrows():
        source = universities[universities["id"] == row["source_id"]].iloc[0]
        target = universities[universities["id"] == row["target_id"]].iloc[0]
        fig.add_trace(
            go.Scattergeo(
                lat=[source["latitude"], target["latitude"]],
                lon=[source["longitude"], target["longitude"]],
                mode="lines",
                line=dict(width=row["weight"] * 0.5, color="orange"),
                opacity=0.6,
            )
        )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        title="3D Realistic Globe of Universities",
    )
    return fig


# Streamlit UI
st.title("University Network Analysis")
st.sidebar.header("Analysis Options")


analysis_tab, visualization_tab = st.tabs(["Analysis", "Visualization"])

# Map view selection
view_option = st.sidebar.radio("Choose Map View", ["3D Globe (Pydeck)", "2D Map", "3D Realistic Globe"])

# Visualization Tab
with visualization_tab:
    if view_option == "3D Globe (Pydeck)":
        st.pydeck_chart(create_3d_globe_view(universities, references))
    elif view_option == "2D Map":
        folium_map = create_2d_map_view(universities, references)
        st_folium(folium_map, width=800, height=600)
    elif view_option == "3D Realistic Globe":
        st.plotly_chart(create_realistic_globe_view(universities, references), use_container_width=True)

