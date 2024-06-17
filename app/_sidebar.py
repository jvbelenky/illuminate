import streamlit as st
from app._widget import (
    update_room,
    update_standard,
    update_ozone,
    close_sidebar,
)

SELECT_LOCAL = "Select local file..."
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]
ss = st.session_state


def room_sidebar(room):
    """display room editing panel in sidebar"""
    cols = st.columns([10, 1])
    cols[0].subheader("Edit Room")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        args=[room],
        use_container_width=True,
        key="close_room",
    )

    st.subheader("Dimensions", divider="grey")
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

    st.subheader("Standards", divider="grey")
    standards = [
        "ANSI IES RP 27.1-22 (America) - UL8802",
        "ANSI IES RP 27.1-22 (America)",
        "IEC 62471-6:2022 (International)",
    ]

    st.selectbox(
        "Select photobiological safety standard",
        options=standards,
        on_change=update_standard,
        args=[room],
        key="room_standard",
        help="The ANSI IES RP 27.1-22 standard corresponds to the photobiological limits for UV exposure set by the American Conference of Governmental Industrial Hygienists (ACGIH), the relevant standard in the US. The IEC 62471-6:2022 standard corresponds to the limits set by the International Commission on Non-Ionizing Radiation Protection (ICNIRP), which apply most places outside of the US. Both standards indicate that the measurement should be taken at 1.8 meters up from the floor, but UL8802 (Ultraviolet (UV) Germicidal Equipment and Systems) indicates that it should be taken at 1.9 meters instead.",
    )

    st.subheader("Indoor Chemistry", divider="grey")
    # st.write("Coming soon")
    cols = st.columns(2)
    cols[0].number_input(
        "Air changes per hour from ventilation",
        on_change=update_ozone,
        args=[room],
        min_value=0.0,
        step=0.1,
        key="air_changes",
        help="Note that outdoor ozone is almost always at a higher concentration than indoor ozone. Increasing the air changes from ventilation will reduce the increase in ozone due to GUV, but may increase the total indoor ozone concentration. However, increasing ventilation will also increase the rate of removal of any secondary products that may form from the ozone.",
    )
    cols[1].number_input(
        "Ozone decay constant",
        on_change=update_ozone,
        args=[room],
        min_value=0.0,
        step=0.1,
        key="ozone_decay_constant",
        help="An initial ozone decay constant of 2.7 is typical of indoor environments (Nazaroff and Weschler; DOI: 10.1111/ina.12942); ",
    )

    st.subheader("Units", divider="grey")
    st.write("Coming soon")

    unitindex = 0 if room.units == "meters" else 1
    st.selectbox(
        "Room units",
        ["meters", "feet"],
        index=unitindex,
        key="room_units",
        on_change=update_room,
        disabled=True,
    )

    st.subheader("Reflectance", divider="grey")
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

    st.button(
        "Close",
        on_click=close_sidebar,
        args=[room],
        use_container_width=True,
    )


def project_sidebar(room):
    """sidebar content for saving and loading files"""
    cols = st.columns([10, 1])
    cols[0].header("Project")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        args=[room],
        key="close_project",
        use_container_width=True,
    )

    st.write("*Coming soon...*")

    st.subheader("Save Project", divider="grey")

    st.download_button(
        label="Save",
        data="{some_dummy_data}",
        file_name="illuminate.json",
        use_container_width=True,
        key="download_project",
        disabled=True,
    )

    st.subheader("Load Project", divider="grey")
    uploaded_file = st.file_uploader(
        "Load Project",
        type="json",
        on_change=None,
        key="upload_project",
        label_visibility="collapsed",
        disabled=True,
    )
    if uploaded_file is not None:
        pass


def default_sidebar(room):
    """default display of sidebar showing instructions"""
    cols = st.columns([10, 1])
    cols[0].title("Welcome to Illuminate-GUV!")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        args=[room],
        use_container_width=True,
        key="close_about",
    )

    st.header("A free and open source simulation tool for germicidal UV applications")
    st.subheader("Getting Started", divider="grey")
    st.write(
        """
        To run your first simulation, simply click on the `Add Luminaire` 
        button on the right panel, select a photometric file from the dropdown menu, 
        and click the red `Calculate` button to immediately see results.
        """
    )

    st.subheader("Editing the Room", divider="grey")
    st.write(
        """
        In the `Edit Room` menu, you can change the size of the room, the air changes from ventilation and ozone decay
        rate, as well as the photobiological safety standard to calculate for. Updating these options will update the 
        calculation zones, so be sure to hit `Calculate` again afterdoing so.
        """
    )

    st.subheader("Adding and Editing Luminaires", divider="grey")
    st.write(
        """
        For more complex simulations, you can configure the position and orientation of the luminaire,
        or add more luminaires. You can also upload your own photometric file - note that if you do this, you
        should also provide a spectrum file, or photobiological safety calculations may be inaccurate. 
        
        Note that if a luminaire is placed outside the room boundaries, it will not appear in the plot, 
        but will still participate in calculations, but not if you uncheck the box labeled `Enabled`.
        """
    )
    st.subheader("Adding and Editing Calculation Zones", divider="grey")
    st.write(
        """
        Illuminate-GUV comes pre-loaded with three key calculation zones important for 
        assessing the functioning of GUV systems. One is for assessing system efficacy--average 
        fluence in the room. The other two are for assessing photobiological 
        safety - the *spectrally weighted* horizontal irradiance taken at 1.8 or 1.9 meters 
        from the floor over an 8 hour period determines allowable skin exposure, while 
        *spectrally weighted* vertical irradiance at the same height with an 80 degree field 
        of view in the horizontal plane determines allowable eye exposure. These three special
        calculation zones are not possible to edit, except for the spacing of the grid, which 
        may be desirable for a finer calculation. They also can't be deleted, but they can be
        disabled.
        """
    )
    st.write(
        """
        You can also define your own calculation zones, whether a plane or a
        volume. Currently, only planes normal to the floor are supported. These calculation 
        zones will have their statistics displayed in the Results page alongside the built-in
        calculation zones.
        """
    )

    st.subheader("Plotting Interaction", divider="grey")
    st.write(
        """
        Click and drag anywhere in the plot to change the view mode. To remove a luminaire or calculation 
        zone from the plot, click on its entry in the legend. Note that invisible luminaires and calculation 
        zones still participate in calculations. Currently, the room plot is only for visualization, and it 
        is not possible to select and edit objects in the room by clicking on them.
        """
    )

    st.subheader("Features Under Development", divider="grey")
    st.write(
        """
        - **Saving and load projects**: Save all the parameters of a project as a .json blob, and upload again
        - **Mobile view**: Clean layout configured for mobile devices\n
        - **Exporting results**: Export the result of any calculation zone, or all calculation zones, for use with other modeling software
        - **Generating a report**: Generate a polished safety and efficacy report of an installation with a click of a button
        - **Copying objects**: Duplicate a luminaire or calculation zone
        - **Interactive plotting**: Place luminaires and draw calculation zones directly onto the interactive visualization plot
        - **Locally installable app**: Run easily as a desktop app without internet access
        - **Support for other GUV wavelengths**: Currently, only GUV222 with krypton-chloride lamps is supported. Future releases will also support GUV254        
        - **More accurate near-field modeling**: Definitions of GUV sources that take into account emission surface geometry and near-field radiation distribution.
        - *...and much more!*
        """
    )
