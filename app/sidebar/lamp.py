import streamlit as st
from app.widget import initialize_lamp, close_sidebar, persistent_checkbox
from app.lamp_utils import (
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
    update_lamp_scaling,
    update_lamp_width,
    update_lamp_length,
    update_lamp_depth,
    update_source_density,
    update_intensity_map,
    update_lamp_visibility,
    update_lamp_intensity_units,
    # adjust_yscale,
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
    lamp = ss.selected_lamp

    initialize_lamp(lamp)  # initialize widgets
    lamp_name_widget(lamp)  # name

    lamp_type_widget(lamp)
    if lamp.guv_type == "Other":
        lamp_wavelength_options(lamp)

    lamp_file_options(lamp)  # file input

    # download files
    cols = st.columns([1.5, 2, 2])
    show_info = cols[0].checkbox("Show lamp info")
    if lamp.filedata is not None:
        # fname = str(lamp.filename)
        # fname = fname.split(".ies")[0].replace(" ", "_") + ".ies"
        fname = lamp.lamp_id + ".ies"
        cols[1].download_button(
            "Download .ies file",
            data=lamp.save_ies(original=True),
            file_name=fname,
            use_container_width=True,
            key=f"download_ies_{lamp.lamp_id}",
        )
    if lamp.spectra is not None:
        # fname = str(lamp.filename)
        # fname = fname.split(".csv")[0].replace(" ", "_") + "_spectrum.csv"
        fname = lamp.lamp_id + "_spectrum.csv"
        cols[2].download_button(
            "Download spectrum .csv",
            data=lamp.spectra.to_csv(),
            file_name=fname,
            use_container_width=True,
            key=f"download_spectrum_{lamp.lamp_id}",
        )
    if show_info:
        lamp_info(lamp)  # plot and display other info if file has been selected
    lamp_position_options(lamp)  # position, orientation, etc

    # prevent lamp from participating in calculations
    lamp.enabled = st.checkbox(
        "Luminaire enabled",
        on_change=update_lamp_visibility,
        args=[lamp],
        key=f"enabled_{lamp.lamp_id}",
        help="If this box is unchecked, the luminaire will remain in the room, but not participate in calculations.",
    )

    st.checkbox("Show advanced lamp settings", key="advanced_lamp_settings")
    if ss["advanced_lamp_settings"]:
        # st.header("Advanced settings")
        lamp_scaling_options(lamp)
        lamp_source_options(lamp)  # specify source  properties
        lamp_advanced_options(lamp)

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


def lamp_scaling_options(lamp):

    st.subheader("Photometry scaling")
    cols = st.columns([1, 2])

    methods = {
        "factor": "Scale to relative value",
        "max": "Scale to max irradiance (µW/cm²)",
        "total": "Scale to total power (mW)",
        "center": "Scale to center irradiance (µW/cm²)",
    }
    # current_mode = lamp._scale_mode
    labels = list(methods.keys())
    # idx = labels.index(current_mode)

    defaults = {"factor": lamp.scaling_factor}
    if lamp.ies is not None:
        defaults["max"] = lamp.ies.max()
        defaults["total"] = lamp.ies.total()
        defaults["center"] = lamp.ies.center()

    cols[1].selectbox(
        "Scaling method",
        options=labels,
        format_func=lambda x: methods[x],
        # index=idx,
        key=f"scale_method_{lamp.lamp_id}",
    )

    cols[0].number_input(
        "Value",
        min_value=0.0,
        value=defaults.get(ss[f"scale_method_{lamp.lamp_id}"], 1.0),
        format="%.3f",
        key=f"scale_value_{lamp.lamp_id}",
        on_change=update_lamp_scaling,
        args=[lamp],
    )

def lamp_wavelength_options(lamp):
    """
    NOTE: Currently not used
    """
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
        top = lamp.get_total_power()
        st.write(f"Total optical output: **:violet[{round(top,1)}] mW**")
        cols = st.columns(2)
        skinmax, eyemax = lamp.get_limits(ss.room.standard)
        cols[0].write(f"Max 8-hour skin dose: **:violet[{round(skinmax, 1)}] mJ/cm²**")
        cols[1].write(f"Max 8-hour eye dose: **:violet[{round(eyemax, 1)}] mJ/cm²**")

    # cols = st.columns([1,3, 1])

    if lamp.filedata is not None:
        iesfig, iesax = lamp.plot_ies()
        handles, labels = iesax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        iesax.legend(
            by_label.values(),
            by_label.keys(),
            loc="upper center",
            bbox_to_anchor=[1.6, -0.1, 0, 1.1],
        )
        st.pyplot(iesfig)  # , use_container_width=True)

    cols = st.columns([2.8, 0.7])
    if lamp.spectra is not None:
        yscale = cols[1].selectbox(
            "y-scale",
            options=["linear", "log"],
            key="spectra_yscale",
        )
        spectrafig, _ = lamp.spectra.plot(
            title="",
            weights=True,
            label=True,
        )
        spectrafig.set_size_inches(6, 4.5, forward=True)
        spectrafig.axes[0].set_yscale(yscale)
        cols[0].pyplot(spectrafig, use_container_width=True)

    if lamp.filename in ss.vendored_spectra.keys():

        if "PREVIEW" not in lamp.filename:
            link = ss.reports[lamp.filename].replace(" ", "%20")
            st.markdown(f"[View Full Report]({link})")


def lamp_position_options(lamp):

    # Position inputs
    cola, colb = st.columns([0.75, 0.25])
    cola.subheader("Position and orientation options")
    colb.write("")
    colb.write(f"Units: {ss.room.units}")

    col1, col2, col3 = st.columns(3)
    col1.number_input(
        "Position X",
        min_value=0.0,
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
        key=f"pos_x_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )
    col2.number_input(
        "Position Y",
        min_value=0.0,
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
        key=f"pos_y_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )
    col3.number_input(
        "Position Z",
        min_value=0.0,
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
        key=f"pos_z_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )

    # Rotation input
    st.number_input(
        "Rotation",
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
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
        key=f"aim_x_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )
    col5.number_input(
        "Aim Y",
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
        key=f"aim_y_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )
    col6.number_input(
        "Aim Z",
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
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
        format="%0.2f",
        step=1.0,
        key=f"tilt_{lamp.lamp_id}",
        on_change=update_from_tilt,
        args=[lamp],
    )
    col8.number_input(
        "Orientation",
        format="%0.2f",
        step=1.0,
        key=f"orientation_{lamp.lamp_id}",
        on_change=update_from_orientation,
        args=[lamp],
    )


def lamp_source_options(lamp):
    """maybe move to separate lamp report page."""

    cols = st.columns([0.75, 0.25])
    cols[0].subheader(
        "Near-field lamp options",
        help="These options are only used for calculation's inside a lamp's photometric distance",
    )
    cols[1].write("")
    cols[1].write(f"Units: {lamp.surface.units}")

    # st.markdown(
    # f"Source dimensions ({lamp.surface.units})",
    # help="These values were set automatically from your .ies file. If they are incorrect, you can change them and download the corrected .ies file.",
    # )

    cols = st.columns(3)
    cols[0].number_input(
        "Source width",
        min_value=0.0,
        format="%0.3f",
        key=f"width_{lamp.lamp_id}",
        on_change=update_lamp_width,
        args=[lamp],
        help="X-axis distance for the lamp's emissive surface",
    )
    cols[1].number_input(
        "Source length",
        min_value=0.0,
        format="%0.3f",
        key=f"length_{lamp.lamp_id}",
        on_change=update_lamp_length,
        args=[lamp],
        help="Y-axis distance of the lamp's emissive surface",
    )

    cols[2].number_input(
        "Source depth",
        min_value=0.0,
        format="%0.3f",
        key=f"depth_{lamp.lamp_id}",
        on_change=update_lamp_depth,
        args=[lamp],
        help="Determines the minimum mounting distance of the luminaire.",
    )
    if lamp.surface.photometric_distance is not None:
        val = round(lamp.surface.photometric_distance, 4)
        st.markdown(
            f"**Photometric distance:** {val} {lamp.surface.units}",
            help="Near-field specific calculations are only performed within this distance from the lamp.",
        )

    if lamp.filedata is not None:
        old_ies = lamp.save_ies(original=True)
        new_ies = lamp.save_ies(original=False)
        fname = lamp.lamp_id + ".ies"
        # fname = str(lamp.filename)
        # fname = fname.split(".ies")[0].replace(" ", "_") + ".ies"
        st.download_button(
            "Download updated .ies file",
            data=new_ies,  # lamp.save_ies(original=False),
            file_name=fname,
            use_container_width=True,
            type="secondary" if new_ies == old_ies else "primary",
            key=f"download_updated_ies_{lamp.lamp_id}",
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

    if lamp.surface.intensity_map_orig is not None:
        clear = cols[1].button("Clear", use_container_width=True)
        if clear:
            lamp.load_intensity_map(None)

    if lamp.surface.width is not None and lamp.surface.length is not None:
        st.pyplot(lamp.plot_surface(), use_container_width=True)

    if ss.warning_message is not None:
        st.warning(ss.warning_message)
        ss.warning_message = None


def lamp_advanced_options(lamp):
    st.subheader("Lamp intensity units")
    st.selectbox(
        "Intensity units",
        options=["mW/sr", "uW/cm²"],
        index=0 if lamp.intensity_units.lower() == "mw/sr" else 1,
        label_visibility="collapsed",
        on_change=update_lamp_intensity_units,
        args=[lamp],
        key=f"intensity_units_{lamp.lamp_id}",
    )
    st.write(
        "Most photometric files are in units of mW/sr, but some GUV photometric files may be in uW/cm². If your calculation seems suspiciously off by a factor of 10, try changing this option."
    )
