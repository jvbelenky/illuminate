import streamlit as st
from guv_calcs.calc_zone import CalcPlane, CalcVol
from guv_calcs._website_helpers import add_new_lamp, add_new_zone
from guv_calcs._widget import (
    initialize_lamp,
    initialize_zone,
    initialize_room,
    clear_lamp_cache,
    clear_zone_cache,
)

ss = st.session_state


def top_ribbon(room):

    c = st.columns([1, 1, 1.5, 1, 1.5, 1, 1])
    edit_room = c[0].button("Edit Room  ", use_container_width=True)
    add_lamp = c[1].button("Add Luminaire", use_container_width=True)
    lamp_select(room, c[2])
    add_calc_zone = c[3].button("Add Calc Zone", use_container_width=True)
    zone_select(room, c[4])
    show_results = c[5].button("Show Results", use_container_width=True)
    calc = c[6].button("Calculate!", type="primary", use_container_width=True)

    # st.divider()
    if calc:
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

    if show_results:
        ss.editing = "results"
        clear_lamp_cache(room)
        clear_zone_cache(room)
        st.rerun()


def lamp_select(room, col=None):
    """drop down menu for selecting luminaires"""
    lamp_names = {"Select luminaire to edit": None}
    for lamp_id, lamp in room.lamps.items():
        lamp_names[lamp.name] = lamp_id
    lamp_sel_idx = list(lamp_names.values()).index(ss.selected_lamp_id)

    if col is None:
        selected_lamp_name = st.selectbox(
            "Select luminaire to edit", options=list(lamp_names), index=lamp_sel_idx, label_visibility="collapsed",
        )
    else:
        selected_lamp_name = col.selectbox(
            "Select luminaire to edit", options=list(lamp_names), index=lamp_sel_idx, label_visibility="collapsed",
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


def zone_select(room, col=None):
    """drop down menu for selecting calc zones"""
    zone_names = {"Select calc zone to edit": None}
    for zone_id, zone in room.calc_zones.items():
        zone_names[zone.name] = zone_id
    zone_sel_idx = list(zone_names.values()).index(ss.selected_zone_id)
    if col is None:
        selected_zone_name = st.selectbox(
            "Select calculation zone to edit", options=list(zone_names), index=zone_sel_idx, label_visibility="collapsed",
        )
    else:
        selected_zone_name = col.selectbox(
            "Select calculation zone to edit", options=list(zone_names), index=zone_sel_idx, label_visibility="collapsed",
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
