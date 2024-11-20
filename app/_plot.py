import streamlit as st

ss = st.session_state


def room_plot():
    if ss.selected_lamp_id:
        select_id = ss.selected_lamp_id
    elif ss.selected_zone_id:
        select_id = ss.selected_zone_id
    else:
        select_id = None
    ss.fig = ss.room.plotly(fig=ss.fig, select_id=select_id)

    if ss.show_results:
        if ss.editing is None:
            ar_scale = 0.5
        else:
            ar_scale = 0.3  # this won't show
    else:
        if ss.editing is None:
            ar_scale = 0.8  # full middle page
        else:
            ar_scale = 0.6
    ss.fig.layout.scene.aspectratio.x *= ar_scale
    ss.fig.layout.scene.aspectratio.y *= ar_scale
    ss.fig.layout.scene.aspectratio.z *= ar_scale
    ss.fig.layout.scene.xaxis.range = ss.fig.layout.scene.xaxis.range[::-1]

    st.plotly_chart(ss.fig, use_container_width=True, height=750)
