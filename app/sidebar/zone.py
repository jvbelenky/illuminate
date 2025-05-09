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
    zone = ss.room.calc_zones[ss.selected_zone_id]

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
        zone = ss.room.calc_zones[ss.selected_zone_id]
        initialize_zone(zone)
        st.text_input(
            "Name",
            key=f"name_{zone.zone_id}",
            on_change=update_zone_name,
            args=[zone],
            disabled=DISABLED,
        )

    if ss.editing == "planes":
        # Set calculation type (vertical / horizontal / all angles)
        options = [
            "Planar Normal (Horizontal irradiance, directional)",
            "Planar Maximum (All angles, directional)",
            "Fluence Rate (All angles)",
            "Vertical irradiance (Directional)",
            "Vertical irradiance",
        ]
        if zone.direction == 0:
            if zone.vert:
                calc_idx = 4
            else:
                calc_idx = 2
        else:
            if not zone.horiz and not zone.vert:
                calc_idx = 1
            elif zone.horiz and not zone.vert:
                calc_idx = 0
            elif not zone.horiz and zone.vert:
                calc_idx = 3

        st.selectbox(
            "Calculation type",
            options,
            index=calc_idx,
            on_change=update_calc_type,
            args=[zone, options],
            disabled=DISABLED,
            key="calc_type",
        )

        col1, col2 = st.columns([2, 2])
        col1.selectbox(
            "Reference surface",
            options=["xy", "xz", "yz"],
            key=f"ref_surface_{zone.zone_id}",
            on_change=update_ref_surface,
            args=[zone],
            disabled=DISABLED,
        )

        if zone.direction == 0:
            col2.selectbox(
                "Normal direction",
                options=[None],
                key=f"direction_{zone.zone_id}",
                disabled=True,
            )
        else:
            col2.selectbox(
                "Normal direction",
                options=[1, -1],
                key=f"direction_{zone.zone_id}",
                on_change=update_direction,
                args=[zone],
                disabled=DISABLED,
            )
        # field of views
        cols = st.columns(2)
        cols[0].number_input(
            "Normal (Vertical) Field of View",
            step=1,
            key=f"fov_vert_{zone.zone_id}",
            on_change=update_fov,
            args=[zone],
            disabled=DISABLED,
            help="For calculating eye-dose. 80° per ANSI/IES RP 27.1-22. Max value: 180°",
        )
        cols[1].number_input(
            "In-Plane Field of View",
            step=1,
            key=f"fov_horiz_{zone.zone_id}",
            on_change=update_fov,
            args=[zone],
            disabled=DISABLED,
            help="For calculating eye-dose, given that most people do not have eyes in the back of their head. Values will be calculated as the largest value possible within the provided field of view. Max value: 360°",
        )

        col1, col2 = st.columns([2, 1])
        # height, dimensions
        col1.number_input(
            "Height",
            min_value=0.0,
            key=f"height_{zone.zone_id}",
            on_change=update_plane_height,
            args=[zone],
            disabled=DISABLED,
        )
        col2.write("")
        col2.write("")
        col2.write(ss.room.units)
        plane_dimensions(zone, DISABLED)
        dose_and_offset_options(zone, DISABLED)

    elif ss.editing == "volumes":
        volume_dimensions(zone, DISABLED)
        dose_and_offset_options(zone, DISABLED)
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
        cols = st.columns(2)
        cols[0].checkbox(
            "Enabled",
            on_change=update_zone_visibility,
            args=[zone],
            key=f"enabled_{zone.zone_id}",
        )
        cols[1].checkbox(
            "Show values",
            on_change=update_zone_visibility,
            args=[zone],
            key=f"show_values_{zone.zone_id}",
        )

        disable_download = False  # True zone.values is None else False

        st.download_button(
            "Export Solution",
            data=zone.export(),
            file_name=zone.name + ".csv",
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


def plane_dimensions(zone, DISABLED):
    x = zone.ref_surface[0].upper()
    y = zone.ref_surface[1].upper()
    col1, col2 = st.columns(2)
    with col1:
        st.number_input(
            f"{x}1",
            # min_value=0.0,
            key=f"x1_{zone.zone_id}",
            on_change=update_plane_x1,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            f"{x}2",
            # min_value=0.0,
            key=f"x2_{zone.zone_id}",
            on_change=update_plane_x2,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            f"Num columns ({x} points)",
            min_value=1,
            key=f"x_num_points_{zone.zone_id}",
            on_change=update_plane_points,
            args=[zone],
            disabled=False,
        )
        st.number_input(
            f"Column ({x}) spacing",
            # min_value=0.01,
            # max_value=float(abs(zone.x2 - zone.x1)),
            key=f"x_spacing_{zone.zone_id}",
            on_change=update_plane_x_spacing,
            args=[zone],
            disabled=False,
        )
    with col2:
        st.number_input(
            f"{y}1",
            # min_value=0.0,
            key=f"y1_{zone.zone_id}",
            on_change=update_plane_y1,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            f"{y}2",
            # min_value=0.0,
            key=f"y2_{zone.zone_id}",
            on_change=update_plane_y2,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            f"Num rows ({y} points)",
            min_value=1,
            key=f"y_num_points_{zone.zone_id}",
            on_change=update_plane_points,
            args=[zone],
            disabled=False,
        )
        st.number_input(
            f"Row ({y}) spacing",
            # min_value=0.01,
            # max_value=float(abs(zone.y2 - zone.y1)),
            key=f"y_spacing_{zone.zone_id}",
            on_change=update_plane_y_spacing,
            args=[zone],
            disabled=False,
        )


def volume_dimensions(zone, DISABLED):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input(
            "X1",
            key=f"x1_{zone.zone_id}",
            on_change=update_vol_x1,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            "X2",
            key=f"x2_{zone.zone_id}",
            on_change=update_vol_x2,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            "Num columns (X points)",
            min_value=1,
            key=f"x_num_points_{zone.zone_id}",
            on_change=update_vol_points,
            args=[zone],
        )
        st.number_input(
            "Column (X) spacing",
            key=f"x_spacing_{zone.zone_id}",
            on_change=update_vol_x_spacing,
            args=[zone],
        )
    with col2:
        st.number_input(
            "Y1",
            key=f"y1_{zone.zone_id}",
            on_change=update_vol_y1,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            "Y2",
            key=f"y2_{zone.zone_id}",
            on_change=update_vol_y2,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            "Num rows (Y points)",
            min_value=1,
            key=f"y_num_points_{zone.zone_id}",
            on_change=update_vol_points,
            args=[zone],
        )
        st.number_input(
            "Row (Y) spacing",
            key=f"y_spacing_{zone.zone_id}",
            on_change=update_vol_y_spacing,
            args=[zone],
        )
    with col3:
        st.number_input(
            "Z1",
            key=f"z1_{zone.zone_id}",
            on_change=update_vol_z1,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            "Z2",
            key=f"z2_{zone.zone_id}",
            on_change=update_vol_z2,
            args=[zone],
            disabled=DISABLED,
        )
        st.number_input(
            "Num vertical stacks (Z points)",
            min_value=1,
            key=f"z_num_points_{zone.zone_id}",
            on_change=update_vol_points,
            args=[zone],
        )
        st.number_input(
            "Vertical (Z) spacing",
            key=f"z_spacing_{zone.zone_id}",
            on_change=update_vol_z_spacing,
            args=[zone],
        )


def dose_and_offset_options(zone, DISABLED):
    cols = st.columns(2)
    # Set dose vs irradiance
    if zone.calctype == "Plane":
        value_options = ["Irradiance (uW/cm²)", "Dose (mJ/cm²)"]
    else:
        value_options = ["Fluence rate (uW/cm²)", "Dose (mJ/cm²)"]
    # value_index = 1 if zone.dose else 0
    cols[0].selectbox(
        "Value display type",
        options=[0, 1],
        format_func=lambda x: value_options[x],
        disabled=DISABLED,
        on_change=update_value_type,
        args=[zone],
        key=f"dose_{zone.zone_id}",
    )
    if zone.dose:
        cols[1].number_input(
            "Exposure time (hours)",
            disabled=DISABLED,
            on_change=update_dose_time,
            args=[zone],
            key=f"hours_{zone.zone_id}",
        )
    boundary_options = ["On the Boundary", "Offset from Boundary"]
    st.selectbox(
        "Offset",
        options=[0, 1],
        format_func=lambda x: boundary_options[x],
        on_change=update_offset,
        args=[zone],
        key=f"offset_{zone.zone_id}",
        help="Offset from boundary: Points are generated at an offset from the calc zone dimensions. On the boundary: points are generated on the boundary of the calc zone dimensions.",
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


def update_calc_type(zone, options):
    calc_type = ss["calc_type"]
    if calc_type == options[0]:
        zone.horiz = True
        zone.vert = False
    elif calc_type in [options[1], options[2]]:
        zone.horiz = False
        zone.vert = False
    elif calc_type in [options[3], options[4]]:
        zone.horiz = False
        zone.vert = True
    if calc_type in [options[2], options[4]]:
        zone.set_direction(0)
    else:
        zone.set_direction(1)
        ss[f"direction_{zone.zone_id}"] = 1


def update_ref_surface(zone):
    ref_surface = set_val(f"ref_surface_{zone.zone_id}", zone.ref_surface)
    update_dims = True if ref_surface != zone.ref_surface else False
    zone.set_ref_surface(ref_surface)
    if update_dims:
        if ref_surface == "xy":
            zone.set_dimensions(0, ss.room.x, 0, ss.room.y)
        elif ref_surface == "xz":
            zone.set_dimensions(0, ss.room.x, 0, ss.room.z)
        elif ref_surface == "yz":
            zone.set_dimensions(0, ss.room.y, 0, ss.room.z)
        ss[f"x1_{zone.zone_id}"] = zone.x1
        ss[f"x2_{zone.zone_id}"] = zone.x2
        ss[f"y1_{zone.zone_id}"] = zone.y1
        ss[f"y2_{zone.zone_id}"] = zone.y2


def update_direction(zone):
    direction = set_val(f"direction_{zone.zone_id}", zone.direction)
    zone.set_direction(direction)


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
    zone.set_offset(bool(offset))


def update_fov(zone):
    """update the vertical or horizontal field of view ="""
    zone.fov_vert = set_val(f"fov_vert_{zone.zone_id}", zone.fov_vert)
    zone.fov_horiz = set_val(f"fov_horiz_{zone.zone_id}", zone.fov_horiz)


def update_value_type(zone):
    """set whether zone is dose or irradiance"""
    dose = set_val(f"dose_{zone.zone_id}", zone.dose)
    zone.set_value_type(bool(dose))


def update_dose_time(zone):
    """set the number of hours the zone dose is calculated over"""
    hours = set_val(f"hours_{zone.zone_id}", zone.hours)
    zone.set_dose_time(hours)
