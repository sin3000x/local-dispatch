from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import plotly.graph_objects as go

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


def _format_slot_range(slot: int, time_unit_in_minutes: int) -> str:
    start_total_minutes = slot * time_unit_in_minutes
    end_total_minutes = start_total_minutes + time_unit_in_minutes

    start_minute_of_day = start_total_minutes % (24 * 60)
    end_minute_of_day = end_total_minutes % (24 * 60)

    start_hour = start_minute_of_day // 60
    start_minute = start_minute_of_day % 60
    end_hour = end_minute_of_day // 60
    end_minute = end_minute_of_day % 60

    return f"{start_hour:02d}:{start_minute:02d}~{end_hour:02d}:{end_minute:02d}"


def _group_lookup(schedule_input: ESDScheduleInput):
    return {group.group_id: group for group in schedule_input.groups}


def _slot_dock_assignments(schedule_output: ESDScheduleOutput) -> Dict[int, List[Tuple[str, int, int]]]:
    assignments: Dict[int, List[Tuple[str, int, int]]] = defaultdict(list)
    for group_id, usage in schedule_output.capacity_usage.items():
        for slot, capacity in usage.items():
            for dock_idx in range(capacity.dock_num):
                assignments[slot].append((group_id, dock_idx, capacity.dock_num))
    return assignments


def plot_esd_schedule(
    schedule_input: ESDScheduleInput,
    schedule_output: ESDScheduleOutput,
    *,
    show: bool = True,
    output_html: Optional[str] = None,
):
    """Build an interactive Plotly schedule chart.

    Each dock cell is split into two halves: the upper half shows volume usage
    and the lower half shows piece-count usage.
    """

    slots = _collect_time_slots(schedule_input, schedule_output)
    groups = _group_lookup(schedule_input)
    assignments = _slot_dock_assignments(schedule_output)
    max_docks = max([c.dock_num for c in schedule_input.delivery_capacities] + [1])
    palette = ["#2563EB", "#DC2626", "#16A34A", "#9333EA", "#EA580C", "#0891B2", "#BE123C", "#4F46E5"]
    group_ids = list(schedule_output.capacity_usage.keys())
    group_colors = {group_id: palette[idx % len(palette)] for idx, group_id in enumerate(group_ids)}

    fig = go.Figure()

    for slot in slots:
        capacity = schedule_input.delivery_capacities[slot] if slot < len(schedule_input.delivery_capacities) else None
        dock_num = capacity.dock_num if capacity else max_docks
        slot_label = _format_slot_range(slot, schedule_input.time_unit_in_minutes)
        for dock in range(1, max_docks + 1):
            left, right = slot - 0.45, slot + 0.45
            bottom, top = dock - 0.4, dock + 0.4
            mid = dock
            fig.add_shape(
                type="rect",
                x0=left,
                x1=right,
                y0=bottom,
                y1=top,
                line={"color": "#CBD5E1", "width": 1},
                fillcolor="#F8FAFC",
                layer="below",
            )
            fig.add_shape(
                type="line",
                x0=left,
                x1=right,
                y0=mid,
                y1=mid,
                line={"color": "#CBD5E1", "width": 1},
                layer="below",
            )
            if dock > dock_num:
                fig.add_shape(
                    type="rect",
                    x0=left,
                    x1=right,
                    y0=bottom,
                    y1=top,
                    line={"color": "#E2E8F0", "width": 1},
                    fillcolor="#EFF6FF",
                    layer="below",
                    opacity=0.35,
                )
                continue

            cells = [cell for cell in assignments.get(slot, []) if cell[1] == dock - 1]
            if not cells:
                continue

            group_id, _, _ = cells[0]
            group = groups.get(group_id)
            usage = schedule_output.capacity_usage[group_id][slot]
            volume_ratio = min(1.0, usage.vol_per_dock / capacity.vol_per_dock) if capacity and capacity.vol_per_dock else 0.0
            pc_ratio = min(1.0, usage.pc_per_dock / capacity.pc_per_dock) if capacity and capacity.pc_per_dock else 0.0
            color = group_colors[group_id]

            fig.add_shape(
                type="rect",
                x0=left,
                x1=right,
                y0=mid,
                y1=top,
                line={"color": color, "width": 1},
                fillcolor=color,
                layer="above",
                opacity=max(0.25, 0.25 + 0.65 * volume_ratio),
            )
            fig.add_shape(
                type="rect",
                x0=left,
                x1=right,
                y0=bottom,
                y1=mid,
                line={"color": color, "width": 1},
                fillcolor=color,
                layer="above",
                opacity=max(0.25, 0.25 + 0.65 * pc_ratio),
            )

            fig.add_annotation(
                x=slot,
                y=dock + 0.22,
                text=f"{group_id}<br>vol {usage.vol_per_dock}",
                showarrow=False,
                font={"color": "white", "size": 10},
            )
            fig.add_annotation(
                x=slot,
                y=dock - 0.22,
                text=f"{group_id}<br>pc {usage.pc_per_dock}",
                showarrow=False,
                font={"color": "white", "size": 10},
            )

            fig.add_trace(
                go.Scatter(
                    x=[slot],
                    y=[dock],
                    mode="markers",
                    marker={"size": 46, "color": "rgba(0,0,0,0)"},
                    hovertemplate=(
                        f"<b>{group_id}</b><br>"
                        f"时间段: {slot_label}<br>"
                        f"垛口: {dock}<br>"
                        f"vol_per_dock: {usage.vol_per_dock}<br>"
                        f"pc_per_dock: {usage.pc_per_dock}<br>"
                        f"目标完成时间: {schedule_output.groups.get(group_id)}<br>"
                        f"earliest_load_time: {group.earliest_load_time if group else None}<br>"
                        f"target_finish_time: {group.target_finish_time if group else None}<br>"
                        f"priority: {group.priority if group else None}<br>"
                        f"create_time: {group.create_time if group else None}<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

    fig.update_layout(
        title="ESD 排产交互式产能占用图",
        height=max(700, max_docks * 90 + 220),
        width=max(1000, len(slots) * 110),
        plot_bgcolor="white",
        hovermode="closest",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.04, "xanchor": "center", "x": 0.5},
        margin={"l": 70, "r": 40, "t": 100, "b": 70},
    )
    fig.update_xaxes(
        title_text="时间段",
        tickmode="array",
        tickvals=slots,
        ticktext=[_format_slot_range(slot, schedule_input.time_unit_in_minutes) for slot in slots],
        showgrid=True,
        gridcolor="#EEF2F7",
        range=[min(slots) - 0.5, max(slots) + 0.5],
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
