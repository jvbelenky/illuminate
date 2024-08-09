import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from guv_calcs import Room
from ._zone_utils import add_standard_zones
from ._lamp_utils import add_new_lamp, get_ies_files
from ._top_ribbon import calculate

SELECT_LOCAL = "Select local file..."
ss = st.session_state


def initialize():

    ss.editing = "about"  # determines what displays in the sidebar
    ss.show_results = False
    ss.show_room = True  # show the room plot once on load
    ss.error_message = None  # dynamic holder
    ss.warning_message = None

    ss.selected_lamp_id = None  # no lamp initially selected
    ss.selected_zone_id = None  # no zone initially selected
    ss.uploaded_files = {}
    ss.uploaded_spectras = {}

    # load lamp list
    ss.index_data, ss.vendored_lamps, ss.vendored_spectra, ss.reports = get_ies_files()
    ss.lamp_options = [None] + list(ss.vendored_lamps.keys()) + [SELECT_LOCAL]

    # initialize figures
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

    # initialize room object and add zones to it
    ss.room = Room(standard="ANSI IES RP 27.1-22 (America)")

    add_standard_zones()

    # populate with lamp from url if available
    preview_lamp_name = st.query_params.get("preview_lamp")
    if preview_lamp_name is not None:
        vals = ss.index_data.values()
        default_list = [x for x in vals if x["reporting_name"] == preview_lamp_name][0]
        defaults = default_list.get("preview_setup", {})
        add_new_lamp(name=preview_lamp_name, interactive=False, defaults=defaults)
        calculate()  # normally a callback
        ss.editing = None  # just for aesthetics
