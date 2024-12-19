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
    update_lamp_position,
    update_lamp_rotation,
    update_lamp_orientation,
    update_from_tilt,
    update_from_orientation,
    update_source_parameters,
    update_source_density,
    update_intensity_map,
    update_lamp_visibility,
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

    # if ss.selected_lamp.filedata is not None:
    lamp_source_options(ss.selected_lamp)  # specify source  properties

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
    ss.selected_lamp.enabled = st.checkbox(
        "Enabled",
        on_change=update_lamp_visibility,
        args=[ss.selected_lamp],
        key=f"enabled_{ss.selected_lamp.lamp_id}",
    )


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
            data=lamp.save_ies(original=True),
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
    st.subheader("Position and orientation options")

    col1, col2, col3 = st.columns(3)
    col1.number_input(
        "Position X",
        min_value=0.0,
        step=0.1,
        key=f"pos_x_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )
    col2.number_input(
        "Position Y",
        min_value=0.0,
        step=0.1,
        key=f"pos_y_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )
    col3.number_input(
        "Position Z",
        min_value=0.0,
        step=0.1,
        key=f"pos_z_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )

    # Rotation input
    st.number_input(
        "Rotation",
        min_value=0.0,
        max_value=360.0,
        step=1.0,
        key=f"rotation_{lamp.lamp_id}",
        on_change=update_lamp_rotation,
        args=[lamp],
    )

    st.markdown(
        "Set aim point", help="Setting aim point will update the tilt and orientation"
    )

    # Aim point inputs
    col4, col5, col6 = st.columns(3)
    col4.number_input(
        "Aim X",
        key=f"aim_x_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )
    col5.number_input(
        "Aim Y",
        key=f"aim_y_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )
    col6.number_input(
        "Aim Z",
        key=f"aim_z_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )

    st.markdown(
        "Set tilt and orientation",
        help="Setting tilt and orientation will also update the aim point",
    )
    col7, col8 = st.columns(2)
    col7.number_input(
        "Tilt",
        format="%.1f",
        step=1.0,
        key=f"tilt_{lamp.lamp_id}",
        on_change=update_from_tilt,
        args=[lamp],
    )
    col8.number_input(
        "Orientation",
        format="%.1f",
        step=1.0,
        key=f"orientation_{lamp.lamp_id}",
        on_change=update_from_orientation,
        args=[lamp],
    )


def lamp_source_options(lamp):
    """maybe move to separate lamp report page."""

    st.subheader(
        "Near-field lamp options",
        help="These options are only used for calculation's inside a lamp's photometric distance",
    )

    st.markdown(
        "Source dimensions",
        help="These values were set automatically from your .ies file. If they are incorrect, you can change them and download the corrected .ies file.",
    )

    cols = st.columns([1, 1, 1, 0.8])

    cols[0].number_input(
        "Source width",
        min_value=0.0,
        key=f"width_{lamp.lamp_id}",
        on_change=update_source_parameters,
        args=[lamp],
        help="X-axis distance for the lamp's emissive surface",
    )
    cols[1].number_input(
        "Source length",
        min_value=0.0,
        key=f"length_{lamp.lamp_id}",
        on_change=update_source_parameters,
        help="Y-axis distance of the lamp's emissive surface",
        args=[lamp],
    )

    cols[2].number_input(
        "Source depth",
        min_value=0.0,
        key=f"depth_{lamp.lamp_id}",
        on_change=update_source_parameters,
        args=[lamp],
        help="Determines the minimum mounting distance of the luminaire.",
    )

    cols[3].selectbox(
        "Source units",
        options=["feet", "meters"],
        key=f"units_{lamp.lamp_id}",
        on_change=update_source_parameters,
        args=[lamp],
        help="Units for all source parameters",
    )
    if lamp.photometric_distance is not None:
        if lamp.units == "meters":
            val = round(lamp.photometric_distance,4)
        else:
            val = round(lamp.photometric_distance * 0.3048, 4)
        st.markdown(
            f"**Photometric distance:** {val} meters",
            help="Near-field specific calculations are only performed within this distance from the lamp.",
        )

    cols = st.columns(2)

    cols[0].number_input(
        "Source point density",
        min_value=0,
        step=1,
        on_change=update_source_density,
        args=[lamp],
        key=f"source_density_{lamp.lamp_id}",
        help="This parameter determined the fineness of the source discretization.",
    )

    cols[1].file_uploader(
        "Upload relative intensity map",
        type="csv",
        on_change=update_intensity_map,
        args=[lamp],
        key=f"intensity_map_{lamp.lamp_id}",
        help="Upload a relative intensity map of the source's surface. Otherwise, source is assumed to be a uniform radiator.",
    )

    if lamp.width is not None and lamp.length is not None:
        st.pyplot(lamp.plot_surface(), use_container_width=True)
