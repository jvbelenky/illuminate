import streamlit as st
import requests
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from guv_calcs import Room, get_full_disinfection_table
from ._lamp_utils import add_new_lamp, get_ies_files, get_defaults
from ._top_ribbon import calculate
from ._widget import initialize_zone

SELECT_LOCAL = "Select local file..."
ss = st.session_state


def initialize():

    ss.online = is_internet_available()

    ss.editing = "about"  # determines what displays in the sidebar
    ss.show_results = False
    ss.show_room = True  # show the room plot once on load
    ss.error_message = None  # dynamic holder
    ss.warning_message = None

    ss.selected_lamp_id = None  # no lamp initially selected
    ss.selected_zone_id = None  # no zone initially selected
    ss.uploaded_files = {}
    ss.uploaded_spectras = {}

    ss.guv_dict = {}
    ss.guv_dict["Krypton chloride (222 nm)"] = 222
    ss.guv_dict["Low-pressure mercury (254 nm)"] = 254
    # ss.guv_dict["Other"] = 268 # to be added later

    df = get_full_disinfection_table()

    wavelengths = df[df["Medium"] == "Aerosol"]["wavelength [nm]"]
    ss.wavelength_options = list(wavelengths.sort_values().unique())
    ss.wavelength_options.remove(222)
    ss.wavelength_options.remove(254)
    ss.custom_wavelength = False

    # load lamp list
    ss.vendored_lamps, ss.vendored_spectra, ss.reports = get_ies_files()
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
    ss.room.add_standard_zones()
    for zone_id, zone in ss.room.calc_zones.items():
        initialize_zone(zone)

    # populate with lamp from url if available
    preview_lamp_name = st.query_params.get("preview_lamp")
    if preview_lamp_name is not None:
        # clean up the preview lamp name, not all browsers do by default_list
        name = preview_lamp_name.replace("%20", " ")
        default_list = get_defaults(name)
        if len(default_list) > 0:
            defaults = default_list[0].get("preview_setup", {})
            add_new_lamp(name=preview_lamp_name, interactive=False, defaults=defaults)
            calculate()  # normally a callback
            ss.editing = None  # just for aesthetics
        else:
            st.warning(f"{preview_lamp_name} was not found in the index.")


def is_internet_available(timeout=1):
    """
    Check if the internet connection is available by pinging a reliable URL.
    Returns True if the internet is accessible, False otherwise.
    """
    try:
        response = requests.head("https://illuminate.osluv.org", timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def room_plot():
    if ss.selected_lamp_id:
        select_id = ss.selected_lamp_id
    elif ss.selected_zone_id:
        select_id = ss.selected_zone_id
    else:
        select_id = None
    ss.fig = ss.room.plotly(fig=ss.fig, select_id=select_id)

    if ss.show_results:
        if ss.editing is None:
            ar_scale = 0.5
        else:
            ar_scale = 0.3  # this won't show
    else:
        if ss.editing is None:
            ar_scale = 0.8  # full middle page
        else:
            ar_scale = 0.6
    ss.fig.layout.scene.aspectratio.x *= ar_scale
    ss.fig.layout.scene.aspectratio.y *= ar_scale
    ss.fig.layout.scene.aspectratio.z *= ar_scale
    ss.fig.layout.scene.xaxis.range = ss.fig.layout.scene.xaxis.range[::-1]

    st.plotly_chart(ss.fig, use_container_width=True, height=750)
