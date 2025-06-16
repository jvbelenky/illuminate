import streamlit as st
from app.init_app import initialize, room_plot
from app.top_ribbon import top_ribbon
from app.results import results_page
from app.sidebar.lamp import lamp_sidebar
from app.sidebar.zone import zone_sidebar
from app.sidebar.room import room_sidebar
from app.sidebar.project import project_sidebar
from app.sidebar.default import default_sidebar

# from app._widget import show_results

# layout / page setup
st.set_page_config(
    page_title="Illuminate",
    layout="wide",
    initial_sidebar_state="expanded",
)
# st.set_option("deprecation.showPyplotGlobalUse", False)  # silence this warning
st.markdown(
    "<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True
)

# Remove whitespace from the top of the page and sidebar
st.markdown(
    """
        <style>
               .css-18e3th9 {
                    padding-top: 0rem;
                    padding-bottom: 10rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
               .css-1d391kg {
                    padding-top: 3.5rem;
                    padding-right: 1rem;
                    padding-bottom: 3.5rem;
                    padding-left: 1rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)

CONTACT_STR = "Questions? Comments? Found a bug? Want a feature? E-mail contact@osluv.org, or stay anonymous by using [this form](https://docs.google.com/forms/d/e/1FAIpQLSdDzLD3bJVmFvW_M3Pj9H5_91GL1RbTey_eXRSXO-ZBMyLJ-w/viewform)"

# Check and initialize session state variables
ss = st.session_state
if "init" not in ss:
    ss.init = True
    initialize()

top_ribbon()
if ss.show_results or ss.editing is not None:
    left_pane, right_pane = st.columns([2, 3])
else:
    left_pane, right_pane = st.columns([1, 100])


with left_pane:
    if ss.editing is not None:
        if ss.editing == "lamps" and ss.selected_lamp_id is not None:
            lamp_sidebar()
        elif ss.editing in ["zones", "planes", "volumes"] and ss.selected_zone_id:
            zone_sidebar()
        elif ss.editing == "room":
            room_sidebar()
        elif ss.editing == "about":
            default_sidebar()
        elif ss.editing == "project":
            project_sidebar()
        else:
            st.write("")
        if ss.show_results:
            # add this here since it'll look nicer than on the results side
            st.markdown(CONTACT_STR)
    else:
        if ss.show_results:
            room_plot()
            st.markdown(CONTACT_STR)
        # if not ss.show_results, then this is an empty panel

with right_pane:
    cols = st.columns(2)
    show_room = st.button("Show Updated Room", use_container_width=True)
    if ss.show_results:
        if show_room and ss.editing is not None:
            room_plot()
            ss.show_room = False
        results_page()
    else:
        if show_room or ss.show_room:
            room_plot()
            ss.show_room = False
        st.markdown(CONTACT_STR)


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
