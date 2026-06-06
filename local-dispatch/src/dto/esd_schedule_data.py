from dataclasses import dataclass, field
from typing import List, NamedTuple, Dict


@dataclass
class Group:
    """一个分组"""

    group_id: str  # 分组id
    earliest_load_time: int  # 最早开始装车的时间点
    target_finish_time: int  # 目标装车完成的时间点
    vol: float  # 体积（方量）
    pc: float  # 件数
    priority: int  # 优先级，数字越小优先级越高
    create_time: int  # 创建时间


class DeliveryCapacity(NamedTuple):
    """一个时间单位的发货产能"""

    vol_per_dock: float  # 每个垛口在这个时间单位内可以装载的体积（方量）
    pc_per_dock: float  # 每个垛口在这个时间单位内可以装载的件数
    dock_num: int  # 这个时间单位的垛口数量


@dataclass
class ESDScheduleInput:
    """算法输入"""

    # 一个时间单位表示多少分钟
    time_unit_in_minutes: int = 30
    # 分组列表
    groups: List[Group] = field(default_factory=list)
    # 发货产能列表，从第一天的 0 点开始
    delivery_capacities: List[DeliveryCapacity] = field(default_factory=list)

    def __post_init__(self):
        # 计算每天的时间单位数量
        self.daily_time_units: int = 24 * 60 // self.time_unit_in_minutes


@dataclass
class ESDScheduleOutput:
    """算法输出"""

    # 分组 id -> 装车完成的时间点
    groups: Dict[str, int] = field(default_factory=dict)
    # 每个分组在每个时间点占用的产能，如 {group1: {0: (10m^3, 1pc, 1)}, {1: (5m^3, 0pc, 1)}}
    capacity_usage: Dict[str, Dict[int, DeliveryCapacity]] = field(default_factory=dict)