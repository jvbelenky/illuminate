import streamlit as st
import requests
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from guv_calcs.room import Room
from guv_calcs.calc_zone import CalcPlane, CalcVol
from guv_calcs._website_helpers import (
    add_new_lamp,
    add_new_zone,
    get_ies_files,
    get_local_ies_files,
    add_standard_zones,
    # get_disinfection_table,
    make_file_list,
    print_standard_zones,
)
from guv_calcs._widget import (
    initialize_lamp,
    initialize_zone,
    remove_lamp,
    remove_zone,
    update_lamp_name,
    update_zone_name,
    update_lamp_visibility,
    update_zone_visibility,
    update_lamp_position,
    update_lamp_orientation,
    update_from_tilt,
    update_from_orientation,
    update_plane_dimensions,
    update_vol_dimensions,
    clear_lamp_cache,
    clear_zone_cache,
    update_room,
    initialize_room,
)
import warnings

warnings.filterwarnings("ignore")
# layout / page setup
st.set_page_config(
    page_title="GUV Calcs",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.set_option("deprecation.showPyplotGlobalUse", False)  # silence this warning
st.write(
    "<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True
)
ss = st.session_state

SELECT_LOCAL = "Select local file..."
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]

if "lampfile_options" not in ss:
    ies_files = get_local_ies_files()  # local files for testing
    vendored_lamps = get_ies_files()  # files from assays.osluv.org
    ss.vendored_lamps = vendored_lamps
    options = [None] + list(vendored_lamps.keys()) + [SELECT_LOCAL]
    ss.lampfile_options = options

# Check and initialize session state variables
if "room" not in ss:
    ss.room = Room()
    ss.room = add_standard_zones(ss.room)
    
    preview_lamp = st.query_params.get("preview_lamp")
    if preview_lamp:
        lamp_id = add_new_lamp(ss.room, interactive=False)
        lamp = ss.room.lamps[f'Lamp{lamp_id}']
        fdata = requests.get(ss.vendored_lamps[preview_lamp]).content
        lamp.reload(filename=preview_lamp, filedata=fdata)
        ss.room.calculate()
        ss.editing = "results"
        st.rerun()

room = ss.room

if "editing" not in ss:
    ss.editing = None  # determines what displays in the sidebar

if "selected_lamp_id" not in ss:
    ss.selected_lamp_id = None  # use None when no lamp is selected

if "selected_zone_id" not in ss:
    ss.selected_zone_id = None  # use None when no lamp is selected

if "uploaded_files" not in ss:
    ss.uploaded_files = {}

if "fig" not in ss:
    ss.fig = go.Figure()
    # Adding an empty scatter3d trace
    ss.fig.add_trace(
        go.Scatter3d(
            x=[0],  # No data points yet
            y=[0],
            z=[0],
            opacity=0,
            showlegend=False,
            customdata=["placeholder"],
        )
    )
    ss.eyefig = plt.figure()
    ss.skinfig = plt.figure()
fig = ss.fig


# Set up overall layout
left_pane, right_pane = st.columns([4, 1])

with st.sidebar:
    # Lamp editing sidebar
    if ss.editing == "lamps" and ss.selected_lamp_id is not None:
        st.subheader("Edit Luminaire")
        selected_lamp = room.lamps[ss.selected_lamp_id]

        # name
        st.text_input(
            "Name",
            key=f"name_{selected_lamp.lamp_id}",
            on_change=update_lamp_name,
            args=[selected_lamp],
        )

        # File input
        fname_idx = ss.lampfile_options.index(selected_lamp.filename)
        fname = st.selectbox(
            "Select lamp",
            ss.lampfile_options,
            index=fname_idx,
            key=f"file_{selected_lamp.lamp_id}",
        )

        # determine fdata from fname
        if fname == SELECT_LOCAL:
            uploaded_file = st.file_uploader(
                "Upload a file", type="ies", key=f"upload_{selected_lamp.lamp_id}"
            )
            if uploaded_file is not None:
                fdata = uploaded_file.read()
                fname = uploaded_file.name
                # add the uploaded file to the session state and upload
                ss.uploaded_files[fname] = fdata
                make_file_list()
            else:
                fdata = None
        elif fname is None:
            fdata = None
        else:
            # only reload if different from before
            if fname != selected_lamp.filename:
                try:
                    lampdata = ss.vendored_lamps[fname]
                    fdata = requests.get(lampdata).content
                except KeyError:
                    fdata = ss.uploaded_files[fname]

        # now both fname and fdata are set. the lamp object handles it if they are None.
        if fname != selected_lamp.filename and fdata != selected_lamp.filedata:
            selected_lamp.reload(filename=fname, filedata=fdata)

        # plot if there is data to plot with
        if selected_lamp.filedata is not None:
            iesfig, iesax = selected_lamp.plot_ies()
            st.pyplot(iesfig, use_container_width=True)

        ########################################################
        ### Somewhere in here there should be spectra stuff!

        # if SELECT_LOCAL and selected_lamp.spectra is None:
        # # button appears prompting user to upload spectra
        # st.button("Upload spectra")
        # uploaded_spectra = st.file_uploader(
        # "Upload spectra CSV", key=f"spectra_upload_{selected_lamp.lamp_id}"
        # )
        # if uploaded_spectra is not None:
        # load_spectra(selected_lamp)
        # else:
        # st.write("In order for GUV photobiological safety calculations to be accurate, a spectra is required. Please upload a .csv file with exactly 1 header row, where the first column is Wavelength, and the second column is intensity. :red[If a spectra is not provided, photobiological safety calculations will be inaccurate.]")

        # Position inputs
        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input(
                "Position X",
                min_value=0.0,
                step=0.1,
                key=f"pos_x_{selected_lamp.lamp_id}",
                on_change=update_lamp_position,
                args=[selected_lamp],
            )
        with col2:
            st.number_input(
                "Position Y",
                min_value=0.0,
                step=0.1,
                key=f"pos_y_{selected_lamp.lamp_id}",
                on_change=update_lamp_position,
                args=[selected_lamp],
            )
        with col3:
            st.number_input(
                "Position Z",
                min_value=0.0,
                step=0.1,
                key=f"pos_z_{selected_lamp.lamp_id}",
                on_change=update_lamp_position,
                args=[selected_lamp],
            )

        # Rotation input
        angle = st.number_input(
            "Rotation",
            min_value=0.0,
            max_value=360.0,
            step=1.0,
            key=f"rotation_{selected_lamp.lamp_id}",
        )
        selected_lamp.rotate(angle)
        st.write("Set aim point")

        # Aim point inputs
        col4, col5, col6 = st.columns(3)
        with col4:
            st.number_input(
                "Aim X",
                key=f"aim_x_{selected_lamp.lamp_id}",
                on_change=update_lamp_orientation,
                args=[selected_lamp],
            )
        with col5:
            st.number_input(
                "Aim Y",
                key=f"aim_y_{selected_lamp.lamp_id}",
                on_change=update_lamp_orientation,
                args=[selected_lamp],
            )
        with col6:
            st.number_input(
                "Aim Z",
                key=f"aim_z_{selected_lamp.lamp_id}",
                on_change=update_lamp_orientation,
                args=[selected_lamp],
            )

        st.write("Set tilt and orientation")
        col7, col8 = st.columns(2)
        with col7:
            st.number_input(
                "Tilt",
                format="%.1f",
                step=1.0,
                key=f"tilt_{selected_lamp.lamp_id}",
                on_change=update_from_tilt,
                args=[selected_lamp, room],
            )
        with col8:
            st.number_input(
                "Orientation",
                format="%.1f",
                step=1.0,
                key=f"orientation_{selected_lamp.lamp_id}",
                on_change=update_from_orientation,
                args=[selected_lamp, room],
            )

        selected_lamp.enabled = st.checkbox(
            "Enabled",
            on_change=update_lamp_visibility,
            args=[selected_lamp],
            key=f"enabled_{selected_lamp.lamp_id}",
        )

        del_button = col7.button(
            "Delete Lamp", type="primary", use_container_width=True
        )
        close_button = col8.button("Close", use_container_width=True)

        if close_button:  # maybe replace with an enable/disable button?
            ss.editing = None
            ss.selected_lamp_id = None
            if selected_lamp.filename is None:
                room.remove_lamp(selected_lamp.lamp_id)
                remove_lamp(selected_lamp)
            st.rerun()
        if del_button:
            room.remove_lamp(selected_lamp.lamp_id)
            remove_lamp(selected_lamp)
            ss.editing = None
            ss.selected_lamp_id = None
            st.rerun()
    # calc zone editing sidebar
    elif ss.editing in ["zones", "planes", "volumes"] and ss.selected_zone_id:
        st.subheader("Edit Calculation Zone")
        if ss.selected_zone_id in SPECIAL_ZONES:
            DISABLED = True
        else:
            DISABLED = False

        if ss.editing == "zones":
            cola, colb = st.columns([3, 1])
            calc_types = ["Plane", "Volume"]
            zone_type = cola.selectbox("Select calculation type", options=calc_types)
            colb.write("")
            colb.write("")
            if colb.button("Go"):
                calc_ids = room.calc_zones.keys()
                if zone_type == "Plane":
                    idx = len([v for v in calc_ids if "Plane" in v]) + 1
                    new_zone = CalcPlane(
                        zone_id=ss.selected_zone_id,
                        name="CalcPlane" + str(idx),
                    )
                    ss.editing = "planes"
                elif zone_type == "Volume":
                    idx = len([v for v in calc_ids if "Vol" in v]) + 1
                    new_zone = CalcVol(
                        zone_id=ss.selected_zone_id,
                        name="CalcVol" + str(idx),
                    )
                    ss.editing = "volumes"
                room.add_calc_zone(new_zone)
                initialize_zone(new_zone)
                st.rerun()
        elif ss.editing in ["planes", "volumes"]:
            selected_zone = room.calc_zones[ss.selected_zone_id]
            st.text_input(
                "Name",
                key=f"name_{selected_zone.zone_id}",
                on_change=update_zone_name,
                args=[selected_zone],
                disabled=DISABLED,
            )

        if ss.editing == "planes":

            col1, col2 = st.columns([2, 1])
            # xy dimensions and height
            col1.number_input(
                "Height",
                min_value=0.0,
                key=f"height_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            col2.write("")
            col2.write("")
            col2.write(room.units)
            col2, col3 = st.columns(2)
            with col2:
                st.number_input(
                    "X1",
                    min_value=0.0,
                    key=f"x1_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "X2",
                    min_value=0.0,
                    key=f"x2_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "X spacing",
                    min_value=0.01,
                    key=f"x_spacing_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                    disabled=False,
                )
            with col3:
                st.number_input(
                    "Y1",
                    min_value=0.0,
                    key=f"y1_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "Y2",
                    min_value=0.0,
                    key=f"y2_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "Y spacing",
                    min_value=0.01,
                    key=f"y_spacing_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                    disabled=False,
                )

            # Set calculation type (vertical / horizontal / all angles)
            options = ["All angles", "Horizontal irradiance", "Vertical irradiance"]
            if not selected_zone.vert and not selected_zone.horiz:
                calc_type_index = 0
            if selected_zone.horiz and not selected_zone.vert:
                calc_type_index = 1
            if not selected_zone.horiz and selected_zone.vert:
                calc_type_index = 2
            calc_type = st.selectbox(
                "Calculation type", options, index=calc_type_index, disabled=DISABLED
            )
            if calc_type == "All angles":
                selected_zone.horiz = False
                selected_zone.vert = False
            elif calc_type == "Horizontal irradiance":
                selected_zone.horiz = True
                selected_zone.vert = False
            elif calc_type == "Vertical irradiance":
                selected_zone.horiz = False
                selected_zone.vert = True

            # Toggle 80 degree field of view
            selected_zone.fov80 = st.checkbox(
                "Field of View 80°",
                key=f"fov80_{selected_zone.zone_id}",
                disabled=DISABLED,
            )

            # Set dose vs irradiance
            value_options = ["Irradiance (uW/cm2)", "Dose (mJ/cm2)"]
            value_index = 1 if selected_zone.dose else 0
            value_type = st.selectbox(
                "Value display type",
                options=value_options,
                index=value_index,
                disabled=DISABLED,
            )
            if value_type == "Dose (mJ/cm2)":
                selected_zone.set_value_type(dose=True)
                dose_time = st.number_input(
                    "Exposure time (hours)",
                    value=selected_zone.hours,
                    disabled=DISABLED,
                )
                selected_zone.set_dose_time(dose_time)
            elif value_type == "Irradiance (uW/cm2)":
                selected_zone.set_value_type(dose=False)

            st.checkbox(
                "Offset",
                key=f"offset_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=False,
            )

        elif ss.editing == "volumes":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.number_input(
                    "X1",
                    min_value=0.0,
                    key=f"x1_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "X2",
                    min_value=0.0,
                    key=f"x2_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "X spacing",
                    min_value=0.01,
                    key=f"x_spacing_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=False,
                )
            with col2:
                st.number_input(
                    "Y1",
                    min_value=0.0,
                    key=f"y1_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "Y2",
                    min_value=0.0,
                    key=f"y2_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "Y spacing",
                    min_value=0.01,
                    key=f"y_spacing_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=False,
                )
            with col3:
                st.number_input(
                    "Z1",
                    min_value=0.0,
                    key=f"z1_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "Z2",
                    min_value=0.0,
                    key=f"z2_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=DISABLED,
                )
                st.number_input(
                    "Z spacing",
                    min_value=0.01,
                    key=f"z_spacing_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                    disabled=False,
                )

            st.checkbox(
                "Offset",
                key=f"offset_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=False,
            )
        if ss.editing == "zones":
            del_button = st.button("Cancel", use_container_width=True, disabled=False)
            close_button = None
        elif ss.editing in ["planes", "volumes"]:

            selected_zone.enable = st.checkbox(
                "Enabled",
                # value=selected_zone.enable,
                on_change=update_zone_visibility,
                args=[selected_zone],
                key=f"enabled_{selected_zone.zone_id}",
            )
            col7, col8 = st.columns(2)
            del_button = col7.button(
                "Delete",
                type="primary",
                use_container_width=True,
                disabled=DISABLED,
            )
            close_button = col8.button(
                "Close", use_container_width=True, disabled=False
            )

        if close_button:  # maybe replace with an enable/disable button?
            if not isinstance(selected_zone, (CalcPlane, CalcVol)):
                remove_zone(selected_zone)
                room.remove_calc_zone(ss.selected_zone_id)
            ss.editing = None
            ss.selected_zone_id = None
            st.rerun()
        if del_button:
            room.remove_calc_zone(ss.selected_zone_id)
            remove_zone(selected_zone)
            ss.editing = None
            ss.selected_zone_id = None
            st.rerun()
    # room editing sidebar
    elif ss.editing == "room":
        st.header("Edit Room")

        st.subheader("Dimensions")
        col_a, col_b, col_c = st.columns(3)

        col_a.number_input(
            "Room length (x)",
            key="room_x",
            on_change=update_room,
            args=[room],
        )
        col_b.number_input(
            "Room width (y)",
            key="room_y",
            on_change=update_room,
            args=[room],
        )
        col_c.number_input(
            "Room height (z)",
            key="room_z",
            on_change=update_room,
            args=[room],
        )
        st.subheader("Units")
        st.write("Coming soon")

        unitindex = 0 if room.units == "meters" else 1
        units = st.selectbox(
            "Room units",
            ["meters", "feet"],
            index=unitindex,
            key="room_units",
            on_change=update_room,
            disabled=True,
        )

        st.subheader("Reflectance")
        st.write("Coming soon")
        col1, col2, col3 = st.columns(3)
        col1.number_input(
            "Ceiling",
            min_value=0,
            max_value=1,
            key="reflectance_ceiling",
            on_change=update_room,
            args=[room],
            disabled=True,
        )
        col2.number_input(
            "North Wall",
            min_value=0,
            max_value=1,
            key="reflectance_north",
            on_change=update_room,
            args=[room],
            disabled=True,
        )
        col3.number_input(
            "East Wall",
            min_value=0,
            max_value=1,
            key="reflectance_east",
            on_change=update_room,
            args=[room],
            disabled=True,
        )
        col1.number_input(
            "South Wall",
            min_value=0,
            max_value=1,
            key="reflectance_south",
            on_change=update_room,
            args=[room],
            disabled=True,
        )
        col2.number_input(
            "West Wall",
            min_value=0,
            max_value=1,
            key="reflectance_west",
            on_change=update_room,
            args=[room],
            disabled=True,
        )
        col3.number_input(
            "Floor",
            min_value=0,
            max_value=1,
            key="reflectance_floor",
            on_change=update_room,
            args=[room],
            disabled=True,
        )

        st.subheader("Indoor Chemistry")
        st.write("Coming soon")
        st.number_input(
            "Ozone Decay Constant",
            min_value=0,
            key="ozone_decay_constant",
            disabled=True,
        )

        close_button = st.button("Close", use_container_width=True)
        if close_button:
            ss.editing = None
            st.rerun()
    elif ss.editing == "results":
        st.title("Results")

        # do some checks first. do we actually have any lamps?
        msg = "You haven't added any luminaires yet! Try adding a luminaire by clicking the `Add Luminaire` button, and then hit `Calculate`"
        if not room.lamps:
            st.warning(msg)
        elif all(lamp.filedata is None for lampid, lamp in room.lamps.items()):
            st.warning(msg)

        # check that all positions of lamps and calc zones are where they're supposed to be
        msgs = room.check_positions()
        for msg in msgs:
            if msg is not None:
                st.warning(msg, icon="⚠️")

        print_standard_zones(room)

        # Display all other results
        if any(key not in SPECIAL_ZONES for key in room.calc_zones.keys()):
            st.subheader("User Defined Calculation Zones")
            for zone_id, zone in room.calc_zones.items():
                vals = zone.values
                if vals is not None:
                    st.subheader(zone.name, ":")
                    st.write("Average:", round(vals.mean(), 3))
                    st.write("Min:", round(vals.min(), 3))
                    st.write("Max:", round(vals.max(), 3))

        st.write("")
        st.write("")
        st.write("")
        close_button = st.button("Close", use_container_width=True)
        if close_button:
            ss.editing = None
            st.rerun()
    else:
        st.title("Welcome to GUV-Calcs!")
        st.header(
            "A free and open source simulation tool for germicidal UV applications"
        )
        st.write(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        )

        show_results = st.button(
            "Show results", use_container_width=True, key="results_tab"
        )

        if show_results:
            ss.editing = "results"
            clear_lamp_cache(room)
            clear_zone_cache(room)
            st.rerun()

        # col1,col2 = st.columns(2)
        # add_lamp = col1.button("Add lamp",use_container_width=True,key='addlamp_tab')
        # add_calc_zone = col2.button("Add calc zone",use_container_width=True,key="addzone_tab")
        # calculate = col1.button("Calculate!",type="primary",use_container_width=True,key="calculate_tab")
        # show_results = col2.button("Show results",use_container_width=True,key="results_tab")
        # if add_lamp:
        # add_new_lamp(room)
        # if add_calc_zone:
        # add_new_zone(room)
        # if calculate:
        # room.calculate()
        # ss.editing = "results"
        # # clear out any other selected objects and remove ones that haven't been fully initialized
        # clear_lamp_cache(room)
        # clear_zone_cache(room)
        # st.rerun()


with right_pane:
    calculate = st.button("Calculate!", type="primary", use_container_width=True)
    edit_room = st.button("Edit Room", use_container_width=True)

    # Dropdown menus for luminaires; map display names to IDs
    lamp_names = {None: None}
    for lamp_id, lamp in room.lamps.items():
        lamp_names[lamp.name] = lamp_id
    lamp_sel_idx = list(lamp_names.values()).index(ss.selected_lamp_id)
    selected_lamp_name = st.selectbox(
        "Select luminaire", options=list(lamp_names), index=lamp_sel_idx
    )
    selected_lamp_id = lamp_names[selected_lamp_name]
    if ss.selected_lamp_id != selected_lamp_id:
        # if different, update and rerun
        ss.selected_lamp_id = selected_lamp_id
        if ss.selected_lamp_id is not None:
            # if lamp is selected, open editing pane
            ss.editing = "lamps"
            selected_lamp = room.lamps[ss.selected_lamp_id]
            # initialize widgets in editing pane
            initialize_lamp(selected_lamp)
            # clear widgets of anything to do with zone editing if it's currently loaded
            clear_zone_cache(room)
        st.rerun()

    add_lamp = st.button("Add Luminaire", use_container_width=True)

    # Drop down menu for calculation zones
    zone_names = {None: None}
    for zone_id, zone in room.calc_zones.items():
        zone_names[zone.name] = zone_id
    zone_sel_idx = list(zone_names.values()).index(ss.selected_zone_id)
    selected_zone_name = st.selectbox(
        "Select calculation zone", options=list(zone_names), index=zone_sel_idx
    )
    selected_zone_id = zone_names[selected_zone_name]
    if ss.selected_zone_id != selected_zone_id:
        ss.selected_zone_id = selected_zone_id
        if ss.selected_zone_id is not None:
            selected_zone = room.calc_zones[ss.selected_zone_id]
            if isinstance(selected_zone, CalcPlane):
                ss.editing = "planes"
                initialize_zone(selected_zone)
            elif isinstance(selected_zone, CalcVol):
                ss.editing = "volumes"
                initialize_zone(selected_zone)
            else:
                ss.editing = "zones"
            clear_lamp_cache(room)
        st.rerun()
    add_calc_zone = st.button("Add Calculation Zone", use_container_width=True)

    # st.write("")
    # show_results = st.button("Show results")

    if calculate:
        room.calculate()
        ss.editing = "results"
        # clear out any other selected objects and remove ones that haven't been fully initialized
        clear_lamp_cache(room)
        clear_zone_cache(room)
        st.rerun()

    if edit_room:
        ss.editing = "room"
        initialize_room(room)
        clear_lamp_cache(room)
        clear_zone_cache(room)
        st.rerun()

    if add_lamp:
        add_new_lamp(room)

    if add_calc_zone:
        add_new_zone(room)

    # if show_results:
    # ss.editing = "results"
    # clear_lamp_cache(room)
    # clear_zone_cache(room)
    # st.rerun()

# plot
with left_pane:
    # fig, ax = room.plot(select_id=ss.selected_lamp_id)
    # st.pyplot(fig,use_container_width=True)
    if ss.selected_lamp_id:
        select_id = ss.selected_lamp_id
    elif ss.selected_zone_id:
        select_id = ss.selected_zone_id
    else:
        select_id = None
    fig = room.plotly(fig=fig, select_id=select_id)
    st.plotly_chart(fig, use_container_width=True, height=750)
