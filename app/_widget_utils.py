import streamlit as st
import warnings
from guv_calcs.calc_zone import CalcPlane, CalcVol

ss = st.session_state

SELECT_LOCAL = "Select local file..."


def close_sidebar(which=None, hard=False):
    ss.editing = None
    if which == "lamps":
        clear_lamp_cache(hard=hard)
    elif which in ["zones", "planes", "volumes"]:
        clear_zone_cache(hard=hard)


def close_results():
    ss.show_results = False


def update_room():
    """update the room dimensions and the special calc zones that live in it"""
    ss.room.x = set_val("room_x", ss.room.x)
    ss.room.y = set_val("room_y", ss.room.y)
    ss.room.z = set_val("room_z", ss.room.z)
    ss.room.set_dimensions()

    ss.room.calc_zones["WholeRoomFluence"].set_dimensions(
        x2=ss.room.x,
        y2=ss.room.y,
        z2=ss.room.z,
    )
    ss.room.calc_zones["SkinLimits"].set_dimensions(
        x2=ss.room.x,
        y2=ss.room.y,
    )
    ss.room.calc_zones["EyeLimits"].set_dimensions(
        x2=ss.room.x,
        y2=ss.room.y,
    )


def update_standard():
    """update what standard is used, recalculate if necessary"""
    # store whether recalculation is necessary
    RECALCULATE = False
    if ("UL8802" in ss.room.standard) ^ ("UL8802" in ss["room_standard"]):
        RECALCULATE = True
    # update room standard
    ss.room.standard = set_val("room_standard", ss.room.standard)
    # update other widget
    ss["room_standard_results"] = ss.room.standard
    # update calc zones
    update_calc_zones()
    # recalculate if necessary eg: if value has changed
    if RECALCULATE:
        ss.room.calculate()


def update_standard_results():
    """update what standard is used based on results page, recalculate if necessary"""
    # store whether recalculation is necessary
    RECALCULATE = False
    if ("UL8802" in ss.room.standard) ^ ("UL8802" in ss["room_standard_results"]):
        RECALCULATE = True
    # update room standard
    ss.room.standard = set_val("room_standard_results", ss.room.standard)
    # update other widget
    ss["room_standard"] = ss.room.standard
    # update calc zones
    update_calc_zones()
    # recalculate if necessary eg: if value has changed
    if RECALCULATE:
        ss.room.calculate()


def update_calc_zones():
    if "UL8802" in ss.room.standard:
        ss.room.calc_zones["SkinLimits"].set_height(1.9)
        ss.room.calc_zones["EyeLimits"].set_height(1.9)
        ss.room.calc_zones["EyeLimits"].fov80 = False
        ss.room.calc_zones["EyeLimits"].vert = False
        ss.room.calc_zones["SkinLimits"].horiz = False
    else:
        ss.room.calc_zones["SkinLimits"].set_height(1.8)
        ss.room.calc_zones["EyeLimits"].set_height(1.8)
        ss.room.calc_zones["EyeLimits"].fov80 = True
        ss.room.calc_zones["EyeLimits"].vert = True
        ss.room.calc_zones["SkinLimits"].horiz = True


def clear_lamp_cache(hard=False):
    """
    remove any lamps from the room and the widgets that don't have an
    associated filename, and deselect the lamp.
    """
    if ss.selected_lamp_id in ss.room.lamps:
        selected_lamp = ss.room.lamps[ss.selected_lamp_id]
        if selected_lamp.filename is None or hard:
            remove_lamp(selected_lamp)
            ss.room.remove_lamp(ss.selected_lamp_id)
    ss.selected_lamp_id = None


def clear_zone_cache(hard=False):
    """
    remove any calc zones from the room and the widgets that don't have an
    associated zone type, and deselect the zone
    """
    if ss.selected_zone_id in ss.room.calc_zones:
        selected_zone = ss.room.calc_zones[ss.selected_zone_id]
        if not isinstance(selected_zone, (CalcPlane, CalcVol)) or hard:
            remove_zone(selected_zone)
            ss.room.remove_calc_zone(ss.selected_zone_id)
    ss.selected_zone_id = None


def initialize_results():
    keys = [
        "air_changes_results",
        "ozone_decay_constant_results",
        "room_standard_results",
    ]
    vals = [ss.room.air_changes, ss.room.ozone_decay_constant, ss.room.standard]
    add_keys(keys, vals)


def initialize_room():
    keys = [
        "room_x",
        "room_y",
        "room_z",
        "room_standard",
        "reflectance_ceiling",
        "reflectance_north",
        "reflectance_east",
        "reflectance_south",
        "reflectance_west",
        "reflectance_floor",
        "air_changes",
        "ozone_decay_constant",
        "air_changes_results",
        "ozone_decay_constant_results",
        "room_standard_results",
    ]
    vals = [
        ss.room.x,
        ss.room.y,
        ss.room.z,
        ss.room.standard,
        ss.room.reflectance_ceiling,
        ss.room.reflectance_north,
        ss.room.reflectance_east,
        ss.room.reflectance_south,
        ss.room.reflectance_west,
        ss.room.reflectance_floor,
        ss.room.air_changes,
        ss.room.ozone_decay_constant,
        ss.room.air_changes,
        ss.room.ozone_decay_constant,
        ss.room.standard,
    ]
    add_keys(keys, vals)


def initialize_lamp(lamp):
    """initialize lamp editing widgets with their present values"""
    keys = [
        f"name_{lamp.lamp_id}",
        f"pos_x_{lamp.lamp_id}",
        f"pos_y_{lamp.lamp_id}",
        f"pos_z_{lamp.lamp_id}",
        f"aim_x_{lamp.lamp_id}",
        f"aim_y_{lamp.lamp_id}",
        f"aim_z_{lamp.lamp_id}",
        f"rotation_{lamp.lamp_id}",
        f"orientation_{lamp.lamp_id}",
        f"tilt_{lamp.lamp_id}",
        f"enabled_{lamp.lamp_id}",
    ]
    vals = [
        lamp.name,
        lamp.x,
        lamp.y,
        lamp.z,
        lamp.aimx,
        lamp.aimy,
        lamp.aimz,
        lamp.angle,
        lamp.heading,
        lamp.bank,
        lamp.enabled,
    ]
    add_keys(keys, vals)


def initialize_zone(zone):
    """initialize zone editing widgets with their present values"""
    keys = [
        f"name_{zone.zone_id}",
        f"x1_{zone.zone_id}",
        f"y1_{zone.zone_id}",
        f"x2_{zone.zone_id}",
        f"y2_{zone.zone_id}",
        f"x_spacing_{zone.zone_id}",
        f"y_spacing_{zone.zone_id}",
        f"offset_{zone.zone_id}",
        f"enabled_{zone.zone_id}",
        f"show_values_{zone.zone_id}",
    ]
    if isinstance(zone, CalcPlane):
        keys.append(f"height_{zone.zone_id}")
        keys.append(f"fov80_{zone.zone_id}")
    elif isinstance(zone, CalcVol):
        keys.append(f"z1_{zone.zone_id}")
        keys.append(f"z2_{zone.zone_id}")
        keys.append(f"z_spacing_{zone.zone_id}")

    vals = [
        zone.name,
        zone.x1,
        zone.y1,
        zone.x2,
        zone.y2,
        zone.x_spacing,
        zone.y_spacing,
        zone.offset,
        zone.enabled,
        zone.show_values,
    ]
    if isinstance(zone, CalcPlane):
        vals.append(zone.height)
        vals.append(zone.fov80)
    elif isinstance(zone, CalcVol):
        vals.append(zone.z1)
        vals.append(zone.z2)
        vals.append(zone.z_spacing)

    add_keys(keys, vals)


def update_ozone_results():
    ss.room.air_changes = set_val("air_changes_results", ss.room.air_changes)
    ss.room.ozone_decay_constant = set_val(
        "ozone_decay_constant_results", ss.room.ozone_decay_constant
    )
    ss["air_changes"] = set_val("air_changes_results", ss.room.air_changes)
    ss["ozone_decay_constant"] = set_val(
        "ozone_decay_constant_results", ss.room.ozone_decay_constant
    )


def update_ozone():

    ss.room.air_changes = set_val("air_changes", ss.room.air_changes)
    ss.room.ozone_decay_constant = set_val(
        "ozone_decay_constant", ss.room.ozone_decay_constant
    )

    ss["air_changes_results"] = set_val("air_changes", ss.room.air_changes)
    ss["ozone_decay_constant_results"] = set_val(
        "ozone_decay_constant", ss.room.ozone_decay_constant
    )


def update_lamp_name(lamp):
    """update lamp name from widget"""
    lamp.name = set_val(f"name_{lamp.lamp_id}", lamp.name)


def update_zone_name(zone):
    """update zone name from widget"""
    zone.name = set_val(f"name_{zone.zone_id}", zone.name)


def update_lamp_visibility(lamp):
    """update whether lamp shows in plot or not from widget"""
    lamp.enabled = set_val(f"enabled_{lamp.lamp_id}", lamp.enabled)


def update_zone_visibility(zone):
    """update whether calculation zone shows up in plot or not from widget"""
    zone.enabled = set_val(f"enabled_{zone.zone_id}", zone.enabled)
    zone.show_values = set_val(f"show_values_{zone.zone_id}", zone.show_values)


def update_plane_dimensions(zone):
    """update dimensions and spacing of calculation volume from widgets"""

    zone.x1 = set_val(f"x1_{zone.zone_id}", zone.x1)
    zone.x2 = set_val(f"x2_{zone.zone_id}", zone.x2)
    zone.y1 = set_val(f"y1_{zone.zone_id}", zone.y1)
    zone.y2 = set_val(f"y2_{zone.zone_id}", zone.y2)
    zone.height = set_val(f"height_{zone.zone_id}", zone.height)

    zone.x_spacing = set_val(f"x_spacing_{zone.zone_id}", zone.x_spacing)
    zone.y_spacing = set_val(f"y_spacing_{zone.zone_id}", zone.y_spacing)

    zone.offset = set_val(f"offset_{zone.zone_id}", zone.offset)

    zone._update()


def update_vol_dimensions(zone):
    """update dimensions and spacing of calculation volume from widgets"""
    zone.x1 = set_val(f"x1_{zone.zone_id}", zone.x1)
    zone.x2 = set_val(f"x2_{zone.zone_id}", zone.x2)
    zone.y1 = set_val(f"y1_{zone.zone_id}", zone.y1)
    zone.y2 = set_val(f"y2_{zone.zone_id}", zone.y2)
    zone.z1 = set_val(f"z1_{zone.zone_id}", zone.z1)
    zone.z2 = set_val(f"z2_{zone.zone_id}", zone.z2)
    zone.x_spacing = set_val(f"x_spacing_{zone.zone_id}", zone.x_spacing)
    zone.y_spacing = set_val(f"y_spacing_{zone.zone_id}", zone.y_spacing)
    zone.z_spacing = set_val(f"z_spacing_{zone.zone_id}", zone.z_spacing)
    zone.offset = set_val(f"offset_{zone.zone_id}", zone.offset)
    zone._update()


def update_lamp_position(lamp):
    """update lamp position and aim point based on widget input"""

    x = set_val(f"pos_x_{lamp.lamp_id}", lamp.x)
    y = set_val(f"pos_y_{lamp.lamp_id}", lamp.y)
    z = set_val(f"pos_z_{lamp.lamp_id}", lamp.z)
    lamp.move(x, y, z)
    # update widgets
    update_lamp_aim_point(lamp)


def update_lamp_orientation(lamp):
    """update lamp object aim point, and tilt/orientation widgets"""
    aimx = set_val(f"aim_x_{lamp.lamp_id}", lamp.aimx)
    aimy = set_val(f"aim_y_{lamp.lamp_id}", lamp.aimy)
    aimz = set_val(f"aim_z_{lamp.lamp_id}", lamp.aimz)
    lamp.aim(aimx, aimy, aimz)
    ss[f"orientation_{lamp.lamp_id}"] = lamp.heading
    ss[f"tilt_{lamp.lamp_id}"] = lamp.bank


def update_from_tilt(lamp):
    """update tilt+aim point in lamp, and aim point widget"""
    tilt = set_val(f"tilt_{lamp.lamp_id}", lamp.bank)
    lamp.set_tilt(tilt, dimensions=ss.room.dimensions)
    update_lamp_aim_point(lamp)


def update_from_orientation(lamp):
    """update orientation+aim point in lamp, and aim point widget"""
    orientation = set_val(f"orientation_{lamp.lamp_id}", lamp.heading)
    lamp.set_orientation(orientation, ss.room.dimensions)
    update_lamp_aim_point(lamp)


def update_lamp_aim_point(lamp):
    """reset aim point widget if any other parameter has been altered"""
    ss[f"aim_x_{lamp.lamp_id}"] = lamp.aimx
    ss[f"aim_y_{lamp.lamp_id}"] = lamp.aimy
    ss[f"aim_z_{lamp.lamp_id}"] = lamp.aimz


def remove_lamp(lamp):
    """remove widget parameters if lamp has been deleted"""
    keys = [
        f"name_{lamp.lamp_id}",
        f"pos_x_{lamp.lamp_id}",
        f"pos_y_{lamp.lamp_id}",
        f"pos_z_{lamp.lamp_id}",
        f"aim_x_{lamp.lamp_id}",
        f"aim_y_{lamp.lamp_id}",
        f"aim_z_{lamp.lamp_id}",
        f"rotation_{lamp.lamp_id}",
        f"orientation_{lamp.lamp_id}",
        f"tilt_{lamp.lamp_id}",
    ]
    remove_keys(keys)


def remove_zone(zone):
    """remove widget parameters if calculation zone has been deleted"""

    keys = [
        f"name_{zone.zone_id}",
        f"x_{zone.zone_id}",
        f"y_{zone.zone_id}",
        f"x_spacing_{zone.zone_id}",
        f"y_spacing_{zone.zone_id}",
        f"offset_{zone.zone_id}",
        f"enabled_{zone.zone_id}",
    ]
    if isinstance(zone, CalcPlane):
        keys.append(f"height_{zone.zone_id}")
        remove_keys(keys)
    elif isinstance(zone, CalcVol):
        keys.append(f"zdim_{zone.zone_id}")
        keys.append(f"zspace_{zone.zone_id}")
        remove_keys(keys)


def set_val(key, default):
    if key in ss:
        val = ss[key]
    else:
        warnings.warn(f"{key} not in session state")
        val = default
    return val


def remove_keys(keys):
    """remove parameters from widget"""
    for key in keys:
        if key in ss:
            del ss[key]


def add_keys(keys, vals):
    """initialize widgets with parameters"""
    for key, val in zip(keys, vals):
        ss[key] = val
