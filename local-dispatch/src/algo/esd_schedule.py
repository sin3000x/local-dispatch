from typing import List

from dto.esd_schedule_data import DeliveryCapacity, ESDScheduleInput, ESDScheduleOutput


class ESDScheduler:
    def __init__(self, esd_schedule_data: ESDScheduleInput) -> None:
        self.esd_schedule_data = esd_schedule_data

    def schedule(self) -> ESDScheduleOutput:
        # 先对所有 group 做全局排序：目标发车时间越早越优先；
        # 目标时间相同则优先级更高（数值更小）者优先；
        # 仍相同则更早创建的 group 优先。
        groups = sorted(
            self.esd_schedule_data.groups,
            key=lambda group: (
                group.target_finish_time,
                group.priority,
                group.create_time,
            ),
        )

        # availability[i] 表示第 i 个时间片还剩余多少个垛口可用。
        # 后续每成功安排一个 group，就会把它占用到的时间片垛口数减 1。
        availability: List[int] = [
            capacity.dock_num for capacity in self.esd_schedule_data.delivery_capacities
        ]
        output = ESDScheduleOutput()

        for group in groups:
            finish_time, usage = self._allocate_group(group, availability)
            output.groups[group.group_id] = finish_time
            output.capacity_usage[group.group_id] = usage

        return output

    def _allocate_group(self, group, availability):
        # 允许的结束时间优先级如下：
        # 1. 尽量贴近目标时间，先尝试等于 target_finish_time；
        # 2. 如果做不到，优先尝试更早的结束时间；
        # 3. 最后才考虑更晚的结束时间。
        max_slot = len(self.esd_schedule_data.delivery_capacities) - 1
        preferred_finishes = list(
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
            start_time, usage = self._find_window(group, availability, finish_time)
            if usage:
                return finish_time, usage

        raise ValueError(f"Unable to schedule group {group.group_id}")

    def _find_window(self, group, availability, finish_time):
        capacities = self.esd_schedule_data.delivery_capacities
        start_time = finish_time
        total_vol = 0.0
        total_pc = 0.0

        # 先从结束时间开始，向前倒推可以使用的时间片，
        # 直到累计到足够的体积和件数，或者已经早于最早可发时间。
        while start_time >= group.earliest_load_time:
            # 如果该时间片已经没有垛口可用，就跳过这一格继续往前找。
            if availability[start_time] <= 0:
                start_time -= 1
                continue

            slot_capacity = capacities[start_time]
            total_vol += slot_capacity.vol_per_dock
            total_pc += slot_capacity.pc_per_dock
            if total_vol >= group.vol and total_pc >= group.pc:
                break
            start_time -= 1

        # 倒推后依然不够，说明这个结束时间不可行。
        if total_vol < group.vol or total_pc < group.pc:
            return None, {}

        # 真正分配时，按照时间顺序把每个时间片的产能扣给当前 group。
        # 注意：同一个时间片的垛口数不能超用，所以每占用一次就把 availability 减 1。
        usage = {}
        remaining_vol = group.vol
        remaining_pc = group.pc
        for slot in range(start_time, finish_time + 1):
            if availability[slot] <= 0:
                continue
            slot_capacity = capacities[slot]
            used_vol = min(slot_capacity.vol_per_dock, remaining_vol)
            used_pc = min(slot_capacity.pc_per_dock, remaining_pc)
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

        # 理论上只要前面可行，这里不应再失败；
        # 但为了保险，如果出现残余量则回滚并返回不可行。
        if remaining_vol > 0 or remaining_pc > 0:
            for slot in usage:
                availability[slot] += 1
            return None, {}

        # 返回的是“最后一个被占用的时刻”，也就是结束时间。
        return start_time, usage
