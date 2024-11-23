import streamlit as st
from ._widget import initialize_lamp, close_sidebar
from ._lamp_utils import (
    load_uploaded_spectra,
    lamp_select_widget,
    update_wavelength_select,
    update_custom_wavelength,
    update_custom_wavelength_check,
    lamp_upload_widget,
    spectra_upload_widget,
    lamp_name_widget,
    lamp_type_widget,
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
CHINESE_STD = "PLACEHOLDER"
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

    lamp_type_widget(ss.selected_lamp)
    if ss.selected_lamp.guv_type == "Other":
        lamp_wavelength_options(ss.selected_lamp)

    lamp_file_options(ss.selected_lamp)  # file input
    lamp_info(ss.selected_lamp)  # plot and display other info if file has been selected
    lamp_position_options(ss.selected_lamp)  # position, orientation, etc
    # lamp_source_options(ss.selected_lamp) # specify source  properties

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


def lamp_wavelength_options(lamp):
    if lamp.wavelength in ss.wavelength_options:
        wv_idx = ss.wavelength_options.index(lamp.wavelength)
    else:
        wv_idx = 0
    st.selectbox(
        "Select wavelength [nm]",
        options=ss.wavelength_options,
        index=wv_idx,
        on_change=update_wavelength_select,
        args=[lamp],
        key="wavelength_select",
        disabled=ss.custom_wavelength,
    )
    st.number_input(
        "Enter wavelength [nm]",
        value=ss.wavelength,
        on_change=update_custom_wavelength,
        args=[lamp],
        disabled=not ss.custom_wavelength,
        key="custom_wavelength_input",
    )

    st.checkbox(
        "Enter custom wavelength",
        value=False,
        on_change=update_custom_wavelength_check,
        key="custom_wavelength_check",
        help="Estimates for k may not be available",
    )


def lamp_file_options(lamp):
    """widgets and plots to do with lamp file sources"""

    if lamp.guv_type == "Krypton chloride (222 nm)":

        lamp_select_widget(lamp)

        if lamp.filename == SELECT_LOCAL:
            lamp_upload_widget(lamp)
            # spectra_upload_widget(lamp)

        if lamp.filename in ss.uploaded_files:
            if lamp.filename in ss.uploaded_spectras:
                load_uploaded_spectra(lamp)
            else:
                st.warning(
                    """
                    In order for GUV photobiological safety calculations to be
                    accurate, a spectra is required. :red[If a spectra is not provided,
                    photobiological safety calculations may be inaccurate.]
                    """
                )
                spectra_upload_widget(lamp)
            if ss.warning_message is not None:
                st.warning(ss.warning_message)

    else:
        if lamp.filename in ss.uploaded_files:
            lamp_select_widget(lamp)
        else:
            lamp_upload_widget(lamp)

        if lamp.guv_type == "Other":
            if lamp.filename in ss.uploaded_files:
                if lamp.filename in ss.uploaded_spectras:
                    load_uploaded_spectra(lamp)
                else:
                    spectra_upload_widget(lamp)


def lamp_info(lamp):
    """display info and plot if there is data to plot with"""

    if lamp.filedata is not None:
        cols = st.columns(2)
        skinmax, eyemax = lamp.get_limits(ss.room.standard)
        cols[0].write(f"Max 8-hour skin dose: **:violet[{round(skinmax, 1)}] mJ/cm²**")
        cols[1].write(f"Max 8-hour eye dose: **:violet[{round(eyemax, 1)}] mJ/cm²**")

    PLOT_IES, PLOT_SPECTRA = False, False
    cols = st.columns([2, 2, 1])
    if lamp.filedata is not None:
        fname = str(lamp.filename)
        fname = fname.split(".ies")[0].replace(" ", "_") + ".ies"
        cols[0].download_button(
            "Download .ies file",
            data=lamp.save_ies(),
            file_name=fname,
            use_container_width=True,
            key=f"download_ies_{lamp.lamp_id}",
        )
        PLOT_IES = cols[0].checkbox("Show polar plot", key="show_polar", value=False)

    if lamp.spectra is not None:
        fname = str(lamp.filename)
        fname = fname.split(".csv")[0].replace(" ", "_") + "_spectrum.csv"
        cols[1].download_button(
            "Download spectrum .csv",
            data=lamp.spectra.to_csv(),
            file_name=fname,
            use_container_width=True,
            key=f"download_spectrum_{lamp.lamp_id}",
        )
        PLOT_SPECTRA = cols[1].checkbox(
            "Show spectra plot", key="show_spectra", value=False
        )
        if PLOT_SPECTRA:
            cols[2].write("")
            cols[2].write("")
            cols[2].write("")
            yscale = cols[2].selectbox(
                "Spectra y-scale",
                options=["linear", "log"],
                label_visibility="collapsed",
                key="spectra_yscale",
            )
        else:
            yscale = "linear"  # kludgey default value setting

    if PLOT_IES and PLOT_SPECTRA:
        # plot both charts side by side
        iesfig, iesax = lamp.plot_ies()
        # fig, ax = plt.subplots()
        spectrafig, _ = lamp.spectra.plot(
            # fig=fig, ax=ax,
            title="",
            weights=True,
            label=True,
        )
        spectrafig.set_size_inches(5, 6, forward=True)
        spectrafig.axes[0].set_yscale(yscale)
        cols = st.columns(2)
        cols[1].pyplot(spectrafig, use_container_width=True)
        cols[0].pyplot(iesfig, use_container_width=True)
    elif PLOT_IES and not PLOT_SPECTRA:
        # just display the ies file plot
        iesfig, iesax = lamp.plot_ies()
        st.pyplot(iesfig, use_container_width=True)
    elif PLOT_SPECTRA and not PLOT_IES:
        # display just the spectra
        spectrafig, _ = lamp.spectra.plot(
            # fig=fig, ax=ax,
            title="",
            weights=True,
            label=True,
        )
        spectrafig.set_size_inches(6, 4, forward=True)
        spectrafig.axes[0].set_yscale(yscale)
        st.pyplot(spectrafig, use_container_width=True)

    if lamp.filename in ss.vendored_spectra.keys():

        if "PRERELEASE" not in lamp.filename:
            link = ss.reports[lamp.filename].replace(" ", "%20")
            st.markdown(f"[View Full Report]({link})")


def lamp_position_options(lamp):

    # Position inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        lamp_x_widget(lamp)
    with col2:
        lamp_y_widget(lamp)
    with col3:
        lamp_z_widget(lamp)

    # Rotation input
    lamp_angle_widget(lamp)
    st.markdown(
        "Set aim point", help="Setting aim point will update the tilt and orientation"
    )

    # Aim point inputs
    col4, col5, col6 = st.columns(3)
    with col4:
        lamp_aimx_widget(lamp)
    with col5:
        lamp_aimy_widget(lamp)
    with col6:
        lamp_aimz_widget(lamp)

    st.markdown(
        "Set tilt and orientation",
        help="Setting tilt and orientation will also update the aim point",
    )
    col7, col8 = st.columns(2)
    with col7:
        lamp_tilt_widget(lamp)
    with col8:
        lamp_orientation_widget(lamp)


def lamp_source_options(lamp):
    """TODO: everything. length, width, depth, and units."""
    cols = st.columns(3)
