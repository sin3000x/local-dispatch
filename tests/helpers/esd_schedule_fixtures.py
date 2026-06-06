from typing import List

from src.dto.esd_schedule_data import DeliveryCapacity, ESDScheduleInput, Group  # pyright: ignore[reportMissingImports]


def build_sample_groups() -> List[Group]:
    return [
        Group(
            group_id="group-1",
            earliest_load_time=0,
            target_finish_time=2,
            vol=12.5,
            pc=8,
            priority=1,
            create_time=0,
        ),
        Group(
            group_id="group-2",
            earliest_load_time=1,
            target_finish_time=4,
            vol=9.0,
            pc=6,
            priority=2,
            create_time=1,
        ),
        Group(
            group_id="group-3",
            earliest_load_time=2,
            target_finish_time=5,
            vol=15.0,
            pc=10,
            priority=1,
            create_time=2,
        ),
    ]


def build_sample_delivery_capacities() -> List[DeliveryCapacity]:
    return [
        DeliveryCapacity(vol_per_dock=10.0, pc_per_dock=5, dock_num=2),
        DeliveryCapacity(vol_per_dock=10.0, pc_per_dock=5, dock_num=2),
        DeliveryCapacity(vol_per_dock=12.0, pc_per_dock=6, dock_num=1),
        DeliveryCapacity(vol_per_dock=12.0, pc_per_dock=6, dock_num=1),
        DeliveryCapacity(vol_per_dock=8.0, pc_per_dock=5, dock_num=3),
        DeliveryCapacity(vol_per_dock=8.0, pc_per_dock=5, dock_num=3),
    ]


def build_sample_schedule_input() -> ESDScheduleInput:
    return ESDScheduleInput(
        time_unit_in_minutes=30,
        groups=build_sample_groups(),
        delivery_capacities=build_sample_delivery_capacities(),
    )
