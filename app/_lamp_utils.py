import streamlit as st
from pathlib import Path
import requests
import numpy as np
import matplotlib.pyplot as plt
from guv_calcs.lamp import Lamp
from app._widget_utils import (
    set_val,
    initialize_lamp,
    update_lamp_aim_point,
    update_lamp_orientation,
    clear_zone_cache,
)

ss = st.session_state
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
SELECT_LOCAL = "Select local file..."


def add_new_lamp(name=None, interactive=True, defaults={}):
    """necessary logic for adding new lamp to room and to state"""
    # initialize lamp
    new_lamp_idx = len(ss.room.lamps) + 1
    # set initial position
    new_lamp_id = f"Lamp{new_lamp_idx}"
    name = new_lamp_id if name is None else name
    x, y = get_lamp_position(lamp_idx=new_lamp_idx, x=ss.room.x, y=ss.room.y)
    new_lamp = Lamp(
        lamp_id=new_lamp_id,
        name=name,
        x=defaults.get("x", x),
        y=defaults.get("y", y),
        z=defaults.get("z", ss.room.z - 0.1),
        spectral_weight_source=WEIGHTS_URL,
    )
    new_lamp.set_tilt(defaults.get("tilt", 0))
    new_lamp.set_orientation(defaults.get("orientation", 0))
    new_lamp.rotate(defaults.get("rotation", 0))
    update_lamp_aim_point(new_lamp)
    update_lamp_orientation(new_lamp)
    # add to session and to room
    ss.room.add_lamp(new_lamp)
    # remove any zone stuff in the buffer
    clear_zone_cache()
    if interactive:
        # select for editing
        initialize_lamp(new_lamp)
        ss.editing = "lamps"
        ss.selected_lamp_id = new_lamp.lamp_id
    else:
        load_prepopulated_lamp(new_lamp, new_lamp.name)


def load_lamp(lamp):
    """update lamp filename from widget"""
    fname = set_val(f"file_{lamp.lamp_id}", lamp.filename)
    fdata = None
    spectra_data = None
    if fname in ss.vendored_spectra.keys():
        load_prepopulated_lamp(lamp, fname)
    elif fname in ss.uploaded_files.keys():
        # previously uploaded files
        fdata = ss.uploaded_files[fname]
        _load_lamp(lamp, fname, fdata, spectra_data)
    # elif fname == SELECT_LOCAL:
    else:
        _load_lamp(lamp, fname, fdata, spectra_data)


def load_prepopulated_lamp(lamp, fname):
    """load prepopulated lamp from osluv server"""
    # files from osluv server
    lampdata = ss.vendored_lamps[fname]
    fdata = requests.get(lampdata).content
    spectra_source = ss.vendored_spectra[fname]
    spectra_data = requests.get(spectra_source).content
    lamp.reload(filename=fname, filedata=fdata)
    _load_spectra(lamp, spectra_data)


def load_uploaded_lamp(lamp):
    """load the .ies file of a user-uploaded file"""
    uploaded_file = set_val(f"upload_{lamp.lamp_id}", None)

    if uploaded_file is not None:
        fname = uploaded_file.name
        if fname in ss.uploaded_files:
            fdata = ss.uploaded_files[fname]
        else:
            fdata = uploaded_file.read()
            # add the uploaded file to the session state
            ss.uploaded_files[fname] = fdata
            make_file_list()
        # load into lamp object
        lamp.reload(filename=fname, filedata=fdata)
        # load spectra if present
        load_uploaded_spectra(lamp)


def load_uploaded_spectra(lamp):
    """load the .csv file of a user-uploaded spectra"""
    # first check if we've loaded it already
    if lamp.filename in ss.uploaded_spectras:
        spectra_data = ss.uploaded_spectras[lamp.filename]
    else:
        uploaded_spectra = set_val(f"spectra_upload_{lamp.lamp_id}", None)
        if uploaded_spectra is not None:
            # add to list
            spectra_data = uploaded_spectra.read()
            ss.uploaded_spectras[lamp.filename] = spectra_data
        else:
            spectra_data = None
    _load_spectra(lamp, spectra_data)


def _load_lamp(lamp, fname=None, fdata=None, spectra_data=None):
    lamp.reload(filename=fname, filedata=fdata)
    _load_spectra(lamp, spectra_data)


def _load_spectra(lamp, data=None):
    lamp.load_spectra(data)
    # prep figure
    if len(lamp.spectra) > 0:
        fig, ax = plt.subplots()
        ss.spectrafig = lamp.plot_spectra(fig=fig, title="")


def make_file_list():
    """generate current list of lampfile options, both locally uploaded and from assays.osluv.org"""
    vendorfiles = list(ss.vendored_lamps.keys())
    uploadfiles = list(ss.uploaded_files.keys())
    ss.lamp_options = [None] + vendorfiles + uploadfiles + [SELECT_LOCAL]
    return ss.lamp_options


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
    reports = {}

    for guid, data in index_data.items():
        filename = data["slug"]
        name = data["reporting_name"]
        if data.get("sketch", False):
            name += " (PRERELEASE DATA)"
        ies_files[name] = f"{BASE_URL}/{filename}.ies"
        spectra[name] = f"{BASE_URL}/{filename}-spectrum.csv"
        reports[name] = f"{BASE_URL}/{filename}.html"

    return index_data, ies_files, spectra, reports


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
