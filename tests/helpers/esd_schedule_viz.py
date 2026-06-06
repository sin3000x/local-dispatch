from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.dto.esd_schedule_data import ESDScheduleInput, ESDScheduleOutput


def _collect_time_slots(
    schedule_input: ESDScheduleInput, schedule_output: ESDScheduleOutput
) -> List[int]:
    slots = set(range(len(schedule_input.delivery_capacities)))
    for finish_time in schedule_output.groups.values():
        slots.add(finish_time)
    for usage in schedule_output.capacity_usage.values():
        slots.update(usage.keys())
    return sorted(slots)


def _sum_group_usage(
    schedule_output: ESDScheduleOutput,
) -> Tuple[Dict[int, float], Dict[int, float], Dict[str, Dict[int, float]], Dict[str, Dict[int, float]]]:
    vol_by_slot: Dict[int, float] = defaultdict(float)
    pc_by_slot: Dict[int, float] = defaultdict(float)
    group_vol: Dict[str, Dict[int, float]] = defaultdict(dict)
    group_pc: Dict[str, Dict[int, float]] = defaultdict(dict)

    for group_id, usage in schedule_output.capacity_usage.items():
        for slot, capacity in usage.items():
            vol_by_slot[slot] += capacity.vol_per_dock
            pc_by_slot[slot] += capacity.pc_per_dock
            group_vol[group_id][slot] = group_vol[group_id].get(slot, 0.0) + capacity.vol_per_dock
            group_pc[group_id][slot] = group_pc[group_id].get(slot, 0.0) + capacity.pc_per_dock

    return vol_by_slot, pc_by_slot, group_vol, group_pc


def _expand_group_dock_cells(
    schedule_output: ESDScheduleOutput,
) -> Dict[int, List[Tuple[str, int]]]:
    """Expand group usage into dock-sized visual cells per time slot."""

    dock_cells: Dict[int, List[Tuple[str, int]]] = defaultdict(list)
    for group_id, usage in schedule_output.capacity_usage.items():
        for slot, capacity in usage.items():
            dock_cells[slot].extend((group_id, dock_idx) for dock_idx in range(capacity.dock_num))
    return dock_cells


def _format_slot_time(slot: int, time_unit_in_minutes: int) -> str:
    total_minutes = slot * time_unit_in_minutes
    day = total_minutes // (24 * 60)
    minute_of_day = total_minutes % (24 * 60)
    hour = minute_of_day // 60
    minute = minute_of_day % 60
    day_prefix = f"第 {day + 1} 天 " if day else ""
    return f"{day_prefix}{hour:02d}:{minute:02d}"


def _group_lookup(schedule_input: ESDScheduleInput):
    return {group.group_id: group for group in schedule_input.groups}


def plot_esd_schedule(
    schedule_input: ESDScheduleInput,
    schedule_output: ESDScheduleOutput,
    *,
    show: bool = True,
    output_html: Optional[str] = None,
):
    """Build an interactive Plotly schedule chart.

    Hover a dock cell to inspect group details, target time, actual finish time,
    consumed capacity, and raw slot capacity. When ``output_html`` is provided,
    the figure is also written to that HTML file.
    """

    slots = _collect_time_slots(schedule_input, schedule_output)
    capacities = {i: c for i, c in enumerate(schedule_input.delivery_capacities)}
    group_ids = list(schedule_output.capacity_usage.keys())
    groups = _group_lookup(schedule_input)
    dock_cells = _expand_group_dock_cells(schedule_output)
    palette = [
        "#2563EB",
        "#DC2626",
        "#16A34A",
        "#9333EA",
        "#EA580C",
        "#0891B2",
        "#BE123C",
        "#4F46E5",
        "#65A30D",
        "#C026D3",
    ]
    group_colors = {group_id: palette[idx % len(palette)] for idx, group_id in enumerate(group_ids)}
    max_docks = max(
        [c.dock_num for c in schedule_input.delivery_capacities]
        + [len(v) for v in dock_cells.values()]
        + [1]
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("体积产能占用", "件数产能占用"),
    )

    metrics = [
        (1, "体积", "vol_per_dock", "vol"),
        (2, "件数", "pc_per_dock", "pc"),
    ]

    for row, metric_name, capacity_attr, group_attr in metrics:
        # Raw capacity cells.
        raw_x = []
        raw_y = []
        raw_text = []
        raw_customdata = []
        for slot in slots:
            capacity = capacities.get(slot)
            dock_num = capacity.dock_num if capacity else 0
            for dock_idx in range(dock_num):
                raw_x.append(slot)
                raw_y.append(dock_idx + 1)
                raw_text.append("")
                raw_customdata.append(
                    [
                        slot,
                        _format_slot_time(slot, schedule_input.time_unit_in_minutes),
                        dock_idx + 1,
                        dock_num,
                        getattr(capacity, capacity_attr) if capacity else 0,
                        getattr(capacity, capacity_attr) * dock_num if capacity else 0,
                    ]
                )

        fig.add_trace(
            go.Scatter(
                x=raw_x,
                y=raw_y,
                mode="markers+text",
                text=raw_text,
                marker={
                    "symbol": "square",
                    "size": 46,
                    "color": "#E5E7EB",
                    "line": {"color": "#9CA3AF", "width": 1},
                },
                name="原始产能",
                legendgroup="raw-capacity",
                showlegend=row == 1,
                customdata=raw_customdata,
                hovertemplate=(
                    "<b>原始产能</b><br>"
                    "时间节点: %{customdata[0]}<br>"
                    "开始时间: %{customdata[1]}<br>"
                    "垛口: %{customdata[2]} / %{customdata[3]}<br>"
                    f"单垛口{metric_name}: %{{customdata[4]}}<br>"
                    f"总{metric_name}: %{{customdata[5]}}<extra></extra>"
                ),
            ),
            row=row,
            col=1,
        )

        for group_id in group_ids:
            x = []
            y = []
            text = []
            customdata = []
            group = groups.get(group_id)
            usage = schedule_output.capacity_usage.get(group_id, {})
            for slot in slots:
                capacity = usage.get(slot)
                if not capacity:
                    continue

                slot_cells = dock_cells.get(slot, [])
                cell_indexes = [idx for idx, (cell_group_id, _) in enumerate(slot_cells) if cell_group_id == group_id]
                for visual_idx in cell_indexes:
                    capacity_per_dock = getattr(capacity, capacity_attr)
                    x.append(slot)
                    y.append(visual_idx + 1)
                    text.append(group_id)
                    customdata.append(
                        [
                            group_id,
                            slot,
                            _format_slot_time(slot, schedule_input.time_unit_in_minutes),
                            visual_idx + 1,
                            schedule_output.groups.get(group_id),
                            _format_slot_time(
                                schedule_output.groups.get(group_id, slot),
                                schedule_input.time_unit_in_minutes,
                            ),
                            group.earliest_load_time if group else None,
                            group.target_finish_time if group else None,
                            group.priority if group else None,
                            group.create_time if group else None,
                            getattr(group, group_attr) if group else None,
                            capacity_per_dock,
                            capacity.dock_num,
                        ]
                    )

            if not x:
                continue

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="markers+text",
                    text=text,
                    textfont={"color": "white", "size": 11},
                    marker={
                        "symbol": "square",
                        "size": 46,
                        "color": group_colors[group_id],
                        "line": {"color": "white", "width": 1},
                    },
                    name=group_id,
                    legendgroup=group_id,
                    showlegend=row == 1,
                    customdata=customdata,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "时间节点: %{customdata[1]}<br>"
                        "开始时间: %{customdata[2]}<br>"
                        "垛口: %{customdata[3]}<br>"
                        "完成节点: %{customdata[4]}<br>"
                        "完成时间: %{customdata[5]}<br>"
                        "最早装车节点: %{customdata[6]}<br>"
                        "目标完成节点: %{customdata[7]}<br>"
                        "优先级: %{customdata[8]}<br>"
                        "创建时间: %{customdata[9]}<br>"
                        f"Group总{metric_name}: %{{customdata[10]}}<br>"
                        f"本垛口占用{metric_name}: %{{customdata[11]}}<br>"
                        "占用垛口数: %{customdata[12]}<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )

    fig.update_layout(
        title="ESD 排产交互式产能占用图",
        height=max(720, max_docks * 74 + 260),
        width=max(1000, len(slots) * 105),
        hovermode="closest",
        plot_bgcolor="white",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.04, "xanchor": "center", "x": 0.5},
        margin={"l": 70, "r": 40, "t": 120, "b": 70},
    )
    fig.update_xaxes(
        title_text="时间节点",
        tickmode="array",
        tickvals=slots,
        ticktext=[f"{slot}<br>{_format_slot_time(slot, schedule_input.time_unit_in_minutes)}" for slot in slots],
        showgrid=True,
        gridcolor="#EEF2F7",
    )
    fig.update_yaxes(
        title_text="垛口",
        tickmode="array",
        tickvals=list(range(1, max_docks + 1)),
        ticktext=[f"垛口 {idx}" for idx in range(1, max_docks + 1)],
        range=[0.5, max_docks + 0.5],
        autorange="reversed",
        showgrid=True,
        gridcolor="#EEF2F7",
    )

    if output_html:
        Path(output_html).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_html, include_plotlyjs="cdn", auto_open=show)
    elif show:
        fig.show()

    return fig
