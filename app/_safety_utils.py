import streamlit as st
import numpy as np
from guv_calcs import get_tlv

ss = st.session_state


def get_unweighted_hours_to_tlv(wavelength=222):
    """
    calculate hours to tlv without taking into account lamp spectra
    """
    skin_standard, eye_standard = _get_standards(ss.room.standard)
    mono_skinmax, mono_eyemax = _get_mono_limits(wavelength)

    skin_limits = ss.room.calc_zones["SkinLimits"]
    eye_limits = ss.room.calc_zones["EyeLimits"]

    skin_hours = mono_skinmax * 8 / skin_limits.values.max()
    eye_hours = mono_eyemax * 8 / eye_limits.values.max()
    return skin_hours, eye_hours


def get_weighted_hours_to_tlv(wavelength=222):
    """
    calculate the hours to tlv in a particular room, given a particular installation of lamps

    technically speaking; in the event of overlapping beams, it is possible to check which
    lamps are shining on that spot and what their spectra are. this function currently doesn't do that

    TODO: good lord this function is a nightmare. let's make it less horrible eventually
    """

    skin_standard, eye_standard = _get_standards(ss.room.standard)
    mono_skinmax, mono_eyemax = _get_mono_limits(wavelength)

    skin_limits = ss.room.calc_zones["SkinLimits"]
    eye_limits = ss.room.calc_zones["EyeLimits"]

    skin_hours, eyes_hours, skin_maxes, eye_maxes = _tlvs_over_lamps(wavelength)

    # now check that overlapping beams in the calc zone aren't pushing you over the edge
    # max irradiance in the wholeplane
    global_skin_max = round(skin_limits.values.max() / 3.6 / 8, 3)  # to uW/cm2
    global_eye_max = round(eye_limits.values.max() / 3.6 / 8, 3)
    # max irradiance on the plane produced by each lamp
    local_skin_max = round(max(skin_maxes), 3)
    local_eye_max = round(max(eye_maxes), 3)

    if global_skin_max > local_skin_max or global_eye_max > local_eye_max:
        # first pick a lamp to use the spectra of. one with a spectra is preferred.
        chosen_lamp = _select_representative_lamp(skin_standard)
        if chosen_lamp.spectra is not None:
            # calculate weighted if possible
            new_skin_hours = (
                chosen_lamp.spectra.get_seconds_to_tlv(global_skin_max, skin_standard)
                / 3600
            )
            new_eye_hours = (
                chosen_lamp.spectra.get_seconds_to_tlv(global_eye_max, eye_standard)
                / 3600
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
        raise KeyError(f"Standard {standard} is not valid")

    return skin_standard, eye_standard


def _get_mono_limits(wavelength):
    """
    load the monochromatic skin and eye limits at a given wavelength
    """
    skin_standard, eye_standard = _get_standards(ss.room.standard)
    skin_tlv = get_tlv(wavelength, skin_standard)
    eye_tlv = get_tlv(wavelength, eye_standard)
    return skin_tlv, eye_tlv


def _tlvs_over_lamps(wavelength=222):
    """calculate the hours to TLV over each lamp in the calc zone"""

    skin_standard, eye_standard = _get_standards(ss.room.standard)
    mono_skinmax, mono_eyemax = _get_mono_limits(wavelength)
    # iterate over all lamps
    hours_to_tlv_skin, hours_to_tlv_eye = [], []
    skin_maxes, eye_maxes = [], []
    for lamp_id, lamp in ss.room.lamps.items():
        if len(lamp.max_irradiances) > 0:
            # get max irradiance shown by this lamp upon both zones
            skin_irradiance = lamp.max_irradiances["SkinLimits"]
            eye_irradiance = lamp.max_irradiances["EyeLimits"]

            if lamp.spectra is not None:
                # if lamp has a spectra associated with it, calculate the weighted spectra
                skin_hours = (
                    lamp.spectra.get_seconds_to_tlv(skin_irradiance, skin_standard)
                    / 3600
                )
                eye_hours = (
                    lamp.spectra.get_seconds_to_tlv(eye_irradiance, eye_standard) / 3600
                )
            else:
                # if it doesn't, first, yell.
                if ss.wavelength == 222:
                    st.warning(
                        f"{lamp.name} does not have an associated spectra. Photobiological safety calculations may be inaccurate."
                    )

                # then just use the monochromatic approximation
                skin_hours = mono_skinmax / (skin_irradiance * 3.6)
                eye_hours = mono_eyemax / (eye_irradiance * 3.6)
            hours_to_tlv_skin.append(skin_hours)
            hours_to_tlv_eye.append(eye_hours)
            skin_maxes.append(skin_irradiance)
            eye_maxes.append(eye_irradiance)
        else:
            hours_to_tlv_skin, hours_to_tlv_eye = [np.inf], [np.inf]
            skin_maxes, eye_maxes = [0], [0]
    if len(ss.room.lamps.items()) == 0:
        hours_to_tlv_skin, hours_to_tlv_eye = [np.inf], [np.inf]
        skin_maxes, eye_maxes = [0], [0]

    return hours_to_tlv_skin, hours_to_tlv_eye, skin_maxes, eye_maxes


def _select_representative_lamp(standard):
    """
    select a lamp to use for calculating the spectral limits in the event
    that no single lamp is contributing exclusively to the TLVs
    """
    if len(set([lamp.filename for lamp_id, lamp in ss.room.lamps.items()])) <= 1:
        # if they're all the same just use the first lamp in the list
        chosen_lamp = ss.room.lamps[next(iter(ss.room.lamps))]
    else:
        # otherwise pick the least convenient one
        weighted_sums = {}
        for lamp_id, lamp in ss.room.lamps.items():
            # iterate through all lamps and pick the one with the highest value sum
            if lamp.spectra is not None and lamp.filename is not None:
                # either eye or skin standard can be used for this purpose
                weighted_sums[lamp_id] = lamp.spectra.sum(weight=standard)

        if len(weighted_sums) > 0:
            chosen_id = max(weighted_sums, key=weighted_sums.get)
            chosen_lamp = ss.room.lamps[chosen_id]
        else:
            # if no lamps have a spectra then it doesn't matter. pick any lamp.
            chosen_lamp = ss.room.lamps[next(iter(ss.room.lamps))]
    return chosen_lamp


def make_hour_string(hours, which):
    """format string for printing hours to tlv"""
    if hours > 8:
        hours_str = f":blue[**Indefinite ({round(hours,2)})**]"
    else:
        hours_str = f":red[**{round(hours,2)}**]"
        dim = round((hours / 8) * 100, 1)
        hours_str += f" *(To be compliant with {which} TLVs, this lamp must be dimmed to {dim}% of its present power)*"
    return hours_str
