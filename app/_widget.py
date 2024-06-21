import streamlit as st
from ._lamp_utils import (
    load_lamp,
    load_uploaded_lamp,
    load_uploaded_spectra,
    make_file_list,
)
from ._widget_utils import (
    update_lamp_name,
    update_lamp_position,
    update_lamp_orientation,
    update_from_tilt,
    update_from_orientation,
    update_lamp_visibility,
)

ss = st.session_state


def lamp_name_widget(lamp):
    return st.text_input(
        "Name",
        key=f"name_{lamp.lamp_id}",
        on_change=update_lamp_name,
        args=[lamp],
    )


def lamp_select_widget(lamp):
    ss.lamp_options = make_file_list()
    fname_idx = ss.lamp_options.index(lamp.filename)
    return st.selectbox(
        "Select lamp",
        ss.lamp_options,
        index=fname_idx,
        on_change=load_lamp,
        args=[lamp],
        key=f"file_{lamp.lamp_id}",
    )


def lamp_upload_widget(lamp):
    return st.file_uploader(
        "Upload .ies file",
        type="ies",
        on_change=load_uploaded_lamp,
        args=[lamp],
        key=f"upload_{lamp.lamp_id}",
    )


def spectra_upload_widget(lamp):
    return st.file_uploader(
        "Upload spectra .csv file",
        type="csv",
        on_change=load_uploaded_spectra,
        args=[lamp],
        key=f"spectra_upload_{lamp.lamp_id}",
        help="A valid spectra file is a .csv where the first column is a list of wavelengths, and the second column is a list of corresponding relative intensities.",
    )


def lamp_x_widget(lamp):
    return st.number_input(
        "Position X",
        min_value=0.0,
        step=0.1,
        key=f"pos_x_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )


def lamp_y_widget(lamp):
    return st.number_input(
        "Position Y",
        min_value=0.0,
        step=0.1,
        key=f"pos_y_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )


def lamp_z_widget(lamp):
    return st.number_input(
        "Position Z",
        min_value=0.0,
        step=0.1,
        key=f"pos_z_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )


def lamp_angle_widget(lamp):
    return st.number_input(
        "Rotation",
        min_value=0.0,
        max_value=360.0,
        step=1.0,
        key=f"rotation_{lamp.lamp_id}",
    )


def lamp_aimx_widget(lamp):
    return st.number_input(
        "Aim X",
        key=f"aim_x_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )


def lamp_aimy_widget(lamp):
    return st.number_input(
        "Aim Y",
        key=f"aim_y_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )


def lamp_aimz_widget(lamp):
    return st.number_input(
        "Aim Z",
        key=f"aim_z_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )


def lamp_tilt_widget(lamp):
    return st.number_input(
        "Tilt",
        format="%.1f",
        step=1.0,
        key=f"tilt_{lamp.lamp_id}",
        on_change=update_from_tilt,
        args=[lamp],
    )


def lamp_orientation_widget(lamp):
    return st.number_input(
        "Orientation",
        format="%.1f",
        step=1.0,
        key=f"orientation_{lamp.lamp_id}",
        on_change=update_from_orientation,
        args=[lamp],
    )


def lamp_enabled_widget(lamp):
    return st.checkbox(
        "Enabled",
        on_change=update_lamp_visibility,
        args=[lamp],
        key=f"enabled_{lamp.lamp_id}",
    )
