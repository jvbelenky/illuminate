import streamlit as st
from guv_calcs import get_tlv
from ._widget import initialize_lamp, close_sidebar
from ._safety_utils import _get_standards
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

    lamp_type_widget()
    if ss.lamp_type == "Other":
        lamp_wavelength_options()

    lamp_file_options()  # file input
    if ss.selected_lamp.filename in ss.vendored_spectra.keys():

        if "PRERELEASE" not in ss.selected_lamp.filename:
            link = ss.reports[ss.selected_lamp.filename].replace(" ", "%20")
            st.markdown(f"[View Full Report]({link})")

    if ss.selected_lamp.filedata is not None:
        cola, colb = st.columns(2)
        skin_standard, eye_standard = _get_standards(ss.room.standard)
        if ss.selected_lamp.spectra is not None:
            max_skin_dose = ss.selected_lamp.spectra.get_tlv(skin_standard)
            max_eye_dose = ss.selected_lamp.spectra.get_tlv(eye_standard)
        else:
            max_skin_dose = get_tlv(ss.wavelength, skin_standard)
            max_eye_dose = get_tlv(ss.wavelength, eye_standard)
        cola.write(
            "Max 8-hour skin dose: **:violet["
            + str(round(max_skin_dose, 1))
            + "] mJ/cm2**"
        )
        colb.write(
            "Max 8-hour eye dose: **:violet["
            + str(round(max_eye_dose, 1))
            + "] mJ/cm2**"
        )

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
    
def lamp_wavelength_options():
    if ss.wavelength in ss.wavelength_options:
        wv_idx = ss.wavelength_options.index(ss.wavelength)
    else:
        wv_idx = 0
    st.selectbox(
        "Select wavelength [nm]",
        options=ss.wavelength_options,
        index=wv_idx,
        on_change=update_wavelength_select,
        key="wavelength_select",
        disabled=ss.custom_wavelength,
    )
    st.number_input(
        "Enter wavelength [nm]",
        value=ss.wavelength,
        on_change=update_custom_wavelength,
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

def lamp_file_options():
    """widgets and plots to do with lamp file sources"""

    if ss.wavelength == 222:

        lamp_select_widget(ss.selected_lamp)

        if ss.selected_lamp.filename == SELECT_LOCAL:
            lamp_upload_widget(ss.selected_lamp)
            # spectra_upload_widget(ss.selected_lamp)

        if ss.selected_lamp.filename in ss.uploaded_files:
            if ss.selected_lamp.filename in ss.uploaded_spectras:
                load_uploaded_spectra(ss.selected_lamp)
            else:
                st.warning(
                    """
                    In order for GUV photobiological safety calculations to be
                    accurate, a spectra is required. :red[If a spectra is not provided,
                    photobiological safety calculations may be inaccurate.]
                    """
                )
                spectra_upload_widget(ss.selected_lamp)
            if ss.warning_message is not None:
                st.warning(ss.warning_message)
                
    else:
        lamp_upload_widget(ss.selected_lamp)
        if ss.guv_type == "Other":
            if ss.selected_lamp.filename in ss.uploaded_files:
                if ss.selected_lamp.filename in ss.uploaded_spectras:
                    load_uploaded_spectra(ss.selected_lamp)
                else:
                    spectra_upload_widget(ss.selected_lamp)


def lamp_plots():
    """plot if there is data to plot with"""
    PLOT_IES, PLOT_SPECTRA = False, False
    cols = st.columns(3)
    if ss.selected_lamp.filedata is not None:
        PLOT_IES = cols[0].checkbox("Show polar plot", key="show_polar", value=False)

    if ss.selected_lamp.spectra is not None:
        PLOT_SPECTRA = cols[1].checkbox(
            "Show spectra plot", key="show_spectra", value=False
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
        # fig, ax = plt.subplots()
        spectrafig, _ = ss.selected_lamp.spectra.plot(
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
        iesfig, iesax = ss.selected_lamp.plot_ies()
        st.pyplot(iesfig, use_container_width=True)
    elif PLOT_SPECTRA and not PLOT_IES:
        # display just the spectra
        spectrafig, _ = ss.selected_lamp.spectra.plot(
            # fig=fig, ax=ax,
            title="",
            weights=True,
            label=True,
        )
        spectrafig.set_size_inches(6, 4, forward=True)
        spectrafig.axes[0].set_yscale(yscale)
        st.pyplot(spectrafig, use_container_width=True)


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
