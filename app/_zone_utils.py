import streamlit as st
from guv_calcs.calc_zone import CalcPlane, CalcVol, CalcZone
from ._widget_utils import initialize_zone, clear_lamp_cache

ss = st.session_state


def add_standard_zones():
    """pre-populate the calc zone list"""

    fluence = CalcVol(
        zone_id="WholeRoomFluence",
        name="Whole Room Fluence",
        x1=0,
        x2=ss.room.x,
        y1=0,
        y2=ss.room.y,
        z1=0,
        z2=ss.room.z,
        show_values=False,
    )

    height = 1.9 if ss.room.units == "meters" else 6.23

    skinzone = CalcPlane(
        zone_id="SkinLimits",
        name="Skin Dose (8 Hours)",
        height=height,
        x1=0,
        x2=ss.room.x,
        y1=0,
        y2=ss.room.y,
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
        x2=ss.room.x,
        y1=0,
        y2=ss.room.y,
        vert=True,
        horiz=False,
        fov80=True,
        dose=True,
        hours=8,
    )
    for zone in [fluence, skinzone, eyezone]:
        ss.room.add_calc_zone(zone)
        initialize_zone(zone)


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
