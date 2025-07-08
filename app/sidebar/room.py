import streamlit as st
import numpy as np
from matplotlib import colormaps
from app.widget import close_sidebar, set_val, add_keys, persistent_checkbox

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
        value=ss.room.x,
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
        key="room_x",
        on_change=update_room_x,
    )
    col2.number_input(
        "Room width (y)",
        value=ss.room.y,
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
        key="room_y",
        on_change=update_room_y,
    )
    col3.number_input(
        "Room height (z)",
        value=ss.room.z,
        format=f"%0.{ss.room.precision}f",
        step=1 / (10 ** ss.room.precision),
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

    cols = st.columns([1, 2])
    cols[0].number_input(
        "Display Precision",
        min_value=1,
        max_value=9,
        on_change=update_precision,
        key="precision",
        help="Sets the global value precision for all dimension values in the room. This will only affect display values - if you enter a value of 1.09, then change precision from 2 to 1, the true value will still be 1.09, but display as 1.1 unless it is changed manually.",
    )

    st.subheader("Reflectance", divider="grey")
    enable_ref = st.checkbox(
        "Enable Reflections", on_change=enable_reflectance, key="enable_reflectance"
    )
    cols = st.columns(2)
    allcols = cols + cols + cols

    keys = ["floor", "ceiling", "south", "north", "east", "west"]
    labels = ["Floor", "Ceiling", "South Wall", "North Wall", "East Wall", "West Wall"]

    for col, key, label in zip(allcols, keys, labels):
        col.number_input(
            label,
            min_value=0.0,
            max_value=1.0,
            format="%0.3f",
            key=f"{key}_reflectance",
            on_change=update_reflectance,
            args=[key],
            disabled=not enable_ref,
        )
    persistent_checkbox(
        "Show advanced reflection options",
        key="advanced_reflection",
        on_change=enable_advanced_reflections,
        args=[keys],
    )

    if ss["advanced_reflection"]:
        advanced_reflection_options(keys, labels)

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

    st.subheader("Display", divider="grey")
    st.selectbox(
        "Colormap",
        options=list(colormaps),
        on_change=update_colormap,
        key="colormap",
        help="Set the display colormap of all. We recommend sticking with `plasma`, `viridis`, or `magma`, but any MatPlotLib colormap is allowed. Colormaps ending with `_r` are reversed versions of the base colormap.",
    )
    st.write("")
    st.write("")

    st.button(
        "Close",
        on_click=close_sidebar,
        use_container_width=True,
    )


def enable_advanced_reflections(keys):
    """if the advanced reflection option is enabled, initialize the keys with parameter values from the room object"""

    if ss["advanced_reflection"]:
        xkeys = [f"{key}_x_spacing" for key in keys]
        ykeys = [f"{key}_y_spacing" for key in keys]
        xvals = [ss.room.ref_manager.x_spacings[key] for key in keys]
        yvals = [ss.room.ref_manager.y_spacings[key] for key in keys]
        other_keys = ["max_num_passes", "threshold"]
        other_vals = [ss.room.ref_manager.max_num_passes, ss.room.ref_manager.threshold]
        allkeys = xkeys + ykeys + other_keys
        allvals = xvals + yvals + other_vals
        add_keys(allkeys, allvals)


def advanced_reflection_options(keys, labels):
    """display the spacing and interreflection options for the reflectance module"""
    st.subheader(
        "Reflectance surface spacing",
        help="Determine the fineness of the reflection surface discretization. Smaller values will cause the calculation to slow down, but may increase accuracy. Larger values will result in a faster calculation.",
    )
    cols = st.columns(3)
    cols[0].write(f"Units: {ss.room.units}")
    cols[1].write("Column (X) Spacing")
    cols[2].write("Row (Y) Spacing")
    with cols[0]:
        for label in labels:
            # st.write("")
            st.write(label)
            st.write("")
    with cols[1]:
        for key in keys:
            st.number_input(
                "Column Spacing",
                min_value=0.0,
                step=0.1,
                on_change=update_reflectance_spacing,
                args=[key],
                key=f"{key}_x_spacing",
                label_visibility="collapsed",
            )
    with cols[2]:
        for key in keys:
            st.number_input(
                "Row Spacing",
                min_value=0.0,
                step=0.1,
                on_change=update_reflectance_spacing,
                args=[key],
                key=f"{key}_y_spacing",
                label_visibility="collapsed",
            )

    st.subheader("Interreflection Settings", help="These settings determine how many ")
    cols = st.columns(2)
    cols[0].number_input(
        "Maximum number of iterations",
        min_value=0,
        key="max_num_passes",
        help="Interreflection calculation will terminate after at most this number of loops",
    )
    cols[1].number_input(
        "Percent threshold",
        min_value=0.0,
        max_value=1.0,
        key="threshold",
        help="Interreflection calculation will terminate if the contribution of each loop falls below this percentage of the initial value",
    )


def update_reflectance(key):
    """update the reflectance by wall key"""
    ref = set_val(f"{key}_reflectance", ss.room.ref_manager.reflectances[key])
    ss.room.set_reflectance(ref, key)


def update_reflectance_spacing(key):
    """update the reflectance spacing settings by wall key"""
    xval = set_val(f"{key}_x_spacing", ss.room.ref_manager.x_spacings[key])
    yval = set_val(f"{key}_y_spacing", ss.room.ref_manager.y_spacings[key])
    ss.room.set_reflectance_spacing(xval, yval, key)


def update_room_x():
    x = set_val("room_x", ss.room.x)
    ss.room.set_dimensions(x=x)
    # ss.room.calc_zones["WholeRoomFluence"].set_dimensions(x2=ss.room.x)
    # ss.room.calc_zones["SkinLimits"].set_dimensions(x2=ss.room.x)
    # ss.room.calc_zones["EyeLimits"].set_dimensions(
    # x2=ss.room.x,
    # )


def update_room_y():
    y = set_val("room_y", ss.room.y)
    ss.room.set_dimensions(y=y)
    # ss.room.calc_zones["WholeRoomFluence"].set_dimensions(
    # y2=ss.room.y,
    # )
    # ss.room.calc_zones["SkinLimits"].set_dimensions(
    # y2=ss.room.y,
    # )
    # ss.room.calc_zones["EyeLimits"].set_dimensions(
    # y2=ss.room.y,
    # )


def update_room_z():
    z = set_val("room_z", ss.room.z)
    ss.room.set_dimensions(z=z)
    # ss.room.calc_zones["WholeRoomFluence"].set_dimensions(
    # z2=ss.room.z,
    # )


def update_units():
    """update room units"""
    units = set_val("room_units", ss.room.units)

    # save all calc zone number of points and preserve them
    zone_points = {}
    for zone_id, zone in ss.room.calc_zones.items():
        zone_points[zone_id] = zone.num_points

    # update room dims
    if units == "feet":
        room_dims = [dim / 0.3048 for dim in ss.room.dimensions]
        for lamp in ss.room.lamps.values():
            new_pos = [val / 0.3048 for val in lamp.position]
            new_aim = [val / 0.3048 for val in lamp.aim_point]
            lamp.move(*new_pos)
            lamp.aim(*new_aim)
        for zone in ss.room.calc_zones.values():
            dims = np.array(zone.dimensions).T
            zone_dims = []
            for dim in dims:
                for val in dim:
                    zone_dims.append(val / 0.3048)
            zone.set_dimensions(*zone_dims)
            if zone.calctype == "Plane":
                zone.set_height(zone.height / 0.3048)

    elif units == "meters":
        room_dims = [dim * 0.3048 for dim in ss.room.dimensions]
        for lamp in ss.room.lamps.values():
            new_pos = [val * 0.3048 for val in lamp.position]
            new_aim = [val * 0.3048 for val in lamp.aim_point]
            lamp.move(*new_pos)
            lamp.aim(*new_aim)
        for zone in ss.room.calc_zones.values():
            dims = np.array(zone.dimensions).T
            zone_dims = []
            for dim in dims:
                for val in dim:
                    zone_dims.append(val * 0.3048)
            zone.set_dimensions(*zone_dims)
            if zone.calctype == "Plane":
                zone.set_height(zone.height * 0.3048)

    ss.room.set_dimensions(*room_dims)
    ss["room_x"] = room_dims[0]
    ss["room_y"] = room_dims[1]
    ss["room_z"] = room_dims[2]

    for zone_id, num_points in zone_points.items():
        zone = ss.room.calc_zones[zone_id]
        zone.set_num_points(*num_points)

    ss.room.set_units(units)


def update_precision():
    """update global dimensions precision"""
    ss.room.precision = set_val("precision", ss.room.precision)


def update_colormap():
    """update global colormap"""
    colormap = set_val("colormap", ss.room.scene.colormap)
    ss.room.set_colormap(colormap)


def update_reflections():
    """update room reflections"""
    keys = ss.room.ref_manager.reflectances.keys()
    for key in keys:
        val = set_val(f"{key}_reflectance", ss.room.ref_manager.reflectances[key])
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
