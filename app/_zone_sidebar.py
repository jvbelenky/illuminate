import streamlit as st
from guv_calcs import CalcPlane, CalcVol
from ._widget import (
    initialize_zone,
    update_zone_name,
    update_plane_dimensions,
    update_plane_spacing,
    update_plane_points,
    update_vol_dimensions,
    update_vol_spacing,
    update_vol_points,
    update_offset,
    update_zone_visibility,
    update_fov,
    close_sidebar,
)

SELECT_LOCAL = "Select local file..."
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]
ss = st.session_state


def zone_sidebar():
    cols = st.columns([10, 1])
    cols[0].header("Edit Calculation Zone")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        args=["zones", False],
        use_container_width=True,
        key="close_zone",
    )

    if ss.selected_zone_id in SPECIAL_ZONES:
        DISABLED = True
    else:
        DISABLED = False
    selected_zone = ss.room.calc_zones[ss.selected_zone_id]

    if ss.editing == "zones":
        cola, colb = st.columns([3, 1])
        calc_types = ["Plane", "Volume"]
        cola.selectbox(
            "Select calculation type", options=calc_types, key="select_zone_type"
        )
        colb.write("")
        colb.write("")
        colb.button("Go", on_click=create_zone, use_container_width=True)
    elif ss.editing in ["planes", "volumes"]:
        selected_zone = ss.room.calc_zones[ss.selected_zone_id]
        initialize_zone(selected_zone)
        st.text_input(
            "Name",
            key=f"name_{selected_zone.zone_id}",
            on_change=update_zone_name,
            args=[selected_zone],
            disabled=DISABLED,
        )

    if ss.editing == "planes":
        col1, col2 = st.columns([2, 1])
        # xy dimensions and height
        col1.number_input(
            "Height",
            min_value=0.0,
            key=f"height_{selected_zone.zone_id}",
            on_change=update_plane_dimensions,
            args=[selected_zone],
            disabled=DISABLED,
        )
        col2.write("")
        col2.write("")
        col2.write(ss.room.units)
        col2, col3 = st.columns(2)
        with col2:
            st.number_input(
                "X1",
                # min_value=0.0,
                key=f"x1_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X2",
                # min_value=0.0,
                key=f"x2_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Number of X points",
                min_value=1,
                key=f"x_num_points_{selected_zone.zone_id}",
                on_change=update_plane_points,
                args=[selected_zone],
                disabled=False,
            )
            # st.number_input(
            # "X spacing",
            # # min_value=0.01,
            # # max_value=float(abs(selected_zone.x2 - selected_zone.x1)),
            # key=f"x_spacing_{selected_zone.zone_id}",
            # on_change=update_plane_spacing,
            # args=[selected_zone],
            # disabled=False,
            # )

        with col3:
            st.number_input(
                "Y1",
                # min_value=0.0,
                key=f"y1_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y2",
                # min_value=0.0,
                key=f"y2_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Number of Y points",
                min_value=1,
                key=f"y_num_points_{selected_zone.zone_id}",
                on_change=update_plane_points,
                args=[selected_zone],
                disabled=False,
            )
            # st.number_input(
            # "Y spacing",
            # # min_value=0.01,
            # # max_value=float(abs(selected_zone.y2 - selected_zone.y1)),
            # key=f"y_spacing_{selected_zone.zone_id}",
            # on_change=update_plane_spacing,
            # args=[selected_zone],
            # disabled=False,
            # )

        # Set calculation type (vertical / horizontal / all angles)
        options = ["All angles", "Horizontal irradiance", "Vertical irradiance"]
        if not selected_zone.vert and not selected_zone.horiz:
            calc_type_index = 0
        if selected_zone.horiz and not selected_zone.vert:
            calc_type_index = 1
        if not selected_zone.horiz and selected_zone.vert:
            calc_type_index = 2
        calc_type = st.selectbox(
            "Calculation type", options, index=calc_type_index, disabled=DISABLED
        )
        if calc_type == "All angles":
            selected_zone.horiz = False
            selected_zone.vert = False
        elif calc_type == "Horizontal irradiance":
            selected_zone.horiz = True
            selected_zone.vert = False
        elif calc_type == "Vertical irradiance":
            selected_zone.horiz = False
            selected_zone.vert = True

        # Toggle 80 degree field of view
        cols = st.columns(2)
        cols[0].number_input(
            "Vertical Field of View",
            step=1,
            key=f"fov_vert_{selected_zone.zone_id}",
            on_change=update_fov,
            args=[selected_zone],
            disabled=DISABLED,
            help="For calculating eye-dose. 80° per ANSI/IES RP 27.1-22. Max value: 180°",
        )
        cols[1].number_input(
            "Horizontal Field of View",
            step=1,
            key=f"fov_horiz_{selected_zone.zone_id}",
            on_change=update_fov,
            args=[selected_zone],
            disabled=DISABLED,
            help="For calculating eye-dose, given that most people do not have eyes in the back of their head. Values will be calculated as the largest value possible within the provided field of view. Max value: 360°",
        )

        # Set dose vs irradiance
        value_options = ["Irradiance (uW/cm2)", "Dose (mJ/cm2)"]
        value_index = 1 if selected_zone.dose else 0
        value_type = st.selectbox(
            "Value display type",
            options=value_options,
            index=value_index,
            disabled=DISABLED,
        )
        if value_type == "Dose (mJ/cm2)":
            selected_zone.set_value_type(dose=True)
            dose_time = st.number_input(
                "Exposure time (hours)",
                value=selected_zone.hours,
                disabled=DISABLED,
            )
            selected_zone.set_dose_time(dose_time)
        elif value_type == "Irradiance (uW/cm2)":
            selected_zone.set_value_type(dose=False)

        st.checkbox(
            "Offset",
            key=f"offset_{selected_zone.zone_id}",
            on_change=update_offset,
            args=[selected_zone],
            disabled=False,
        )

    elif ss.editing == "volumes":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input(
                "X1",
                # min_value=0.0,
                key=f"x1_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X2",
                # min_value=0.0,
                key=f"x2_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Number of X points",
                min_value=1,
                key=f"x_num_points_{selected_zone.zone_id}",
                on_change=update_vol_points,
                args=[selected_zone],
            )
            # st.number_input(
            # "X spacing",
            # # min_value=0.01,
            # # max_value=float(abs(selected_zone.x2 - selected_zone.x1)),
            # key=f"x_spacing_{selected_zone.zone_id}",
            # on_change=update_vol_spacing,
            # args=[selected_zone]
            # )
        with col2:
            st.number_input(
                "Y1",
                # min_value=0.0,
                key=f"y1_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y2",
                # min_value=0.0,
                key=f"y2_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Number of Y points",
                min_value=1,
                key=f"y_num_points_{selected_zone.zone_id}",
                on_change=update_vol_points,
                args=[selected_zone],
            )
            # st.number_input(
            # "Y spacing",
            # # min_value=0.01,
            # # max_value=float(abs(selected_zone.y2 - selected_zone.y1)),
            # key=f"y_spacing_{selected_zone.zone_id}",
            # on_change=update_vol_spacing,
            # args=[selected_zone],
            # )
        with col3:
            st.number_input(
                "Z1",
                # min_value=0.0,
                key=f"z1_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Z2",
                # min_value=0.0,
                key=f"z2_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Number of Z points",
                min_value=1,
                key=f"z_num_points_{selected_zone.zone_id}",
                on_change=update_vol_points,
                args=[selected_zone],
            )
            # st.number_input(
            # "Z spacing",
            # # min_value=0.01,
            # # max_value=float(abs(selected_zone.z2 - selected_zone.z1)),
            # key=f"z_spacing_{selected_zone.zone_id}",
            # on_change=update_vol_spacing,
            # args=[selected_zone],
            # )

        st.checkbox(
            "Offset",
            key=f"offset_{selected_zone.zone_id}",
            on_change=update_vol_dimensions,
            args=[selected_zone],
            disabled=False,
        )
        st.checkbox(
            "Show fluence isosurface",
            on_change=update_zone_visibility,
            args=[selected_zone],
            key=f"show_values_{selected_zone.zone_id}",
        )
    if ss.editing == "zones":
        st.button(
            "Cancel",
            on_click=close_sidebar,
            args=["zones", True],
            use_container_width=True,
            disabled=False,
            key="cancel_zone",
        )

    elif ss.editing in ["planes", "volumes"]:
        st.checkbox(
            "Enabled",
            on_change=update_zone_visibility,
            args=[selected_zone],
            key=f"enabled_{selected_zone.zone_id}",
        )

        disable_download = True if selected_zone.values is None else False
        st.download_button(
            "Export Solution",
            data=selected_zone.export(),
            file_name=selected_zone.name + ".csv",
            use_container_width=True,
            disabled=disable_download,
        )

        col7, col8 = st.columns(2)
        col7.button(
            "Delete",
            on_click=close_sidebar,
            args=["zones", True],
            type="primary",
            use_container_width=True,
            disabled=DISABLED,
            key="delete_zone",
        )
        col8.button(
            "Close",
            on_click=close_sidebar,
            args=["zones", False],
            use_container_width=True,
            disabled=False,
            key="close_zone2",
        )


def create_zone():
    if ss["select_zone_type"] == "Plane":
        new_zone = CalcPlane(zone_id=ss.selected_zone_id)
        ss.editing = "planes"
    elif ss["select_zone_type"] == "Volume":
        new_zone = CalcVol(zone_id=ss.selected_zone_id)
        ss.editing = "volumes"
    ss.room.add_calc_zone(new_zone)
