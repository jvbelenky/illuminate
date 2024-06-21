import streamlit as st
import pandas as pd
from pathlib import Path
from ._safety_utils import (
    get_unweighted_hours_to_tlv,
    get_weighted_hours_to_tlv,
    make_hour_string,
)
from ._widget_utils import close_results, update_ozone_results, update_standard_results

ss = st.session_state
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]


def results_page():
    """display results in the customizable panel"""
    cols = st.columns([15, 1])
    cols[0].header("Results")
    cols[1].button(
        "X", on_click=close_results, use_container_width=True, key="close_results"
    )

    # do some checks first. do we actually have any lamps?
    nolamps_msg = "You haven't added any luminaires yet! Try adding a luminaire by clicking the `Add Luminaire` button, selecting a file from the drop-down list, and then hit `Calculate`"
    if not ss.room.lamps:
        st.warning(nolamps_msg)
    elif all(lamp.filedata is None for lampid, lamp in ss.room.lamps.items()):
        st.warning(nolamps_msg)
    else:
        # check that all positions of lamps and calc zones are where they're supposed to be
        msgs = ss.room.check_positions()
        for msg in msgs:
            if msg is not None:
                st.warning(msg)
        # if we're good print the results
        print_safety()
        print_efficacy()
        print_airchem()

    # Display all other results
    if any(key not in SPECIAL_ZONES for key in ss.room.calc_zones.keys()):
        st.subheader("User Defined Calculation Zones", divider="grey")
        for zone_id, zone in ss.room.calc_zones.items():
            vals = zone.values
            if vals is not None and zone.zone_id not in SPECIAL_ZONES:
                st.subheader(zone.name, ":")
                unitstr = zone.units
                if zone.dose:
                    unitstr += "/" + str(zone.hours) + " hours"
                st.write("Average:", round(vals.mean(), 3), unitstr)
                st.write("Min:", round(vals.min(), 3), unitstr)
                st.write("Max:", round(vals.max(), 3), unitstr)


def print_safety():
    """print photobiological safety results"""
    st.subheader(
        "Photobiological Safety",
        divider="grey",
        help="Photobiological safety standards are set in the USA by the American Conference of Governmental Industrial Hygienists (ACGIH) and elsewhere in the world by the  International Commission on Non-Ionizing Radiation Protection (ICNIRP). At 222 nm, the ACGIH limits for skin are 479 mJ/cm2 over 8 hours, and for eyes they are 161 mJ/cm2 over 8 hours. The ICNIRP limits are the same for both eyes and skin; 23 mJ/cm2 over 8 hours. However, though KrCl lamps are approximately monochromatic, this is only an approximation, and individual KrCl lamps may have different threshold limit values (TLVs) depending on their spectral content.",
    )
    standards = [
        "ANSI IES RP 27.1-22 (America)",
        "ANSI IES RP 27.1-22 (America) - UL8802",
        "IEC 62471-6:2022 (International)",
    ]
    st.selectbox(
        "Select photobiological safety standard",
        options=standards,
        on_change=update_standard_results,
        # args=[room],
        key="room_standard_results",
        help="The ANSI IES RP 27.1-22 standard corresponds to the photobiological limits for UV exposure set by the American Conference of Governmental Industrial Hygienists (ACGIH), the relevant standard in the US. The IEC 62471-6:2022 standard corresponds to the limits set by the International Commission on Non-Ionizing Radiation Protection (ICNIRP), which apply most places outside of the US. Both standards indicate that the measurement should be taken at 1.8 meters up from the floor, but UL8802 (Ultraviolet (UV) Germicidal Equipment and Systems) indicates that it should be taken at 1.9 meters instead. Additionally, though ANSI IES RP 27.1-22 indicates that eye exposure limits be taken with a 80 degere field of view parallel to the floor, considering only vertical irradiance, UL8802 indicates that measurements be taken in the 'worst case' direction, resulting in a stricter limit.",
    )
    skin = ss.room.calc_zones["SkinLimits"]
    eye = ss.room.calc_zones["EyeLimits"]
    SHOW_SKIN = True if skin.values is not None else False
    SHOW_EYES = True if eye.values is not None else False
    if SHOW_SKIN and SHOW_EYES:

        hours_skin_uw, hours_eye_uw = get_unweighted_hours_to_tlv()

        # print the max values
        skin = ss.room.calc_zones["SkinLimits"]
        skin_max = round(skin.values.max(), 2)
        color = "red" if hours_skin_uw < 8 else "blue"
        skin_str = "**:" + color + "[" + str(skin_max) + "]** " + skin.units

        eye = ss.room.calc_zones["EyeLimits"]
        eye_max = round(eye.values.max(), 2)
        color = "red" if hours_eye_uw < 8 else "blue"
        eye_str = "**:" + color + "[" + str(eye_max) + "]** " + eye.units
        cols = st.columns(2)
        with cols[0]:
            st.write("**Max Skin Dose (8 Hours)**: ", skin_str)
        with cols[1]:
            st.write("**Max Eye Dose (8 Hours)**: ", eye_str)

        cols[0].markdown("**Hours before skin TLV is reached:**")
        cols[1].markdown("**Hours before eye TLV is reached:**")
        hours_skin_uw_str = make_hour_string(hours_skin_uw, "skin")
        hours_eye_uw_str = make_hour_string(hours_eye_uw, "eye")

        writecols = st.columns([1, 6, 1, 6])
        writecols[1].markdown(
            f"With monochromatic assumption: {hours_skin_uw_str}",
            help="These results assume that all lamps in the simulation are perfectly monochromatic 222nm sources. They don't rely on any data besides anies file. For most *filtered* KrCl lamps, but not all, the monochromatic approximation is a reasonable assumption.",
        )
        writecols[3].markdown(
            f"With monochromatic assumption: {hours_eye_uw_str}",
            help="These results assume that all lamps in the simulation are perfectly monochromatic 222nm sources. They don't rely on any data besides anies file. For most *filtered* KrCl lamps, but not all, the monochromatic approximation is a reasonable assumption.",
        )

        # weighted hours to TLV
        hours_skin_w, hours_eye_w = get_weighted_hours_to_tlv()
        hours_skin_w_str = make_hour_string(hours_skin_w, "skin")
        hours_eye_w_str = make_hour_string(hours_eye_w, "eye")

        writecols[1].markdown(
            f"With spectral weighting: {hours_skin_w_str}",
            help="These results take into account the spectra of the lamps in the simulation. Because Threshold Limit Values (TLVs) are calculated by summing over the *entire* spectrum, not just the peak wavelength, some lamps may have effective TLVs substantially below the monochromatic TLVs at 222nm.",
        )
        writecols[3].markdown(
            f"With spectral weighting: {hours_eye_w_str}",
            help="These results take into account the spectra of the lamps in the simulation. Because Threshold Limit Values (TLVs) are calculated by summing over the *entire* spectrum, not just the peak wavelength, some lamps may have effective TLVs substantially below the monochromatic TLVs at 222nm.",
        )

        SHOW_PLOTS = st.checkbox("Show Plots", value=True)
        if SHOW_PLOTS:
            cols = st.columns(2)
            skintitle = (
                "8-Hour Skin Dose (Max: " + str(skin_max) + " " + skin.units + ")"
            )
            eyetitle = "8-Hour Eye Dose (Max: " + str(eye_max) + " " + eye.units + ")"

            cols[0].pyplot(
                skin.plot_plane(title=skintitle),
                **{"transparent": "True"},
            )
            cols[1].pyplot(
                eye.plot_plane(title=eyetitle),
                **{"transparent": "True"},
            )


def print_efficacy():
    """print germicidal efficacy results"""
    st.subheader(
        "Efficacy",
        divider="grey",
        help="Equivalent air changes from UV (eACH-UV) in a *well-mixed room* is determined by the average fluence [mW/cm2] multiplied by the susceptibility value k [cm2/mW] multiplied by the number of seconds in an hour (3600). **Note that values of k are highly uncertain and should be considered preliminary.**",
    )
    fluence = ss.room.calc_zones["WholeRoomFluence"]
    if fluence.values is not None:
        fluence.values
        avg_fluence = round(fluence.values.mean(), 3)
        fluence_str = ":blue[" + str(avg_fluence) + "] μW/cm2"
    else:
        fluence_str = None
    st.write("Average fluence: ", fluence_str)

    if fluence.values is not None:
        SHOW_KPLOT = st.checkbox("Show Plot", value=True)
        if SHOW_KPLOT:
            st.pyplot(ss.kfig)
        SHOW_KDATA = st.checkbox("Show Data", value=True)
        if SHOW_KDATA:
            st.dataframe(ss.kdf, hide_index=True)
        if SHOW_KPLOT or SHOW_KDATA:
            st.markdown(
                "See any missing data? Let us know [here](https://docs.google.com/forms/d/e/1FAIpQLSdpHgV3I0vYE1i8wsImyepMDumuuEfF9nY6BVtNhErMSW9iPg/viewform)"
            )


def print_airchem():
    """display indoor air chemistry results"""
    st.subheader(
        "Ozone Generation",
        divider="grey",
        help="Given an assumed air change rate from ventilation and an ozone decay rate typical for indoor environments, the anticipated total increase in ozone in parts per billion. This calculation currently assumes an ozone generation constant of 10, calculated by Peng 2022 (DOI: 10.1021/acs.estlett.3c00314) for an Ushio B1. Eventually this calculation will take into account individual lamp spectra.",
    )
    cols = st.columns(2)
    cols[0].number_input(
        "Air changes per hour from ventilation",
        on_change=update_ozone_results,
        # args=[room],
        min_value=0.0,
        step=0.1,
        key="air_changes_results",
        help="Note that outdoor ozone is almost always at a higher concentration than indoor ozone. Increasing the air changes from ventilation will reduce the increase in ozone due to GUV, but may increase the total indoor ozone concentration. However, increasing ventilation will also increase the rate of removal of any secondary products that may form from the ozone.",
    )
    cols[1].number_input(
        "Ozone decay constant",
        on_change=update_ozone_results,
        # args=[room],
        min_value=0.0,
        step=0.1,
        key="ozone_decay_constant_results",
        help="An initial ozone decay constant of 2.7 is typical of indoor environments (Nazaroff and Weschler; DOI: 10.1111/ina.12942); ",
    )
    fluence = ss.room.calc_zones["WholeRoomFluence"]
    if fluence.values is not None:
        ozone_ppb = calculate_ozone_increase()
        ozone_color = "red" if ozone_ppb > 5 else "blue"
        ozone_str = f":{ozone_color}[**{round(ozone_ppb,2)} ppb**]"
    else:
        ozone_str = "Not available"
    st.write(f"Estimated increase in indoor ozone from UV: {ozone_str}")


def calculate_ozone_increase():
    """
    ozone generation constant is currently hardcoded to 10 for GUV222
    this should really be based on spectra instead
    but this is a relatively not very big deal, because
    """
    avg_fluence = ss.room.calc_zones["WholeRoomFluence"].values.mean()
    ozone_gen = 10  # hardcoded for now, eventually should be based on spectra
    ach = ss.room.air_changes
    ozone_decay = ss.room.ozone_decay_constant
    ozone_increase = avg_fluence * ozone_gen / (ach + ozone_decay)
    return ozone_increase


def get_disinfection_table(fluence):
    """
    Retrieve and format inactivtion data for this room.

    Currently assumes all lamps are GUV222. in the future will need something
    cleverer than this
    """

    wavelength = 222

    fname = Path("data/disinfection_table.csv")
    df = pd.read_csv(fname)
    df = df[df["Medium"] == "Aerosol"]
    df = df[df["wavelength [nm]"] == wavelength]

    # calculate eACH before filling nans
    k1 = df["k1 [cm2/mJ]"].fillna(0).astype(float)
    k2 = df["k2 [cm2/mJ]"].fillna(0).astype(float)
    f = df["% resistant"].str.rstrip("%").astype("float").fillna(0) / 100
    eACH = (k1 * (1 - f) + k2 - k2 * (1 - f)) * fluence * 3.6

    volume = ss.room.get_volume()
    # convert to cubic feet for cfm
    if ss.room.units == "meters":
        volume = volume / (0.3048 ** 3)
    cadr_uv_cfm = eACH * volume / 60
    cadr_uv_lps = cadr_uv_cfm * 0.47195

    df["eACH-UV"] = eACH.round(2)
    df["CADR-UV [cfm]"] = cadr_uv_cfm.round(2)
    df["CADR-UV [lps]"] = cadr_uv_lps.round(2)

    newkeys = [
        "eACH-UV",
        "CADR-UV [cfm]",
        "CADR-UV [lps]",
        "Organism",
        "Species",
        "Strain",
        "Type (Viral)",
        "Enveloped (Viral)",
        "k1 [cm2/mJ]",
        "k2 [cm2/mJ]",
        "% resistant",
        "Medium (specific)",
        "Full Citation",
    ]
    df = df[newkeys].fillna(" ")
    df = df.rename(
        columns={"Medium (specific)": "Medium", "Full Citation": "Reference"}
    )
    df = df.sort_values("Species")

    return df
