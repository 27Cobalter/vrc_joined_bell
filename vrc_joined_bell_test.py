import datetime
import os
import freezegun

from vrc_joined_bell import (
    is_silent,
    is_silent_exclude_event,
    is_silent_time,
)

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"


@freezegun.freeze_time("2020-11-01 01:00:00")
def test_is_silent():
    config = {
        "silent": {
            "time": {
                "start": "00:00:00",
                "end": "04:00:00",
            },
            "exclude": {
                "match_group": ["27Cobalter"],
            },
        }
    }
    assert is_silent(config, "bootjp／ぶーと") == True

    config = {
        "silent": {
            "time": {
                "start": "00:00:00",
                "end": "04:00:00",
            },
            "exclude": {
                "days_of_week": ["Mon"],
                "match_group": ["bootjp／ぶーと"],
            },
        }
    }
    assert is_silent(config, "bootjp／ぶーと") == False

    # test for nothing array.
    config = {
        "silent": {
            "time": {
                "start": "00:00:00",
                "end": "04:00:00",
            },
            "exclude": {},
        }
    }
    assert is_silent(config, "") == True


@freezegun.freeze_time("2020-11-01")
def test_is_silent_exclude_event():
    assert is_silent_exclude_event(["27Cobalter"], "27Cobalter") == True
    assert is_silent_exclude_event(["27Cobalter"], "bootjp／ぶーと") == False


@freezegun.freeze_time("2020-11-01 01:00:00")
def test_is_silent_time():
    start = datetime.datetime.strptime("00:00:00", "%H:%M:%S").time()
    end = datetime.datetime.strptime("04:00:00", "%H:%M:%S").time()
    assert is_silent_time(start, end) == True
    start = datetime.datetime.strptime("02:00:00", "%H:%M:%S").time()
    assert is_silent_time(start, end) == False
