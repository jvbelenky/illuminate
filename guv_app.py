import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import requests
import plotly.graph_objs as go
from guv_calcs.room import Room
from guv_calcs.lamp import Lamp
from guv_calcs.calc_zone import CalcZone, CalcPlane, CalcVol
from guv_calcs._website_helpers import (
    get_lamp_position,
    get_ies_files,
    add_standard_zones,
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
)

# TODO:
# suppress that widget warning in the terminal (eventually, or whatever)
# figure out way to get plotly to show fullscreen
# calc zone plotting. for fluence/volumes: draw a dashed line box. for planes: scatterplot just like acuity.

# layout / page setup
st.set_page_config(
    page_title="GUV Calcs",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.set_option("deprecation.showPyplotGlobalUse", False)  # silence this warning
st.write(
    "<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True
)

# Check and initialize session state variables
if "room" not in st.session_state:
    st.session_state.room = Room()
    st.session_state.room = add_standard_zones(st.session_state.room)
room = st.session_state.room

if "editing" not in st.session_state:
    st.session_state.editing = None  # determines what displays in the sidebar

if "selected_lamp_id" not in st.session_state:
    st.session_state.selected_lamp_id = None  # use None when no lamp is selected

if "selected_lamp" not in st.session_state:
    st.session_state.selected_lamp = None

if "selected_zone_id" not in st.session_state:
    st.session_state.selected_zone_id = None  # use None when no lamp is selected

if "fig" not in st.session_state:
    st.session_state.fig = go.Figure()
    # Adding an empty scatter3d trace
    st.session_state.fig.add_trace(
        go.Scatter3d(
            x=[0],  # No data points yet
            y=[0],
            z=[0],
            opacity=0,
            showlegend=False,
        )
    )
fig = st.session_state.fig

# Set up overall layout
left_pane, right_pane = st.columns([4, 1])

vendored_lamps = get_ies_files() # (name, URL)

with st.sidebar:
    # Lamp editing sidebar
    if (
        st.session_state.editing == "lamps"
        and st.session_state.selected_lamp_id is not None
    ):
        st.subheader("Edit Luminaire")
        selected_lamp = room.lamps[st.session_state.selected_lamp_id]

        # name
        st.text_input(
            "Name",
            key=f"name_{selected_lamp.lamp_id}",
            on_change=update_lamp_name,
            args=[selected_lamp],
        )

        SELECT_LOCAL = "Select local file..."

        # File input
        options = [None] + list(vendored_lamps.keys()) + [SELECT_LOCAL]
        
        fname_idx = options.index(selected_lamp.filename)
        fname = st.selectbox(
            "Select lamp", options, key=f"file_{selected_lamp.lamp_id}", index=fname_idx
        )

        fdata = None

        if fname == SELECT_LOCAL:
            uploaded_file = st.file_uploader(
                "Upload a file", key=f"upload_{selected_lamp.lamp_id}"
            )
            if uploaded_file is not None:
                fdata = uploaded_file.read()

        if fname not in [None, SELECT_LOCAL]:
            if fname != selected_lamp.filename:
                if fdata is None:
                    fdata = requests.get(vendored_lamps[fname]).content
                selected_lamp.reload(fname, fdata)
            iesfig, iesax = selected_lamp.plot_ies()
            st.pyplot(iesfig, use_container_width=True)

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

        st.checkbox(
            "Show in plot",
            on_change=update_lamp_visibility,
            args=[selected_lamp],
            key=f"visible_{selected_lamp.lamp_id}",
        )

        del_button = col7.button(
            "Delete Lamp", type="primary", use_container_width=True
        )
        close_button = col8.button("Close", use_container_width=True)

        if close_button:  # maybe replace with an enable/disable button?
            st.session_state.editing = None
            st.session_state.selected_lamp_id = None
            if selected_lamp.filename is None:
                room.remove_lamp(selected_lamp.lamp_id)
                remove_lamp(selected_lamp)
            st.rerun()
        if del_button:
            room.remove_lamp(selected_lamp.lamp_id)
            remove_lamp(selected_lamp)
            st.session_state.editing = None
            st.session_state.selected_lamp_id = None
            st.rerun()
    # calc zone editing sidebar
    elif (
        st.session_state.editing
        in ["zones", "planes", "volumes"]
        # and st.session_state.selected_zone_id
    ):
        st.subheader("Edit Calculation Zone")
        if st.session_state.editing == "zones":
            cola, colb = st.columns([3, 1])
            calc_types = ["Plane", "Volume"]
            zone_type = cola.selectbox("Select calculation type", options=calc_types)
            colb.write("")
            colb.write("")
            if colb.button("Go"):
                if zone_type == "Plane":
                    idx = len([val for val in room.calc_zones.keys() if "Plane" in val]) + 1
                    new_zone = CalcPlane(
                        zone_id=st.session_state.selected_zone_id,
                        name="CalcPlane" + str(idx),
                    )
                    st.session_state.editing = "planes"
                elif zone_type == "Volume":
                    idx = len([val for val in room.calc_zones.keys() if "Vol" in val]) + 1
                    new_zone = CalcVol(
                        zone_id=st.session_state.selected_zone_id, name="CalcVol" + str(idx)
                    )
                    st.session_state.editing = "volumes"
                room.add_calc_zone(new_zone)
                initialize_zone(new_zone)
                st.rerun()            
        elif st.session_state.editing in ["planes", "volumes"]:
            selected_zone = room.calc_zones[st.session_state.selected_zone_id]
            st.text_input(
                "Name",
                key=f"name_{selected_zone.zone_id}",
                on_change=update_zone_name,
                args=[selected_zone],
            )

        if st.session_state.editing == "planes":

            col1, col2 = st.columns([2, 1])
            # xy dimensions and height
            col1.number_input(
                "Height",
                min_value=0.0,
                key=f"height_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
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
                )
                st.number_input(
                    "X2",
                    min_value=0.0,
                    key=f"x2_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "X spacing",
                    min_value=0.01,
                    key=f"x_spacing_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                )
            with col3:
                st.number_input(
                    "Y1",
                    min_value=0.0,
                    key=f"y1_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "Y2",
                    min_value=0.0,
                    key=f"y2_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "Y spacing",
                    min_value=0.01,
                    key=f"y_spacing_{selected_zone.zone_id}",
                    on_change=update_plane_dimensions,
                    args=[selected_zone],
                )
            options = ["All angles", "Horizontal irradiance", "Vertical irradiance"]
            calc_type = st.selectbox("Calculation type", options, index=0)
            if calc_type == "Horizontal irradiance":
                selected_zone.vert = False
                selected_zone.horiz = True
            elif calc_type == "Vertical irradiance":
                selected_zone.vert = True
                selected_zone.horiz = False
            elif calc_type == "All angles":
                selected_zone.vert = False
                selected_zone.horiz = False

            selected_zone.fov80 = st.checkbox("Field of View 80°")

            value_options = ["Irradiance (uW/cm2)", "Dose (mJ/cm2)"]
            value_index = 1 if selected_zone.dose else 0
            value_type = st.selectbox(
                "Value display type", options=value_options, index=value_index
            )
            if value_type == "Dose (mJ/cm2)":
                selected_zone.set_value_type(dose=True)
                dose_time = st.number_input(
                    "Exposure time (hours)", value=selected_zone.hours
                )
                selected_zone.set_dose_time(dose_time)
            elif value_type == "Irradiance (uW/cm2)":
                selected_zone.set_value_type(dose=False)

            st.checkbox(
                "Offset",
                key=f"offset_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
            )

        elif st.session_state.editing == "volumes":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.number_input(
                    "X1",
                    min_value=0.0,
                    key=f"x1_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "X2",
                    min_value=0.0,
                    key=f"x2_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "X spacing",
                    min_value=0.01,
                    key=f"x_spacing_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
            with col2:
                st.number_input(
                    "Y1",
                    min_value=0.0,
                    key=f"y1_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "Y2",
                    min_value=0.0,
                    key=f"y2_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "Y spacing",
                    min_value=0.01,
                    key=f"y_spacing_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
            with col3:
                st.number_input(
                    "Z1",
                    min_value=0.0,
                    key=f"z1_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "Z2",
                    min_value=0.0,
                    key=f"z2_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )
                st.number_input(
                    "Z spacing",
                    min_value=0.01,
                    key=f"z_spacing_{selected_zone.zone_id}",
                    on_change=update_vol_dimensions,
                    args=[selected_zone],
                )

            st.checkbox(
                "Offset",
                key=f"offset_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
            )
        if st.session_state.editing == "zones":
            del_button = st.button("Cancel", use_container_width=True)
            close_button = None
        elif st.session_state.editing in ["planes", "volumes"]:

            st.checkbox(
                "Show in plot",
                on_change=update_zone_visibility,
                args=[selected_zone],
                key=f"visible_{selected_zone.zone_id}",
            )
            col7, col8 = st.columns(2)
            del_button = col7.button("Delete", type="primary", use_container_width=True)
            close_button = col8.button("Close", use_container_width=True)

        if close_button:  # maybe replace with an enable/disable button?
            if isinstance(selected_zone, CalcZone):
                remove_zone(selected_zone)
                room.remove_calc_zone(st.session_state.selected_zone_id)
            st.session_state.editing = None
            st.session_state.selected_zone_id = None
            st.rerun()
        if del_button:
            room.remove_calc_zone(st.session_state.selected_zone_id)
            remove_zone(selected_zone)
            st.session_state.editing = None
            st.session_state.selected_zone_id = None
            st.rerun()
    # room editing sidebar
    elif st.session_state.editing == "room":
        st.subheader("Edit Room")
        # set room dimensions and units
        col_a, col_b, col_c = st.columns(3)
        units = st.selectbox("Room units", ["meters", "feet"], index=0)

        x = col_a.number_input("Room length (x)", value=room.x)
        y = col_b.number_input("Room width (y)", value=room.y)
        z = col_c.number_input("Room height (z)", value=room.z)

        dimensions = np.array((x, y, z))
        if units != room.units:
            room.set_units(units)
            st.rerun()
        if (dimensions != room.dimensions).any():
            room.set_dimensions(dimensions)
            st.rerun()

        close_button = st.button("Close", use_container_width=True)
        if close_button:
            st.session_state.editing = None
            st.rerun()
    elif st.session_state.editing == "results":
        st.subheader("Results")
        for zone_id, zone in room.calc_zones.items():
            vals = zone.values
            st.write(zone.name, ":")
            st.write("Average:", round(vals.mean(), 3))
            st.write("Min:", round(vals.min(), 3))
            st.write("Max:", round(vals.max(), 3))

        st.write("")
        st.write("")
        st.write("")
        close_button = st.button("Close", use_container_width=True)
        if close_button:
            st.session_state.editing = None
            st.rerun()
    else:
        st.write("")

with right_pane:
    calculate = st.button("Calculate!", type="primary", use_container_width=True)
    # st.divider()
    edit_room = st.button("Edit Room", use_container_width=True)
    # st.divider()

    # Dropdown menus for luminaires; map display names to IDs
    lamp_names = {None: None}
    for lamp_id, lamp in room.lamps.items():
        lamp_names[lamp.name] = lamp_id
    lamp_sel_idx = list(lamp_names.values()).index(st.session_state.selected_lamp_id)
    selected_lamp_name = st.selectbox(
        "Select luminaire", options=list(lamp_names), index=lamp_sel_idx
    )
    selected_lamp_id = lamp_names[selected_lamp_name]
    if st.session_state.selected_lamp_id != selected_lamp_id:
        # if different, update and rerun
        st.session_state.selected_lamp_id = selected_lamp_id
        if st.session_state.selected_lamp_id is not None:
            # if lamp is selected, open editing pane
            st.session_state.editing = "lamps"
            selected_lamp = room.lamps[st.session_state.selected_lamp_id]
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
    zone_sel_idx = list(zone_names.values()).index(st.session_state.selected_zone_id)
    selected_zone_name = st.selectbox(
        "Select calculation zone", options=list(zone_names), index=zone_sel_idx
    )
    selected_zone_id = zone_names[selected_zone_name]
    if st.session_state.selected_zone_id != selected_zone_id:
        st.session_state.selected_zone_id = selected_zone_id
        if st.session_state.selected_zone_id is not None:
            selected_zone = room.calc_zones[st.session_state.selected_zone_id]
            if isinstance(selected_zone, CalcPlane):
                st.session_state.editing = "planes"
                initialize_zone(selected_zone)
            elif isinstance(selected_zone, CalcVol):
                st.session_state.editing = "volumes"
                initialize_zone(selected_zone)
            else:
                st.session_state.editing = "zones"
            clear_lamp_cache(room)
        st.rerun()
    add_calc_zone = st.button("Add Calculation Zone", use_container_width=True)

    st.write("")
    show_results = st.button("Show results")

    if calculate:
        room.calculate()
        st.session_state.editing = "results"
        # clear out any other selected objects and remove ones that haven't been fully initialized
        clear_lamp_cache(room)
        clear_zone_cache(room)
        st.rerun()

    if edit_room:
        st.session_state.editing = "room"
        clear_lamp_cache(room)
        clear_zone_cache(room)
        st.rerun()

    # Adding new lamps
    if add_lamp:
        # initialize lamp
        new_lamp_idx = len(room.lamps) + 1
        # set initial position
        xpos, ypos = get_lamp_position(lamp_idx=new_lamp_idx, x=room.x, y=room.y)
        new_lamp_id = f"Lamp{new_lamp_idx}"
        new_lamp = Lamp(lamp_id=new_lamp_id, x=xpos, y=ypos, z=room.z)
        # add to session and to room
        # st.session_state.lamps.append(new_lamp)
        room.add_lamp(new_lamp)
        initialize_lamp(new_lamp)
        # Automatically select for editing
        st.session_state.editing = "lamps"
        st.session_state.selected_lamp_id = new_lamp.lamp_id
        clear_zone_cache(room)
        st.rerun()

    # Adding new calculation zones
    if add_calc_zone:
        # initialize calculation zone
        new_zone_idx = len(room.calc_zones) + 1
        new_zone_id = f"CalcZone{new_zone_idx}"
        # this zone object contains nothing but the name and ID and will be
        # replaced by a CalcPlane or CalcVol object
        new_zone = CalcZone(
            zone_id=new_zone_id, visible=False
        )
        # add to room
        room.add_calc_zone(new_zone)
        # select for editing
        st.session_state.editing = "zones"
        st.session_state.selected_zone_id = new_zone_id
        clear_lamp_cache(room)
        st.rerun()

    if show_results:
        st.session_state.editing = "results"
        clear_lamp_cache(room)
        clear_zone_cache(room)
        st.rerun()

# plot
with left_pane:
    # fig, ax = room.plot(select_id=st.session_state.selected_lamp_id)
    # st.pyplot(fig,use_container_width=True)
    if st.session_state.selected_lamp_id:
        select_id = st.session_state.selected_lamp_id
    elif st.session_state.selected_zone_id:
        select_id = st.session_state.selected_zone_id
    else:
        select_id = None
    fig = room.plotly(fig=fig, select_id=select_id)
    st.plotly_chart(fig, use_container_width=True, height=750)
