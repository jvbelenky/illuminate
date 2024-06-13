import streamlit as st
import requests
import warnings
import matplotlib.pyplot as plt
from guv_calcs.calc_zone import CalcPlane, CalcVol

ss = st.session_state

SELECT_LOCAL = "Select local file..."


def close_sidebar(room, which=None, hard=False):
    ss.editing = None
    if which == "lamps":
        clear_lamp_cache(room=room, hard=hard)
    elif which in ["zones", "planes", "volumes"]:
        clear_zone_cache(room=room, hard=hard)


def close_results():
    ss.show_results = False


def update_lamp_filename(lamp):
    """update lamp filename from widget"""
    fname = set_val(f"file_{lamp.lamp_id}", lamp.filename)
    spectra_data = None
    fdata = None
    if fname != SELECT_LOCAL:
        if fname in ss.vendored_spectra.keys():
            # files from osluv server
            lampdata = ss.vendored_lamps[fname]
            fdata = requests.get(lampdata).content
            spectra_source = ss.vendored_spectra[fname]
            spectra_data = requests.get(spectra_source).content
        elif fname in ss.uploaded_files.keys():
            # previously uploaded files
            fdata = ss.uploaded_files[fname]

    lamp.reload(filename=fname, filedata=fdata)
    lamp.load_spectra(spectra_data)
    if len(lamp.spectra) > 0:
        fig, ax = plt.subplots()
        ss.spectrafig = lamp.plot_spectra(fig=fig, title="")


def update_room(room):
    """update the room dimensions and the special calc zones that live in it"""
    room.x = set_val("room_x", room.x)
    room.y = set_val("room_y", room.y)
    room.z = set_val("room_z", room.z)
    room.set_dimensions()

    room.calc_zones["WholeRoomFluence"].set_dimensions(
        x2=room.x,
        y2=room.y,
        z2=room.z,
    )
    room.calc_zones["SkinLimits"].set_dimensions(
        x2=room.x,
        y2=room.y,
    )
    room.calc_zones["EyeLimits"].set_dimensions(
        x2=room.x,
        y2=room.y,
    )
    ss.room = room


def update_room_standard(room):
    room.standard = ss["room_standard"]
    if "UL8802" in room.standard:
        room.calc_zones["SkinLimits"].set_height(1.9)
        room.calc_zones["EyeLimits"].set_height(1.9)
    else:
        room.calc_zones["SkinLimits"].set_height(1.8)
        room.calc_zones["EyeLimits"].set_height(1.8)


def clear_lamp_cache(room, hard=False):
    """
    remove any lamps from the room and the widgets that don't have an
    associated filename, and deselect the lamp.
    """
    if ss.selected_lamp_id:
        selected_lamp = room.lamps[ss.selected_lamp_id]
        if selected_lamp.filename is None or hard:
            remove_lamp(selected_lamp)
            room.remove_lamp(ss.selected_lamp_id)
    ss.selected_lamp_id = None


def clear_zone_cache(room, hard=False):
    """
    remove any calc zones from the room and the widgets that don't have an
    associated zone type, and deselect the zone
    """
    if ss.selected_zone_id:
        selected_zone = room.calc_zones[ss.selected_zone_id]
        if not isinstance(selected_zone, (CalcPlane, CalcVol)) or hard:
            remove_zone(selected_zone)
            room.remove_calc_zone(ss.selected_zone_id)
    ss.selected_zone_id = None


def initialize_results(room):
    keys = ["air_changes_results", "ozone_decay_constant_results"]
    vals = [room.air_changes, room.ozone_decay_constant]
    add_keys(keys, vals)


def initialize_room(room):
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
    ]
    vals = [
        room.x,
        room.y,
        room.z,
        room.standard,
        room.reflectance_ceiling,
        room.reflectance_north,
        room.reflectance_east,
        room.reflectance_south,
        room.reflectance_west,
        room.reflectance_floor,
        room.air_changes,
        room.ozone_decay_constant,
        room.air_changes,
        room.ozone_decay_constant,
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
    ]
    if isinstance(zone, CalcPlane):
        keys.append(f"height_{zone.zone_id}"),
        keys.append(f"fov80_{zone.zone_id}"),
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
    ]
    if isinstance(zone, CalcPlane):
        vals.append(zone.height)
        vals.append(zone.fov80)
    elif isinstance(zone, CalcVol):
        vals.append(zone.z1)
        vals.append(zone.z2)
        vals.append(zone.z_spacing)

    add_keys(keys, vals)


def update_ozone_results(room):
    room.air_changes = set_val("air_changes_results", room.air_changes)
    room.ozone_decay_constant = set_val(
        "ozone_decay_constant_results", room.ozone_decay_constant
    )
    ss["air_changes"] = set_val("air_changes_results", room.air_changes)
    ss["ozone_decay_constant"] = set_val(
        "ozone_decay_constant_results", room.ozone_decay_constant
    )


def update_ozone(room):

    room.air_changes = set_val("air_changes", room.air_changes)
    room.ozone_decay_constant = set_val(
        "ozone_decay_constant", room.ozone_decay_constant
    )

    ss["air_changes_results"] = set_val("air_changes", room.air_changes)
    ss["ozone_decay_constant_results"] = set_val(
        "ozone_decay_constant", room.ozone_decay_constant
    )


def update_lamp_name(lamp):
    """update lamp name from widget"""
    lamp.name = set_val(f"enabled_{lamp.lamp_id}", lamp.name)


def update_zone_name(zone):
    """update zone name from widget"""
    zone.name = set_val(f"name_{zone.zone_id}", zone.name)


def update_lamp_visibility(lamp):
    """update whether lamp shows in plot or not from widget"""
    lamp.enabled = set_val(f"enabled_{lamp.lamp_id}", lamp.enabled)


def update_zone_visibility(zone):
    """update whether calculation zone shows up in plot or not from widget"""
    zone.enabled = set_val(f"enabled_{zone.zone_id}", zone.enabled)


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


def update_from_tilt(lamp, room):
    """update tilt+aim point in lamp, and aim point widget"""
    tilt = set_val(f"tilt_{lamp.lamp_id}", lamp.bank)
    lamp.set_tilt(tilt, dimensions=room.dimensions)
    update_lamp_aim_point(lamp)


def update_from_orientation(lamp, room):
    """update orientation+aim point in lamp, and aim point widget"""
    orientation = set_val(f"orientation_{lamp.lamp_id}", lamp.heading)
    lamp.set_orientation(orientation, room.dimensions)
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
