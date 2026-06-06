from src.algo.esd_schedule import ESDScheduler
from src.dto.esd_schedule_data import DeliveryCapacity, ESDScheduleInput, ESDScheduleOutput, Group
from tests.helpers.esd_schedule_fixtures import build_sample_schedule_input
from tests.helpers.esd_schedule_viz import plot_esd_schedule


def build_input(groups, capacities, time_unit_in_minutes=30):
    return ESDScheduleInput(
        time_unit_in_minutes=time_unit_in_minutes,
        groups=groups,
        delivery_capacities=capacities,
    )


def test_schedule_sorts_by_target_priority_and_create_time():
    groups = [
        Group(
            group_id="g-3",
            earliest_load_time=0,
            target_finish_time=3,
            vol=2,
            pc=2,
            priority=2,
            create_time=2,
        ),
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=1,
            vol=2,
            pc=2,
            priority=2,
            create_time=1,
        ),
        Group(
            group_id="g-2",
            earliest_load_time=0,
            target_finish_time=1,
            vol=2,
            pc=2,
            priority=1,
            create_time=2,
        ),
    ]
    capacities = [
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=1),
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=1),
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=1),
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=1),
    ]

    output = ESDScheduler(build_input(groups, capacities)).schedule()

    assert list(output.groups.keys()) == ["g-2", "g-1", "g-3"]


def test_schedule_prefers_target_time_when_feasible():
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=1,
            vol=8,
            pc=8,
            priority=1,
            create_time=0,
        )
    ]
    capacities = [
        DeliveryCapacity(vol_per_dock=5, pc_per_dock=5, dock_num=1),
        DeliveryCapacity(vol_per_dock=5, pc_per_dock=5, dock_num=1),
        DeliveryCapacity(vol_per_dock=5, pc_per_dock=5, dock_num=1),
    ]

    output = ESDScheduler(build_input(groups, capacities)).schedule()

    assert output.groups["g-1"] == 1
    assert set(output.capacity_usage["g-1"].keys()) == {0, 1}


def test_schedule_prefers_earlier_when_target_is_not_feasible():
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=2,
            vol=10,
            pc=10,
            priority=1,
            create_time=0,
        )
    ]
    capacities = [
        DeliveryCapacity(vol_per_dock=4, pc_per_dock=4, dock_num=1),
        DeliveryCapacity(vol_per_dock=4, pc_per_dock=4, dock_num=1),
        DeliveryCapacity(vol_per_dock=4, pc_per_dock=4, dock_num=1),
        DeliveryCapacity(vol_per_dock=4, pc_per_dock=4, dock_num=1),
    ]

    output = ESDScheduler(build_input(groups, capacities)).schedule()

    assert output.groups["g-1"] == 2
    assert set(output.capacity_usage["g-1"].keys()) == {0, 1, 2}


def test_schedule_respects_dock_capacity_for_same_slot():
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=0,
            vol=6,
            pc=6,
            priority=1,
            create_time=0,
        ),
        Group(
            group_id="g-2",
            earliest_load_time=0,
            target_finish_time=0,
            vol=6,
            pc=6,
            priority=1,
            create_time=1,
        ),
        Group(
            group_id="g-3",
            earliest_load_time=0,
            target_finish_time=0,
            vol=6,
            pc=6,
            priority=1,
            create_time=2,
        ),
    ]
    capacities = [
        DeliveryCapacity(vol_per_dock=6, pc_per_dock=6, dock_num=2),
        DeliveryCapacity(vol_per_dock=6, pc_per_dock=6, dock_num=2),
    ]

    output = ESDScheduler(build_input(groups, capacities)).schedule()

    # 第 0 个时间片最多只能安排 2 个 group，第三个 group 只能顺延到第 1 个时间片。
    assert output.groups == {"g-1": 0, "g-2": 0, "g-3": 1}
    assert output.capacity_usage["g-1"][0].dock_num == 1
    assert output.capacity_usage["g-2"][0].dock_num == 1
    assert output.capacity_usage["g-3"][1].dock_num == 1


def test_visualization_uses_length_for_usage_and_separates_groups_in_same_slot():
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=0,
            vol=3,
            pc=2,
            priority=1,
            create_time=0,
        ),
        Group(
            group_id="g-2",
            earliest_load_time=0,
            target_finish_time=0,
            vol=2,
            pc=3,
            priority=1,
            create_time=1,
        ),
    ]
    capacities = [DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=2)]

    output = ESDScheduler(build_input(groups, capacities)).schedule()
    fig = plot_esd_schedule(build_input(groups, capacities), output, show=False)

    assert output.groups == {"g-1": 0, "g-2": 0}
    assert len(fig.layout.shapes) >= 6

    first_top_bar = fig.layout.shapes[2]
    first_bottom_bar = fig.layout.shapes[3]
    second_top_bar = fig.layout.shapes[4]
    second_bottom_bar = fig.layout.shapes[5]

    assert first_top_bar["x1"] == second_top_bar["x0"]
    assert first_bottom_bar["x1"] == second_bottom_bar["x0"]
    assert first_top_bar.opacity is None
    assert first_bottom_bar.opacity is None


def test_visualization_non_overlapping_segments_with_multiple_groups_in_same_time_slot():
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=0,
            vol=2,
            pc=2,
            priority=1,
            create_time=0,
        ),
        Group(
            group_id="g-2",
            earliest_load_time=0,
            target_finish_time=0,
            vol=2,
            pc=2,
            priority=1,
            create_time=1,
        ),
        Group(
            group_id="g-3",
            earliest_load_time=0,
            target_finish_time=0,
            vol=2,
            pc=2,
            priority=1,
            create_time=2,
        ),
    ]
    capacities = [DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=3)]

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    fig = plot_esd_schedule(build_input(groups, capacities), output, show=False)

    assert output.groups == {"g-1": 0, "g-2": 0, "g-3": 0}

    # 第 0 个时间片的 3 个 group 会紧密排在同一个垛口里，不重叠也不留空隙。
    bar_shapes = [shape for shape in fig.layout.shapes if shape["type"] == "rect" and shape["layer"] == "above"]
    assert len(bar_shapes) == 6

    top_bars = bar_shapes[::2]
    bottom_bars = bar_shapes[1::2]

    assert top_bars[0]["x1"] == top_bars[1]["x0"]
    assert top_bars[1]["x1"] == top_bars[2]["x0"]
    assert bottom_bars[0]["x1"] == bottom_bars[1]["x0"]
    assert bottom_bars[1]["x1"] == bottom_bars[2]["x0"]

    plot_esd_schedule(es_input, output, show=True)


def test_visualization_background_hover_shows_slot_total_capacity():
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=0,
            vol=2,
            pc=2,
            priority=1,
            create_time=0,
        )
    ]
    capacities = [DeliveryCapacity(vol_per_dock=12, pc_per_dock=34, dock_num=1)]

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    fig = plot_esd_schedule(es_input, output, show=False)

    background_hover_traces = [trace for trace in fig.data if trace.hovertemplate and "总产能 vol" in trace.hovertemplate]
    assert background_hover_traces
    assert "总产能 vol: 12" in background_hover_traces[0].hovertemplate
    assert "总产能 pc: 34" in background_hover_traces[0].hovertemplate


def test_visualization_background_hover_exists_for_unused_dock_area():
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=0,
            vol=2,
            pc=2,
            priority=1,
            create_time=0,
        )
    ]
    capacities = [
        DeliveryCapacity(vol_per_dock=12, pc_per_dock=34, dock_num=1),
        DeliveryCapacity(vol_per_dock=12, pc_per_dock=34, dock_num=2),
    ]

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    fig = plot_esd_schedule(es_input, output, show=False)

    unavailable_hover_traces = [trace for trace in fig.data if trace.hovertemplate and "该时刻该垛口不可用" in trace.hovertemplate]
    assert unavailable_hover_traces
