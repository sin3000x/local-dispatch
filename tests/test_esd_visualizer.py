from tests.test_esd_scheduler import build_input
from src.dto.esd_schedule_data import Group, DeliveryCapacity  # pyright: ignore[reportMissingImports]
from tests.helpers.esd_schedule_viz import plot_esd_schedule
from src.algo.esd_schedule import ESDScheduler  # pyright: ignore[reportMissingImports]


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

    fig = plot_esd_schedule(es_input, output, show=show_plot)

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
