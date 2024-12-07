import pydeck as pdk
import pandas as pd
import streamlit as st
import plotly.express as px

# ฟังก์ชันโหลดข้อมูล CSV
@st.cache_data
def load_data_latin(path):
    return pd.read_csv(path, encoding="latin1")

@st.cache_data
def load_data_utf8(path):
    return pd.read_csv(path, encoding="utf-8")

# ฟังก์ชันสร้าง ViewState
def update_view_state(lat, lon, zoom, pitch):
    return pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=pitch)

# ฟังก์ชันสร้าง Layer สำหรับเส้นเชื่อม (Edges)
def create_edge_layer(data, source_lon, source_lat, edge_width):
    return pdk.Layer(
        "ArcLayer",
        data=data,
        get_source_position=[source_lon, source_lat],
        get_target_position=["longitude", "latitude"],
        get_width=edge_width,
        auto_highlight=True,
        pickable=True,
        get_source_color=[255, 102, 0, 160],
        get_target_color=[0, 102, 255, 160],
    )

# ฟังก์ชันสร้าง Layer สำหรับจุด (Nodes)
def create_node_layer(data, node_size, node_color):
    return pdk.Layer(
        "ScatterplotLayer",
        data=data[["Affiliation", "latitude", "longitude"]].drop_duplicates(),
        get_position=["longitude", "latitude"],
        get_radius=node_size,
        get_color=node_color,
        pickable=True,
    )

# ฟังก์ชันปรับสี Node ตามธีมแผนที่
def get_node_color(map_style):
    return {
        "light": [0, 102, 204, 200],  # น้ำเงินสดใส
        "dark": [255, 255, 0, 200],  # เหลืองสว่าง
        "satellite": [204, 0, 153, 200],  # ม่วงสด
        "streets": [0, 204, 102, 200],  # เขียวสดใส
    }.get(map_style, [0, 102, 204, 200])  # ค่าเริ่มต้น

# ฟังก์ชันแสดงแผนที่ด้วย Pydeck
def display_map(data, view_state, edge_layer, node_layer, map_style):
    st.pydeck_chart(
        pdk.Deck(
            layers=[edge_layer, node_layer],
            initial_view_state=view_state,
            map_style=f"mapbox://styles/mapbox/{map_style}-v9",
            tooltip={"html": "<b>Target:</b> {Affiliation}", "style": {"color": "white"}},
        )
    )

# ค่าเริ่มต้น
path1 = "colab_count.csv"
path2 = "Cited.csv"
edges_with_coords = load_data_latin(path1)
cited = load_data_latin(path2)


default_lat = 13.74310735  # Chulalongkorn University
default_lon = 100.5328837
default_zoom = 7
default_pitch = 50
default_edge_width = 3

# ส่วนของ Streamlit
st.header("Visualization Project")
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1:
    st.sidebar.header("Visualization Settings")

    # เลือกธีมแผนที่
    map_style = st.sidebar.selectbox("Select Map Style", ["light", "dark", "satellite", "streets"], index=0)

    # เลือกรูปแบบ Node Size
    node_size_option = st.sidebar.radio("Select Node Size", ["Small", "Medium", "Big"], index=1)
    node_size = {"Small": 100, "Medium": 5000, "Big": 200000}[node_size_option]

# แสดงมหาวิทยาลัยต่างช่าติ
show_overseas = st.sidebar.checkbox("Show Overseas Universities", value=True)
# พิกัดประเทศไทย
thailand_bounds = {
    "north": 19.83,
    "south": 5.64,
    "east": 105.65,
    "west": 97.34
}
if not show_overseas:
    edges_with_coords = edges_with_coords[
        (edges_with_coords["target_lat"] > thailand_bounds["south"]) &
        (edges_with_coords["target_lat"] < thailand_bounds["north"]) &
        (edges_with_coords["target_lon"] > thailand_bounds["west"]) &
        (edges_with_coords["target_lon"] < thailand_bounds["east"])
]

    # ปรับขนาด Edge ผ่าน Slider
    edge_width = st.sidebar.slider("Edge Size", 1, 20, default_edge_width, step=1)

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

    # สร้าง Layer
    node_color = get_node_color(map_style)
    edge_layer = create_edge_layer(edges_with_coords, default_lon, default_lat, edge_width)
    node_layer = create_node_layer(edges_with_coords, node_size, node_color)

    # แสดงแผนที่
    display_map(edges_with_coords, dynamic_view_state, edge_layer, node_layer, map_style)

with tab2:
    # แปลง Date_sort ให้เป็น datetime
    cited["Date_sort"] = pd.to_datetime(cited["Date_sort"])

    # จัดเรียงข้อมูลตามวันที่และ Subject_area_abbrev
    cited = cited.sort_values(by=["Subject_area_abbrev", "Date_sort"])

    # คำนวณค่าที่สะสม
    cited["Cited_Cumsum"] = cited.groupby("Subject_area_abbrev")["Cited"].cumsum()  # Cited สะสม
    cited["ID_Cumsum"] = cited.groupby("Subject_area_abbrev").cumcount() + 1         # ID สะสม

    # เพิ่มคอลัมน์ Month-Year
    cited["Month-Year"] = cited["Date_sort"].dt.to_period("M").astype(str)

    # กำหนดขอบเขตของแกน X และ Y
    max_id = cited["ID_Cumsum"].max()
    max_cited = cited["Cited_Cumsum"].max()

    # ปรับขนาดขั้นต่ำและสูงสุดของจุด
    min_size, max_size = 20, 100
    cited["Adjusted_Size"] = cited["Cited"].clip(lower=1)  # กำหนดค่า Cited ขั้นต่ำที่ 1 เพื่อหลีกเลี่ยงจุดที่เล็กเกินไป
    cited["Adjusted_Size"] = (
        (cited["Adjusted_Size"] - cited["Adjusted_Size"].min())
        / (cited["Adjusted_Size"].max() - cited["Adjusted_Size"].min())
        * (max_size - min_size)
        + min_size
    )

    # UI สำหรับปรับความเร็ว Animation
    st.title("Cumulative Analysis of Cited vs IDs")
    st.write("Visualizing the cumulative citations vs cumulative IDs by subject area over time.")
    speed = st.slider("Select Animation Speed (ms per frame)", min_value=100, max_value=2000, value=500, step=100)

    # Plot animation using Scatter Plot
    fig = px.scatter(
        cited,
        x="ID_Cumsum",
        y="Cited_Cumsum",
        color="Subject_area_abbrev",
        animation_frame="Month-Year",
        animation_group="Subject_area_abbrev",
        size="Adjusted_Size",  # ใช้คอลัมน์ที่ปรับขนาดแล้ว
        hover_name="Subject_area_name",
        title="Cumulative Citations vs IDs by Subject Area",
        labels={
            "ID_Cumsum": "Cumulative ID Count",
            "Cited_Cumsum": "Cumulative Citation Count",
        },
        color_discrete_sequence=px.colors.qualitative.Dark24,
        range_x=[0, cited["ID_Cumsum"].max() + 10],
        range_y=[0, cited["Cited_Cumsum"].max() + 50],
        height=600
    )

    # อัปเดตความเร็ว Animation
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = speed

    # แสดงกราฟ
    st.plotly_chart(fig, use_container_width=True)