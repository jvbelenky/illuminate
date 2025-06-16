import streamlit as st
import numpy as np
from app.widget import close_results, set_val, persistent_checkbox

# from ._top_ribbon import check_recalculation

ss = st.session_state
SPECIAL_ZONES = ["WholeRoomFluence", "SkinLimits", "EyeLimits"]


def results_page():
    """display results in the customizable panel"""
    cols = st.columns([15, 1])
    cols[0].header("Results")
    cols[1].button(
        "X", on_click=close_results, use_container_width=True, key="close_results"
    )

    # do some checks first. do we actually have any lamps?
    lamps = ss.room.lamps
    if not lamps:
        msg = "You haven't added any luminaires yet! Try adding a luminaire by clicking the `Add Luminaire` button."
        st.warning(msg)
    elif all(v.filedata is None for v in lamps.values()):
        msg = "You've added at least one luminaire, but you haven't selected a file to define it. Navigate to a luminaire in the `Select luminaire...` menu, then select a file from the `Lamp file` drop-down list in the left-hand panel."
        st.warning(msg)
    elif all(not v.enabled for v in lamps.values()):
        msg = "You've added at least one luminaire, but all luminaires are currently disabled."
        st.warning(msg)
    elif all(not v.enabled or v.filedata is None for v in lamps.values()):
        msg = "All luminaires are currently either disabled, or missing filedata."
        st.warning(msg)
    else:
        # check that all positions of lamps and calc zones are where they're supposed to be
        msgs = ss.room.check_positions()
        for msg in msgs:
            if msg is not None:
                st.warning(msg)
    # if we're good print the results
    print_summary()
    zones = ss.room.calc_zones
    user_zones = [key for key in zones.keys() if key not in SPECIAL_ZONES]
    if len(user_zones) > 0:
        if any([zones[key].values is not None for key in user_zones]):
            print_user_defined_zones()
    print_safety()
    print_efficacy()
    if all(["Krypton chloride" in lamp.guv_type for lamp in lamps.values()]):
        print_airchem()

    export_options()


def print_summary():
    st.subheader("Summary", divider="grey")
    fluence_values = ss.room.calc_zones["WholeRoomFluence"].get_values()
    skin = ss.room.calc_zones["SkinLimits"]
    eye = ss.room.calc_zones["EyeLimits"]
    skin_values = skin.get_values()
    eye_values = eye.get_values()

    # avg fluence
    if fluence_values is not None:
        fluence_str = f"**:violet[{fluence_values.mean():.3f}]** μW/cm²"
        st.write("**Average fluence:** " + fluence_str)

    if skin_values is not None and eye_values is not None:

        weighted_skin_dose, weighted_eye_dose = check_lamps(ss.room, warn=False)

        # determine colors
        skincolor, eyecolor = "blue", "blue"
        if weighted_skin_dose.max() > 3:
            skincolor = "red"
        if weighted_eye_dose.max() > 3:
            eyecolor = "red"

        skin_str = f"**:{skincolor}[{skin_values.max():.2f}]** {skin.units}"
        st.write("**Max Skin Dose (8 Hours)**: ", skin_str)

        eye_str = f"**:{eyecolor}[{eye_values.max():.2f}]** {eye.units}"
        st.write("**Max Eye Dose (8 Hours)**: ", eye_str)

        if max(weighted_skin_dose.max(), weighted_eye_dose.max()) > 3:
            st.error("This installation does not comply with selected TLVs.")

    st.download_button(
        "Generate Report",
        data=ss.room.generate_report(),
        file_name="guv_report.csv",
    )


def print_user_defined_zones():

    """all user-defined calc zones, basic stats and"""
    st.subheader("User Defined Calculation Zones", divider="grey")
    for zone_id, zone in ss.room.calc_zones.items():
        
        vals = zone.get_values()
        if vals is not None and zone.zone_id not in SPECIAL_ZONES:
            cols = st.columns(2)
            if zone.calctype == "Plane":
                cols[0].pyplot(
                    zone.plot_plane(title=zone.name)[0],
                    **{"transparent": "True"},
                )
            elif zone.calctype == "Volume":
                fig = zone.plot_volume(title=zone.name)
                cols[0].plotly_chart(fig, use_container_width=True, height=450)                
                        
            cols[1].write("")
            cols[1].write("")
            # cols[1].write(f"***{zone.name}***")
            cols[1].subheader(zone.name)
            unitstr = zone.units
            if zone.dose:
                unitstr = f"mJ/cm² over {zone.hours} hours"
                avgstr = f"**Average:** \t{vals.mean():.1f} {unitstr}"
                maxstr = f"**Max:** \t{vals.max():.1f} {unitstr}"
                minstr = f"**Min:** \t{vals.min():.1f} {unitstr}"
            else:
                unitstr = "uW/cm²"
                avgstr = f"**Average:** \t{vals.mean():.3f} {unitstr}"
                maxstr = f"**Max:** \t{vals.max():.3f} {unitstr}"
                minstr = f"**Min:** \t{vals.min():.3f} {unitstr}"
            cols[1].write(avgstr)
            cols[1].write(maxstr)
            cols[1].write(minstr)
            cols[1].write("")
            cols[1].write("")
            try:
                cols[1].download_button(
                    "Export Values",
                    data=zone.export(),
                    file_name=zone.name + ".csv",
                    use_container_width=True,
                    disabled=True if zone.values is None else False,
                )
            except NotImplementedError:
                pass


def print_safety():
    """print photobiological safety results"""
    st.subheader(
        "Photobiological Safety",
        divider="grey",
        help="Photobiological safety standards are set in the USA by the American Conference of Governmental Industrial Hygienists (ACGIH) and elsewhere in the world by the  International Commission on Non-Ionizing Radiation Protection (ICNIRP). At 222 nm, the ACGIH limits for skin are 479 mJ/cm2 over 8 hours, and for eyes they are 161 mJ/cm2 over 8 hours. The ICNIRP limits are the same for both eyes and skin; 23 mJ/cm2 over 8 hours. However, though KrCl lamps are approximately monochromatic, this is only an approximation, and individual KrCl lamps may have different threshold limit values (TLVs) depending on their spectral content.",
    )
    st.selectbox(
        "Select photobiological safety standard",
        options=ss.standards,
        on_change=update_standard_results,
        key="room_standard_results",
        help="The ANSI IES RP 27.1-22 standard corresponds to the photobiological limits for UV exposure set by the American Conference of Governmental Industrial Hygienists (ACGIH). The IEC 62471-6:2022 standard corresponds to the limits set by the International Commission on Non-Ionizing Radiation Protection (ICNIRP). Both standards indicate that the measurement should be taken at 1.8 meters up from the floor, but UL8802 (Ultraviolet (UV) Germicidal Equipment and Systems) indicates that it should be taken at 1.9 meters instead. Additionally, though ANSI IES RP 27.1-22 indicates that eye exposure limits be taken with a 80 degere field of view parallel to the floor, considering only vertical irradiance, UL8802 indicates that measurements be taken in the 'worst case' direction, resulting in a stricter limit.",
    )

    skin = ss.room.calc_zones["SkinLimits"]
    eye = ss.room.calc_zones["EyeLimits"]
    skin_values = skin.get_values()
    eye_values = eye.get_values()

    SHOW_SKIN = True if skin_values is not None else False
    SHOW_EYES = True if eye_values is not None else False
    if SHOW_SKIN and SHOW_EYES:
        cols = st.columns(2)

        weighted_skin_dose, weighted_eye_dose = check_lamps(ss.room, warn=True)

        skinmax = skin_values.max().round(1)
        skinmax_w = weighted_skin_dose.max().round(2)
        skin_hrs = round(3 * 8 / weighted_skin_dose.max(), 1)

        eyemax = eye_values.max().round(1)
        eyemax_w = weighted_eye_dose.max().round(2)
        eye_hrs = round(3 * 8 / weighted_eye_dose.max(), 1)

        skincolor, eyecolor = "blue", "blue"
        if weighted_skin_dose.max() > 3:
            skincolor = "red"
        if weighted_eye_dose.max() > 3:
            eyecolor = "red"

        if skin_hrs < 8:
            skin_hours_str = f"\tHours to skin TLV: **:{skincolor}[{skin_hrs}]** hours"
        else:
            skin_hours_str = (
                f"\tHours to skin TLV: **:{skincolor}[Indefinite]** ({skin_hrs} hours)"
            )
        cols[0].write(skin_hours_str)
        cols[0].write(f"\tMax 8-hour skin dose: **:{skincolor}[{skinmax:.1f}]** mJ/cm²")
        cols[0].write(
            f"\tMax 8-hour *weighted* skin dose: **:{skincolor}[{skinmax_w:.2f}]** mJ/cm²"
        )

        if eye_hrs < 8:
            eye_hours_str = f"\tHours to eye TLV: **:{eyecolor}[{eye_hrs}]** hours"
        else:
            eye_hours_str = (
                f"\tHours to eye TLV: **:{eyecolor}[Indefinite]** ({eye_hrs} hours)"
            )
        cols[1].write(eye_hours_str)
        cols[1].write(f"\tMax 8-hour eye dose: **:{eyecolor}[{eyemax:.1f}]** mJ/cm²")
        cols[1].write(
            f"\tMax 8-hour *weighted* eye dose: **:{eyecolor}[{eyemax_w:.2f}]** mJ/cm²"
        )

        SHOW_PLOTS = st.checkbox("Show Plots", value=True)
        if SHOW_PLOTS:
            cols = st.columns(2)
            skintitle = f"8-Hour Skin Dose (Max: {skinmax:.1f} {skin.units})"
            eyetitle = f"8-Hour Eye Dose (Max: {eyemax:.1f} {eye.units})"

            cols[0].pyplot(
                skin.plot_plane(title=skintitle)[0],
                **{"transparent": "True"},
            )
            cols[1].pyplot(
                eye.plot_plane(title=eyetitle)[0],
                **{"transparent": "True"},
            )


def check_lamps(room, warn=True):
    """
    Iterate through every lamp in the Room object and assess whether it
    individually exceeds the skin or eye limits.  If warn is True, print a
    warning and dimming recommendation

    Then, check if the combination of all lamps exceeds the limits, even if no
    individual lamp does.

    Finally, apply the recommended dimming, and check if doing so will make the
    installation compliant.

    Return the weighted skin and eye dose, which must be < 3 mJ to be compliant.

    TODO: Possibly worth moving this function into guv-calcs instead.

    """

    skin = room.calc_zones["SkinLimits"]
    eye = room.calc_zones["EyeLimits"]
    skin_values = skin.get_values()
    eye_values = eye.get_values()

    skindims, eyedims = {}, {}
    weighted_skin_dose = np.zeros(skin_values.shape)
    weighted_eye_dose = np.zeros(eye_values.shape)

    dimmed_weighted_skin_dose = np.zeros(skin_values.shape)
    dimmed_weighted_eye_dose = np.zeros(eye_values.shape)

    # check if any individual lamp exceeds the limits
    for lampid, lamp in room.lamps.items():
        if lampid in eye.lamp_values.keys() and lampid in skin.lamp_values.keys():
            # fetch the limits for this specific lamp
            skinmax, eyemax = room.lamps[lampid].get_limits(room.standard)
            # these are irradiance values, not dose
            skinrad, eyerad = skin.lamp_values[lampid], eye.lamp_values[lampid]
            # to dose
            skinvals, eyevals = skinrad * 3.6 * skin.hours, eyerad * 3.6 * eye.hours
            # weighting function for this specific lamp
            skinweight, eyeweight = 3 / skinmax, 3 / eyemax
            # % dimming required to be compliant
            skindim, eyedim = skinmax / skinvals.max(), eyemax / eyevals.max()
            # add to total dose
            weighted_skin_dose += skinvals * skinweight
            weighted_eye_dose += eyevals * eyeweight

            skindims[lampid], eyedims[lampid] = skindim, eyedim
            total_dim = min(skindim, eyedim, 1)
            dimmed_weighted_eye_dose += eyevals * eyeweight * total_dim
            dimmed_weighted_skin_dose += skinvals * skinweight * total_dim

            # individual lamp check
            if min(skindim, eyedim, 1) < 1:
                skindim, eyedim = round(skindim * 100, 1), round(eyedim * 100, 1)
                if skindim < 100:
                    string = f"{lamp.name} must be dimmed to **{skindim}%** its present power to comply with selected skin TLVs"
                    if eyedim < 100:
                        string += f" and to **{eyedim}%** to comply with eye TLVs."
                elif eyedim < 100:
                    string = f"{lamp.name} must be dimmed to **{eyedim}%** its present power comply with selected eye TLVs"
                if warn:
                    st.warning(string)

            if (
                lamp.guv_type != "Low-pressure mercury (254 nm)"
                and lamp.spectra is None
                and lamp.filedata is not None
                and warn
            ):
                msg = f"{lamp.name} is missing a spectrum. Photobiological safety calculations may be inaccurate."
                st.warning(msg)

    # Check if seemingly-compliant installations actually aren't
    dimvals = list(skindims.values()) + list(eyedims.values())
    DIMMING_NOT_REQUIRED = all([dim > 1 for dim in dimvals])
    LAMPS_COMPLIANT = (
        max(weighted_skin_dose.max().round(2), weighted_eye_dose.max().round(2)) <= 3
    )
    DIMMED_LAMPS_COMPLIANT = (
        max(
            dimmed_weighted_skin_dose.max().round(2),
            dimmed_weighted_eye_dose.max().round(2),
        )
        <= 3
    )
    if DIMMING_NOT_REQUIRED and not LAMPS_COMPLIANT:
        string = "Though all lamps are individually compliant, dose must be reduced to "
        skindim = round(3 / weighted_skin_dose.max() * 100, 1)
        eyedim = round(3 / weighted_eye_dose.max() * 100, 1)
        if weighted_skin_dose.max() > 3:
            string += (
                f"**{skindim}%** its present value to comply with selected skin TLVs"
            )
            if weighted_eye_dose.max() > 3:
                string += f" and to **{eyedim}%** to comply with selected eye TLVs."
        elif weighted_eye_dose.max() > 3:
            string += (
                f"**{eyedim}%** its present value to comply with selected eye TLVs"
            )
        if warn:
            st.warning(string)

    # check if dimming will make the installation compliant
    if not DIMMED_LAMPS_COMPLIANT:
        string = "Even after applying dimming, this installation may not be compliant. Dose must be reduced to "
        skindim = round(3 / weighted_skin_dose.max() * 100, 1)
        eyedim = round(3 / weighted_eye_dose.max() * 100, 1)
        if dimmed_weighted_skin_dose.max() > 3:
            string += (
                f"**{skindim}%** its present value to comply with selected skin TLVs"
            )
            if dimmed_weighted_eye_dose.max() > 3:
                string += f" and to {eyedim}% to comply with eye TLVs."
        elif dimmed_weighted_eye_dose.max() > 3:
            string += (
                f"**{eyedim}%** its present value to comply with selected eye TLVs"
            )
        if warn:
            st.warning(string)

    return weighted_skin_dose, weighted_eye_dose


def print_efficacy():
    """print germicidal efficacy results"""
    st.subheader(
        "Pathogen Reduction in Air",
        divider="grey",
        help="Equivalent air changes from UV (eACH-UV) in a *well-mixed room* is determined by the average fluence [mW/cm2] multiplied by the susceptibility value k [cm2/mW] multiplied by the number of seconds in an hour (3600). **Note that values of k are highly uncertain and should be considered preliminary.**",
    )
    fluence = ss.room.calc_zones["WholeRoomFluence"]
    fluence_values = fluence.get_values()
    if fluence_values is not None:
        avg_fluence = round(fluence_values.mean(), 3)
        fluence_str = "**:violet[" + str(avg_fluence) + "]** μW/cm2"
    else:
        fluence_str = None
    st.write("**Average fluence:** ", fluence_str)

    if fluence_values is not None and fluence_values.sum() > 0:
        SHOW_KPLOT = st.checkbox("Show Plot", value=True)
        if SHOW_KPLOT:
            st.pyplot(ss.kfig)
        SHOW_KDATA = st.checkbox("Show Data", value=False)
        if SHOW_KDATA:
            st.data_editor(
                ss.kdf,
                disabled=True,
                column_config={"Link": st.column_config.LinkColumn(display_text="[X]")},
                hide_index=True,
            )
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
    fluence_values = ss.room.calc_zones["WholeRoomFluence"].get_values()
    if fluence_values is not None:
        ozone_ppb = calculate_ozone_increase()
        ozone_color = "red" if ozone_ppb > 5 else "blue"
        ozone_str = f":{ozone_color}[**{round(ozone_ppb,2)} ppb**]"
    else:
        ozone_str = "Not available"
    st.write(f"Estimated increase in indoor ozone from UV: {ozone_str}")


def calculate_ozone_increase():
    """
    ozone generation constant is currently hardcoded to 10 for GUV222
    this should really be based on spectra instead, but the dependence is not very strong
    at least for GUV222 sources
    """
    avg_fluence = ss.room.calc_zones["WholeRoomFluence"].values.mean()
    ozone_gen = 10  # hardcoded for now, eventually should be based on spectra
    ach = ss.room.air_changes
    ozone_decay = ss.room.ozone_decay_constant
    ozone_increase = avg_fluence * ozone_gen / (ach + ozone_decay)
    return ozone_increase


def export_options():
    """
    a results-page option for exporting all results
    """

    st.subheader("Export Results", divider="grey")
    col, col2 = st.columns(2)
    include_plots = col2.checkbox("Include result plots")

    col.download_button(
        "Export All Results",
        data=ss.room.export_zip(include_plots=include_plots),
        file_name="illuminate.zip",
        use_container_width=True,
        type="primary",
        key="export_all_results",
    )

    for zone_id, zone in ss.room.calc_zones.items():
        if zone.calctype in ["Plane", "Volume"]:
            col.download_button(
                zone.name,
                data=zone.export(),
                file_name=zone.name + ".csv",
                use_container_width=True,
                disabled=True if zone.values is None else False,
            )


def update_standard_results():
    """update what standard is used based on results page, recalculate if necessary"""
    # store whether recalculation is necessary
    RECALCULATE = False
    if ("UL8802" in ss.room.standard) ^ ("UL8802" in ss["room_standard_results"]):
        RECALCULATE = True
    # update room standard
    standard = set_val("room_standard_results", ss.room.standard)
    ss.room.set_standard(standard)  # this will also update the standard calc zones
    # update other widget
    ss["room_standard"] = ss.room.standard
    # recalculate if necessary eg: if value has changed
    if RECALCULATE:
        ss.room.calculate_by_id("EyeLimits")
        ss.room.calculate_by_id("SkinLimits")


def update_ozone_results():
    ss.room.air_changes = set_val("air_changes_results", ss.room.air_changes)
    ss.room.ozone_decay_constant = set_val(
        "ozone_decay_constant_results", ss.room.ozone_decay_constant
    )
    ss["air_changes"] = set_val("air_changes_results", ss.room.air_changes)
    ss["ozone_decay_constant"] = set_val(
        "ozone_decay_constant_results", ss.room.ozone_decay_constant
    )
