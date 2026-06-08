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
        # 保存本次调度所需的全部输入数据。
        # 包括 group 列表、每个时间片的产能配置等，后续所有调度计算都基于这份数据展开。
        self.esdata: ESDScheduleInput = esdata
        # 预先记录最后一个可用时间片的下标，避免后续频繁计算长度。
        # 该值主要用于生成候选结束时间时做边界控制，防止越界访问。
        self.max_slot: int = len(self.esdata.delivery_capacities) - 1

    def schedule(self) -> ESDScheduleOutput:
        """
        执行完整的 ESD 调度流程，并返回调度结果。

        调度原则：
        1. 先按目标完成时间、优先级、创建时间对任务排序，优先处理更紧急的 group；
        2. 依次为每个 group 寻找一个满足体积和件数要求的连续时间窗；
        3. 一旦某个时间窗被成功分配，对应时间片的剩余垛口数会立即扣减；
        4. 如果某个 group 无法找到可行时间窗，则在结果中标记为未分配。
        """
        groups: List[Group] = sorted(
            self.esdata.groups,
            key=attrgetter("target_finish_time", "priority", "create_time"),
        )

        # availability 表示每个时间片当前还剩多少个可用垛口。
        # 它与 delivery_capacities 一一对应：下标是时间片，值是该时间片剩余的 dock 数。
        # 调度过程中会持续修改它，因此它代表的是“全局剩余产能”，而不是单个 group 的局部视图。
        # fmt: off
        availability: List[int] = [
            capacity.dock_num
            for capacity in self.esdata.delivery_capacities
        ]
        # fmt: on
        output: ESDScheduleOutput = ESDScheduleOutput()

        for group in groups:
            # 逐个尝试为当前 group 分配时间窗。
            # 成功时记录实际完成时间以及该 group 在各时间片上的产能使用明细；失败时则记为空。
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
        """
        为单个 group 寻找一个可行的连续时间窗，并完成真正的资源分配。

        返回值含义：
        - 成功时返回 (实际结束时间, 各时间片使用明细)
        - 失败时返回 None

        这里采用“先尝试候选结束时间，再向前寻找开始时间”的策略：
        既尽量让任务贴近目标完成时间，又能在产能紧张时通过延后结束时间作为兜底。
        """
        # 候选结束时间按优先级从高到低尝试。
        # 越靠前的候选越接近目标完成时间，因此更符合“尽量按时完成”的业务期望。
        for finish_time in self._candidate_finish_times(group):
            allocation = self._try_allocate_window(group, availability, finish_time)
            if allocation is not None:
                # allocation 的键是时间片下标，最大的键就是本次分配得到的实际结束时间。
                return max(allocation), allocation

        # 所有候选结束时间都失败，说明当前剩余产能已无法满足该 group 的需求。
        # 这里记录日志，便于后续排查是需求过大、时间窗不足，还是产能被前序任务消耗过多。
        logger.warning(
            "ESD 调度失败：group=%s, target_finish_time=%s, earliest_load_time=%s, "
            "vol=%s, pc=%s，原因：可用产能不足或不存在满足垛口约束的连续时间窗。",
            group.group_id,
            group.target_finish_time,
            group.earliest_load_time,
            group.vol,
            group.pc,
        )
        return None

    def _candidate_finish_times(self, group: Group) -> List[int]:
        """
        生成当前 group 的候选结束时间列表。

        候选顺序分两部分：
        1. 先尝试从目标完成时间向前回退到最早装载时间，优先满足“按时完成”；
        2. 若前半段全部失败，再尝试目标完成时间之后的时间片，允许适度延期。

        这种排序方式可以在尽量贴近业务期望的同时，保留一定的延迟兜底能力。
        """
        max_slot: int = self.max_slot
        preferred = list(
            range(
                min(group.target_finish_time, max_slot),
                group.earliest_load_time - 1,
                -1,
            )
        )
        # 目标时间之后的时间片作为兜底候选，避免因为严格卡点而错失可行方案。
        preferred.extend(
            range(min(group.target_finish_time + 1, max_slot), max_slot + 1)
        )
        return preferred

    def _try_allocate_window(
        self, group: Group, availability: List[int], finish_time: int
    ) -> Optional[Dict[int, DeliveryCapacity]]:
        """
        针对某一个候选结束时间，尝试找到并提交一个完整的连续时间窗。

        流程如下：
        1. 从结束时间开始向前寻找最早可行的开始时间；
        2. 如果找到了开始时间，就将该时间窗正式写入结果并扣减产能；
        3. 任一步失败都返回 None，表示该候选结束时间不可用。
        """
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
        """
        从候选结束时间开始向前扫描，寻找最早可行的开始时间。

        这里判断的不是“整个区间是否都空闲”，而是：
        从结束时间往前累计每个时间片的单垛口产能，直到累计体积和累计件数同时满足 group 的需求。

        只要某个时间片还有剩余垛口，就可以把该时间片纳入当前窗口；
        如果某个时间片已经没有可用垛口，则跳过它继续向前找。
        """
        capacities: List[DeliveryCapacity] = self.esdata.delivery_capacities
        start_time: int = finish_time
        total_vol: float = 0.0
        total_pc: float = 0.0

        while start_time >= group.earliest_load_time:
            # 如果该时间片已经没有剩余垛口，则不能纳入窗口，只能继续向前寻找。
            if availability[start_time] <= 0:
                start_time -= 1
                continue

            slot_capacity: DeliveryCapacity = capacities[start_time]
            total_vol += slot_capacity.vol_per_dock
            total_pc += slot_capacity.pc_per_dock

            # 当累计产能同时覆盖体积和件数需求时，当前 start_time 就是最早可行开始时间。
            # 之所以称为“最早”，是因为我们是从后往前扫描，第一次满足条件的位置就是最靠前的可行起点。
            if total_vol >= group.vol and total_pc >= group.pc:
                return start_time

            start_time -= 1

        # 扫描到最早装载时间后仍未满足需求，说明该候选结束时间不可行。
        return None

    def _commit_window(
        self,
        group: Group,
        availability: List[int],
        start_time: int,
        finish_time: int,
    ) -> Optional[Dict[int, DeliveryCapacity]]:
        """
        将已经确认可行的时间窗写入调度结果，并扣减对应的可用垛口。

        `usage` 会记录每个时间片实际分配给该 group 的产能明细，便于：
        - 输出调度结果；
        - 回溯某个 group 的时间窗构成；
        - 排查为什么某段时间片被占用。

        如果在提交过程中发现仍然无法完全满足需求，则会回滚已经扣减的垛口，
        以免污染全局可用产能并影响后续 group 的调度。
        """
        capacities: List[DeliveryCapacity] = self.esdata.delivery_capacities
        usage: Dict[int, DeliveryCapacity] = {}
        remaining_vol: float = group.vol
        remaining_pc: float = group.pc

        for slot in range(start_time, finish_time + 1):
            # 若该时间片没有剩余垛口，则直接跳过。
            # 理论上前置搜索已经保证时间窗可行，这里主要是防御性处理，避免异常数据导致错误扣减。
            if availability[slot] <= 0:
                continue

            slot_capacity: DeliveryCapacity = capacities[slot]
            # 单个时间片最多只能贡献一个垛口的产能，因此这里按照剩余需求与单垛口能力取较小值。
            used_vol: float = min(slot_capacity.vol_per_dock, remaining_vol)
            used_pc: float = min(slot_capacity.pc_per_dock, remaining_pc)
            if used_vol <= 0 and used_pc <= 0:
                continue

            # 占用一个垛口，并同步减少 group 的剩余需求。
            availability[slot] -= 1
            remaining_vol -= used_vol
            remaining_pc -= used_pc
            usage[slot] = DeliveryCapacity(
                vol_per_dock=used_vol, pc_per_dock=used_pc, dock_num=1
            )

        # 如果仍然存在未覆盖的需求，说明该窗口在提交时并未真正满足业务约束。
        # 需要把前面已经占用的垛口恢复，确保全局可用产能保持一致。
        if remaining_vol > 0 or remaining_pc > 0:
            for slot in usage:
                availability[slot] += 1
            return None

        return usage
