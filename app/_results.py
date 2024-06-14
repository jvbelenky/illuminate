import streamlit as st
import numpy as np
from app._widget import close_results, update_ozone_results

ss = st.session_state
WEIGHTS_URL = "data/UV Spectral Weighting Curves.csv"
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]


def results_page(room):
    """display results in the customizable panel"""
    cols = st.columns([15, 1])
    cols[0].header("Results")
    cols[1].button(
        "X", on_click=close_results, use_container_width=True, key="close_results"
    )

    # do some checks first. do we actually have any lamps?
    nolamps_msg = "You haven't added any luminaires yet! Try adding a luminaire by clicking the `Add Luminaire` button, selecting a file from the drop-down list, and then hit `Calculate`"
    if not room.lamps:
        st.warning(nolamps_msg)
    elif all(lamp.filedata is None for lampid, lamp in room.lamps.items()):
        st.warning(nolamps_msg)
    else:
        # check that all positions of lamps and calc zones are where they're supposed to be
        msgs = room.check_positions()
        for msg in msgs:
            if msg is not None:
                st.warning(msg)
        # if we're good print the results
        print_safety(room)
        print_efficacy(room)
        print_airchem(room)

    # Display all other results
    if any(key not in SPECIAL_ZONES for key in room.calc_zones.keys()):
        st.subheader("User Defined Calculation Zones", divider="grey")
        for zone_id, zone in room.calc_zones.items():
            vals = zone.values
            if vals is not None and zone.zone_id not in SPECIAL_ZONES:
                st.subheader(zone.name, ":")
                unitstr = zone.units
                if zone.dose:
                    unitstr += "/" + str(zone.hours) + " hours"
                st.write("Average:", round(vals.mean(), 3), unitstr)
                st.write("Min:", round(vals.min(), 3), unitstr)
                st.write("Max:", round(vals.max(), 3), unitstr)


def print_safety(room):
    """print photobiological safety results"""
    st.subheader(
        "Photobiological Safety",
        divider="grey",
        help="""Photobiological safety standards are set in the USA by the American Conference of Governmental Industrial Hygienists (ACGIH) and elsewhere in the world by the  International Commission on Non-Ionizing Radiation Protection (ICNIRP). At 222 nm, the ACGIH limits for skin are 479 mJ/cm2 over 8 hours, and for eyes they are 161 mJ/cm2 over 8 hours. The ICNIRP limits are the same for both eyes and skin; 23 mJ/cm2 over 8 hours. However, though KrCl lamps are approximately monochromatic, this is only an approximation, and individual KrCl lamps may have different threshold limit values (TLVs) depending on their spectral content.""",
    )
    skin = room.calc_zones["SkinLimits"]
    eye = room.calc_zones["EyeLimits"]
    SHOW_SKIN = True if skin.values is not None else False
    SHOW_EYES = True if eye.values is not None else False
    if SHOW_SKIN and SHOW_EYES:

        hours_skin_uw, hours_eye_uw = get_unweighted_hours_to_tlv(room)

        # print the max values
        skin = room.calc_zones["SkinLimits"]
        skin_max = round(skin.values.max(), 2)
        color = "red" if hours_skin_uw < 8 else "blue"
        skin_str = "**:" + color + "[" + str(skin_max) + "]** " + skin.units

        eye = room.calc_zones["EyeLimits"]
        eye_max = round(eye.values.max(), 2)
        color = "red" if hours_eye_uw < 8 else "blue"
        eye_str = "**:" + color + "[" + str(eye_max) + "]** " + eye.units
        cols = st.columns(2)
        with cols[0]:
            st.write("**Max Skin Dose (8 Hours)**: ", skin_str)
        with cols[1]:
            st.write("**Max Eye Dose (8 Hours)**: ", eye_str)

        st.markdown("**Hours before first TLV is reached:**")

        # unweighted hours to TLV
        hours_to_tlv = min([hours_skin_uw, hours_eye_uw])
        if hours_to_tlv > 8:
            hour_str = ":blue[Indefinite]"
        else:
            hour_str = f":red[**{round(hours_to_tlv,2)}**]"
            dim = round((hours_to_tlv / 8) * 100, 1)
            hour_str += f" *(To be compliant with TLVs, this lamp must be dimmed to {dim}% of its present power)*"

        writecols = st.columns([1, 12])
        writecols[1].markdown(
            f"With monochromatic assumption: {hour_str}",
            help="These results assume that all lamps in the simulation are perfectly monochromatic 222nm sources. They don't rely on any data besides anies file. For most *filtered* KrCl lamps, but not all, the monochromatic approximation is a reasonable assumption.",
        )

        # weighted hours to TLV
        hours_skin_w, hours_eye_w = get_weighted_hours_to_tlv(room)
        hours_to_tlv = min([hours_skin_w, hours_eye_w])
        if hours_to_tlv > 8:
            hour_str = ":blue[Indefinite]"
        else:
            hour_str = f":red[**{round(hours_to_tlv,2)}**]"
            dim = round((hours_to_tlv / 8) * 100, 1)
            hour_str += f" *(To be compliant with TLVs, this lamp must be dimmed to {dim}% of its present power)*"

        writecols[1].markdown(
            f"With spectral weighting: {hour_str}",
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


def print_efficacy(room):
    """print germicidal efficacy results"""
    st.subheader(
        "Efficacy",
        divider="grey",
        help="Equivalent air changes from UV (eACH-UV) in a *well-mixed room* is determined by the average fluence [mW/cm2] multiplied by the susceptibility value k [cm2/mW] multiplied by the number of seconds in an hour (3600). **Note that values of k are highly uncertain and should be considered preliminary.**"
    )
    fluence = room.calc_zones["WholeRoomFluence"]
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


def print_airchem(room):
    """display indoor air chemistry results"""
    st.subheader(
        "Indoor Air Chemistry",
        divider="grey",
        help="Given an assumed air change rate from ventilation and an ozone decay rate typical for indoor environments, the anticipated total increase in ozone in parts per billion. This calculation currently assumes an ozone generation constant of 10, calculated by Peng 2022 (DOI: 10.1021/acs.estlett.3c00314) for an Ushio B1. Eventually this calculation will take into account individual lamp spectra."
    )
    cols = st.columns(2)
    cols[0].number_input(
        "Air changes per hour from ventilation",
        on_change=update_ozone_results,
        args=[room],
        min_value=0.0,
        step=0.1,
        key="air_changes_results",
        help="Note that outdoor ozone is almost always at a higher concentration than indoor ozone. Increasing the air changes from ventilation will reduce the increase in ozone due to GUV, but may increase the total indoor ozone concentration. However, increasing ventilation will also increase the rate of removal of any secondary products that may form from the ozone."
    )
    cols[1].number_input(
        "Ozone decay constant",
        on_change=update_ozone_results,
        args=[room],
        min_value=0.0,
        step=0.1,
        key="ozone_decay_constant_results",
        help="An initial ozone decay constant of 2.7 is typical of indoor environments (Nazaroff and Weschler; DOI: 10.1111/ina.12942); ",
    )
    fluence = room.calc_zones["WholeRoomFluence"]
    if fluence.values is not None:
        ozone_ppb = calculate_ozone_increase(room)
        ozone_color = "red" if ozone_ppb > 5 else "blue"
        ozone_str = f":{ozone_color}[**{round(ozone_ppb,2)} ppb**]"
    else:
        ozone_str = "Not available"
    st.write(f"Estimated increase in indoor ozone from UV: {ozone_str}")


def get_unweighted_hours_to_tlv(room):
    """
    calculate hours to tlv without taking into account lamp spectra
    """

    skin_standard, eye_standard = _get_standards(room.standard)
    mono_skinmax, mono_eyemax = _get_mono_limits(222, room)

    skin_limits = room.calc_zones["SkinLimits"]
    eye_limits = room.calc_zones["EyeLimits"]

    skin_hours = mono_skinmax * 8 / skin_limits.values.max()
    eye_hours = mono_eyemax * 8 / eye_limits.values.max()
    return skin_hours, eye_hours


def get_weighted_hours_to_tlv(room):
    """
    calculate the hours to tlv in a particular room, given a particular installation of lamps

    technically speaking; in the event of overlapping beams, it is possible to check which
    lamps are shining on that spot and what their spectra are. this function currently doesn't do that

    TODO: good lord this function is a nightmare. let's make it less horrible eventually
    """

    skin_standard, eye_standard = _get_standards(room.standard)
    mono_skinmax, mono_eyemax = _get_mono_limits(222, room)

    skin_limits = room.calc_zones["SkinLimits"]
    eye_limits = room.calc_zones["EyeLimits"]

    skin_hours, eyes_hours, skin_maxes, eye_maxes = _tlvs_over_lamps(room)

    # now check that overlapping beams in the calc zone aren't pushing you over the edge
    # max irradiance in the wholeplane
    global_skin_max = round(skin_limits.values.max() / 3.6 / 8, 3)  # to uW/cm2
    global_eye_max = round(eye_limits.values.max() / 3.6 / 8, 3)
    # max irradiance on the plane produced by each lamp
    local_skin_max = round(max(skin_maxes), 3)
    local_eye_max = round(max(eye_maxes), 3)

    if global_skin_max > local_skin_max or global_eye_max > local_eye_max:
        # first pick a lamp to use the spectra of. one with a spectra is preferred.
        chosen_lamp = _select_representative_lamp(room, skin_standard)
        if len(chosen_lamp.spectra) > 0:
            # calculate weighted if possible
            new_skin_hours = _get_weighted_hours(
                chosen_lamp, global_skin_max, skin_standard
            )
            new_eye_hours = _get_weighted_hours(
                chosen_lamp, global_eye_max, eye_standard
            )
        else:
            # these will be in mJ/cm2/8 hrs
            new_skin_hours = mono_skinmax * 8 / skin_limits.values.max()
            new_eye_hours = mono_eyemax * 8 / eye_limits.values.max()

        skin_hours.append(new_skin_hours)
        eyes_hours.append(new_eye_hours)
    return min(skin_hours), min(eyes_hours)


def _get_standards(standard):
    """return the relevant skin and eye limit standards"""
    if "ANSI IES RP 27.1-22" in standard:
        skin_standard = "ANSI IES RP 27.1-22 (Skin)"
        eye_standard = "ANSI IES RP 27.1-22 (Eye)"
    elif "IEC 62471-6:2022" in standard:
        skin_standard = "IEC 62471-6:2022 (Eye/Skin)"
        eye_standard = skin_standard
    else:
        raise KeyError(f"Room standard {standard} is not valid")

    return skin_standard, eye_standard


def _get_mono_limits(wavelength, room):
    """
    load the monochromatic skin and eye limits at a given wavelength
    """
    # just pick the first lamp in the list
    lamp_id = next(iter(room.lamps))
    weights = room.lamps[lamp_id].spectral_weightings

    skin_standard, eye_standard = _get_standards(room.standard)
    skindata = dict(zip(*weights[skin_standard]))
    eyedata = dict(zip(*weights[eye_standard]))

    return 3 / skindata[wavelength], 3 / eyedata[wavelength]


def _tlvs_over_lamps(room):
    """calculate the hours to TLV over each lamp in the calc zone"""

    skin_standard, eye_standard = _get_standards(room.standard)
    mono_skinmax, mono_eyemax = _get_mono_limits(222, room)

    # iterate over all lamps
    hours_to_tlv_skin, hours_to_tlv_eye = [], []
    skin_maxes, eye_maxes = [], []
    for lamp_id, lamp in room.lamps.items():
        if len(lamp.max_irradiances) > 0:
            # get max irradiance shown by this lamp upon both zones
            skin_irradiance = lamp.max_irradiances["SkinLimits"]
            eye_irradiance = lamp.max_irradiances["EyeLimits"]

            if len(lamp.spectra) > 0:
                # if lamp has a spectra associated with it, calculate the weighted spectra
                skin_hours = _get_weighted_hours(lamp, skin_irradiance, skin_standard)
                eye_hours = _get_weighted_hours(lamp, eye_irradiance, eye_standard)
            else:
                # if it doesn't, first, yell.
                st.warning(
                    f"{lamp.name} does not have an associated spectra. Photobiological safety calculations will be inaccurate."
                )
                # then just use the monochromatic approximation
                skin_hours = mono_skinmax * 8 / skin_irradiance
                eye_hours = mono_eyemax * 8 / eye_irradiance
            hours_to_tlv_skin.append(skin_hours)
            hours_to_tlv_eye.append(eye_hours)
            skin_maxes.append(skin_irradiance)
            eye_maxes.append(eye_irradiance)
        else:
            hours_to_tlv_skin, hours_to_tlv_eye = [np.inf], [np.inf]
            skin_maxes, eye_maxes = [0], [0]
    if len(room.lamps.items()) == 0:
        hours_to_tlv_skin, hours_to_tlv_eye = [np.inf], [np.inf]
        skin_maxes, eye_maxes = [0], [0]

    return hours_to_tlv_skin, hours_to_tlv_eye, skin_maxes, eye_maxes


def _get_weighted_hours(lamp, irradiance, standard):
    """
    calculate hours to tlv for a particular lamp, calc zone, and standard
    """

    # get spectral data for this lamp
    wavelength = lamp.spectra["Unweighted"][0]
    rel_intensities = lamp.spectra["Unweighted"][1]
    # determine total power in the spectra as it corresponds to total power
    idx = np.intersect1d(np.argwhere(wavelength >= 200), np.argwhere(wavelength <= 280))
    spectral_power = _sum_spectrum(wavelength[idx], rel_intensities[idx])
    ratio = irradiance / spectral_power
    power_distribution = rel_intensities[idx] * ratio  # true spectra at calc plane
    # load weights according to the standard
    weights_list = lamp.spectral_weightings[standard]
    # interpolate to match the spectra
    weighting = np.interp(wavelength, weights_list[0], weights_list[1])

    # weight the normalized spectra
    weighted_spectra = power_distribution * weighting[idx]
    # sum to get weighted power
    weighted_power = _sum_spectrum(wavelength[idx], weighted_spectra)

    seconds_to_tlv = 3000 / weighted_power  # seconds to reach 3 mJ/3000 uJ
    hours_to_tlv = seconds_to_tlv / 3600  # hours to limit
    return hours_to_tlv


def _sum_spectrum(wavelength, intensity):
    """
    sum across a spectrum
    """
    weighted_intensity = [
        intensity[i] * (wavelength[i] - wavelength[i - 1])
        for i in range(1, len(wavelength))
    ]
    return sum(weighted_intensity)


def _select_representative_lamp(room, standard):
    """
    select a lamp to use for calculating the spectral limits in the event
    that no single lamp is contributing exclusively to the TLVs
    """
    if len(set([lamp.filename for lamp_id, lamp in room.lamps.items()])) <= 1:
        # if they're all the same just use the first lamp in the list
        chosen_lamp = room.lamps[next(iter(room.lamps))]
    else:
        # otherwise pick the least convenient one
        weighted_sums = {}
        for lamp_id, lamp in room.lamps.items():
            # iterate through all lamps and pick the one with the highest value sum
            if len(lamp.spectra) > 0:
                # either eye or skin standard can be used for this purpose
                weighted_sums[lamp_id] = lamp.spectra[standard].sum()

        if len(weighted_sums) > 0:
            chosen_id = max(weighted_sums, key=weighted_sums.get)
            chosen_lamp = room.lamps[chosen_id]
        else:
            # if no lamps have a spectra then it doesn't matter. pick any lamp.
            chosen_lamp = room.lamps[next(iter(room.lamps))]
    return chosen_lamp


def calculate_ozone_increase(room):
    """
    ozone generation constant is currently hardcoded to 10 for GUV222
    this should really be based on spectra instead
    but this is a relatively not very big deal, because
    """
    avg_fluence = room.calc_zones["WholeRoomFluence"].values.mean()
    ozone_gen = 10  # hardcoded for now, eventually should be based on spectra bu
    ach = room.air_changes
    ozone_decay = room.ozone_decay_constant
    ozone_increase = avg_fluence * ozone_gen / (ach + ozone_decay)
    return ozone_increase
