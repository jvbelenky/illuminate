import streamlit as st
import matplotlib.pyplot as plt
from guv_calcs.calc_zone import CalcPlane, CalcVol

from app._website_helpers import make_file_list
from app._results import print_standard_zones
from app._widget import (
    initialize_lamp,
    initialize_zone,
    remove_lamp,
    remove_zone,
    update_lamp_filename,
    update_lamp_name,
    update_zone_name,
    update_lamp_position,
    update_lamp_orientation,
    update_from_tilt,
    update_from_orientation,
    update_plane_dimensions,
    update_vol_dimensions,
    update_lamp_visibility,
    update_zone_visibility,
    update_room,
    update_room_standard,
)

SELECT_LOCAL = "Select local file..."
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]
ss = st.session_state


def lamp_file_options(selected_lamp):
    """widgets and plots to do with lamp file sources"""
    # File input
    fname_idx = ss.lampfile_options.index(selected_lamp.filename)
    st.selectbox(
        "Select lamp",
        ss.lampfile_options,
        index=fname_idx,
        on_change=update_lamp_filename,
        args=[selected_lamp],
        key=f"file_{selected_lamp.lamp_id}",
    )
    # if anything but select_local has been selected, lamp should have reloaded
    fname = selected_lamp.filename

    # determine fdata from fname
    fdata = None
    spectra_data = None  # TEMP
    if selected_lamp.filename == SELECT_LOCAL:
        uploaded_file = st.file_uploader(
            "Upload a file", type="ies", key=f"upload_{selected_lamp.lamp_id}"
        )
        if uploaded_file is not None:
            fdata = uploaded_file.read()
            fname = uploaded_file.name
            # add the uploaded file to the session state and upload
            ss.uploaded_files[fname] = fdata
            make_file_list()
            # load into lamp object
            selected_lamp.reload(filename=fname, filedata=fdata)
            # st.rerun here?
            st.rerun()

    if selected_lamp.filename in ss.uploaded_files and len(selected_lamp.spectra) == 0:

        st.write(
            """In order for GUV photobiological safety calculations to be
             accurate, a spectra is required. Please upload a .csv file with 
             exactly 1 header row, where the first column is wavelengths, and the 
             second column is relative intensities. :red[If a spectra is not provided, 
             photobiological safety calculations will be inaccurate.]"""
        )
        uploaded_spectra = st.file_uploader(
            "Upload spectra CSV",
            type="csv",
            key=f"spectra_upload_{selected_lamp.lamp_id}",
        )
        if uploaded_spectra is not None:
            spectra_data = uploaded_spectra.read()
            selected_lamp.load_spectra(spectra_data)
            fig, ax = plt.subplots()
            ss.spectrafig = selected_lamp.plot_spectra(fig=fig, title="")
            st.rerun()

    # plot if there is data to plot with
    PLOT_IES, PLOT_SPECTRA = False, False
    cols = st.columns(3)
    if selected_lamp.filedata is not None:
        PLOT_IES = cols[0].checkbox("Show polar plot", key="show_polar", value=True)
    if len(selected_lamp.spectra) > 0:
        PLOT_SPECTRA = cols[1].checkbox(
            "Show spectra plot", key="show_spectra", value=True
        )
        yscale = cols[2].selectbox(
            "Spectra y-scale",
            options=["linear", "log"],
            label_visibility="collapsed",
            key="spectra_yscale",
        )
        if yscale is None:
            yscale = "linear"  # kludgey default value setting

    if PLOT_IES and PLOT_SPECTRA:
        # plot both charts side by side
        iesfig, iesax = selected_lamp.plot_ies()
        ss.spectrafig.set_size_inches(5, 6, forward=True)
        ss.spectrafig.axes[0].set_yscale(yscale)
        cols = st.columns(2)
        cols[1].pyplot(ss.spectrafig, use_container_width=True)
        cols[0].pyplot(iesfig, use_container_width=True)
    elif PLOT_IES and not PLOT_SPECTRA:
        # just display the ies file plot
        iesfig, iesax = selected_lamp.plot_ies()
        st.pyplot(iesfig, use_container_width=True)
    elif PLOT_SPECTRA and not PLOT_IES:
        # display just the spectra
        ss.spectrafig.set_size_inches(6.4, 4.8, forward=True)
        ss.spectrafig.axes[0].set_yscale(yscale)
        st.pyplot(ss.spectrafig, use_container_width=True)


def lamp_sidebar(room):
    st.subheader("Edit Luminaire")
    selected_lamp = room.lamps[ss.selected_lamp_id]
    # do this before initializing

    initialize_lamp(selected_lamp)
    # name
    st.text_input(
        "Name",
        key=f"name_{selected_lamp.lamp_id}",
        on_change=update_lamp_name,
        args=[selected_lamp],
    )

    # file input
    lamp_file_options(selected_lamp)

    # Position inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input(
            "Position X",
            min_value=0.0,
            step=0.1,
            key=f"pos_x_{selected_lamp.lamp_id}",
            on_change=update_lamp_position,
            args=[selected_lamp],
        )
    with col2:
        st.number_input(
            "Position Y",
            min_value=0.0,
            step=0.1,
            key=f"pos_y_{selected_lamp.lamp_id}",
            on_change=update_lamp_position,
            args=[selected_lamp],
        )
    with col3:
        st.number_input(
            "Position Z",
            min_value=0.0,
            step=0.1,
            key=f"pos_z_{selected_lamp.lamp_id}",
            on_change=update_lamp_position,
            args=[selected_lamp],
        )

    # Rotation input
    angle = st.number_input(
        "Rotation",
        min_value=0.0,
        max_value=360.0,
        step=1.0,
        key=f"rotation_{selected_lamp.lamp_id}",
    )
    selected_lamp.rotate(angle)
    st.write("Set aim point")

    # Aim point inputs
    col4, col5, col6 = st.columns(3)
    with col4:
        st.number_input(
            "Aim X",
            key=f"aim_x_{selected_lamp.lamp_id}",
            on_change=update_lamp_orientation,
            args=[selected_lamp],
        )
    with col5:
        st.number_input(
            "Aim Y",
            key=f"aim_y_{selected_lamp.lamp_id}",
            on_change=update_lamp_orientation,
            args=[selected_lamp],
        )
    with col6:
        st.number_input(
            "Aim Z",
            key=f"aim_z_{selected_lamp.lamp_id}",
            on_change=update_lamp_orientation,
            args=[selected_lamp],
        )

    st.write("Set tilt and orientation")
    col7, col8 = st.columns(2)
    with col7:
        st.number_input(
            "Tilt",
            format="%.1f",
            step=1.0,
            key=f"tilt_{selected_lamp.lamp_id}",
            on_change=update_from_tilt,
            args=[selected_lamp, room],
        )
    with col8:
        st.number_input(
            "Orientation",
            format="%.1f",
            step=1.0,
            key=f"orientation_{selected_lamp.lamp_id}",
            on_change=update_from_orientation,
            args=[selected_lamp, room],
        )

    selected_lamp.enabled = st.checkbox(
        "Enabled",
        on_change=update_lamp_visibility,
        args=[selected_lamp],
        key=f"enabled_{selected_lamp.lamp_id}",
    )

    del_button = col7.button("Delete Lamp", type="primary", use_container_width=True)
    close_button = col8.button("Close", use_container_width=True)

    if close_button:  # maybe replace with an enable/disable button?
        ss.editing = None
        ss.selected_lamp_id = None
        if selected_lamp.filename is None:
            room.remove_lamp(selected_lamp.lamp_id)
            remove_lamp(selected_lamp)
        st.rerun()
    if del_button:
        room.remove_lamp(selected_lamp.lamp_id)
        remove_lamp(selected_lamp)
        ss.editing = None
        ss.selected_lamp_id = None
        st.rerun()


def zone_sidebar(room):
    st.subheader("Edit Calculation Zone")
    if ss.selected_zone_id in SPECIAL_ZONES:
        DISABLED = True
    else:
        DISABLED = False
    selected_zone = room.calc_zones[ss.selected_zone_id]

    if ss.editing == "zones":
        cola, colb = st.columns([3, 1])
        calc_types = ["Plane", "Volume"]
        zone_type = cola.selectbox("Select calculation type", options=calc_types)
        colb.write("")
        colb.write("")
        if colb.button("Go", use_container_width=True):
            calc_ids = room.calc_zones.keys()
            if zone_type == "Plane":
                idx = len([v for v in calc_ids if "Plane" in v]) + 1
                new_zone = CalcPlane(
                    zone_id=ss.selected_zone_id,
                    name="CalcPlane" + str(idx),
                )
                ss.editing = "planes"
            elif zone_type == "Volume":
                idx = len([v for v in calc_ids if "Vol" in v]) + 1
                new_zone = CalcVol(
                    zone_id=ss.selected_zone_id,
                    name="CalcVol" + str(idx),
                )
                ss.editing = "volumes"
            room.add_calc_zone(new_zone)

            st.rerun()
    elif ss.editing in ["planes", "volumes"]:
        selected_zone = room.calc_zones[ss.selected_zone_id]
        initialize_zone(selected_zone)
        st.text_input(
            "Name",
            key=f"name_{selected_zone.zone_id}",
            on_change=update_zone_name,
            args=[selected_zone],
            disabled=DISABLED,
        )

    if ss.editing == "planes":

        col1, col2 = st.columns([2, 1])
        # xy dimensions and height
        col1.number_input(
            "Height",
            min_value=0.0,
            key=f"height_{selected_zone.zone_id}",
            on_change=update_plane_dimensions,
            args=[selected_zone],
            disabled=DISABLED,
        )
        col2.write("")
        col2.write("")
        col2.write(room.units)
        col2, col3 = st.columns(2)
        with col2:
            st.number_input(
                "X1",
                min_value=0.0,
                key=f"x1_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X2",
                min_value=0.0,
                key=f"x2_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X spacing",
                min_value=0.01,
                key=f"x_spacing_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=False,
            )
        with col3:
            st.number_input(
                "Y1",
                min_value=0.0,
                key=f"y1_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y2",
                min_value=0.0,
                key=f"y2_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y spacing",
                min_value=0.01,
                key=f"y_spacing_{selected_zone.zone_id}",
                on_change=update_plane_dimensions,
                args=[selected_zone],
                disabled=False,
            )

        # Set calculation type (vertical / horizontal / all angles)
        options = ["All angles", "Horizontal irradiance", "Vertical irradiance"]
        if not selected_zone.vert and not selected_zone.horiz:
            calc_type_index = 0
        if selected_zone.horiz and not selected_zone.vert:
            calc_type_index = 1
        if not selected_zone.horiz and selected_zone.vert:
            calc_type_index = 2
        calc_type = st.selectbox(
            "Calculation type", options, index=calc_type_index, disabled=DISABLED
        )
        if calc_type == "All angles":
            selected_zone.horiz = False
            selected_zone.vert = False
        elif calc_type == "Horizontal irradiance":
            selected_zone.horiz = True
            selected_zone.vert = False
        elif calc_type == "Vertical irradiance":
            selected_zone.horiz = False
            selected_zone.vert = True

        # Toggle 80 degree field of view
        selected_zone.fov80 = st.checkbox(
            "Field of View 80°",
            key=f"fov80_{selected_zone.zone_id}",
            disabled=DISABLED,
        )

        # Set dose vs irradiance
        value_options = ["Irradiance (uW/cm2)", "Dose (mJ/cm2)"]
        value_index = 1 if selected_zone.dose else 0
        value_type = st.selectbox(
            "Value display type",
            options=value_options,
            index=value_index,
            disabled=DISABLED,
        )
        if value_type == "Dose (mJ/cm2)":
            selected_zone.set_value_type(dose=True)
            dose_time = st.number_input(
                "Exposure time (hours)",
                value=selected_zone.hours,
                disabled=DISABLED,
            )
            selected_zone.set_dose_time(dose_time)
        elif value_type == "Irradiance (uW/cm2)":
            selected_zone.set_value_type(dose=False)

        st.checkbox(
            "Offset",
            key=f"offset_{selected_zone.zone_id}",
            on_change=update_plane_dimensions,
            args=[selected_zone],
            disabled=False,
        )

    elif ss.editing == "volumes":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input(
                "X1",
                min_value=0.0,
                key=f"x1_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X2",
                min_value=0.0,
                key=f"x2_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "X spacing",
                min_value=0.01,
                key=f"x_spacing_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=False,
            )
        with col2:
            st.number_input(
                "Y1",
                min_value=0.0,
                key=f"y1_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y2",
                min_value=0.0,
                key=f"y2_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Y spacing",
                min_value=0.01,
                key=f"y_spacing_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=False,
            )
        with col3:
            st.number_input(
                "Z1",
                min_value=0.0,
                key=f"z1_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Z2",
                min_value=0.0,
                key=f"z2_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=DISABLED,
            )
            st.number_input(
                "Z spacing",
                min_value=0.01,
                key=f"z_spacing_{selected_zone.zone_id}",
                on_change=update_vol_dimensions,
                args=[selected_zone],
                disabled=False,
            )

        st.checkbox(
            "Offset",
            key=f"offset_{selected_zone.zone_id}",
            on_change=update_vol_dimensions,
            args=[selected_zone],
            disabled=False,
        )
    if ss.editing == "zones":
        del_button = st.button("Cancel", use_container_width=True, disabled=False)
        close_button = None
    elif ss.editing in ["planes", "volumes"]:
        selected_zone.enable = st.checkbox(
            "Enabled",
            # value=selected_zone.enable,
            on_change=update_zone_visibility,
            args=[selected_zone],
            key=f"enabled_{selected_zone.zone_id}",
        )
        col7, col8 = st.columns(2)
        del_button = col7.button(
            "Delete",
            type="primary",
            use_container_width=True,
            disabled=DISABLED,
        )
        close_button = col8.button("Close", use_container_width=True, disabled=False)

    if close_button:  # maybe replace with an enable/disable button?
        if not isinstance(selected_zone, (CalcPlane, CalcVol)):
            remove_zone(selected_zone)
            room.remove_calc_zone(ss.selected_zone_id)
        ss.editing = None
        ss.selected_zone_id = None
        st.rerun()
    if del_button:
        remove_zone(selected_zone)
        room.remove_calc_zone(ss.selected_zone_id)
        ss.editing = None
        ss.selected_zone_id = None
        st.rerun()


def room_sidebar(room):
    """display room editing panel in sidebar"""
    st.header("Edit Room")

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
        # index=standards.index(room.standard),
        on_change=update_room_standard,
        args=[room],
        key="room_standard",
    )

    st.subheader("Indoor Chemistry", divider="grey")
    # st.write("Coming soon")
    cols = st.columns(2)
    room.air_changes = cols[0].number_input(
        "Air changes per hour from ventilation",
        min_value=0.0,
        step=0.1,
        key="air_changes",
    )
    room.ozone_decay_constant = cols[1].number_input(
        "Ozone decay constant",
        min_value=0.0,
        step=0.1,
        key="ozone_decay_constant",
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

    close_button = st.button("Close", use_container_width=True)
    if close_button:
        ss.editing = None
        st.rerun()


def results_sidebar(room):
    """display results in the customizable panel"""
    cols = st.columns([4, 1])
    cols[0].title("Results")
    cols[1].write("")
    cols[1].write("")
    close_button = cols[1].button("Close", use_container_width=True)

    # do some checks first. do we actually have any lamps?
    msg = "You haven't added any luminaires yet! Try adding a luminaire by clicking the `Add Luminaire` button, and then hit `Calculate`"
    if not room.lamps:
        st.warning(msg)
    elif all(lamp.filedata is None for lampid, lamp in room.lamps.items()):
        st.warning(msg)

    # check that all positions of lamps and calc zones are where they're supposed to be
    msgs = room.check_positions()
    for msg in msgs:
        if msg is not None:
            st.warning(msg, icon="⚠️")

    print_standard_zones(room)

    # Display all other results
    if any(key not in SPECIAL_ZONES for key in room.calc_zones.keys()):
        st.subheader("User Defined Calculation Zones")
        for zone_id, zone in room.calc_zones.items():
            vals = zone.values
            if vals is not None and zone.name not in SPECIAL_ZONES:
                st.subheader(zone.name, ":")
                unitstr = zone.units
                if zone.dose:
                    unitstr += "/" + str(zone.hours) + " hours"
                st.write("Average:", round(vals.mean(), 3), unitstr)
                st.write("Min:", round(vals.min(), 3), unitstr)
                st.write("Max:", round(vals.max(), 3), unitstr)

    st.write("")
    st.write("")
    st.write("")

    if close_button:
        ss.editing = None
        st.rerun()


def default_sidebar(room):
    """default display of sidebar showing instructions"""
    st.title("Welcome to Illuminate-GUV!")
    st.header("A free and open source simulation tool for germicidal UV applications")
    st.subheader("Getting Started", divider="grey")
    st.write(
        """
        To run your first simulation, simply click on the `Add Luminaire` 
        button on the right panel, select a photometric file from the dropdown menu, 
        and click the red `Calculate` button to immediately see results.
        """
    )

    st.subheader("Interpreting the Results", divider="grey")
    st.write(
        """
        After adding a luminaire and clicking `Calculate`, the Results page will show several outputs:
        
        - **Efficacy:** GUV system efficacy is determined approximately by the average fluence multiplied by the susceptibility value k. *Note that k values for aerosolized pathogens have high uncertainty associated with them, and these values should be understood as possible ranges.*
        - **Ozone increase:** Given an assumed air change rate from ventilation and an ozone decay rate typical for indoor environments, the anticipated total increase in ozone in parts per billion.
        - **Photobiological safety:** Spectrally-weighted calculations for eye and skin safety, per the selected standard. If either limit is exceeded, a dimming requirement is reported. By default, the standard selected is ANSI IES RP 27.1-22, which uses the post-2022 ACGIH Threshold Limit Values (TLVs) with height set by UL8802 at 1.9 meters.
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
        - **Mobile view**: Clean layout configured for mobile devices\n
        - **Exporting results**: Export the result of any calculation zone, or all calculation zones, for use with other modeling software
        - **Generating a report**: Generate a polished safety and efficacy report of an installation with a click of a button
        - **Copying objects**: Duplicate a luminaire or calculation zone
        - **Interactive plotting**: Place luminaires and draw calculation zones directly onto the interactive visualization plot
        - **Saving and load projects**: Save all the parameters of a project as a .json blob, and upload again
        - **Locally installable app**: Run easily as a desktop app without internet access
        - **Support for other GUV wavelengths**: Currently, only GUV222 with krypton-chloride lamps is supported. Future releases will also support GUV254        
        - **More accurate near-field modeling**: Definitions of GUV sources that take into account emission surface geometry and near-field radiation distribution.
        - *...and much more!*
        """
    )

    st.subheader("References", divider="grey")
    st.write("*Coming soon...*")

    # col1,col2 = st.columns(2)
    # add_lamp = col1.button("Add lamp",use_container_width=True,key='addlamp_tab')
    # add_calc_zone = col2.button("Add calc zone",use_container_width=True,key="addzone_tab")
    # calculate = col1.button("Calculate!",type="primary",use_container_width=True,key="calculate_tab")
    # show_results = col2.button("Show results",use_container_width=True,key="results_tab")
    # if add_lamp:
    # add_new_lamp(room)
    # if add_calc_zone:
    # add_new_zone(room)
    # if calculate:
    # room.calculate()
    # ss.editing = "results"
    # # clear out any other selected objects and remove ones that haven't been fully initialized
    # clear_lamp_cache(room)
    # clear_zone_cache(room)
    # st.rerun()
