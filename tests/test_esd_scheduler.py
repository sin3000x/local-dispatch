from src.algo.esd_schedule import ESDScheduler
from src.dto.esd_schedule_data import DeliveryCapacity, ESDScheduleInput, Group
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


def test_schedule_can_show_visualization_when_run_standalone(request):
    schedule_input = build_sample_schedule_input()
    output = ESDScheduler(schedule_input).schedule()
    assert output is not None

    # 当 pytest 只收集到当前这一个测试时，认为是在单独运行可视化测试，自动打开交互图。
    # 跑完整测试套件时不会弹窗，避免阻塞 CI 或日常测试。
    show_plot = len(request.session.items) == 1
    plot_esd_schedule(schedule_input, output, show=show_plot)
