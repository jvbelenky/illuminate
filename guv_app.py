import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from guv_calcs.room import Room
from app._top_ribbon import top_ribbon, calculate
from app._plot import room_plot
from app._results import results_page
from app._lamp_utils import add_new_lamp, get_ies_files
from app._lamp_sidebar import lamp_sidebar
from app._zone_utils import add_standard_zones
from app._zone_sidebar import zone_sidebar
from app._sidebar import (
    room_sidebar,
    default_sidebar,
    project_sidebar,
)

# layout / page setup
st.set_page_config(
    page_title="Illuminate",
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
CONTACT_STR = "Questions? Comments? Found a bug? Want a feature? E-mail contact-assay@osluv.org, or stay anonymous by using [this form](https://docs.google.com/forms/d/e/1FAIpQLSdDzLD3bJVmFvW_M3Pj9H5_91GL1RbTey_eXRSXO-ZBMyLJ-w/viewform)"

# Check and initialize session state variables
if "editing" not in ss:
    ss.editing = "about"  # determines what displays in the sidebar

if "show_results" not in ss:
    ss.show_results = False

if "selected_lamp_id" not in ss:
    ss.selected_lamp_id = None  # use None when no lamp is selected

if "selected_zone_id" not in ss:
    ss.selected_zone_id = None  # use None when no lamp is selected

if "uploaded_files" not in ss:
    ss.uploaded_files = {}
    ss.uploaded_spectras = {}

if "lampfile_options" not in ss:
    # ies_files = get_local_ies_files()  # local files for testing
    idx, lamps, spectras = get_ies_files()  # files from assays.osluv.org
    ss.index_data, ss.vendored_lamps, ss.vendored_spectra = get_ies_files()
    ss.lamp_options = [None] + list(ss.vendored_lamps.keys()) + [SELECT_LOCAL]
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
    ss.kfig = None
    ss.kdf = None

if "room" not in ss:
    ss.room = Room(standard="ANSI IES RP 27.1-22 (America)")
    add_standard_zones()

    preview_lamp_name = st.query_params.get("preview_lamp")
    if preview_lamp_name:
        vals = ss.index_data.values()
        default_list = [x for x in vals if x["reporting_name"] == preview_lamp_name][0]
        defaults = default_list.get("preview_setup", {})
        add_new_lamp(name=preview_lamp_name, interactive=False, defaults=defaults)
        # calculate and display results
        calculate()  # normally a callback
        ss.editing = None  # just for aesthetics

top_ribbon()

if ss.show_results or ss.editing is not None:
    left_pane, right_pane = st.columns([2, 3])
else:
    left_pane, right_pane = st.columns([1, 100])


with left_pane:
    if ss.editing is not None:
        if ss.editing == "lamps" and ss.selected_lamp_id is not None:
            lamp_sidebar()
        elif ss.editing in ["zones", "planes", "volumes"] and ss.selected_zone_id:
            zone_sidebar()
        elif ss.editing == "room":
            room_sidebar()
        elif ss.editing == "about":
            default_sidebar()
        elif ss.editing == "project":
            project_sidebar()
        else:
            st.write("")
        if ss.show_results:
            # add this here since it'll look nicer than on the results side
            st.markdown(CONTACT_STR)
    else:
        if ss.show_results:
            room_plot()
            st.markdown(CONTACT_STR)
        # if not ss.show_results, then this is an empty panel

with right_pane:
    if ss.show_results:
        results_page()
    else:
        room_plot()
        st.markdown(CONTACT_STR)
