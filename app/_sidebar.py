import streamlit as st
import json
import guv_calcs
from guv_calcs import Room
from ._widget import (
    initialize_room,
    initialize_zone,
    initialize_lamp,
    update_calc_zones,
    update_room,
    update_standard,
    update_ozone,
    close_sidebar,
)
from ._top_ribbon import show_results

SELECT_LOCAL = "Select local file..."
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]
ss = st.session_state


def room_sidebar():
    """display room editing panel in sidebar"""
    cols = st.columns([10, 1])
    cols[0].subheader("Edit Room")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        use_container_width=True,
        key="close_room",
    )

    st.subheader("Dimensions", divider="grey")
    col_a, col_b, col_c = st.columns(3)

    col_a.number_input(
        "Room length (x)",
        key="room_x",
        on_change=update_room,
    )
    col_b.number_input(
        "Room width (y)",
        key="room_y",
        on_change=update_room,
    )
    col_c.number_input(
        "Room height (z)",
        key="room_z",
        on_change=update_room,
    )

    st.subheader("Standards", divider="grey")
    
    st.selectbox(
        "Select photobiological safety standard",
        options=ss.standards,
        on_change=update_standard,
        key="room_standard",
        help="The ANSI IES RP 27.1-22 standard corresponds to the photobiological limits for UV exposure set by the American Conference of Governmental Industrial Hygienists (ACGIH). The IEC 62471-6:2022 standard corresponds to the limits set by the International Commission on Non-Ionizing Radiation Protection (ICNIRP). Both standards indicate that the measurement should be taken at 1.8 meters up from the floor, but UL8802 (Ultraviolet (UV) Germicidal Equipment and Systems) indicates that it should be taken at 1.9 meters instead. Additionally, though ANSI IES RP 27.1-22 indicates that eye exposure limits be taken with a 80 degere field of view parallel to the floor, considering only vertical irradiance, UL8802 indicates that measurements be taken in the 'worst case' direction, resulting in a stricter limit.",
    )
    st.subheader("Indoor Chemistry", divider="grey")
    cols = st.columns(2)
    with cols[0]:
        st.number_input(
            "Air changes per hour from ventilation",
            on_change=update_ozone,
            min_value=0.0,
            step=0.1,
            key="air_changes",
            help="Note that outdoor ozone is almost always at a higher concentration than indoor ozone. Increasing the air changes from ventilation will reduce the increase in ozone due to GUV, but may increase the total indoor ozone concentration. However, increasing ventilation will also increase the rate of removal of any secondary products that may form from the ozone.",
        )
    with cols[1]:
        st.number_input(
            "Ozone decay constant",
            on_change=update_ozone,
            min_value=0.0,
            step=0.1,
            key="ozone_decay_constant",
            help="An initial ozone decay constant of 2.7 is typical of indoor environments (Nazaroff and Weschler; DOI: 10.1111/ina.12942); ",
        )

    st.subheader("Units", divider="grey")
    st.write("Coming soon")

    unitindex = 0 if ss.room.units == "meters" else 1
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
        disabled=True,
    )
    col2.number_input(
        "North Wall",
        min_value=0,
        max_value=1,
        key="reflectance_north",
        on_change=update_room,
        disabled=True,
    )
    col3.number_input(
        "East Wall",
        min_value=0,
        max_value=1,
        key="reflectance_east",
        on_change=update_room,
        disabled=True,
    )
    col1.number_input(
        "South Wall",
        min_value=0,
        max_value=1,
        key="reflectance_south",
        on_change=update_room,
        disabled=True,
    )
    col2.number_input(
        "West Wall",
        min_value=0,
        max_value=1,
        key="reflectance_west",
        on_change=update_room,
        disabled=True,
    )
    col3.number_input(
        "Floor",
        min_value=0,
        max_value=1,
        key="reflectance_floor",
        on_change=update_room,
        disabled=True,
    )

    st.button(
        "Close",
        on_click=close_sidebar,
        use_container_width=True,
    )


def project_sidebar():
    """sidebar content for saving and loading files"""

    cols = st.columns([10, 1])
    cols[0].header("Project", divider="grey")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        key="close_project",
        use_container_width=True,
    )

    st.subheader
    col1, col2 = st.columns(2)

    col1.download_button(
        label="Save Project",
        data=ss.room.save(),
        file_name="illuminate.guv",
        use_container_width=True,
        key="download_project",
    )
    load = col2.button(
        "Load Project",
        use_container_width=True,
    )

    if load:
        st.file_uploader(
            "Load Project",
            type="guv",
            on_change=upload,
            key="upload_project",
            label_visibility="collapsed",
        )
    if ss.error_message is not None:
        st.error(ss.error_message)
    if ss.warning_message is not None:
        st.warning(ss.warning_message)

    st.header("Export", divider="grey")
    col3, col4 = st.columns(2)
    plots = st.checkbox("Include plots")
    lampfiles = st.checkbox("Include lamp .ies and spectrum files")
    col3.download_button(
        "Export All",
        data=ss.room.export_zip(
            include_plots=plots,
            include_lamp_plots=plots,
            include_lamp_files=lampfiles,
        ),
        file_name="illuminate.zip",
        use_container_width=True,
        key="export_all_project",
    )


def upload():
    """
    callback for uploading a .guv file
    """
    file_ok = False
    file = ss["upload_project"]
    if file is not None:
        try:
            string = file.read().decode("utf-8")
            # this just checks that the json is valid
            dct = json.loads(string)
            saved_version = dct["guv-calcs_version"]
            current_version = guv_calcs.__version__
            if saved_version != current_version:
                ss.warning_message = f"This file was saved with guv-calcs {saved_version}; the current Illuminate version of guv-calcs is {current_version}."

            file_ok = True
        except ValueError:
            ss.error_message = "Something is wrong with your .guv file. Please verify that it is valid json."
            file_ok = False
            st.error(ss.error_message)
    if file_ok:
        ss.room = Room.load(string)
        initialize_room()
        for zone_id, zone in ss.room.calc_zones.items():
            initialize_zone(zone)

        for lamp_id, lamp in ss.room.lamps.items():
            initialize_lamp(lamp)
            # make lampfile options
            if lamp.filename not in ss.vendored_lamps.keys():
                ss.uploaded_files[lamp.filename] = lamp.filedata

        update_calc_zones()
        if ss.show_results:
            ss.room.calculate()
            show_results()

        ss.show_room = True  # show the uploaded file


def default_sidebar():
    """default display of sidebar showing instructions"""
    cols = st.columns([10, 1])
    cols[0].title("Welcome to Illuminate!")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        use_container_width=True,
        key="close_about",
    )

    st.subheader(
        "***A free and open source simulation tool for germicidal UV applications***"
    )

    st.header("Getting Started", divider="grey")
    st.write(
        """
        To run your first simulation, click on the **`Select luminaire...`** menu in the top
        bar, and select **`Add new luminaire`**. The luminaire editing menu will appear on the left panel.
        Select a file from the **`Select lamp`** menu, then click on the red **:red[Calculate!]** button
        in the upper right corner to immediately see average room fluence rate and skin and eye safety results.
        Click the **`About`** button in the upper left corner at any time to return to this page.
        """
    )

    st.subheader("Editing the Room")
    st.write(
        """
        In the **`Edit Room`** menu, you can change the size of the room, the air changes from ventilation and ozone decay
        rate, as well as the photobiological safety standard to calculate for. Updating these options will update the 
        calculation zones, so be sure to hit **:red[Calculate!]** again after doing so.
        """
    )

    st.subheader("Adding and Editing Luminaires")
    st.write(
        """
        For more complex simulations, you can configure the position and orientation of the luminaire,
        or add more luminaires. You can also upload your own photometric file - note that if you do this, you
        should also provide a spectrum file, or photobiological safety calculations may be inaccurate. 
        
        Note that if a luminaire is placed outside the room boundaries, it will not appear in the plot, 
        but will still participate in calculations, but not if you uncheck the box labeled **`Enabled`**.
        """
    )
    st.subheader("Adding and Editing Calculation Zones")  # , divider="grey")
    st.write(
        """
        Illuminate comes pre-loaded with three key calculation zones important for 
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
        volume. Click  on **`Select calculation zone...`** and then on **`Add new calculation zone`** 
        to bring up the calculation zone menu in the left hand panel. Select **`Plane`** or **`Volume`**
        and click **`Go`** to enter the full editing menu.
        
        Currently, only planes normal to the floor are supported. These calculation 
        zones will have their statistics displayed in the Results page alongside the built-in
        calculation zones.
        """
    )

    st.subheader("Calculating")  # , divider="grey")
    st.write(
        """
        When the **:red[Calculate!]** button is pressed, calculations are performed for each luminaire
        and each calculation zone, such that the number of calculations is the product of the 
        number of luminaires and the number of calculation zones. With only a few calculation zones
        and a few luminaires, calculation time should be nearly instantaneous, but for larger numbers
        of lamps and calculation zones, calculation time may be several minutes. Larger numbers of
        calculation points, or very large rooms, may also significantly increase calculation time.
        """
    )

    st.subheader("Saving and Loading")
    st.write(
        """
        Click the **`Project`** button in the top ribbon menu. Click on **`Save Project`** to save the current
        configuration of luminaires and calculation zones. A file called **`illuminate.guv`** will be generated.
        It can be renamed to anything as long as the **`.guv`** extension remains. Depending on your browser
        settings, you may be prompted on a location to save the file, or it may download automatically.
        
        To load a project, click on **`Load Project`** and then on the file upload widget that appears. Select any 
        **`.guv`** file generated by Illuminate to load it. Note that projects saved under earlier versions of guv-calcs
        may not work correctly. To minimize errors for ongoing projects, resave an outdated project using the current
        version of Illuminate.
        
        **`.guv`** files are plain text JSON; you can read them with any plain text reader such as Notepad or Microsoft 
        Word.
        """
    )

    st.header("About the Project", divider="grey")
    st.subheader("Purpose and Scope")
    st.write(
        """
        Illuminate supports both far-UV (222 nm krpyton chloride) and upper-room UV (254 nm low pressure mercury)
        installations. However, currently, only far-UV lamps have pre-filled photometric files and other
        [characterization data](https://assay.osluv.org/). For 254 nm modeling, you will have to provide your own
        photometric file. 
        
        We are eager to work with UV companies to expand the list of characterized fixtures available on Illuminate. Get in contact at contact-assay@osluv.org 
        """
    )
    st.subheader("Source Libraries")  # , divider="grey")
    st.write(
        """
        Illuminate is a free and open source web tool based on the Streamlit library, 
        whose development repository may be found [here](https://github.com/jvbelenky/illuminate/).
        Its core calculations depend on the [GUV-calcs](https://github.com/jvbelenky/guv-calcs/) library, and it uses 
        [PhotomPy](https://github.com/jvbelenky/photompy) for the parsing of 
        photometric files. All three repositories are distributed under an MIT license and are
        written primarily in Python. The features below are immediate priorities; contribution is highly encouraged.
        """
    )

    st.subheader(
        "Features Under Development: [Illuminate](https://github.com/jvbelenky/illuminate)",
        # divider="grey",
    )
    st.write("*Core Features:*")
    st.write(
        """        
        - **Risk reduction calculations**: Based on known pathogen emission rates, number of people present, community wastewater levels, etc.
        - **Occupancy-category comm check**: Select an indoor space type from a dropdown list to compare expected UV disinfection rates to recommended rates by ASHRAE 241, CDC, etc.
        - **Add portable air cleaners to the simulation**: In order to calculate total air cleaning achieved, not just from UV
        """
    )
    st.write("*Tooling Features:*")
    st.write(
        """
        - **Improved mobile view**: Clean layout configured for mobile devices
        - **Generating a report**: Generate a polished safety and efficacy report of an installation with a click of a button
        - **Copying objects**: Duplicate a luminaire or calculation zone
        - **Interactive plotting**: Place luminaires and draw calculation zones directly onto the interactive visualization plot
        - **In-tool CAD support**: Design complex environments directly in the interface
        - **Locally installable app**: Run easily as a desktop app without internet access
        - **Arbitray GUV wavelength support**: Run simulations for any GUV wavelength
        - *...and much more!*
        """
    )

    st.subheader(
        "Features Under Development: [GUV-Calcs](https://github.com/jvbelenky/guv-calcs)",
        # divider="grey",
    )
    st.write(
        """
        - **Support for diffuse reflectance**: Include reflectance values in the fluence and irradiance calculations
        - **Support for design of complex environments**: Whether designing a complex environment 
        - **More accurate near-field modeling**: Definitions of GUV sources that take into account emission surface geometry and near-field radiation distribution.
        
        """
    )
    st.subheader(
        "Features Under Development: [PhotomPy](https://github.com/jvbelenky/photompy)",
        # divider="grey",
    )
    st.write(
        """
        - **Dialux support**: Support for Dialux (.ldt) files
        - **A/B Photometry**: Support for Type A and Type B Photometry
        - **File from angular distribution:** Generate .ies and .ldt files from an angular distribution table
        - **File editing menu:** More extensive file editing and writing support
        """
    )
