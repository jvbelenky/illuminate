import streamlit as st
import warnings
from guv_calcs import CalcPlane, CalcVol

ss = st.session_state
SELECT_LOCAL = "Select local file..."

OLD_STANDARDS = [
    "ANSI IES RP 27.1-22 (America)",
    "ANSI IES RP 27.1-22 (America) - UL8802",
    "IEC 62471-6:2022 (International)",
]

# initialize


def add_keys(keys, vals):
    """initialize widgets with parameters"""
    for key, val in zip(keys, vals):
        ss[key] = val


def fix_room_standard():
    """
    older versions of illuminate had the standard options named differently;
    this function allows for compatibility with older save files
    """

    if ss.room.standard in ss.standards:
        pass
    elif ss.room.standard in OLD_STANDARDS:
        ss.room.standard = ss.standards[OLD_STANDARDS.index(ss.room.standard)]
    else:
        ss.room.standard = "ANSI IES RP 27.1-22 (ACGIH Limits)"


def initialize_results():
    fix_room_standard()
    keys = [
        "air_changes_results",
        "ozone_decay_constant_results",
        "room_standard_results",
    ]
    vals = [ss.room.air_changes, ss.room.ozone_decay_constant, ss.room.standard]
    add_keys(keys, vals)


def initialize_project():
    keys = ["calculate_after_loading", "visualize_after_loading"]
    vals = [False, True]
    add_keys(keys, vals)


def initialize_room():

    fix_room_standard()

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
    x, y, z = ss.room.get_dimensions()
    vals = [
        x,
        y,
        z,
        ss.room.standard,
        ss.room.ref_manager.reflectances["ceiling"],
        ss.room.ref_manager.reflectances["north"],
        ss.room.ref_manager.reflectances["east"],
        ss.room.ref_manager.reflectances["south"],
        ss.room.ref_manager.reflectances["west"],
        ss.room.ref_manager.reflectances["floor"],
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
        f"guv_type_{lamp.lamp_id}",
        f"wavelength_{lamp.lamp_id}",
        f"width_{lamp.lamp_id}",
        f"length_{lamp.lamp_id}",
        f"depth_{lamp.lamp_id}",
        f"source_density_{lamp.lamp_id}",
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
        lamp.guv_type,
        lamp.wavelength,
        lamp.surface.width,
        lamp.surface.length,
        lamp.surface.depth,
        lamp.surface.source_density,
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
        f"x_num_points_{zone.zone_id}",
        f"y_num_points_{zone.zone_id}",
        f"offset_{zone.zone_id}",
        f"enabled_{zone.zone_id}",
        f"show_values_{zone.zone_id}",
    ]
    if isinstance(zone, CalcPlane):
        keys.append(f"height_{zone.zone_id}")
        keys.append(f"fov_vert_{zone.zone_id}")
        keys.append(f"fov_horiz_{zone.zone_id}")
    elif isinstance(zone, CalcVol):
        keys.append(f"z1_{zone.zone_id}")
        keys.append(f"z2_{zone.zone_id}")
        keys.append(f"z_spacing_{zone.zone_id}")
        keys.append(f"z_num_points_{zone.zone_id}")

    vals = [
        zone.name,
        zone.x1,
        zone.y1,
        zone.x2,
        zone.y2,
        zone.x_spacing,
        zone.y_spacing,
        zone.num_x,
        zone.num_y,
        zone.offset,
        zone.enabled,
        zone.show_values,
    ]
    if isinstance(zone, CalcPlane):
        vals.append(zone.height)
        vals.append(zone.fov_vert)
        vals.append(zone.fov_horiz)
    elif isinstance(zone, CalcVol):
        vals.append(zone.z1)
        vals.append(zone.z2)
        vals.append(zone.z_spacing)
        vals.append(zone.num_z)

    add_keys(keys, vals)


# close, clear, and remove


def remove_keys(keys):
    """remove parameters from widget"""
    for key in keys:
        if key in ss:
            del ss[key]


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
        f"guv_type_{lamp.lamp_id}",
        f"wavelength_{lamp.lamp_id}",
        f"width_{lamp.lamp_id}",
        f"length_{lamp.lamp_id}",
        f"depth_{lamp.lamp_id}",
        f"units_{lamp.lamp_id}",
        f"source_density_{lamp.lamp_id}",
        f"enabled_{lamp.lamp_id}",
    ]
    remove_keys(keys)


def remove_zone(zone):
    """remove widget parameters if calculation zone has been deleted"""

    keys = [
        f"name_{zone.zone_id}",
        f"x1_{zone.zone_id}",
        f"y1_{zone.zone_id}",
        f"x2_{zone.zone_id}",
        f"y2_{zone.zone_id}",
        f"x_spacing_{zone.zone_id}",
        f"y_spacing_{zone.zone_id}",
        f"x_num_points_{zone.zone_id}",
        f"y_num_points_{zone.zone_id}",
        f"offset_{zone.zone_id}",
        f"enabled_{zone.zone_id}",
        f"show_values_{zone.zone_id}",
    ]

    if isinstance(zone, CalcPlane):
        keys.append(f"height_{zone.zone_id}")
        keys.append(f"fov_vert_{zone.zone_id}")
        keys.append(f"fov_horiz_{zone.zone_id}")
        remove_keys(keys)
    elif isinstance(zone, CalcVol):
        keys.append(f"z1_{zone.zone_id}")
        keys.append(f"z2_{zone.zone_id}")
        keys.append(f"z_spacing_{zone.zone_id}")
        keys.append(f"z_num_points_{zone.zone_id}")
        remove_keys(keys)


def clear_lamp_cache(hard=False):
    """
    remove any lamps from the room and the widgets that don't have an
    associated filename, and deselect the lamp.
    """
    if ss.selected_lamp_id in ss.room.lamps:
        selected_lamp = ss.room.lamps[ss.selected_lamp_id]
        if hard:
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


def close_sidebar(which=None, hard=False):
    ss.editing = None
    if which == "lamps":
        clear_lamp_cache(hard=hard)
    elif which in ["zones", "planes", "volumes"]:
        clear_zone_cache(hard=hard)


def close_results():
    ss.show_results = False


# update


def set_val(key, default):
    if key in ss:
        val = ss[key]
    else:
        warnings.warn(f"{key} not in session state")
        val = default
    return val


def show_results():
    """show results in right panel"""
    initialize_results()
    ss.show_results = True
    # format the figure and disinfection table now so we don't redo it later
    fluence = ss.room.calc_zones["WholeRoomFluence"]
    if fluence.values is not None:
        df, fig = ss.room.get_disinfection_data(zone_id="WholeRoomFluence")
        ss.kdf = df
        ss.kfig = fig
