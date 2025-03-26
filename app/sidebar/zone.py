import streamlit as st
from guv_calcs import CalcPlane, CalcVol
from app.widget import initialize_zone, close_sidebar, set_val

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
            on_change=update_plane_height,
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
                on_change=update_plane_x1,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X2",
                # min_value=0.0,
                key=f"x2_{selected_zone.zone_id}",
                on_change=update_plane_x2,
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
            st.number_input(
                "X spacing",
                # min_value=0.01,
                # max_value=float(abs(selected_zone.x2 - selected_zone.x1)),
                key=f"x_spacing_{selected_zone.zone_id}",
                on_change=update_plane_x_spacing,
                args=[selected_zone],
                disabled=False,
            )

        with col3:
            st.number_input(
                "Y1",
                # min_value=0.0,
                key=f"y1_{selected_zone.zone_id}",
                on_change=update_plane_y1,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y2",
                # min_value=0.0,
                key=f"y2_{selected_zone.zone_id}",
                on_change=update_plane_y2,
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
            st.number_input(
                "Y spacing",
                # min_value=0.01,
                # max_value=float(abs(selected_zone.y2 - selected_zone.y1)),
                key=f"y_spacing_{selected_zone.zone_id}",
                on_change=update_plane_y_spacing,
                args=[selected_zone],
                disabled=False,
            )

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
                on_change=update_vol_x1,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X2",
                # min_value=0.0,
                key=f"x2_{selected_zone.zone_id}",
                on_change=update_vol_x2,
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
            st.number_input(
                "X spacing",
                # min_value=0.01,
                # max_value=float(abs(selected_zone.x2 - selected_zone.x1)),
                key=f"x_spacing_{selected_zone.zone_id}",
                on_change=update_vol_x_spacing,
                args=[selected_zone],
            )
        with col2:
            st.number_input(
                "Y1",
                # min_value=0.0,
                key=f"y1_{selected_zone.zone_id}",
                on_change=update_vol_y1,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y2",
                # min_value=0.0,
                key=f"y2_{selected_zone.zone_id}",
                on_change=update_vol_y2,
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
            st.number_input(
                "Y spacing",
                # min_value=0.01,
                # max_value=float(abs(selected_zone.y2 - selected_zone.y1)),
                key=f"y_spacing_{selected_zone.zone_id}",
                on_change=update_vol_y_spacing,
                args=[selected_zone],
            )
        with col3:
            st.number_input(
                "Z1",
                # min_value=0.0,
                key=f"z1_{selected_zone.zone_id}",
                on_change=update_vol_z1,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Z2",
                # min_value=0.0,
                key=f"z2_{selected_zone.zone_id}",
                on_change=update_vol_z2,
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
            st.number_input(
                "Z spacing",
                # min_value=0.01,
                # max_value=float(abs(selected_zone.z2 - selected_zone.z1)),
                key=f"z_spacing_{selected_zone.zone_id}",
                on_change=update_vol_z_spacing,
                args=[selected_zone],
            )

        st.checkbox(
            "Offset",
            key=f"offset_{selected_zone.zone_id}",
            on_change=update_offset,
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

        disable_download = False  # True selected_zone.values is None else False

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
        new_zone = CalcPlane(
            zone_id=ss.selected_zone_id, x1=0, x2=ss.room.x, y1=0, y2=ss.room.y
        )
        ss.editing = "planes"
    elif ss["select_zone_type"] == "Volume":
        new_zone = CalcVol(
            zone_id=ss.selected_zone_id,
            x1=0,
            x2=ss.room.x,
            y1=0,
            y2=ss.room.y,
            z1=0,
            z2=ss.room.z,
        )
        ss.editing = "volumes"
    ss.room.add_calc_zone(new_zone)


def update_zone_name(zone):
    """update zone name from widget"""
    zone.name = set_val(f"name_{zone.zone_id}", zone.name)


def update_plane_x1(zone):
    x1 = set_val(f"x1_{zone.zone_id}", zone.x1)
    zone.set_dimensions(x1=x1)


def update_plane_x2(zone):
    x2 = set_val(f"x2_{zone.zone_id}", zone.x2)
    zone.set_dimensions(x2=x2)


def update_plane_y1(zone):
    y1 = set_val(f"y1_{zone.zone_id}", zone.y1)
    zone.set_dimensions(y1=y1)


def update_plane_y2(zone):
    y2 = set_val(f"y2_{zone.zone_id}", zone.y2)
    zone.set_dimensions(y2=y2)


def update_plane_height(zone):
    height = set_val(f"height_{zone.zone_id}", zone.height)
    zone.set_height(height)


def update_plane_points(zone):
    """update number of points in the calculation plane from widgets"""
    num_x = set_val(f"x_num_points_{zone.zone_id}", zone.num_x)
    num_y = set_val(f"y_num_points_{zone.zone_id}", zone.num_y)
    zone.set_num_points(num_x, num_y)
    ss[f"x_spacing_{zone.zone_id}"] = zone.x_spacing
    ss[f"y_spacing_{zone.zone_id}"] = zone.y_spacing


def update_plane_x_spacing(zone):
    """update spacing of calculation plane from widgets"""
    x_spacing = set_val(f"x_spacing_{zone.zone_id}", zone.x_spacing)
    zone.set_spacing(x_spacing=x_spacing)
    ss[f"x_num_points_{zone.zone_id}"] = zone.num_x


def update_plane_y_spacing(zone):
    """update spacing of calculation plane from widgets"""
    y_spacing = set_val(f"y_spacing_{zone.zone_id}", zone.y_spacing)
    zone.set_spacing(y_spacing=y_spacing)
    ss[f"y_num_points_{zone.zone_id}"] = zone.num_y


def update_vol_x1(zone):
    x1 = set_val(f"x1_{zone.zone_id}", zone.x1)
    zone.set_dimensions(x1=x1)


def update_vol_x2(zone):
    x2 = set_val(f"x2_{zone.zone_id}", zone.x2)
    zone.set_dimensions(x2=x2)


def update_vol_y1(zone):
    y1 = set_val(f"y1_{zone.zone_id}", zone.y1)
    zone.set_dimensions(y1=y1)


def update_vol_y2(zone):
    y2 = set_val(f"y2_{zone.zone_id}", zone.y2)
    zone.set_dimensions(y2=y2)


def update_vol_z1(zone):
    z1 = set_val(f"z1_{zone.zone_id}", zone.z1)
    zone.set_dimensions(z1=z1)


def update_vol_z2(zone):
    z2 = set_val(f"z2_{zone.zone_id}", zone.z2)
    zone.set_dimensions(z2=z2)


def update_vol_x_spacing(zone):
    """update spacing of calculation volumr from widgets"""
    x_spacing = set_val(f"x_spacing_{zone.zone_id}", zone.x_spacing)
    zone.set_spacing(x_spacing=x_spacing)
    ss[f"x_num_points_{zone.zone_id}"] = zone.num_x


def update_vol_y_spacing(zone):
    """update spacing of calculation volumr from widgets"""
    y_spacing = set_val(f"y_spacing_{zone.zone_id}", zone.y_spacing)
    zone.set_spacing(y_spacing=y_spacing)
    ss[f"y_num_points_{zone.zone_id}"] = zone.num_y


def update_vol_z_spacing(zone):
    """update spacing of calculation volumr from widgets"""
    z_spacing = set_val(f"z_spacing_{zone.zone_id}", zone.z_spacing)
    zone.set_spacing(z_spacing=z_spacing)
    ss[f"z_num_points_{zone.zone_id}"] = zone.num_z


def update_vol_points(zone):
    """update number of points in the calculation volume from widgets"""
    numx = set_val(f"x_num_points_{zone.zone_id}", zone.num_x)
    numy = set_val(f"y_num_points_{zone.zone_id}", zone.num_y)
    numz = set_val(f"z_num_points_{zone.zone_id}", zone.num_z)
    zone.set_num_points(numx, numy, numz)
    ss[f"x_spacing_{zone.zone_id}"] = zone.x_spacing
    ss[f"y_spacing_{zone.zone_id}"] = zone.y_spacing
    ss[f"z_spacing_{zone.zone_id}"] = zone.z_spacing


def update_zone_visibility(zone):
    """update whether calculation zone shows up in plot or not from widget"""
    zone.enabled = set_val(f"enabled_{zone.zone_id}", zone.enabled)
    zone.show_values = set_val(f"show_values_{zone.zone_id}", zone.show_values)


def update_offset(zone):
    offset = set_val(f"offset_{zone.zone_id}", zone.offset)
    zone.set_offset(offset)


def update_fov(zone):
    """update the vertical or horizontal field of view ="""
    zone.fov_vert = set_val(f"fov_vert_{zone.zone_id}", zone.fov_vert)
    zone.fov_horiz = set_val(f"fov_horiz_{zone.zone_id}", zone.fov_horiz)
