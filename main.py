import pydeck as pdk
import pandas as pd
import streamlit as st

# โหลดข้อมูล CSV
@st.cache_data
def load_data(path):
    return pd.read_csv(path, encoding="latin1")

path = "colab_count.csv"
edges_with_coords = load_data(path)
# ฟังก์ชันสร้าง ViewState
def update_view_state(lat, lon, zoom, pitch):
    return pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=zoom,
        pitch=pitch,
    )

# ค่าเริ่มต้น
default_lat = 13.74310735  # Chulalongkorn University
default_lon = 100.5328837
default_zoom = 7
default_pitch = 50
default_edge_width = 3


st.header("Visualization Project")
# Tabs
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])
    
with tab1:
        # เพิ่มแถบเมนูด้านซ้าย
    st.sidebar.header("Visualization Settings")

    # เลือกธีมแผนที่
    map_style = st.sidebar.selectbox(
        "Select Map Style",
        ["light", "dark", "satellite", "streets"],
        index=0
    )

    # เลือกรูปแบบ Node Size
    node_size_option = st.sidebar.radio(
        "Select Node Size",
        options=["Small", "Medium", "Big"],
        index=1,  # ค่าเริ่มต้นคือ Medium
    )
    node_size_mapping = {
        "Small": 100,
        "Medium": 5000,
        "Big": 200000
    }
    node_size = node_size_mapping[node_size_option]

    # ปรับขนาด Edge ผ่าน Slider
    edge_width = st.sidebar.slider(
        "Edge Size", 1, 20, default_edge_width, step=1
    )

    # เลือก Target ที่สนใจ
    clicked_target = st.selectbox(
        "Select a Target University (or click an edge):", edges_with_coords["Affiliation"].unique()
    )

    # อัปเดต ViewState ตาม Target ที่เลือก
    if clicked_target:
        target_info = edges_with_coords[edges_with_coords["Affiliation"] == clicked_target].iloc[0]
        dynamic_view_state = update_view_state(
            target_info["latitude"], target_info["longitude"], default_zoom, default_pitch
        )
    else:
        dynamic_view_state = update_view_state(default_lat, default_lon, default_zoom, default_pitch)

    # ปรับสี Node ตามธีมแผนที่
    if map_style == "light":
        node_color = [0, 102, 204, 200]  # น้ำเงินสดใส
    elif map_style == "dark":
        node_color = [255, 255, 0, 200]  # เหลืองสว่าง
    elif map_style == "satellite":
        node_color = [204, 0, 153, 200]  # ม่วงสด
    else:  # streets
        node_color = [0, 204, 102, 200]  # เขียวสดใส

    # สร้าง Layer สำหรับเส้นเชื่อม (Edges)
    edge_layer = pdk.Layer(
        "ArcLayer",
        data=edges_with_coords,
        get_source_position=[default_lon, default_lat],
        get_target_position=["longitude", "latitude"],
        get_width=edge_width,  # ขนาด Edge ปรับเอง
        auto_highlight=True,
        pickable=True,
        get_source_color=[255, 102, 0, 160],
        get_target_color=[0, 102, 255, 160],
    )

    # สร้าง Layer สำหรับจุด (Nodes)
    node_layer = pdk.Layer(
        "ScatterplotLayer",
        data=edges_with_coords[["Affiliation", "latitude", "longitude"]].drop_duplicates(),
        get_position=["longitude", "latitude"],
        get_radius=node_size,  # ขนาด Node เลือกเอง
        get_color=node_color,
        pickable=True,
    )

    # แสดง Pydeck
    st.pydeck_chart(
        pdk.Deck(
            layers=[edge_layer, node_layer],
            initial_view_state=dynamic_view_state,
            map_style=f"mapbox://styles/mapbox/{map_style}-v9",
            tooltip={
                "html": "<b>Target:</b> {Affiliation}",
                "style": {"color": "white"},
            },
        )
    )
    
with tab2:
        st.write("This is content in tab 2")
        with st.expander("Click to expand"):
            st.write("Hidden content in tab 2")


