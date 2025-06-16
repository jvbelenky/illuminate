import streamlit as st
from app.widget import close_sidebar

ss = st.session_state


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
        To run your first simulation:
        1. Click on the **`Select luminaire...`** menu and select **`Add new luminaire`**
        2. In the new luminaire editing menu, select a file from the **`Select lamp`** menu.
        3. Click on the red **:red[Calculate!]** button in the upper right corner to immediately see results for skin and eye safety and average room fluence results.
        
        At any time, you can return to this page by clicking the **`About`** button in the upper left corner of the page.
        """
        
        # """
        # To run your first simulation, click on the **`Select luminaire...`** menu in the top
        # bar, and select **`Add new luminaire`**. The luminaire editing menu will appear on the left panel.
        # Select a file from the **`Select lamp`** menu, then click on the red **:red[Calculate!]** button
        # in the upper right corner to immediately see average room fluence rate and skin and eye safety results.
        # Click the **`About`** button in the upper left corner at any time to return to this page.
        # """
    )

    st.subheader("Editing the Room")
    st.write(
        """
        In the **`Edit Room`** menu, you can change the size of the room, the air changes from ventilation and ozone decay
        rate, as well as the photobiological safety standard to calculate for. You can also enable reflections for the room - 
        the default values of 0.078 are typical reflectance values for 222 nm far-UVC.
        """
        
        #Updating these options will update the calculation zones, so be sure to hit **:red[Calculate!]** again after doing so.
        
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
        
        Currently, only planes parallel to walls are supported. These calculation 
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
        [characterization data](https://reports.osluv.org/). For 254 nm modeling, you will have to provide your own
        photometric file. 
        
        We are eager to work with UV companies to expand the list of characterized fixtures available on Illuminate. Get in contact at contact@osluv.org 
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
    
    st.subheader("Recent Features")
    st.write(
        """
        - **Support for diffuse reflectance**: Surface reflectance values can now be specified in the **`Edit Room`** menu
        - **Near-field modeling**: GUV sources can now take into account emission surface geometry and near-field radiation distribution.
        - **Calculation plane**: Calculation planes can now be defined relative to any surface
        - **Locally installable app**: Illuminate can be run locally as a desktop app without internet access - see https://github.com/jvbelenky/illuminate/ for more information. Some use of terminal commands required.
        """
    )

    st.subheader(
        "Features Under Development",
        # divider="grey",
    )
    st.write("*Core Features:*")
    st.write(
        """        
        - **Support for design of complex environments**: For both non-rectangular environments nad the inclusion of obstacles in the room.
        - **Risk reduction calculations**: Based on known pathogen emission rates, number of people present, community wastewater levels, etc.
        - **Occupancy-category comm check**: Select an indoor space type from a dropdown list to compare expected UV disinfection rates to recommended rates by ASHRAE 241, CDC, etc.
        - **Add portable air cleaners to the simulation**: In order to calculate total air cleaning achieved, not just from UV
        """
    )
    st.write("*Tooling Features:*")
    st.write(
        """
        - **Interactive plotting**: Place luminaires and draw calculation zones directly onto the interactive visualization plot
        - **In-tool CAD support**: Design complex environments directly in the interface
        - **Arbitray GUV wavelength support**: Run simulations for any GUV wavelength
        """
    )
    
    st.write("*Photometric File Features*")
    st.write(
        """
        - **Dialux support**: Support for Dialux (.ldt) files
        - **A/B Photometry**: Support for Type A and Type B Photometry
        - **File from angular distribution:** Generate .ies and .ldt files from an angular distribution table
        - **File editing menu:** More extensive file editing and writing support
        """
    )
