import streamlit as st
from guv_calcs.calc_zone import CalcPlane, CalcVol
from ._results import get_disinfection_table
from ._zone_utils import add_new_zone
from ._plot import plot_species
from ._lamp_utils import add_new_lamp
from ._widget_utils import (
    initialize_lamp,
    initialize_zone,
    initialize_room,
    initialize_results,
    clear_lamp_cache,
    clear_zone_cache,
)

ss = st.session_state
ADD_LAMP = "Add new luminaire"
ADD_ZONE = "Add new calculation zone"


def top_ribbon():

    c = st.columns([1, 1, 1, 2, 2, 1, 1])

    # with c[0]:
    c[0].button("About", on_click=show_about, use_container_width=True)
    c[1].button(
        "Project", disabled=True, on_click=show_project, use_container_width=True
    )
    c[2].button("Edit Room", on_click=show_room, use_container_width=True)
    # c[3].button(
    # "Add Luminaire", on_click=add_new_lamp, use_container_width=True
    # )
    lamp_names = {"Select luminaire ... ": None}
    for lamp_id, lamp in ss.room.lamps.items():
        lamp_names[lamp.name] = lamp_id
    lamp_names[ADD_LAMP] = ADD_LAMP
    lamp_sel_idx = list(lamp_names.values()).index(ss.selected_lamp_id)
    c[3].selectbox(
        "Select luminaire to edit",
        options=list(lamp_names),
        on_change=update_lamp_select,
        args=[lamp_names],
        index=lamp_sel_idx,
        label_visibility="collapsed",
        key="lamp_select",
    )

    # c[4].button(
    # "Add Calc Zone", on_click=add_new_zone, use_container_width=True
    # )

    zone_names = {"Select calculation zone...": None}
    for zone_id, zone in ss.room.calc_zones.items():
        zone_names[zone.name] = zone_id
    zone_names[ADD_ZONE] = ADD_ZONE
    zone_sel_idx = list(zone_names.values()).index(ss.selected_zone_id)
    c[4].selectbox(
        "Select calculation zone to edit",
        options=list(zone_names),
        on_change=update_zone_select,
        args=[zone_names],
        index=zone_sel_idx,
        label_visibility="collapsed",
        key="zone_select",
    )

    c[5].button(
        "Show Results",
        on_click=show_results,
        use_container_width=True,
    )

    c[6].button(
        "Calculate!",
        on_click=calculate,
        type="primary",
        use_container_width=True,
    )


def show_about():
    """update sidebar to show about/instructions"""
    ss.editing = "about"
    clear_lamp_cache()
    clear_zone_cache()


def show_project():
    """update sidebar to show save/load options"""
    ss.editing = "project"
    clear_lamp_cache()
    clear_zone_cache()


def show_room():
    """update sidebar to show room editing interface"""
    ss.editing = "room"
    initialize_room()
    clear_lamp_cache()
    clear_zone_cache()


def update_lamp_select(lamp_names):
    """update logic to display new lamp selection in sidebar"""
    clear_lamp_cache()  # first clear out anything old
    if ss["lamp_select"] in lamp_names:
        ss.selected_lamp_id = lamp_names[ss["lamp_select"]]
    if ss.selected_lamp_id is None:
        # this will only happen if users have selected the 'none' option in the dropdown menu
        ss.editing = None
    elif ss.selected_lamp_id == ADD_LAMP:
        add_new_lamp()
    else:
        # if lamp is selected, open editing pane
        ss.editing = "lamps"
        selected_lamp = ss.room.lamps[ss.selected_lamp_id]
        # initialize widgets in editing pane
        initialize_lamp(selected_lamp)
        # clear widgets of anything to do with zone editing if it's currently loaded
        clear_zone_cache()


def update_zone_select(zone_names):
    """update logic to display new zone selection in sidebar"""
    clear_zone_cache()
    if ss["zone_select"] in zone_names:
        ss.selected_zone_id = zone_names[ss["zone_select"]]
    if ss.selected_zone_id is None:
        # this will only happen if users have selected the 'none' option in the dropdown menu
        ss.editing = None
    elif ss.selected_zone_id == ADD_ZONE:
        add_new_zone()
    else:
        selected_zone = ss.room.calc_zones[ss.selected_zone_id]
        if isinstance(selected_zone, CalcPlane):
            ss.editing = "planes"
            initialize_zone(selected_zone)
        elif isinstance(selected_zone, CalcVol):
            ss.editing = "volumes"
            initialize_zone(selected_zone)
        else:
            ss.editing = "zones"
        clear_lamp_cache()


def calculate():
    """calculate and show results in right pane"""
    ss.room.calculate()
    show_results()


def show_results():
    """show results in right panel"""
    initialize_results()
    ss.show_results = True
    # format the figure and disinfection table now so we don't redo it later
    fluence = ss.room.calc_zones["WholeRoomFluence"]
    if fluence.values is not None:
        avg_fluence = fluence.values.mean()
        ss.kdf = get_disinfection_table(avg_fluence)
        ss.kfig = plot_species(ss.kdf, avg_fluence)
