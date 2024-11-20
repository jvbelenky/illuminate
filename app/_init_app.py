import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from guv_calcs import Room, get_full_disinfection_table
from ._lamp_utils import add_new_lamp, get_ies_files
from ._top_ribbon import calculate
from ._widget import initialize_zone

SELECT_LOCAL = "Select local file..."
ss = st.session_state
"""
TODO: get rid of ss.wavelength and ss.guv_type entirely, 
should be set from lamps only
"""


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
    ss.room.add_standard_zones()
    for zone_id, zone in ss.room.calc_zones.items():
        initialize_zone(zone)

    # populate with lamp from url if available
    preview_lamp_name = st.query_params.get("preview_lamp")
    if preview_lamp_name is not None:
        vals = ss.index_data.values()
        # clean up the preview lamp name, not all browsers do by default_list
        name = preview_lamp_name.replace("%20", " ")
        default_list = [x for x in vals if x["reporting_name"] == name]
        if len(default_list) > 0:
            defaults = default_list[0].get("preview_setup", {})
            add_new_lamp(name=preview_lamp_name, interactive=False, defaults=defaults)
            calculate()  # normally a callback
            ss.editing = None  # just for aesthetics
        else:
            st.warning(f"{preview_lamp_name} was not found in the index.")
