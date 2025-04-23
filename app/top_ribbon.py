import streamlit as st
from guv_calcs.calc_zone import CalcPlane, CalcVol, CalcZone
from app.lamp_utils import add_new_lamp
from app.widget import (
    initialize_lamp,
    initialize_zone,
    initialize_room,
    # initialize_results,
    initialize_project,
    clear_lamp_cache,
    clear_zone_cache,
    show_results,
)

ss = st.session_state
ADD_LAMP = "Add new luminaire"
ADD_ZONE = "Add new calculation zone"


def top_ribbon():

    c = st.columns([1, 1, 1, 2, 2, 1])

    # with c[0]:
    c[0].button("About", on_click=show_about, use_container_width=True)
    c[1].button(
        "Project", disabled=False, on_click=show_project, use_container_width=True
    )
    c[2].button("Edit Room", on_click=show_room, use_container_width=True)
    # c[3].button(
    # "Add Luminaire", on_click=add_new_lamp, use_container_width=True
    # )
    lamp_names = ["Select luminaire ... "]
    lamp_names += [lamp.name for lamp in ss.room.lamps.values()]
    lamp_names += [ADD_LAMP]
    lamp_ids = [None] + [lamp_id for lamp_id in ss.room.lamps.keys()] + [ADD_LAMP]
    lamp_sel_idx = lamp_ids.index(ss.selected_lamp_id)
    # if 'lamp_select' not in ss:
    # ss['lamp_select']=lamp_sel_idx
    c[3].selectbox(
        "Select luminaire to edit",
        options=range(len(lamp_names)),
        format_func=lambda x: lamp_names[x],
        on_change=update_lamp_select,
        args=[lamp_ids],
        index=lamp_sel_idx,
        label_visibility="collapsed",
        key="lamp_select",
    )

    # c[4].button(
    # "Add Calc Zone", on_click=add_new_zone, use_container_width=True
    # )

    zone_names = ["Select calculation zone ... "]
    zone_names += [zone.name for zone in ss.room.calc_zones.values()]
    zone_names += [ADD_ZONE]
    zone_ids = [None] + [zone_id for zone_id in ss.room.calc_zones.keys()] + [ADD_ZONE]
    zone_sel_idx = zone_ids.index(ss.selected_zone_id)
    c[4].selectbox(
        "Select calculation zone to edit",
        options=range(len(zone_names)),
        format_func=lambda x: zone_names[x],
        on_change=update_zone_select,
        args=[zone_ids],
        index=zone_sel_idx,
        label_visibility="collapsed",
        key="zone_select",
    )

    if check_recalculation():
        button_type = "primary"
    else:
        button_type = "secondary"

    c[5].button(
        "Calculate!",
        on_click=calculate,
        type=button_type,
        use_container_width=True,
    )


def check_recalculation():
    recalculate = False
    if any([v.enabled and v.filedata is not None for v in ss.room.lamps.values()]):
        CALC = ss.room.calc_state != ss.room.get_calc_state()
        UPDATE = ss.room.update_state != ss.room.get_update_state()
        if CALC or UPDATE:
            recalculate = True
    return recalculate


def show_about():
    """update sidebar to show about/instructions"""
    ss.editing = "about"
    clear_lamp_cache()
    clear_zone_cache()


def show_project():
    """update sidebar to show save/load options"""
    ss.editing = "project"
    initialize_project()
    clear_lamp_cache()
    clear_zone_cache()


def show_room():
    """update sidebar to show room editing interface"""
    ss.editing = "room"
    initialize_room()
    clear_lamp_cache()
    clear_zone_cache()


def update_lamp_select(lamp_ids):
    """update logic to display new lamp selection in sidebar"""

    clear_lamp_cache()  # first clear out anything old
    ss.selected_lamp_id = lamp_ids[ss["lamp_select"]]
    # print(ss["lamp_select"])
    # if ss["lamp_select"] in lamp_names:
    # ss.selected_lamp_id = lamp_names[ss["lamp_select"]]
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


def update_zone_select(zone_ids):
    """update logic to display new zone selection in sidebar"""
    clear_zone_cache()
    ss.selected_zone_id = zone_ids[ss["zone_select"]]
    # if ss["zone_select"] in zone_names:
    # ss.selected_zone_id = zone_names[ss["zone_select"]]
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
    with st.spinner("Calculating...", show_time=True):
        ss.room.calculate()
    show_results()


def add_new_zone():
    """necessary logic for adding new calc zone to room and to state"""
    # clear_zone_cache()
    # initialize calculation zone
    new_zone_idx = len(ss.room.calc_zones) + 1
    new_zone_id = f"CalcZone{new_zone_idx}"
    # this zone object contains nothing but the name and ID and will be
    # replaced by a CalcPlane or CalcVol object
    new_zone = CalcZone(zone_id=new_zone_id, enabled=False)
    # add to room
    ss.room.add_calc_zone(new_zone)
    # select for editing
    ss.editing = "zones"
    ss.selected_zone_id = new_zone_id
    clear_lamp_cache()
