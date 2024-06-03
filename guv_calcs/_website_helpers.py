import numpy as np
import requests
from pathlib import Path
import pandas as pd
import streamlit as st
from guv_calcs.lamp import Lamp
from guv_calcs.calc_zone import CalcPlane, CalcVol, CalcZone
from ._widget import (
    # initialize_lamp,
    # initialize_zone,
    clear_lamp_cache,
    clear_zone_cache,
)

ss = st.session_state
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"


def get_disinfection_table(fluence, room):

    """assumes all lamps are GUV222. in the future will need something cleverer than this"""

    wavelength = 222

    fname = Path("./data/disinfection_table.csv")
    df = pd.read_csv(fname)
    df = df[df["Medium"] == "Aerosol"]
    df = df[df["wavelength [nm]"] == wavelength]
    keys = ["Species", "Medium (specific)", "k [cm2/mJ]", "Ref", "Full Citation"]

    df = df[keys].fillna(" ")

    volume = room.get_volume()

    # convert to cubic feet for cfm
    if room.units == "meters":
        volume = volume / (0.3048 ** 3)

    df["eACH-UV"] = (df["k [cm2/mJ]"] * fluence * 3.6).round(2)
    df["CADR-UV [cfm]"] = (df["eACH-UV"] * volume / 60).round(2)
    df["CADR-UV [lps]"] = (df["CADR-UV [cfm]"] * 0.47195).round(2)
    num_papers = len(df["Ref"].unique())
    df["Ref"] = np.linspace(1, num_papers + 2, num_papers + 2).astype(int)
    df = df.rename(
        columns={"Medium (specific)": "Medium", "Full Citation": "Reference"}
    )
    # references = df["Full Citation"].tolist()
    # for i, ref in enumerate(references):

    newkeys = [
        "Species",
        # "Medium",
        "k [cm2/mJ]",
        "eACH-UV",
        "CADR-UV [cfm]",
        "CADR-UV [lps]",
        "Reference",
    ]
    df = df[newkeys]
    return df


def print_standard_zones(room):
    """
    display results of special calc zones

    TODO: dropdown menu of which standard to check against
    """
    st.subheader("Efficacy", divider="grey")
    fluence = room.calc_zones["WholeRoomFluence"]
    if fluence.values is not None:
        avg_fluence = round(fluence.values.mean(), 3)
        fluence_str = ":blue[" + str(avg_fluence) + "] μW/cm2"
    else:
        fluence_str = None
    st.write("Average fluence: ", fluence_str)

    if fluence.values is not None:
        df = get_disinfection_table(avg_fluence, room)
        st.dataframe(df, hide_index=True)

    st.subheader("Photobiological Safety", divider="grey")
    skin_limit, eye_limit = get_limits()
    skin = room.calc_zones["SkinLimits"]
    eye = room.calc_zones["EyeLimits"]
    if skin.values is not None:
        skin_max = round(skin.values.max(), 3)
        color = "red" if skin_max > skin_limit else "blue"
        skin_str = ":" + color + "[" + str(skin_max) + "] " + skin.units
    else:
        skin_str = None
    if eye.values is not None:
        eye_max = round(eye.values.max(), 3)
        color = "red" if eye_max > eye_limit else "blue"
        eye_str = ":" + color + "[" + str(eye_max) + "] " + eye.units
    else:
        eye_str = None

    col_1, col_2 = st.columns(2)

    with col_1:
        st.write("Max Skin Dose (8 Hours): ", skin_str)
        if skin.values is not None:
            st.pyplot(skin.plot_plane(), **{"transparent": "True"})
        else:
            st.write("(Not available)")

    with col_2:
        st.write("Max Eye Dose (8 Hours): ", eye_str)
        if eye.values is not None:
            st.pyplot(eye.plot_plane(), **{"transparent": "True"})
        else:
            st.write("(Not available)")

    # st.subheader("References", divider="grey")
    # st.write(references)


def get_limits():
    """
    return the eye and skin limits in mJ/cm2/8 hours
    currently a placeholder for future feature when user-defined standard
    selection determines the limits
    """
    skin_limit = 479
    eye_limit = 161
    return skin_limit, eye_limit


def add_new_lamp(room, interactive=True):
    # initialize lamp
    new_lamp_idx = len(room.lamps) + 1
    # set initial position
    xpos, ypos = get_lamp_position(lamp_idx=new_lamp_idx, x=room.x, y=room.y)
    new_lamp_id = f"Lamp{new_lamp_idx}"
    new_lamp = Lamp(
        lamp_id=new_lamp_id,
        x=xpos,
        y=ypos,
        z=room.z,
        spectral_weight_source=WEIGHTS_URL,
    )
    # add to session and to room
    room.add_lamp(new_lamp)
    # initialize_lamp(new_lamp)
    # Automatically select for editing
    ss.editing = "lamps"
    ss.selected_lamp_id = new_lamp.lamp_id
    if interactive:
        clear_zone_cache(room)
        st.rerun()
    else:
        return new_lamp_idx


def add_new_zone(room):
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
    st.rerun()


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
        # initialize_zone(zone)
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
        ies_files[data["reporting_name"]] = f"{BASE_URL}/{filename}.ies"
        spectra[data["reporting_name"]] = f"{BASE_URL}/{filename}-spectrum.csv"

    return ies_files, spectra
