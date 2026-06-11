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


def test_two_docks(show_plot):
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
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=2) for _ in range(4)
    ]

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    output.pprint()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert list(output.esd_result.keys()) == ["g-2", "g-1", "g-3"]
    assert output.esd_result == {"g-2": 1, "g-1": 1, "g-3": 3}


def test_docknum_change(show_plot):
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
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=2),
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=1),
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=2),
        DeliveryCapacity(vol_per_dock=10, pc_per_dock=10, dock_num=2),
    ]

    es_input = build_input(groups, capacities)
    output = ESDScheduler(es_input).schedule()
    output.pprint()

    if show_plot:
        plot_esd_schedule(es_input, output)

    assert list(output.esd_result.keys()) == ["g-2", "g-1", "g-3"]
    assert output.esd_result == {"g-2": 1, "g-1": 2, "g-3": 3}

def test_zero_target_time(show_plot):
    groups = [
        Group(
            group_id="g-1",
            earliest_load_time=0,
            target_finish_time=0,
            vol=2,
            pc=20,
            priority=2,
            create_time=1,
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

    assert output.esd_result == {"g-1": 1}

def test_single_slot(show_plot):
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


def test_minutely(show_plot):
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


def test_empty():
    es_input = build_input([], [])
    output = ESDScheduler(es_input).schedule()
    output.pprint()

    assert output.esd_result == {}


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

