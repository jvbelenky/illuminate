import streamlit as st
import json
import guv_calcs
from guv_calcs import Room
from app.widget import (
    initialize_room,
    initialize_zone,
    initialize_lamp,
    close_sidebar,
    close_results,
    show_results,
)

SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]
ss = st.session_state


def project_sidebar():
    """sidebar content for saving and loading files"""

    cols = st.columns([10, 1])
    cols[0].header("Save", divider="grey", help="Save your project as a .guv file")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        key="close_project",
        use_container_width=True,
    )

    st.download_button(
        label="Save Project",
        data=ss.room.save(),
        file_name="illuminate.guv",
        use_container_width=True,
        key="download_project",
    )
    st.header("Load", divider="grey", help="Load a previously created .guv file")

    st.file_uploader(
        "Load Project",
        type="guv",
        on_change=upload,
        key="upload_project",
        label_visibility="collapsed",
    )
    st.checkbox("Calculate after loading", key="calculate_after_loading")
    st.checkbox("Visualize after loading", key="visualize_after_loading")

    if ss.error_message is not None:
        st.error(ss.error_message)
    if ss.warning_message is not None:
        st.warning(ss.warning_message)

    st.header(
        "Export",
        divider="grey",
        help="Export all project configurations, results, and (optionally) resources and plots.",
    )
    col3, col4 = st.columns(2)
    plots = st.checkbox("Include plots")
    lampfiles = st.checkbox("Include lamp photometric (.ies) and spectrum (.csv) files")
    col3.download_button(
        "Export All",
        data=ss.room.export_zip(
            include_plots=plots,
            include_lamp_plots=plots,
            include_lamp_files=lampfiles,
        ),
        file_name="illuminate.zip",
        use_container_width=True,
        key="export_all_project",
    )


def upload():
    """
    callback for uploading a .guv file
    """

    file_ok, string = check_file(ss["upload_project"])

    if file_ok:
        # string = file.read().decode("utf-8")
        ss.room = Room.load(string)
        initialize_room()
        for zone_id, zone in ss.room.calc_zones.items():
            initialize_zone(zone)

        dct = json.loads(string)
        for lamp_id, lamp in ss.room.lamps.items():
            # temporary kludge!!!
            lamp.filename = dct["data"]["lamps"][lamp_id]["filename"]
            initialize_lamp(lamp)
            # make lampfile options
            if lamp.filename not in ss.vendored_lamps.keys():
                ss.uploaded_files[lamp.filename] = lamp.filedata

        # disable standard calc zones if they're irrelevant
        if "UL8802" in ss.room.standard:
            height = 1.9 if ss.room.units == "meters" else 6.25
        else:
            height = 1.8 if ss.room.units == "meters" else 5.9
        if ss.room.z < height:
            ss.room.calc_zones["SkinLimits"].enabled = False
            ss.room.calc_zones["EyeLimits"].enabled = False

        # update_calc_zones()
        if ss["calculate_after_loading"]:
            ss.room.calculate()
            show_results()
        else:
            close_results()

        if ss["visualize_after_loading"]:
            ss.show_room = True  # show the uploaded file


def check_file(file):
    if file is None:
        file_ok = False
    else:
        try:
            string = file.read().decode("utf-8")
            # this just checks that the json is valid
            dct = json.loads(string)
            saved_version = dct["guv-calcs_version"]
            current_version = guv_calcs.__version__
            if saved_version != current_version:
                ss.warning_message = f"This file was saved with guv-calcs {saved_version}; the current Illuminate version of guv-calcs is {current_version}."

            file_ok = True
        except ValueError:
            ss.error_message = "Something is wrong with your .guv file. Please verify that it is valid json."
            file_ok = False
    return file_ok, string
