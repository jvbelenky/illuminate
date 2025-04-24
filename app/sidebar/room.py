import streamlit as st
from app.widget import close_sidebar, set_val

ss = st.session_state


def room_sidebar():
    """display room editing panel in sidebar"""
    cols = st.columns([10, 1])
    cols[0].subheader("Edit Room")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        use_container_width=True,
        key="close_room",
    )

    st.subheader("Dimensions", divider="grey")
    col1, col2, col3, col4 = st.columns(4)

    col1.number_input(
        "Room length (x)",
        format="%0.3f",
        key="room_x",
        on_change=update_room_x,
    )
    col2.number_input(
        "Room width (y)",
        format="%0.3f",
        key="room_y",
        on_change=update_room_y,
    )
    col3.number_input(
        "Room height (z)",
        format="%0.3f",
        key="room_z",
        on_change=update_room_z,
    )

    unitindex = 0 if ss.room.units == "meters" else 1
    col4.selectbox(
        "Room units",
        ["meters", "feet"],
        index=unitindex,
        key="room_units",
        on_change=update_units,
    )

    st.subheader("Reflectance", divider="grey")
    enable_ref = st.checkbox(
        "Enable Reflections", on_change=enable_reflectance, key="enable_reflectance"
    )
    col1, col2, col3 = st.columns(3)
    col1.number_input(
        "Ceiling",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        format="%0.3f",
        key="reflectance_ceiling",
        on_change=update_reflections,
        disabled=not enable_ref,
    )
    col2.number_input(
        "North Wall",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        format="%0.3f",
        key="reflectance_north",
        on_change=update_reflections,
        disabled=not enable_ref,
    )
    col3.number_input(
        "East Wall",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        format="%0.3f",
        key="reflectance_east",
        on_change=update_reflections,
        disabled=not enable_ref,
    )
    col1.number_input(
        "South Wall",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        format="%0.3f",
        key="reflectance_south",
        on_change=update_reflections,
        disabled=not enable_ref,
    )
    col2.number_input(
        "West Wall",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        format="%0.3f",
        key="reflectance_west",
        on_change=update_reflections,
        disabled=not enable_ref,
    )
    col3.number_input(
        "Floor",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        format="%0.3f",
        key="reflectance_floor",
        on_change=update_reflections,
        disabled=not enable_ref,
    )

    st.subheader("Standards", divider="grey")
    st.selectbox(
        "Select photobiological safety standard",
        options=ss.standards,
        on_change=update_standard,
        key="room_standard",
        help="The ANSI IES RP 27.1-22 standard corresponds to the photobiological limits for UV exposure set by the American Conference of Governmental Industrial Hygienists (ACGIH). The IEC 62471-6:2022 standard corresponds to the limits set by the International Commission on Non-Ionizing Radiation Protection (ICNIRP). Both standards indicate that the measurement should be taken at 1.8 meters up from the floor, but UL8802 (Ultraviolet (UV) Germicidal Equipment and Systems) indicates that it should be taken at 1.9 meters instead. Additionally, though ANSI IES RP 27.1-22 indicates that eye exposure limits be taken with a 80 degere field of view parallel to the floor, considering only vertical irradiance, UL8802 indicates that measurements be taken in the 'worst case' direction, resulting in a stricter limit.",
    )
    st.subheader("Indoor Chemistry", divider="grey")
    cols = st.columns(2)
    with cols[0]:
        st.number_input(
            "Air changes per hour from ventilation",
            on_change=update_ozone,
            min_value=0.0,
            step=0.1,
            key="air_changes",
            help="Note that outdoor ozone is almost always at a higher concentration than indoor ozone. Increasing the air changes from ventilation will reduce the increase in ozone due to GUV, but may increase the total indoor ozone concentration. However, increasing ventilation will also increase the rate of removal of any secondary products that may form from the ozone.",
        )
    with cols[1]:
        st.number_input(
            "Ozone decay constant",
            on_change=update_ozone,
            min_value=0.0,
            step=0.1,
            key="ozone_decay_constant",
            help="An initial ozone decay constant of 2.7 is typical of indoor environments (Nazaroff and Weschler; DOI: 10.1111/ina.12942); ",
        )

    st.button(
        "Close",
        on_click=close_sidebar,
        use_container_width=True,
    )


def update_room_x():
    x = set_val("room_x", ss.room.x)
    ss.room.set_dimensions(x=x)
    ss.room.calc_zones["WholeRoomFluence"].set_dimensions(x2=ss.room.x)
    ss.room.calc_zones["SkinLimits"].set_dimensions(x2=ss.room.x)
    ss.room.calc_zones["EyeLimits"].set_dimensions(
        x2=ss.room.x,
    )


def update_room_y():
    y = set_val("room_y", ss.room.y)
    ss.room.set_dimensions(y=y)
    ss.room.calc_zones["WholeRoomFluence"].set_dimensions(
        y2=ss.room.y,
    )
    ss.room.calc_zones["SkinLimits"].set_dimensions(
        y2=ss.room.y,
    )
    ss.room.calc_zones["EyeLimits"].set_dimensions(
        y2=ss.room.y,
    )


def update_room_z():
    z = set_val("room_z", ss.room.z)
    ss.room.set_dimensions(z=z)
    ss.room.calc_zones["WholeRoomFluence"].set_dimensions(
        z2=ss.room.z,
    )

def update_units():
    """update room units"""
    units = set_val("room_units", ss.room.units)
    ss.room.set_units(units)


def update_reflections():
    """update room reflections"""
    keys = ss.room.ref_manager.reflectances.keys()
    for key in keys:
        val = set_val("reflectance_" + key, ss.room.ref_manager.reflectances[key])
        ss.room.set_reflectance(val, key)

def enable_reflectance():    
    """Enable reflectances"""
    ss.room.enable_reflectance = True if ss["enable_reflectance"] else False

def update_ozone():
    """update the air changes and ozone decay constant"""
    ss.room.air_changes = set_val("air_changes", ss.room.air_changes)
    ss.room.ozone_decay_constant = set_val(
        "ozone_decay_constant", ss.room.ozone_decay_constant
    )

    ss["air_changes_results"] = set_val("air_changes", ss.room.air_changes)
    ss["ozone_decay_constant_results"] = set_val(
        "ozone_decay_constant", ss.room.ozone_decay_constant
    )


def update_standard():
    """update what standard is used, recalculate if necessary"""
    # store whether recalculation is necessary
    RECALCULATE = False
    if ("UL8802" in ss.room.standard) ^ ("UL8802" in ss["room_standard"]):
        RECALCULATE = True
    # update room standard
    standard = set_val("room_standard", ss.room.standard)
    ss.room.set_standard(standard)  # also updates calc zones
    # update other widget
    ss["room_standard_results"] = ss.room.standard
    # recalculate if necessary eg: if value has changed
    if RECALCULATE:
        ss.room.calculate_by_id("EyeLimits")
        ss.room.calculate_by_id("SkinLimits")
