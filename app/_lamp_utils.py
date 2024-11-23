import streamlit as st
from pathlib import Path
import requests
import matplotlib.pyplot as plt
from guv_calcs import Lamp, Spectrum, new_lamp_position
from ._widget import (
    set_val,
    initialize_lamp,
    update_lamp_name,
    update_lamp_intensity_units,
    update_lamp_position,
    update_lamp_rotation,
    update_lamp_aim_point,
    update_lamp_orientation,
    update_from_tilt,
    update_from_orientation,
    update_lamp_visibility,
    clear_zone_cache,
    show_results,
)

ss = st.session_state
SELECT_LOCAL = "Select local file..."


def add_new_lamp(name=None, interactive=True, defaults={}):
    """necessary logic for adding new lamp to room and to state"""
    # initialize lamp
    new_lamp_idx = len(ss.room.lamps) + 1
    # set initial position
    new_lamp_id = f"Lamp{new_lamp_idx}"
    name = new_lamp_id if name is None else name

    x, y = new_lamp_position(lamp_idx=new_lamp_idx, x=ss.room.x, y=ss.room.y)
    new_lamp = Lamp(
        lamp_id=new_lamp_id,
        name=name,
        x=defaults.get("x", x),
        y=defaults.get("y", y),
        z=defaults.get("z", ss.room.z - 0.1),
        wavelength=222,
        guv_type="Krypton chloride (222 nm)",
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
    if fname is not SELECT_LOCAL:
        lamp.name = make_lamp_name(fname)
        ss[f"name_{lamp.lamp_id}"] = lamp.name

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
    # set name
    # load ies data
    fdata = requests.get(ss.vendored_lamps[fname]).content
    lamp.reload(filename=fname, filedata=fdata)
    # load spectra data
    spectra_data = requests.get(ss.vendored_spectra[fname]).content
    _load_spectra(lamp, spectra_data)


def load_uploaded_lamp(lamp):
    """load the .ies file of a user-uploaded file"""
    uploaded_file = set_val(f"upload_{lamp.lamp_id}", None)

    if uploaded_file is not None:
        fname = uploaded_file.name
        lamp.name = fname
        ss[f"name_{lamp.lamp_id}"] = fname
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


def make_lamp_name(fname):
    """Generate a unique name"""
    current_lamp_names = [lamp.name for lamp in ss.room.lamps.values()]
    if fname in current_lamp_names:
        matching_names = [n for n in current_lamp_names if fname in n]
        try:
            idexs = []
            for n in matching_names:
                try:
                    idexs.append(int(n[-1]))
                except:
                    continue
            name = fname + " - " + str(max(idexs) + 1)
        except ValueError:
            name = fname + " - 2"
    else:
        name = fname
    return name


def load_uploaded_spectra(lamp):
    """load the .csv file of a user-uploaded spectra"""
    # first check if we've loaded it already
    if lamp.filename in ss.uploaded_spectras:
        spectra_data = ss.uploaded_spectras[lamp.filename]
    else:
        uploaded_spectra = set_val(f"spectra_upload_{lamp.lamp_id}", None)
        if uploaded_spectra is not None:
            spectra_data = uploaded_spectra.read()
            try:
                Spectrum.from_file(spectra_data)
                # add to list if it can load successfully
                ss.uploaded_spectras[lamp.filename] = spectra_data
                ss.warning_message = None
            except ValueError:  # if spectra cannot correctly load, set to zero
                ss.warning_message = "Spectra file is not valid. Double check that it is a .csv with the first column corresponding to wavelengths, and the second column corresponding to relative intensities."
                spectra_data = None
        else:
            spectra_data = None

    _load_spectra(lamp, spectra_data)


def _load_lamp(lamp, fname=None, fdata=None, spectra_data=None):
    lamp.reload(filename=fname, filedata=fdata)
    _load_spectra(lamp, spectra_data)


def _load_spectra(lamp, data=None):
    lamp.load_spectra(data)
    # prep figure
    if lamp.spectra is not None:
        fig, ax = plt.subplots()
        ss.spectrafig, _ = lamp.spectra.plot(
            fig=fig, ax=ax, title="", weights=True, label=True
        )


def make_file_list():
    """generate current list of lampfile options, both locally uploaded and from assays.osluv.org"""
    vendorfiles = list(ss.vendored_lamps.keys())
    uploadfiles = list(ss.uploaded_files.keys())
    if ss.selected_lamp.guv_type == "Krypton chloride (222 nm)":
        ss.lamp_options = [None] + vendorfiles + uploadfiles + [SELECT_LOCAL]
    else:
        ss.lamp_options = [None] + uploadfiles + [SELECT_LOCAL]
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


# widgets
def lamp_name_widget(lamp):
    return st.text_input(
        "Name",
        key=f"name_{lamp.lamp_id}",
        on_change=update_lamp_name,
        args=[lamp],
    )


def lamp_type_widget(lamp):
    options = list(ss.guv_dict.keys())
    return st.selectbox(
        "Lamp type",
        options=options,
        key=f"guv_type_{lamp.lamp_id}",
        on_change=update_wavelength,
        args=[lamp],
    )


def update_wavelength(lamp):
    lamp.guv_type = set_val(f"guv_type_{lamp.lamp_id}", lamp.guv_type)
    lamp.wavelength = ss.guv_dict[lamp.guv_type]
    lamp.reload()
    if ss.show_results:
        show_results()


def update_wavelength_select(lamp):
    lamp.wavelength = set_val("wavelength_select", lamp.wavelength)
    if ss.show_results:
        show_results()


def update_custom_wavelength(lamp):
    lamp.wavelength = set_val("custom_wavelength_input", lamp.wavelength)
    if ss.show_results:
        show_results()


def update_custom_wavelength_check():
    ss.custom_wavelength = set_val("custom_wavelength_check", ss.custom_wavelength)


def lamp_select_widget(lamp):
    ss.lamp_options = make_file_list()
    if lamp.filename in ss.lamp_options:
        fname_idx = ss.lamp_options.index(lamp.filename)
    else:
        fname_idx = 0
        lamp.reload(filename=None, filedata=None)  # unload
        lamp.load_spectra(spectra_source=None)  # unload spectra if any
    if lamp.guv_type == "Krypton chloride (222 nm)":
        helptext = "This dropdown list is populated by data from the OSLUV project 222 nm UV characterization database which may be viewed at https://assay.osluv.org/. You may also upload your own photometric and spectra files."
    else:
        helptext = "There are currently no characterized lamps for the selected lamp type. Please provide your own photometric files."

    cols = st.columns([3, 1])
    cols[0].selectbox(
        "Select lamp",
        ss.lamp_options,
        index=fname_idx,
        on_change=load_lamp,
        args=[lamp],
        key=f"file_{lamp.lamp_id}",
        help=helptext,
    )
    cols[1].selectbox(
        "Intensity units",
        options=["mW/sr", "uW/cm²"],
        index=0 if lamp.intensity_units.lower() == "mw/sr" else 1,
        on_change=update_lamp_intensity_units,
        args=[lamp],
        key=f"intensity_units_{lamp.lamp_id}",
        help="Most photometric files are in units of mW/Sr, but some GUV photometric files may be in uW/cm². If your calculation seems suspiciously off by a large factor, try changing this option.",
    )


def lamp_upload_widget(lamp):
    return st.file_uploader(
        "Upload .ies file",
        type="ies",
        on_change=load_uploaded_lamp,
        args=[lamp],
        key=f"upload_{lamp.lamp_id}",
    )


def spectra_upload_widget(lamp):
    return st.file_uploader(
        "Upload spectra .csv file",
        type="csv",
        on_change=load_uploaded_spectra,
        args=[lamp],
        key=f"spectra_upload_{lamp.lamp_id}",
        help="A valid spectra file is a .csv where the first column is a list of wavelengths, and the second column is a list of corresponding relative intensities.",
    )


def lamp_x_widget(lamp):
    return st.number_input(
        "Position X",
        min_value=0.0,
        step=0.1,
        key=f"pos_x_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )


def lamp_y_widget(lamp):
    return st.number_input(
        "Position Y",
        min_value=0.0,
        step=0.1,
        key=f"pos_y_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )


def lamp_z_widget(lamp):
    return st.number_input(
        "Position Z",
        min_value=0.0,
        step=0.1,
        key=f"pos_z_{lamp.lamp_id}",
        on_change=update_lamp_position,
        args=[lamp],
    )


def lamp_angle_widget(lamp):
    return st.number_input(
        "Rotation",
        min_value=0.0,
        max_value=360.0,
        step=1.0,
        key=f"rotation_{lamp.lamp_id}",
        on_change=update_lamp_rotation,
        args=[lamp],
    )


def lamp_aimx_widget(lamp):
    return st.number_input(
        "Aim X",
        key=f"aim_x_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )


def lamp_aimy_widget(lamp):
    return st.number_input(
        "Aim Y",
        key=f"aim_y_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )


def lamp_aimz_widget(lamp):
    return st.number_input(
        "Aim Z",
        key=f"aim_z_{lamp.lamp_id}",
        on_change=update_lamp_orientation,
        args=[lamp],
    )


def lamp_tilt_widget(lamp):
    return st.number_input(
        "Tilt",
        format="%.1f",
        step=1.0,
        key=f"tilt_{lamp.lamp_id}",
        on_change=update_from_tilt,
        args=[lamp],
    )


def lamp_orientation_widget(lamp):
    return st.number_input(
        "Orientation",
        format="%.1f",
        step=1.0,
        key=f"orientation_{lamp.lamp_id}",
        on_change=update_from_orientation,
        args=[lamp],
    )


def lamp_enabled_widget(lamp):
    return st.checkbox(
        "Enabled",
        on_change=update_lamp_visibility,
        args=[lamp],
        key=f"enabled_{lamp.lamp_id}",
    )
