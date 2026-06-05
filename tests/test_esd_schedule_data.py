from src.dto.esd_schedule_data import ESDScheduleInput, Group
from tests.helpers.esd_schedule_fixtures import build_sample_schedule_input


def test_build_sample_schedule_input():
    schedule_input = build_sample_schedule_input()

    assert isinstance(schedule_input, ESDScheduleInput)
    assert len(schedule_input.groups) > 0
    assert schedule_input.delivery_capacities
    assert all(isinstance(group, Group) for group in schedule_input.groups)
