import numpy as np
from pathlib import Path
import streamlit as st
from guv_calcs.calc_zone import CalcZone, CalcPlane, CalcVol
import requests

def clear_lamp_cache(room):
    if st.session_state.selected_lamp_id:
        selected_lamp = room.lamps[st.session_state.selected_lamp_id]
        if selected_lamp.filename is None:
            remove_lamp(selected_lamp)
            room.remove_lamp(st.session_state.selected_lamp_id)
    st.session_state.selected_lamp_id = None


def clear_zone_cache(room):
    if st.session_state.selected_zone_id:
        selected_zone = room.calc_zones[st.session_state.selected_zone_id]
        if isinstance(selected_zone, CalcZone):
            remove_zone(selected_zone)
            room.remove_calc_zone(st.session_state.selected_zone_id)
    st.session_state.selected_zone_id = None


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
        f"visible_{lamp.lamp_id}",
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
        lamp.visible,
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
        f"visible_{zone.zone_id}",
    ]
    if isinstance(zone, CalcPlane):
        keys.append(f"height_{zone.zone_id}")
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
        zone.visible,
    ]
    if isinstance(zone, CalcPlane):
        vals.append(zone.height)
    elif isinstance(zone, CalcVol):
        vals.append(zone.z1)
        vals.append(zone.z2)
        vals.append(zone.z_spacing)

    add_keys(keys, vals)


def update_lamp_name(lamp):
    """update lamp name from widget"""
    lamp.name = st.session_state[f"name_{lamp.lamp_id}"]


def update_zone_name(zone):
    """update zone name from widget"""
    zone.name = st.session_state[f"name_{zone.zone_id}"]


def update_lamp_visibility(lamp):
    """update whether lamp shows in plot or not from widget"""
    lamp.visible = st.session_state[f"visible_{lamp.lamp_id}"]


def update_zone_visibility(zone):
    """update whether calculation zone shows up in plot or not from widget"""
    zone.visible = st.session_state[f"visible_{zone.zone_id}"]


def update_plane_dimensions(zone):
    """update dimensions and spacing of calculation volume from widgets"""
    zone.x1 = st.session_state[f"x1_{zone.zone_id}"]
    zone.x2 = st.session_state[f"x2_{zone.zone_id}"]
    zone.y1 = st.session_state[f"y1_{zone.zone_id}"]
    zone.y2 = st.session_state[f"y2_{zone.zone_id}"]
    zone.height = st.session_state[f"height_{zone.zone_id}"]

    zone.x_spacing = st.session_state[f"x_spacing_{zone.zone_id}"]
    zone.y_spacing = st.session_state[f"y_spacing_{zone.zone_id}"]

    zone.offset = st.session_state[f"offset_{zone.zone_id}"]

    zone._update()


def update_vol_dimensions(zone):
    """update dimensions and spacing of calculation volume from widgets"""
    zone.x1 = st.session_state[f"x1_{zone.zone_id}"]
    zone.x2 = st.session_state[f"x2_{zone.zone_id}"]
    zone.y1 = st.session_state[f"y1_{zone.zone_id}"]
    zone.y2 = st.session_state[f"y2_{zone.zone_id}"]
    zone.z1 = st.session_state[f"z1_{zone.zone_id}"]
    zone.z2 = st.session_state[f"z2_{zone.zone_id}"]

    zone.x_spacing = st.session_state[f"x_spacing_{zone.zone_id}"]
    zone.y_spacing = st.session_state[f"y_spacing_{zone.zone_id}"]
    zone.z_spacing = st.session_state[f"z_spacing_{zone.zone_id}"]

    zone.offset = st.session_state[f"offset_{zone.zone_id}"]

    zone._update


def update_lamp_position(lamp):
    """update lamp position and aim point based on widget input"""
    x = st.session_state[f"pos_x_{lamp.lamp_id}"]
    y = st.session_state[f"pos_y_{lamp.lamp_id}"]
    z = st.session_state[f"pos_z_{lamp.lamp_id}"]
    lamp.move(x, y, z)
    # update widgets
    update_lamp_aim_point(lamp)


def update_lamp_orientation(lamp):
    """update lamp object aim point, and tilt/orientation widgets"""
    aimx = st.session_state[f"aim_x_{lamp.lamp_id}"]
    aimy = st.session_state[f"aim_y_{lamp.lamp_id}"]
    aimz = st.session_state[f"aim_z_{lamp.lamp_id}"]
    lamp.aim(aimx, aimy, aimz)
    st.session_state[f"orientation_{lamp.lamp_id}"] = lamp.heading
    st.session_state[f"tilt_{lamp.lamp_id}"] = lamp.bank


def update_from_tilt(lamp, room):
    """update tilt+aim point in lamp, and aim point widget"""
    tilt = st.session_state[f"tilt_{lamp.lamp_id}"]
    lamp.set_tilt(tilt, dimensions=room.dimensions)
    update_lamp_aim_point(lamp)


def update_from_orientation(lamp, room):
    """update orientation+aim point in lamp, and aim point widget"""
    orientation = st.session_state[f"orientation_{lamp.lamp_id}"]
    lamp.set_orientation(orientation, room.dimensions)
    update_lamp_aim_point(lamp)


def update_lamp_aim_point(lamp):
    """reset aim point widget if any other parameter has been altered"""
    st.session_state[f"aim_x_{lamp.lamp_id}"] = lamp.aimx
    st.session_state[f"aim_y_{lamp.lamp_id}"] = lamp.aimy
    st.session_state[f"aim_z_{lamp.lamp_id}"] = lamp.aimz


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
    if not isinstance(zone, CalcZone):
        keys = [
            f"name_{zone.zone_id}",
            f"x_{zone.zone_id}",
            f"y_{zone.zone_id}",
            f"x_spacing_{zone.zone_id}",
            f"y_spacing_{zone.zone_id}",
            f"offset_{zone.zone_id}" f"visible_{zone.zone_id}",
        ]
        if isinstance(zone, CalcPlane):
            keys.append(f"height_{zone.zone_id}")
        elif isinstance(zone, CalcVol):
            keys.append(f"zdim_{zone.zone_id}")
            keys.append(f"zspace_{zone.zone_id}")
        remove_keys(keys)


def remove_keys(keys):
    """remove parameters from widget"""
    for key in keys:
        del st.session_state[key]


def add_keys(keys, vals):
    """initialize widgets with parameters"""
    for key, val in zip(keys, vals):
        st.session_state[key] = val


def add_standard_zones(room):
    """pre-populate the calc zone list. cached so it only runs once."""

    fluence = CalcVol(
        zone_id="WholeRoomFluence",
        name="Whole Room Fluence",
        x1=0,
        x2=room.x,
        y1=0,
        y2=room.y,
        z1=0,
        z2=room.z,
    )

    height = 1.9 if room.units == "meters" else 6.23

    skinzone = CalcPlane(
        zone_id="SkinLimits",
        name="Skin Dose (8 Hours)",
        height=height,
        x1=0,
        x2=room.x,
        y1=0,
        y2=room.y,
        vert=False,
        horiz=True,
        fov80=False,
        dose=True,
        hours=8,
    )
    eyezone = CalcPlane(
        zone_id="EyeLimits",
        name="Eye Dose (8 Hours)",
        height=height,
        x1=0,
        x2=room.x,
        y1=0,
        y2=room.y,
        vert=True,
        horiz=False,
        fov80=True,
        dose=True,
        hours=8,
    )
    for zone in [fluence, skinzone, eyezone]:
        room.add_calc_zone(zone)
        initialize_zone(zone)
    return room


def get_lamp_position(lamp_idx, x, y, num_divisions=100):
    """for every new lamp, guess a reasonable position to initialize it in"""
    xp = np.linspace(0, x, num_divisions + 1)
    yp = np.linspace(0, y, num_divisions + 1)
    xidx, yidx = _get_idx(lamp_idx, num_divisions=num_divisions)
    return xp[xidx], yp[yidx]


def _get_idx(num_points, num_divisions=100):
    grid_size = (num_divisions, num_divisions)
    return _place_points(grid_size, num_points)[-1]


def _place_points(grid_size, num_points):
    M, N = grid_size
    grid = np.zeros(grid_size)
    points = []

    # Place the first point in the center
    center = (M // 2, N // 2)
    points.append(center)
    grid[center] = 1  # Marking the grid cell as occupied

    for _ in range(1, num_points):
        max_dist = -1
        best_point = None

        for x in range(M):
            for y in range(N):
                if grid[x, y] == 0:
                    # Calculate the minimum distance to all existing points
                    min_point_dist = min(
                        [np.sqrt((x - px) ** 2 + (y - py) ** 2) for px, py in points]
                    )
                    # Calculate the distance to the nearest boundary
                    min_boundary_dist = min(x, M - 1 - x, y, N - 1 - y)
                    # Find the point where the minimum of these distances is maximized
                    min_dist = min(min_point_dist, min_boundary_dist)

                    if min_dist > max_dist:
                        max_dist = min_dist
                        best_point = (x, y)

        if best_point:
            points.append(best_point)
            grid[best_point] = 1  # Marking the grid cell as occupied
    return points


def get_ies_files():
    """placeholder until I get to grabbing the ies files off the website"""
    # set lamps
    # root = Path("./ies_files")
    # p = root.glob("**/*")
    # ies_files = [x for x in p if x.is_file() and x.suffix == ".ies"]
    # return ies_files

    BASE_URL = 'https://assay.osluv.org/static/assay/'

    index_data = requests.get(f'{BASE_URL}/index.json').json()

    output = {}
    for guid, data in index_data.items():
        output[data['reporting_name']] =  f'{BASE_URL}/{data["slug"]}.ies'

    return output