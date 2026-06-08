from operator import attrgetter
from typing import Dict, List, Optional, Tuple

from aipaas.logger_factory import logger
from dto.esd_schedule_data import (
    DeliveryCapacity,
    ESDScheduleInput,
    ESDScheduleOutput,
    Group,
)


class ESDScheduler:
    def __init__(self, esdata: ESDScheduleInput) -> None:
        self.esdata: ESDScheduleInput = esdata
        self.max_slot: int = len(self.esdata.delivery_capacities) - 1

    def schedule(self) -> ESDScheduleOutput:
        """
        依次为每个 group 分配连续的发货产能时间片。
        """
        groups: List[Group] = sorted(
            self.esdata.groups,
            key=attrgetter("target_finish_time", "priority", "create_time"),
        )

        availability: List[int] = [
            capacity.dock_num for capacity in self.esdata.delivery_capacities
        ]
        output: ESDScheduleOutput = ESDScheduleOutput()

        for group in groups:
            allocated = self._allocate_group(group, availability)
            if allocated is None:
                finish_time, usage = None, {}
            else:
                finish_time, usage = allocated
            output.esd_result[group.group_id] = finish_time
            output.capacity_usage[group.group_id] = usage

        return output

    def _allocate_group(
        self, group: Group, availability: List[int]
    ) -> Optional[Tuple[int, Dict[int, DeliveryCapacity]]]:
        """为单个 group 选择可行的结束时间并分配产能。"""
        for finish_time in self._candidate_finish_times(group):
            allocation = self._try_allocate_window(group, availability, finish_time)
            if allocation is not None:
                return max(allocation), allocation

        logger.warning(
            "ESD 调度失败：group=%s, target_finish_time=%s, earliest_load_time=%s, "
            "vol=%s, pc=%s，原因：可用总产能不足或无法找到满足垛口限制的连续时间窗。",
            group.group_id,
            group.target_finish_time,
            group.earliest_load_time,
            group.vol,
            group.pc,
        )
        return None

    def _candidate_finish_times(self, group: Group) -> List[int]:
        max_slot: int = self.max_slot
        preferred = list(
            range(
                min(group.target_finish_time, max_slot),
                group.earliest_load_time - 1,
                -1,
            )
        )
        preferred.extend(
            range(min(group.target_finish_time + 1, max_slot), max_slot + 1)
        )
        return preferred

    def _try_allocate_window(
        self, group: Group, availability: List[int], finish_time: int
    ) -> Optional[Dict[int, DeliveryCapacity]]:
        """尝试为候选结束时间分配连续时间窗；失败则返回 None。"""
        start_time = self._find_earliest_start(group, availability, finish_time)
        if start_time is None:
            return None

        usage = self._commit_window(group, availability, start_time, finish_time)
        if usage is None:
            return None

        return usage

    def _find_earliest_start(
        self, group: Group, availability: List[int], finish_time: int
    ) -> Optional[int]:
        capacities: List[DeliveryCapacity] = self.esdata.delivery_capacities
        start_time: int = finish_time
        total_vol: float = 0.0
        total_pc: float = 0.0

        while start_time >= group.earliest_load_time:
            if availability[start_time] <= 0:
                start_time -= 1
                continue

            slot_capacity: DeliveryCapacity = capacities[start_time]
            total_vol += slot_capacity.vol_per_dock
            total_pc += slot_capacity.pc_per_dock
            if total_vol >= group.vol and total_pc >= group.pc:
                return start_time
            start_time -= 1

        return None

    def _commit_window(
        self,
        group: Group,
        availability: List[int],
        start_time: int,
        finish_time: int,
    ) -> Optional[Dict[int, DeliveryCapacity]]:
        capacities: List[DeliveryCapacity] = self.esdata.delivery_capacities
        usage: Dict[int, DeliveryCapacity] = {}
        remaining_vol: float = group.vol
        remaining_pc: float = group.pc

        for slot in range(start_time, finish_time + 1):
            if availability[slot] <= 0:
                continue

            slot_capacity: DeliveryCapacity = capacities[slot]
            used_vol: float = min(slot_capacity.vol_per_dock, remaining_vol)
            used_pc: float = min(slot_capacity.pc_per_dock, remaining_pc)
            if used_vol <= 0 and used_pc <= 0:
                continue

            availability[slot] -= 1
            remaining_vol -= used_vol
            remaining_pc -= used_pc
            usage[slot] = DeliveryCapacity(
                vol_per_dock=used_vol, pc_per_dock=used_pc, dock_num=1
            )

        if remaining_vol > 0 or remaining_pc > 0:
            for slot in usage:
                availability[slot] += 1
            return None

        return usage
