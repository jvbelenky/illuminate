import streamlit as st
import requests
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from guv_calcs.room import Room
from app._top_ribbon import top_ribbon
from app._sidebar import (
    lamp_sidebar,
    zone_sidebar,
    room_sidebar,
    results_sidebar,
    default_sidebar,
)
from app._website_helpers import (
    get_local_ies_files,
    get_ies_files,
    add_standard_zones,
    add_new_lamp,
)

# layout / page setup
st.set_page_config(
    page_title="Illuminate-GUV",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.set_option("deprecation.showPyplotGlobalUse", False)  # silence this warning
st.markdown(
    "<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True
)


# Remove whitespace from the top of the page and sidebar
st.markdown(
    """
        <style>
               .css-18e3th9 {
                    padding-top: 0rem;
                    padding-bottom: 10rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
               .css-1d391kg {
                    padding-top: 3.5rem;
                    padding-right: 1rem;
                    padding-bottom: 3.5rem;
                    padding-left: 1rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)

ss = st.session_state

SELECT_LOCAL = "Select local file..."
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]

# Check and initialize session state variables
if "editing" not in ss:
    ss.editing = None  # determines what displays in the sidebar

if "selected_lamp_id" not in ss:
    ss.selected_lamp_id = None  # use None when no lamp is selected

if "selected_zone_id" not in ss:
    ss.selected_zone_id = None  # use None when no lamp is selected

if "uploaded_files" not in ss:
    ss.uploaded_files = {}

if "lampfile_options" not in ss:
    ies_files = get_local_ies_files()  # local files for testing
    (
        index_data,
        vendored_lamps,
        vendored_spectra,
    ) = get_ies_files()  # files from assays.osluv.org
    ss.index_data, ss.vendored_lamps, ss.vendored_spectra = (
        index_data,
        vendored_lamps,
        vendored_spectra,
    )
    options = [None] + list(vendored_lamps.keys()) + [SELECT_LOCAL]
    ss.lampfile_options = options
    ss.spectra_options = []

if "fig" not in ss:
    ss.fig = go.Figure()
    # Adding an empty scatter3d trace to make the plot appear correctly
    ss.fig.add_trace(
        go.Scatter3d(
            x=[0],  # No data points yet
            y=[0],
            z=[0],
            opacity=0,
            showlegend=False,
            customdata=["placeholder"],
        )
    )
    ss.eyefig = plt.figure()
    ss.skinfig = plt.figure()
    ss.spectrafig, _ = plt.subplots()
fig = ss.fig

if "room" not in ss:
    ss.room = Room()
    ss.room = add_standard_zones(ss.room)

    preview_lamp = st.query_params.get("preview_lamp")
    if preview_lamp:
        defaults = [
            x for x in ss.index_data.values() if x["reporting_name"] == preview_lamp
        ][0].get("preview_setup", {})
        lamp_id = add_new_lamp(
            ss.room, name=preview_lamp, interactive=False, defaults=defaults
        )
        lamp = ss.room.lamps[lamp_id]
        # load ies data
        fdata = requests.get(ss.vendored_lamps[preview_lamp]).content
        lamp.reload(filename=preview_lamp, filedata=fdata)
        # load spectra
        spectra_data = requests.get(ss.vendored_spectra[preview_lamp]).content
        lamp.load_spectra(spectra_data)
        fig, ax = plt.subplots()
        ss.spectrafig = lamp.plot_spectra(fig=fig, title="")
        # calculate and display results
        ss.room.calculate()
        ss.editing = "results"
        st.rerun()

room = ss.room

top_ribbon(room)

if ss.editing == "results":
    left_pane, right_pane = st.columns([3, 1.5])
else:
    left_pane, right_pane = st.columns([1.5, 3])

with left_pane:
    # Lamp editing sidebar
    if ss.editing == "lamps" and ss.selected_lamp_id is not None:
        lamp_sidebar(room)
    # calc zone editing sidebar
    elif ss.editing in ["zones", "planes", "volumes"] and ss.selected_zone_id:
        zone_sidebar(room)
    # room editing sidebar
    elif ss.editing == "room":
        room_sidebar(room)
    elif ss.editing == "results":
        results_sidebar(room)
    else:
        default_sidebar(room)

# plot
with right_pane:
    if ss.selected_lamp_id:
        select_id = ss.selected_lamp_id
    elif ss.selected_zone_id:
        select_id = ss.selected_zone_id
    else:
        select_id = None
    fig = room.plotly(fig=fig, select_id=select_id)

    ar_scale = 0.8 if (ss.editing != "results") else 0.5
    fig.layout.scene.aspectratio.x *= ar_scale
    fig.layout.scene.aspectratio.y *= ar_scale
    fig.layout.scene.aspectratio.z *= ar_scale

    fig.layout.scene.xaxis.range = fig.layout.scene.xaxis.range[::-1]

    st.plotly_chart(fig, use_container_width=True, height=750)

    st.write(
        "Questions? Comments? Found a bug? Want a feature? Contact contact-assay@osluv.org"
    )
