import pydeck as pdk
import pandas as pd
import streamlit as st
import plotly.express as px
import altair as alt

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
        # Filter out overseas universities
        edges_with_coords = edges_with_coords[
            (edges_with_coords["latitude"] > thailand_bounds["south"]) &
            (edges_with_coords["latitude"] < thailand_bounds["north"]) &
            (edges_with_coords["longitude"] > thailand_bounds["west"]) &
            (edges_with_coords["longitude"] < thailand_bounds["east"])
    ]

    # ปรับขนาด Edge ผ่าน Slider
    edge_width = st.sidebar.slider("Edge Size", 1, 20, default_edge_width, step=1)

    # กรองจุฬาลงกรณ์มหาวิทยาลัยออก
    edges_with_coords_without_chula = edges_with_coords[edges_with_coords["Affiliation"] != "Chulalongkorn University"]

    # ปรับ count ขั้นต่ำและสูงสุด
    min_count, max_count = st.sidebar.slider(
        "Count Range",
        int(edges_with_coords_without_chula['count'].min()),
        int(edges_with_coords_without_chula['count'].max()),
        (int(edges_with_coords_without_chula['count'].min()), int(edges_with_coords_without_chula['count'].max())),
        step=5
    )

    # กรองข้อมูลด้วย min_count และ max_count
    edges_with_coords = edges_with_coords[
        (edges_with_coords["count"] >= min_count) & 
        (edges_with_coords["count"] <= max_count)
    ]

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
        size=None,
        animation_frame="Month-Year",
        animation_group="Subject_area_abbrev",
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


    # แปลง Date_sort เป็น datetime และเพิ่ม Year
    cited["Date_sort"] = pd.to_datetime(cited["Date_sort"])
    cited["Year"] = cited["Date_sort"].dt.year

    # คำนวณ Subject_area_name ที่มีจำนวน ID มากที่สุดในแต่ละปี
    max_id_per_year = (
        cited.groupby(["Year", "Subject_area_name", "Subject_area_abbrev"])["Id"]
        .count()
        .reset_index(name="ID_Count")
        .sort_values(by=["Year", "ID_Count"], ascending=[True, False])
        .drop_duplicates(subset=["Year"])
        .rename(columns={"Subject_area_name": "Subject_area_name_ID"})
    )

    # คำนวณ Subject_area_name ที่มีจำนวน Cited มากที่สุดในแต่ละปี
    max_cited_per_year = (
        cited.groupby(["Year", "Subject_area_name", "Subject_area_abbrev"])["Cited"]
        .sum()
        .reset_index()
        .sort_values(by=["Year", "Cited"], ascending=[True, False])
        .drop_duplicates(subset=["Year"])
        .rename(columns={"Subject_area_name": "Subject_area_name_Cited", "Cited": "Cited_Count"})
    )

    # Streamlit application
    st.title("Analysis of Subject Areas Over the Years")

    # Visualization for max ID count using Altair
    st.subheader("Visualization: Subject Areas with Maximum ID Count")
    chart_id = alt.Chart(max_id_per_year).mark_bar().encode(
        x=alt.X("Year:O", title="Year"),
        y=alt.Y("ID_Count:Q", title="ID Count"),
        color=alt.Color("Subject_area_name_ID:N", title="Subject Area"),
        tooltip=["Year", "Subject_area_name_ID","Subject_area_abbrev", "ID_Count"]
    ).properties(
        title="Top Subject Areas by ID Count",
        width=600,
        height=400
    ).configure_title(fontSize=20).configure_axis(labelFontSize=12, titleFontSize=14)

    st.altair_chart(chart_id, use_container_width=True)

    # Visualization for max Cited count using Altair
    st.subheader("Visualization: Subject Areas with Maximum Citations")
    chart_cited = alt.Chart(max_cited_per_year).mark_bar().encode(
        x=alt.X("Year:O", title="Year"),
        y=alt.Y("Cited_Count:Q", title="Cited Count"),
        color=alt.Color("Subject_area_name_Cited:N", title="Subject Area"),
        tooltip=["Year", "Subject_area_name_Cited","Subject_area_abbrev", "Cited_Count"]
    ).properties(
        title="Top Subject Areas by Citation Count",
        width=600,
        height=400
    ).configure_title(fontSize=20).configure_axis(labelFontSize=12, titleFontSize=14)

    st.altair_chart(chart_cited, use_container_width=True)