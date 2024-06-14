import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

# import plotly.graph_objs as go
# import numpy as np

ss = st.session_state


def room_plot(room):
    if ss.selected_lamp_id:
        select_id = ss.selected_lamp_id
    elif ss.selected_zone_id:
        select_id = ss.selected_zone_id
    else:
        select_id = None
    ss.fig = room.plotly(fig=ss.fig, select_id=select_id)

    if ss.show_results:
        if ss.editing is None:
            ar_scale = 0.5
        else:
            ar_scale = 0.3  # this won't show
    else:
        if ss.editing is None:
            ar_scale = 0.8  # full middle page
        else:
            ar_scale = 0.6
    # ar_scale = 0.8 if (ss.editing != "results") else 0.5
    ss.fig.layout.scene.aspectratio.x *= ar_scale
    ss.fig.layout.scene.aspectratio.y *= ar_scale
    ss.fig.layout.scene.aspectratio.z *= ar_scale
    ss.fig.layout.scene.xaxis.range = ss.fig.layout.scene.xaxis.range[::-1]

    # # add fluence isosurface
    # # TODO: put this in guv-calcs instead
    # fluence = room.calc_zones["WholeRoomFluence"]
    # traces = [trace.name for trace in fig.data]
    # if fluence.values is not None:

    # X, Y, Z = np.meshgrid(*fluence.points)
    # x, y, z = X.flatten(), Y.flatten(), Z.flatten()
    # values = fluence.values.flatten()
    # isomin = room.calc_zones["WholeRoomFluence"].values.mean() / 2
    # if "Fluence" not in traces:  # add if not in traces
    # ss.fig.add_trace(
    # go.Isosurface(
    # x=x,
    # y=y,
    # z=z,
    # value=values,
    # surface_count=3,
    # isomin=isomin,
    # opacity=0.25,
    # showscale=False,
    # colorbar=None,
    # name="Fluence",
    # customdata=["Fluence"],
    # legendgroup="zones",
    # legendgrouptitle_text="Calculation Zones",
    # showlegend=True,
    # )
    # )
    # else:  # update if trace already exists
    # ss.fig.update_traces(
    # x=x,
    # y=y,
    # z=z,
    # value=values,
    # isomin=isomin,
    # selector=dict(name="Fluence"),
    # )

    # else:  # remove if there are no values here
    # if "Fluence" in traces:
    # del traces[traces.index("Fluence")]

    st.plotly_chart(ss.fig, use_container_width=True, height=750)


def plot_species(df, fluence):
    """violin (kde) and swarmplots showing eACH and CADR for variety of species that have had k measured at 222nm in aerosol"""
    # Plot configuration
    fig, ax1 = plt.subplots(figsize=(8, 5))
    sns.violinplot(
        data=df,
        x="Species",
        y="eACH-UV",
        hue="Kingdom",
        hue_order=["Bacteria", "Virus"],
        inner=None,
        ax=ax1,
        alpha=0.5,
        legend=False,
    )
    sns.swarmplot(
        data=df,
        x="Species",
        y="eACH-UV",
        hue="Kingdom",
        hue_order=["Bacteria", "Virus"],
        ax=ax1,
        size=8,
        alpha=0.9,
    )
    ax1.set_ylabel("eACH-UV")
    ax1.set_xlabel(None)
    # ax1.tick_params(axis='y', labelcolor='b')
    ax1.set_ylim(bottom=0)
    ax1.grid("--")
    ax1.set_xticks(ax1.get_xticks())
    ax1.set_xticklabels(
        ax1.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
    )

    # add a second axis to show CADR
    ax2 = ax1.twinx()
    sns.violinplot(
        data=df,
        x="Species",
        y="CADR-UV [cfm]",
        ax=ax2,
        alpha=0,
        legend=False,
        inner=None,
    )
    ax2.set_ylabel("CADR-UV [cfm]")
    ax2.set_ylim(bottom=0)
    title = f"eACH/CADR from GUV-222 with average fluence {round(fluence,3)} uW/cm2"
    fig.suptitle(title)
    return fig
