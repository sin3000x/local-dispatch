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
            key=lambda group: (
                group.target_finish_time,
                group.priority,
                group.create_time,
            ),
        )

        # availability[i] 表示第 i 个时间片还剩余多少个垛口可用。
        # 每成功安排一个 group，就把它占用到的时间片垛口数减 1。
        availability: List[int] = [
            capacity.dock_num for capacity in self.esdata.delivery_capacities
        ]
        output: ESDScheduleOutput = ESDScheduleOutput()

        for group in groups:
            allocated = self._allocate_group(group, availability)
            if allocated is None:
                return None

            finish_time, usage = allocated
            output.groups[group.group_id] = finish_time
            output.capacity_usage[group.group_id] = usage

        return output

    def _allocate_group(
        self, group: Group, availability: List[int]
    ) -> Optional[Tuple[int, Dict[int, DeliveryCapacity]]]:
        """为单个 group 选择可行的结束时间并分配产能。

        :param group: 当前待分配的分组。
        :param availability: 各时间片剩余垛口数，会在成功分配后被原地修改。
        """
        max_slot: int = self.max_slot
        preferred_finishes: List[int] = list(
            range(
                min(group.target_finish_time, max_slot),
                group.earliest_load_time - 1,
                -1,
            )
        )
        preferred_finishes.extend(
            range(min(group.target_finish_time + 1, max_slot), max_slot + 1)
        )

        for finish_time in preferred_finishes:
            window = self._find_window(group, availability, finish_time)
            if window is not None:
                _, usage = window
                return finish_time, usage

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

    def _find_window(
        self, group: Group, availability: List[int], finish_time: int
    ) -> Optional[Tuple[int, Dict[int, DeliveryCapacity]]]:
        """检查某个候选结束时间是否可行，并完成对应时间窗的产能分配。
        从候选结束时间向前倒推，检查能否凑齐该 group 所需的体积和件数，并在可行时把对应时间片的垛口数扣减掉。

        :param group: 当前待分配的分组。
        :param availability: 各时间片剩余垛口数，会在确认分配时被原地修改。
        :param finish_time: 本次尝试的候选结束时间。
        :returns: 成功时返回 ``(最早占用开始时间, 时间片产能占用明细)``；若该结束时间不可行，则返回 ``None``。
        """
        capacities: List[DeliveryCapacity] = self.esdata.delivery_capacities
        start_time: int = finish_time
        total_vol: float = 0.0
        total_pc: float = 0.0

        # 先从结束时间开始向前倒推，直到累计到足够的体积和件数，
        # 或者已经早于最早可发时间。
        while start_time >= group.earliest_load_time:
            # 如果该时间片已经没有垛口可用，就跳过这一格继续往前找。
            if availability[start_time] <= 0:
                start_time -= 1
                continue

            slot_capacity: DeliveryCapacity = capacities[start_time]
            total_vol += slot_capacity.vol_per_dock
            total_pc += slot_capacity.pc_per_dock
            if total_vol >= group.vol and total_pc >= group.pc:
                break
            start_time -= 1

        # 倒推后依然不够，说明这个结束时间不可行。
        if total_vol < group.vol or total_pc < group.pc:
            return None

        # 真正分配时，按照时间顺序把每个时间片的产能扣给当前 group。
        # 注意：同一个时间片的垛口数不能超用，所以每占用一次就把 availability 减 1。
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
                vol_per_dock=used_vol,
                pc_per_dock=used_pc,
                dock_num=1,
            )

        # 理论上只要前面可行，这里不应再失败；但为了保险，如果出现残余量则回滚。
        if remaining_vol > 0 or remaining_pc > 0:
            for slot in usage:
                availability[slot] += 1
            return None

        # 返回的是“最后一个被占用的时刻”，也就是结束时间。
        return start_time, usage
