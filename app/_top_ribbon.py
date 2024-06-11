import streamlit as st
from guv_calcs.calc_zone import CalcPlane, CalcVol
from app._website_helpers import add_new_lamp, add_new_zone
from app._widget import (
    initialize_lamp,
    initialize_zone,
    initialize_room,
    clear_lamp_cache,
    clear_zone_cache,
)

ss = st.session_state


def top_ribbon(room):

    c = st.columns([1, 1, 1, 1, 1.5, 1, 1.5, 1])

    # with c[0]:
    c[0].button("About", on_click=show_about, args=[room], use_container_width=True)
    c[1].button("Project", on_click=show_project, args=[room], use_container_width=True)
    c[2].button("Edit Room", on_click=show_room, args=[room], use_container_width=True)
    c[3].button(
        "Add Luminaire", on_click=add_new_lamp, args=[room], use_container_width=True
    )
    lamp_names = {"Select luminaire to edit": None}
    for lamp_id, lamp in room.lamps.items():
        lamp_names[lamp.name] = lamp_id
    lamp_sel_idx = list(lamp_names.values()).index(ss.selected_lamp_id)
    c[4].selectbox(
        "Select luminaire to edit",
        options=list(lamp_names),
        on_change=update_lamp_select,
        args=[lamp_names, room],
        index=lamp_sel_idx,
        label_visibility="collapsed",
        key="lamp_select",
    )

    c[5].button(
        "Add Calc Zone", on_click=add_new_zone, args=[room], use_container_width=True
    )

    zone_names = {"Select calc zone to edit": None}
    for zone_id, zone in room.calc_zones.items():
        zone_names[zone.name] = zone_id
    zone_sel_idx = list(zone_names.values()).index(ss.selected_zone_id)
    c[6].selectbox(
        "Select calculation zone to edit",
        options=list(zone_names),
        on_change=update_zone_select,
        args=[zone_names, room],
        index=zone_sel_idx,
        label_visibility="collapsed",
        key="zone_select",
    )

    c[7].button(
        "Calculate!",
        on_click=calculate,
        args=[room],
        type="primary",
        use_container_width=True,
    )


def show_about(room):
    """update sidebar to show about/instructions"""
    ss.editing = "about"
    clear_lamp_cache(room)
    clear_zone_cache(room)


def show_project(room):
    """update sidebar to show save/load options"""
    ss.editing = "project"
    clear_lamp_cache(room)
    clear_zone_cache(room)


def show_room(room):
    """update sidebar to show room editing interface"""
    ss.editing = "room"
    initialize_room(room)
    clear_lamp_cache(room)
    clear_zone_cache(room)


def update_lamp_select(lamp_names, room):
    """update logic to display new lamp selection in sidebar"""
    clear_lamp_cache(room)  # first clear out anything old
    ss.selected_lamp_id = lamp_names[ss["lamp_select"]]
    if ss.selected_lamp_id is not None:
        # if lamp is selected, open editing pane
        ss.editing = "lamps"
        selected_lamp = room.lamps[ss.selected_lamp_id]
        # initialize widgets in editing pane
        initialize_lamp(selected_lamp)
        # clear widgets of anything to do with zone editing if it's currently loaded
        clear_zone_cache(room)
    else:
        # this will only happen if users have selected the 'none' option in the dropdown menu
        ss.editing = None


def update_zone_select(zone_names, room):
    """update logic to display new zone selection in sidebar"""
    clear_zone_cache(room)
    ss.selected_zone_id = zone_names[ss["zone_select"]]
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
    else:
        # this will only happen if users have selected the 'none' option in the dropdown menu
        ss.editing = None


def calculate(room):
    """calculate and show results in right pane"""
    ss.show_results = True
    room.calculate()
