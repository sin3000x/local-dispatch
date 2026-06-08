import pytest

from src.algo.esd_schedule import ESDScheduler  # pyright: ignore[reportMissingImports]
from src.dto.esd_schedule_data import DeliveryCapacity, ESDScheduleInput, Group  # pyright: ignore[reportMissingImports]
from tests.helpers.esd_schedule_viz import plot_esd_schedule


def build_input(groups, capacities, time_unit_in_minutes=30):
    return ESDScheduleInput(
        time_unit_in_minutes=time_unit_in_minutes,
        groups=groups,
        delivery_capacities=capacities,
    )

def test_infeasible(show_plot):
    groups = [
        Group(
            group_id="g-3",
            earliest_load_time=0,
            target_finish_time=3,
            vol=500,
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

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    output.pprint()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert output.esd_result == {"g-2": 1, "g-1": 0, "g-3": None}

def test_case_1_two_docks(show_plot):
    groups = [
        Group(
            group_id="g-3",
            earliest_load_time=0,
            target_finish_time=3,
            vol=5,
            pc=2,
            priority=2,
            create_time=2,
        ),
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=1,
            vol=12,
            pc=2,
            priority=2,
            create_time=1,
        ),
        Group(
            group_id="g-2",
            earliest_load_time=0,
            target_finish_time=1,
            vol=12,
            pc=2,
            priority=1,
            create_time=2,
        ),
    ]
    capacities = [
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=2)
        for _ in range(4)
    ]

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    output.pprint()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert list(output.esd_result.keys()) == ["g-2", "g-1", "g-3"]
    assert output.esd_result == {"g-2": 1, "g-1": 1, "g-3": 3}


def test_case_1(show_plot):
    groups = [
        Group(
            group_id="g-3",
            earliest_load_time=0,
            target_finish_time=3,
            vol=5,
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

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    output.pprint()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert list(output.esd_result.keys()) == ["g-2", "g-1", "g-3"]
    assert output.esd_result == {"g-2": 1, "g-1": 0, "g-3": 3}


def test_case_1_minutely(show_plot):
    groups = [
        Group(
            group_id="g-3",
            earliest_load_time=0,
            target_finish_time=90,
            vol=5,
            pc=2,
            priority=2,
            create_time=2,
        ),
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=30,
            vol=2,
            pc=2,
            priority=2,
            create_time=1,
        ),
        Group(
            group_id="g-2",
            earliest_load_time=0,
            target_finish_time=30,
            vol=2,
            pc=2,
            priority=1,
            create_time=2,
        ),
    ]
    capacities = [
        DeliveryCapacity(vol_per_dock=0.3, pc_per_dock=0.3, dock_num=1)
        for _ in range(90)
    ]

    es_input = build_input(groups, capacities, time_unit_in_minutes=1)
    output = ESDScheduler(es_input).schedule()
    output.pprint()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert list(output.esd_result.keys()) == ["g-2", "g-1", "g-3"]


def test_schedule_prefers_target_time_when_feasible(show_plot):
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

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert output.esd_result["g-1"] == 1
    assert set(output.capacity_usage["g-1"].keys()) == {0, 1}


def test_schedule_prefers_earlier_when_target_is_not_feasible(show_plot):
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

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert output.esd_result["g-1"] == 2
    assert set(output.capacity_usage["g-1"].keys()) == {0, 1, 2}


def test_schedule_respects_dock_capacity_for_same_slot(show_plot):
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

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()

    if show_plot:
        plot_esd_schedule(es_input, output)

    # 第 0 个时间片最多只能安排 2 个 group，第三个 group 只能顺延到第 1 个时间片。
    assert output.esd_result == {"g-1": 0, "g-2": 0, "g-3": 1}
    assert output.capacity_usage["g-1"][0].dock_num == 1
    assert output.capacity_usage["g-2"][0].dock_num == 1
    assert output.capacity_usage["g-3"][1].dock_num == 1


@pytest.fixture
def show_plot(request):
    return request.config.getoption("--plot")


def test_visualization_uses_length_for_usage_and_separates_groups_in_same_slot(
    show_plot,
):
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

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()

    if show_plot:
        plot_esd_schedule(es_input, output)

    fig = plot_esd_schedule(es_input, output)

    assert output.esd_result == {"g-1": 0, "g-2": 0}
    assert len(fig.layout.shapes) >= 6

    bar_shapes = [
        shape
        for shape in fig.layout.shapes
        if shape["type"] == "rect" and shape["layer"] == "above"
    ]
    assert len(bar_shapes) == 4

    top_bars = bar_shapes[::2]
    bottom_bars = bar_shapes[1::2]

    assert all(bar["x0"] < bar["x1"] for bar in top_bars)
    assert all(bar["x0"] < bar["x1"] for bar in bottom_bars)
    assert top_bars[0].opacity is None
    assert bottom_bars[0].opacity is None


def test_visualization_non_overlapping_segments_with_multiple_groups_in_same_time_slot(
    show_plot,
):
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
    fig = plot_esd_schedule(es_input, output, show=show_plot)

    assert output.esd_result == {"g-1": 0, "g-2": 0, "g-3": 0}

    # 第 0 个时间片的 3 个 group 会紧密排在同一个垛口里，不重叠也不留空隙。
    bar_shapes = [
        shape
        for shape in fig.layout.shapes
        if shape["type"] == "rect" and shape["layer"] == "above"
    ]
    assert len(bar_shapes) == 6

    top_bars = bar_shapes[::2]
    bottom_bars = bar_shapes[1::2]

    assert all(bar["x0"] < bar["x1"] for bar in top_bars)
    assert all(bar["x0"] < bar["x1"] for bar in bottom_bars)

    plot_esd_schedule(es_input, output, show=show_plot)


def test_visualization_background_hover_shows_slot_total_capacity(show_plot):
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
    fig = plot_esd_schedule(es_input, output, show=show_plot)

    background_annotations = [
        annotation
        for annotation in fig.layout.annotations
        if annotation.text and "vol" in annotation.text and "pc" in annotation.text
    ]
    assert background_annotations
    assert "vol" in background_annotations[0].text
    assert "pc" in background_annotations[0].text


def test_visualization_background_hover_exists_for_unused_dock_area(show_plot):
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
    fig = plot_esd_schedule(es_input, output, show=show_plot)

    unavailable_annotations = [
        annotation
        for annotation in fig.layout.annotations
        if annotation.text == "该时刻该垛口不可用"
    ]
    assert unavailable_annotations
