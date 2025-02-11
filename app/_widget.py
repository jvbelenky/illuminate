import streamlit as st
import warnings
import numpy as np
from guv_calcs import CalcPlane, CalcVol, get_disinfection_table, plot_disinfection_data

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
    vals = [
        ss.room.x,
        ss.room.y,
        ss.room.z,
        ss.room.standard,
        ss.room.ref_manager.reflectances['ceiling'],
        ss.room.ref_manager.reflectances['north'],
        ss.room.ref_manager.reflectances['east'],
        ss.room.ref_manager.reflectances['south'],
        ss.room.ref_manager.reflectances['west'],
        ss.room.ref_manager.reflectances['floor'],
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
        f"units_{lamp.lamp_id}",
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
        lamp.width,
        lamp.length,
        lamp.depth,
        lamp.units,
        lamp.source_density,
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
        f"enabled_{lamp.lamp_id}",
        f"guv_type_{lamp.lamp_id}",
        f"wavelength_{lamp.lamp_id}",
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
    

def update_reflections():
    keys = ss.room.ref_manager.reflectances.keys()
    if ss["reflection_checkbox"]:        
        for key in keys:
            ss.room.set_reflectance(0, key)
    else:
        for key in keys:
            val = set_val("reflectance_"+key,ss.room.ref_manager.reflectances[key])
            ss.room.set_reflectance(val, key)
    

def show_results():
    """show results in right panel"""
    initialize_results()
    ss.show_results = True
    # format the figure and disinfection table now so we don't redo it later
    fluence = ss.room.calc_zones["WholeRoomFluence"]
    if fluence.values is not None:
        fluence_dict = get_fluence_dict(ss.room)
        if len(fluence_dict) > 0:
            df = get_disinfection_table(fluence_dict, room=ss.room)
            if len(fluence_dict) == 1:
                df = df.drop(columns="wavelength [nm]")
            # move some keys arounds
            new_keys = ["Link"] + [key for key in df.keys() if "Link" not in key]
            ss.kdf = df[new_keys]
            ss.kfig = plot_disinfection_data(
                ss.kdf, fluence_dict=fluence_dict, room=ss.room
            )


def get_fluence_dict(room):
    """
    get a dict of all the wavelengths and the fluences they contribute
    to the Whole Room Fluence
    """

    lamp_types = np.unique([(lamp.wavelength) for lamp in room.lamps.values()], axis=0)
    zone = room.calc_zones["WholeRoomFluence"]
    lamp_wavelengths = {}
    for wavelength in lamp_types:
        val = [
            lamp.lamp_id
            for lamp in room.lamps.values()
            if lamp.wavelength == float(wavelength)
        ]
        lamp_wavelengths[wavelength] = val
    fluence_dict = {}
    for label, lamp_ids in lamp_wavelengths.items():
        vals = np.zeros(zone.values.shape)
        for lamp_id in lamp_ids:
            if lamp_id in zone.lamp_values.keys():
                vals += zone.lamp_values[lamp_id].mean()
        fluence_dict[label] = vals.mean()
    return fluence_dict


def get_lamp_types():
    """
    retrive a dict of all lamp types currently present in the room and the lamp_ids
    for those lamp types
    """
    all_lamp_types = [
        (lamp.guv_type, lamp.wavelength) for lamp in ss.room.lamps.values()
    ]
    lamp_types = np.unique(all_lamp_types, axis=0)
    lamp_labels = {}
    lamps = ss.room.lamps.values()
    for guv_type, wavelength in lamp_types:
        if guv_type in ss.guv_types:
            key = guv_type
            val = [lamp.lamp_id for lamp in lamps if lamp.guv_type == guv_type]
        else:
            key = guv_type + " (" + str(wavelength) + " nm)"
            val = [
                lamp.lamp_id
                for lamp in lamps
                if (lamp.guv_type == guv_type and lamp.wavelength == float(wavelength))
            ]
        lamp_labels[key] = val
    return lamp_labels


def update_zone_name(zone):
    """update zone name from widget"""
    zone.name = set_val(f"name_{zone.zone_id}", zone.name)


def update_zone_visibility(zone):
    """update whether calculation zone shows up in plot or not from widget"""
    zone.enabled = set_val(f"enabled_{zone.zone_id}", zone.enabled)
    zone.show_values = set_val(f"show_values_{zone.zone_id}", zone.show_values)


def update_offset(zone):
    zone.offset = set_val(f"offset_{zone.zone_id}", zone.offset)
    zone._update()


def update_plane_dimensions(zone):
    """update dimensions of calculation plane from widgets"""
    x1 = set_val(f"x1_{zone.zone_id}", zone.x1)
    x2 = set_val(f"x2_{zone.zone_id}", zone.x2)
    y1 = set_val(f"y1_{zone.zone_id}", zone.y1)
    y2 = set_val(f"y2_{zone.zone_id}", zone.y2)
    zone.height = set_val(f"height_{zone.zone_id}", zone.height)
    zone.set_dimensions(x1, x2, y1, y2)


def update_plane_points(zone):
    """update number of points in the calculation plane from widgets"""
    num_x = set_val(f"x_num_points_{zone.zone_id}", zone.num_x)
    num_y = set_val(f"y_num_points_{zone.zone_id}", zone.num_y)
    zone.set_num_points(num_x, num_y)
    ss[f"x_spacing_{zone.zone_id}"] = zone.x_spacing
    ss[f"y_spacing_{zone.zone_id}"] = zone.y_spacing


def update_plane_spacing(zone):
    """update spacing of calculation plane from widgets"""
    x_spacing = set_val(f"x_spacing_{zone.zone_id}", zone.x_spacing)
    y_spacing = set_val(f"y_spacing_{zone.zone_id}", zone.y_spacing)
    zone.set_spacing(x_spacing, y_spacing)
    ss[f"x_num_points_{zone.zone_id}"] = zone.num_x
    ss[f"y_num_points_{zone.zone_id}"] = zone.num_y


def update_vol_dimensions(zone):
    """update dimensions of calculation volume from widgets"""
    x1 = set_val(f"x1_{zone.zone_id}", zone.x1)
    x2 = set_val(f"x2_{zone.zone_id}", zone.x2)
    y1 = set_val(f"y1_{zone.zone_id}", zone.y1)
    y2 = set_val(f"y2_{zone.zone_id}", zone.y2)
    z1 = set_val(f"z1_{zone.zone_id}", zone.z1)
    z2 = set_val(f"z2_{zone.zone_id}", zone.z2)
    zone.set_dimensions(x1, x2, y1, y2, z1, z2)


def update_vol_spacing(zone):
    """update spacing of calculation volumr from widgets"""
    x_spacing = set_val(f"x_spacing_{zone.zone_id}", zone.x_spacing)
    y_spacing = set_val(f"y_spacing_{zone.zone_id}", zone.y_spacing)
    z_spacing = set_val(f"z_spacing_{zone.zone_id}", zone.z_spacing)
    zone.set_spacing(x_spacing, y_spacing, z_spacing)
    ss[f"x_num_points_{zone.zone_id}"] = zone.num_x
    ss[f"y_num_points_{zone.zone_id}"] = zone.num_y
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


def update_fov(zone):
    """update the vertical or horizontal field of view ="""
    zone.fov_vert = set_val(f"fov_vert_{zone.zone_id}", zone.fov_vert)
    zone.fov_horiz = set_val(f"fov_horiz_{zone.zone_id}", zone.fov_horiz)


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
        ss.room.calculate_by_id("EyeLimits")
        ss.room.calculate_by_id("SkinLimits")


def update_standard_results():
    """update what standard is used based on results page, recalculate if necessary"""
    # store whether recalculation is necessary
    print(ss.room.standard)
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
        ss.room.calc_zones["EyeLimits"].fov_vert = 180
        ss.room.calc_zones["EyeLimits"].vert = False
        ss.room.calc_zones["SkinLimits"].horiz = False
    else:
        ss.room.calc_zones["SkinLimits"].set_height(1.8)
        ss.room.calc_zones["EyeLimits"].set_height(1.8)
        ss.room.calc_zones["EyeLimits"].fov80 = 80
        ss.room.calc_zones["EyeLimits"].vert = True
        ss.room.calc_zones["SkinLimits"].horiz = True


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
