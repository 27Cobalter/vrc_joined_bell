import datetime
import time
import glob
import os
import re
import wave
import freezegun

# disable pygame version log
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame
import yaml


def tail(thefile):
    thefile.seek(0, 2)
    offset = thefile.tell()
    while True:
        try:
            line = thefile.readline()
            offset = thefile.tell()
            if not line:
                time.sleep(0.5)
                continue
            if line == "\n" or line == "\r\n":
                continue
            line = line.rstrip("\n")
            yield repr(line)[1:-1]
        except UnicodeDecodeError:
            thefile.seek(offset, 0)
            time.sleep(0.5)


def is_silent_exclude_days_of_week(exclude_days_of_week):
    return datetime.datetime.now().strftime("%a") in exclude_days_of_week


@freezegun.freeze_time("2020-11-01")
def test_is_silent_exclude_days_of_week():
    assert is_silent_exclude_days_of_week(["Sun"]) == True
    assert is_silent_exclude_days_of_week(["Thu"]) == False


def is_silent(config, group):
    start = datetime.datetime.strptime(
        config["silent"]["time"]["start"], "%H:%M:%S"
    ).time()
    end = datetime.datetime.strptime(config["silent"]["time"]["end"], "%H:%M:%S").time()

    if not is_silent_time(start, end):
        return False

    if is_silent_exclude_event(config["silent"]["exclude"]["match_group"], group):
        return False

    if is_silent_exclude_days_of_week(config["silent"]["exclude"]["days_of_week"]):
        return False

    return True


@freezegun.freeze_time("2020-11-01 01:00:00")
def test_is_silent():
    config = {
        "silent": {
            "time": {
                "start": "00:00:00",
                "end": "04:00:00",
            },
            "exclude": {
                "days_of_week": ["Mon"],
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
                "days_of_week": ["Sun"],
                "match_group": ["27Cobalter"],
            },
        }
    }
    assert is_silent(config, "bootjp／ぶーと") == False

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


def is_silent_exclude_event(match_groups, group):
    for match_group in match_groups:
        if match_group == group:
            return True

    return False


@freezegun.freeze_time("2020-11-01")
def test_is_silent_exclude_event():
    assert is_silent_exclude_event(["27Cobalter"], "27Cobalter") == True
    assert is_silent_exclude_event(["27Cobalter"], "bootjp／ぶーと") == False


def is_silent_time(start, end):
    if start == end:
        return False
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end


@freezegun.freeze_time("2020-11-01 01:00:00")
def test_is_silent_time():
    start = datetime.datetime.strptime("00:00:00", "%H:%M:%S").time()
    end = datetime.datetime.strptime("04:00:00", "%H:%M:%S").time()
    assert is_silent_time(start, end) == True
    start = datetime.datetime.strptime("02:00:00", "%H:%M:%S").time()
    assert is_silent_time(start, end) == False


def play(data_path, volume):
    with wave.open(data_path, "rb") as wave_file:
        frame_rate = wave_file.getframerate()
    pygame.mixer.init(frequency=frame_rate)
    player = pygame.mixer.Sound(data_path)
    player.set_volume(volume)
    player.play()


COLUMN_TIME = 0
COLUMN_EVENT_PATTERN = 1
COLUMN_SOUND = 2
COLUMN_MESSAGE = 3

if __name__ == "__main__":
    with open("notice.yml", "r") as conf:
        config = yaml.load(conf, Loader=yaml.SafeLoader)

    data = {}
    print("events")
    for notice in config["notices"]:
        data[notice["event"]] = ["", re.compile(notice["event"]), notice["sound"]]
        print("  " + notice["event"] + ": " + notice["sound"])
        if "message" in notice:
            data[notice["event"]].append(notice["message"])
            print("        " + notice["message"])

    start = datetime.datetime.strptime(
        config["silent"]["time"]["start"], "%H:%M:%S"
    ).time()
    end = datetime.datetime.strptime(
        config["silent_time"]["time"]["end"], "%H:%M:%S"
    ).time()
    behavior = config["silent"]["behavior"]
    volume = config["silent"]["volume"]
    print("sleep time behavior ", behavior, start, "-", end)

    enableCevio = False
    if "cevio" in config:
        import clr
        import sys

        try:
            sys.path.append(os.path.abspath(config["cevio"]["dll"]))

            print("CeVIO dll:", config["cevio"]["dll"])
            clr.AddReference("CeVIO.Talk.RemoteService")
            import CeVIO.Talk.RemoteService as cs

            cs.ServiceControl.StartHost(False)
            talker = cs.Talker()
            talker.Cast = config["cevio"]["cast"]
            talker.Volume = 100
            enableCevio = True
            print("cast:", config["cevio"]["cast"])
        except:
            import traceback

            traceback.print_exc()

    vrcdir = os.environ["USERPROFILE"] + "\\AppData\\LocalLow\\VRChat\\VRChat\\"
    logfiles = glob.glob(vrcdir + "output_log_*.txt")
    logfiles.sort(key=os.path.getctime, reverse=True)

    with open(logfiles[0], "r", encoding="utf-8") as f:
        print("open logfile : ", logfiles[0])
        loglines = tail(f)

        timereg = re.compile(
            "([0-9]{4}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) .*"
        )

        for line in loglines:
            logtime = timereg.match(line)
            if not logtime:
                continue
            for pattern, item in data.items():
                match = item[COLUMN_EVENT_PATTERN].match(line)
                if match and logtime.group(1) != item[COLUMN_TIME]:
                    print(line)
                    item[COLUMN_TIME] = logtime.group(1)
                    silent_time = is_silent(config, group)
                    group = re.sub(r"[-―]", "", match.group(0))

                    if behavior == "ignore" and silent_time:
                        break

                    if behavior == "volume_down" and silent_time:
                        play_volume = volume
                    else:
                        play_volume = 1.0

                    if enableCevio and len(item) == 4:
                        talker.Volume = play_volume * 100
                        if (
                            len(talker.GetPhonemes(group)) != 0
                            and len(talker.GetPhonemes(group))
                            <= config["cevio"]["max_phonemes"]
                        ):
                            state = talker.Speak(group + item[COLUMN_MESSAGE])
                            state.Wait()
                            break

                    play(item[COLUMN_SOUND], play_volume)
                    break
