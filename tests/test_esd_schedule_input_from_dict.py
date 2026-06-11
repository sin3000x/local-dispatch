import json
from dataclasses import asdict

from src.dto.esd_schedule_data import DeliveryCapacity, ESDScheduleInput, Group
from tests.helpers.esd_schedule_fixtures import build_sample_schedule_input


def test_from_dict_roundtrip_via_json():
    original = build_sample_schedule_input()

    restored = ESDScheduleInput.from_dict(json.loads(json.dumps(asdict(original))))

    assert restored == original
    assert restored.daily_time_units == original.daily_time_units


def test_from_dict_accepts_dict_shaped_delivery_capacities():
    data = {
        "time_unit_in_minutes": 60,
        "groups": [
            {
                "group_id": "group-1",
                "earliest_load_time": 0,
                "target_finish_time": 1,
                "vol": 10.0,
                "pc": 5,
                "priority": 1,
                "create_time": 0,
            }
        ],
        "delivery_capacities": [
            {"vol_per_dock": 8.0, "pc_per_dock": 4, "dock_num": 2},
        ],
    }

    restored = ESDScheduleInput.from_dict(data)

    assert restored.time_unit_in_minutes == 60
    assert restored.daily_time_units == 24
    assert restored.groups == [Group(**data["groups"][0])]
    assert restored.delivery_capacities == [
        DeliveryCapacity(vol_per_dock=8.0, pc_per_dock=4, dock_num=2)
    ]


def test_from_dict_uses_defaults_for_missing_fields():
    restored = ESDScheduleInput.from_dict({})

    assert restored.time_unit_in_minutes == 30
    assert restored.groups == []
    assert restored.delivery_capacities == []
    assert restored.daily_time_units == 48
