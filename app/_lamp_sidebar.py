import streamlit as st
import matplotlib.pyplot as plt
from app._website_helpers import make_file_list
from app._widget import (
    initialize_lamp,
    update_lamp_filename,
    update_lamp_name,
    update_lamp_position,
    update_lamp_orientation,
    update_from_tilt,
    update_from_orientation,
    update_lamp_visibility,
    close_sidebar,
)

SELECT_LOCAL = "Select local file..."
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
ss = st.session_state


def lamp_sidebar(room):
    """all sidebar content for editing luminaires"""
    cols = st.columns([10, 1])
    cols[0].header("Edit Luminaire")
    cols[1].button(
        "X",
        on_click=close_sidebar,
        args=[room, "lamps", False],
        use_container_width=True,
        key="close_lamp",
    )

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

    col7.button(
        "Delete Lamp",
        on_click=close_sidebar,
        args=[room, "lamps", True],
        type="primary",
        use_container_width=True,
        key="delete_lamp",
    )
    col8.button(
        "Close",
        on_click=close_sidebar,
        args=[room, "lamps", False],
        use_container_width=True,
        key="close_lamp2",
    )


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

        st.warning(
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
