import streamlit as st
from ._lamp_utils import load_uploaded_spectra
from ._widget_utils import initialize_lamp, close_sidebar
from ._widget import (
    lamp_name_widget,
    lamp_select_widget,
    lamp_upload_widget,
    spectra_upload_widget,
    lamp_x_widget,
    lamp_y_widget,
    lamp_z_widget,
    lamp_angle_widget,
    lamp_aimx_widget,
    lamp_aimy_widget,
    lamp_aimz_widget,
    lamp_tilt_widget,
    lamp_orientation_widget,
    lamp_enabled_widget,
)

SELECT_LOCAL = "Select local file..."
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
CHINESE_STD = "placeholder"
ss = st.session_state


def lamp_sidebar():
    """all sidebar content for editing luminaires"""
    col1, col2 = st.columns([10, 1])
    with col1:
        st.header("Edit Luminaire")
    with col2:
        st.button(
            "X",
            on_click=close_sidebar,
            args=["lamps", False],
            use_container_width=True,
            key="close_lamp_sidebar1",
        )

    ss.selected_lamp = ss.room.lamps[ss.selected_lamp_id]
    initialize_lamp(ss.selected_lamp)  # initialize widgets
    lamp_name_widget(ss.selected_lamp)  # name
    lamp_file_options()  # file input
    lamp_plots()  # plot if file has been selected
    lamp_position_options()  # position, orientation, etc

    col3, col4 = st.columns(2)
    with col3:
        # delete button
        st.button(
            "Delete",
            on_click=close_sidebar,
            args=["lamps", True],
            type="primary",
            use_container_width=True,
            key="delete_lamp",
        )
    with col4:
        # close without deleting
        st.button(
            "Close",
            on_click=close_sidebar,
            args=["lamps", False],
            use_container_width=True,
            key="close_lamp_sidebar2",
        )

    # prevent lamp from participating in calculations
    ss.selected_lamp.enabled = lamp_enabled_widget(ss.selected_lamp)


def lamp_file_options():
    """widgets and plots to do with lamp file sources"""

    lamp_select_widget(ss.selected_lamp)
    # determine fdata from fname
    if ss.selected_lamp.filename == SELECT_LOCAL:
        lamp_upload_widget(ss.selected_lamp)
        spectra_upload_widget(ss.selected_lamp)

    if ss.selected_lamp.filename in ss.uploaded_files:
        if ss.selected_lamp.filename in ss.uploaded_spectras:
            load_uploaded_spectra(ss.selected_lamp)
        else:
            if ss.room.standard is not CHINESE_STD:
                st.warning(
                    """
                    In order for GUV photobiological safety calculations to be
                    accurate, a spectra is required. :red[If a spectra is not provided,
                    photobiological safety calculations will be inaccurate.]
                    """
                )
            spectra_upload_widget(ss.selected_lamp)


def lamp_plots():
    """plot if there is data to plot with"""
    PLOT_IES, PLOT_SPECTRA = False, False
    cols = st.columns(3)
    if ss.selected_lamp.filedata is not None:
        PLOT_IES = cols[0].checkbox("Show polar plot", key="show_polar", value=True)

    if len(ss.selected_lamp.spectra) > 0:
        PLOT_SPECTRA = cols[1].checkbox(
            "Show spectra plot", key="show_spectra", value=True
        )
        yscale = cols[2].selectbox(
            "Spectra y-scale",
            options=["linear", "log"],
            label_visibility="collapsed",
            key="spectra_yscale",
        )
        if yscale is None:
            yscale = "linear"  # kludgey default value setting

    if PLOT_IES and PLOT_SPECTRA:
        # plot both charts side by side
        iesfig, iesax = ss.selected_lamp.plot_ies()
        ss.spectrafig.set_size_inches(5, 6, forward=True)
        ss.spectrafig.axes[0].set_yscale(yscale)
        cols = st.columns(2)
        cols[1].pyplot(ss.spectrafig, use_container_width=True)
        cols[0].pyplot(iesfig, use_container_width=True)
    elif PLOT_IES and not PLOT_SPECTRA:
        # just display the ies file plot
        iesfig, iesax = ss.selected_lamp.plot_ies()
        st.pyplot(iesfig, use_container_width=True)
    elif PLOT_SPECTRA and not PLOT_IES:
        # display just the spectra
        ss.spectrafig.set_size_inches(6.4, 4.8, forward=True)
        ss.spectrafig.axes[0].set_yscale(yscale)
        st.pyplot(ss.spectrafig, use_container_width=True)


def lamp_position_options():

    # Position inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        lamp_x_widget(ss.selected_lamp)
    with col2:
        lamp_y_widget(ss.selected_lamp)
    with col3:
        lamp_z_widget(ss.selected_lamp)

    # Rotation input
    angle = lamp_angle_widget(ss.selected_lamp)
    ss.selected_lamp.rotate(angle)
    st.markdown(
        "Set aim point", help="Setting aim point will update the tilt and orientation"
    )

    # Aim point inputs
    col4, col5, col6 = st.columns(3)
    with col4:
        lamp_aimx_widget(ss.selected_lamp)
    with col5:
        lamp_aimy_widget(ss.selected_lamp)
    with col6:
        lamp_aimz_widget(ss.selected_lamp)

    st.markdown(
        "Set tilt and orientation",
        help="Setting tilt and orientation will also update the aim point",
    )
    col7, col8 = st.columns(2)
    with col7:
        lamp_tilt_widget(ss.selected_lamp)
    with col8:
        lamp_orientation_widget(ss.selected_lamp)
