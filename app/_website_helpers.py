import streamlit as st
import numpy as np
import pandas as pd
import requests
from pathlib import Path
from guv_calcs.lamp import Lamp
from guv_calcs.calc_zone import CalcPlane, CalcVol, CalcZone
from ._widget import (
    initialize_lamp,
    initialize_zone,
    clear_lamp_cache,
    clear_zone_cache,
    update_lamp_aim_point,
    update_lamp_orientation,
)

ss = st.session_state
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"


def add_standard_zones(room):
    """pre-populate the calc zone list"""

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


def add_new_zone(room):
    """necessary logic for adding new calc zone to room and to state"""
    clear_zone_cache(room)
    # initialize calculation zone
    new_zone_idx = len(room.calc_zones) + 1
    new_zone_id = f"CalcZone{new_zone_idx}"
    # this zone object contains nothing but the name and ID and will be
    # replaced by a CalcPlane or CalcVol object
    new_zone = CalcZone(zone_id=new_zone_id, enabled=False)
    # add to room
    room.add_calc_zone(new_zone)
    # select for editing
    ss.editing = "zones"
    ss.selected_zone_id = new_zone_id
    clear_lamp_cache(room)


def add_new_lamp(room, name=None, interactive=True, defaults={}):
    """necessary logic for adding new lamp to room and to state"""
    clear_zone_cache(room)
    clear_lamp_cache(room)
    # initialize lamp
    new_lamp_idx = len(room.lamps) + 1
    # set initial position
    new_lamp_id = f"Lamp{new_lamp_idx}"
    name = new_lamp_id if name is None else name
    x, y = get_lamp_position(lamp_idx=new_lamp_idx, x=room.x, y=room.y)
    new_lamp = Lamp(
        lamp_id=new_lamp_id,
        name=name,
        x=defaults.get("x", x),
        y=defaults.get("y", y),
        z=defaults.get("z", room.z - 0.1),
        spectral_weight_source=WEIGHTS_URL,
    )
    new_lamp.set_tilt(defaults.get("tilt", 0))
    new_lamp.set_orientation(defaults.get("orientation", 0))
    new_lamp.rotate(defaults.get("rotation", 0))
    update_lamp_aim_point(new_lamp)
    update_lamp_orientation(new_lamp)
    # add to session and to room
    room.add_lamp(new_lamp)
    if interactive:
        # select for editing
        initialize_lamp(new_lamp)
        ss.editing = "lamps"
        ss.selected_lamp_id = new_lamp.lamp_id
    else:
        return new_lamp_id


def get_lamp_position(lamp_idx, x, y, num_divisions=100):
    """get the default position for an additional new lamp"""
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


def get_disinfection_table(fluence, room):
    """
    Retrieve and format inactivtion data for this room.

    Currently assumes all lamps are GUV222. in the future will need something
    cleverer than this
    """

    wavelength = 222

    fname = Path("data/disinfection_table.csv")
    df = pd.read_csv(fname)
    df = df[df["Medium"] == "Aerosol"]
    df = df[df["wavelength [nm]"] == wavelength]

    # calculate eACH before filling nans
    k1 = df["k1 [cm2/mJ]"].fillna(0).astype(float)
    k2 = df["k2 [cm2/mJ]"].fillna(0).astype(float)
    f = df["% resistant"].str.rstrip("%").astype("float").fillna(0) / 100
    eACH = (k1 * (1 - f) + k2 - k2 * (1 - f)) * fluence * 3.6

    volume = room.get_volume()
    # convert to cubic feet for cfm
    if room.units == "meters":
        volume = volume / (0.3048 ** 3)
    cadr_uv_cfm = eACH * volume / 60
    cadr_uv_lps = cadr_uv_cfm * 0.47195

    df["eACH-UV"] = eACH.round(2)
    df["CADR-UV [cfm]"] = cadr_uv_cfm.round(2)
    df["CADR-UV [lps]"] = cadr_uv_lps.round(2)

    newkeys = [
        "eACH-UV",
        "CADR-UV [cfm]",
        "CADR-UV [lps]",
        "Organism",
        "Species",
        "Strain",
        "Type (Viral)",
        "Enveloped (Viral)",
        "k1 [cm2/mJ]",
        "k2 [cm2/mJ]",
        "% resistant",
        "Medium (specific)",
        "Full Citation",
    ]
    df = df[newkeys].fillna(" ")
    df = df.rename(
        columns={"Medium (specific)": "Medium", "Full Citation": "Reference"}
    )
    df = df.sort_values("Species")

    return df


def make_file_list():
    """generate current list of lampfile options, both locally uploaded and from assays.osluv.org"""
    SELECT_LOCAL = "Select local file..."
    vendorfiles = list(ss.vendored_lamps.keys())
    uploadfiles = list(ss.uploaded_files.keys())
    options = [None] + vendorfiles + uploadfiles + [SELECT_LOCAL]
    ss.lampfile_options = options


def get_local_ies_files():
    """placeholder until I get to grabbing the ies files off the website"""
    root = Path("./data/ies_files")
    p = root.glob("**/*")
    ies_files = [x for x in p if x.is_file() and x.suffix == ".ies"]
    return ies_files


def get_ies_files():
    """retrive ies files from osluv website"""
    BASE_URL = "https://assay.osluv.org/static/assay"

    index_data = requests.get(f"{BASE_URL}/index.json").json()

    ies_files = {}
    spectra = {}

    for guid, data in index_data.items():
        filename = data["slug"]
        name = data["reporting_name"]
        if data.get("sketch", False):
            name += " (PRERELEASE DATA)"
        ies_files[name] = f"{BASE_URL}/{filename}.ies"
        spectra[name] = f"{BASE_URL}/{filename}-spectrum.csv"

    return index_data, ies_files, spectra
