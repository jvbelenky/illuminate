import streamlit as st
from ._widget_utils import close_sidebar
from ._widget import (
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
)
from ._lamp_utils import load_lamp, load_uploaded_lamp, load_uploaded_spectra

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
    lamp = ss.selected_lamp

    ss.selected_lamp = ss.room.lamps[ss.selected_lamp_id]
    lamp_file_options()  # file input
    if ss.selected_lamp.filename in ss.vendored_spectra.keys():
        if "PRERELEASE" not in ss.selected_lamp.filename:
            link = ss.reports[ss.selected_lamp.filename].replace(" ", "%20")
            st.markdown(f"[View Full Report]({link})")
    lamp_plots()  # plot if file has been selected

    # initialize_lamp(lamp)  # initialize widgets

    with st.form("lamp_form"):
        name = st.text_input("Name", value=lamp.name, key=f"name_{lamp.lamp_id}")
        lamp_file_options()  # file input
        if lamp.filename in ss.vendored_spectra.keys():
            if "PRERELEASE" not in lamp.filename:
                link = ss.reports[lamp.filename].replace(" ", "%20")
                st.markdown(f"[View Full Report]({link})")

        # Position inputs
        col1, col2, col3 = st.columns(3)
        with col1:
            x = st.number_input("Position X", value=lamp.x, key=f"pos_x_{lamp.lamp_id}")
        with col2:
            y = st.number_input("Position Y", value=lamp.y, key=f"pos_y_{lamp.lamp_id}")
        with col3:
            z = st.number_input("Position Z", value=lamp.z, key=f"pos_z_{lamp.lamp_id}")

        # Rotation input
        angle = st.number_input("Rotation", key=f"rotation_{lamp.lamp_id}")
        # Aim point inputs
        st.markdown(
            "Set aim point",
            help="Setting aim point will update the tilt and orientation",
        )
        col4, col5, col6 = st.columns(3)
        with col4:
            aimx = st.number_input(
                "Aim X", value=lamp.aimx, key=f"aim_x_{lamp.lamp_id}"
            )
        with col5:
            aimy = st.number_input(
                "Aim Y", value=lamp.aimy, key=f"aim_y_{lamp.lamp_id}"
            )
        with col6:
            aimz = st.number_input(
                "Aim Z", value=lamp.aimz, key=f"aim_z_{lamp.lamp_id}"
            )

        st.markdown(
            "Set tilt and orientation",
            help="Setting tilt and orientation will also update the aim point",
        )
        col7, col8 = st.columns(2)
        with col7:
            lamp.bank = st.number_input(
                "Tilt",
                value=lamp.bank,
                format="%.1f",
                step=1.0,
                key=f"tilt_{lamp.lamp_id}",
            )
        with col8:
            lamp.heading = st.number_input(
                "Orientation",
                value=lamp.heading,
                format="%.1f",
                step=1.0,
                key=f"orientation_{lamp.lamp_id}",
            )
        # prevent lamp from participating in calculations
        enabled = st.checkbox(
            "Enabled", value=lamp.enabled, key=f"enabled_{lamp.lamp_id}"
        )

        submitted = st.form_submit_button(
            "Submit", type="primary", use_container_width=True
        )
        if submitted:

            lamp = ss.selected_lamp
            lamp.name = name
            load_lamp(lamp)
            load_uploaded_lamp(lamp)
            load_uploaded_spectra(lamp)

            lamp.move(x, y, z)
            print(aimx, lamp.aimx)
            lamp.set_orientation(lamp.heading, ss.room.dimensions)
            lamp.set_tilt(lamp.bank, dimensions=ss.room.dimensions)

            print(aimx, lamp.aimx)
            st.rerun()

            print(aimx, lamp.aimx)
            if any([lamp.aimx != aimx, lamp.aimy != aimy, lamp.aimz != aimz]):
                lamp.aim(aimx, aimy, aimz)
            lamp.rotate(angle)

            lamp.enabled = enabled

    lamp_plots()  # plot if file has been selected
    col3, col4 = st.columns(2)
    with col3:
        # delete button
        st.button(
            "Delete",
            on_click=close_sidebar,
            args=["lamps", True],
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
    lamp_angle_widget(ss.selected_lamp)
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
