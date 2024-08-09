import streamlit as st
from app._init_app import initialize
from app._top_ribbon import top_ribbon
from app._plot import room_plot
from app._results import results_page
from app._lamp_sidebar import lamp_sidebar
from app._zone_sidebar import zone_sidebar
from app._sidebar import (
    room_sidebar,
    default_sidebar,
    project_sidebar,
)

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

CONTACT_STR = "Questions? Comments? Found a bug? Want a feature? E-mail contact-assay@osluv.org, or stay anonymous by using [this form](https://docs.google.com/forms/d/e/1FAIpQLSdDzLD3bJVmFvW_M3Pj9H5_91GL1RbTey_eXRSXO-ZBMyLJ-w/viewform)"

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

    if ss.show_results:
        results_page()
    else:
        show_room = st.button("Show Updated Room")
        if show_room or ss.show_room:
            room_plot()
            ss.show_room = False
        st.markdown(CONTACT_STR)
