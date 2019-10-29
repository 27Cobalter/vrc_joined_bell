import datetime
import time
import glob
import os
import re
import wave

import pygame
import yaml


def tail(thefile):
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line


def is_silent_time(start, end):
    if start == end:
        return False
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end


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
        config["silent_time"]["start"], "%H:%M:%S"
    ).time()
    end = datetime.datetime.strptime(config["silent_time"]["end"], "%H:%M:%S").time()
    behavior = config["silent_time"]["behavior"]
    volume = config["silent_time"]["volume"]
    print("sleep time behavior ", behavior, start, "-", end)

    if "cevio" in config:
        import clr
        import sys

        sys.path.append(os.path.dirname(".\\"))

        clr.AddReference("CeVIO.Talk.RemoteService")
        import CeVIO.Talk.RemoteService as cs

        cs.ServiceControl.StartHost(False)
        talker = cs.Talker()
        talker.Cast = config["cevio"]["cast"]
        talker.Volume = 100
        print("cast:", config["cevio"]["cast"])

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
                    print(line.rstrip("\n"))
                    item[COLUMN_TIME] = logtime.group(1)
                    silent_time = is_silent_time(start, end)

                    if behavior == "ignore" and silent_time:
                        break

                    if behavior == "volume_down" and silent_time:
                        play_volume = volume
                    else:
                        play_volume = 1.0

                    if "cevio" in config and len(item) == 4:
                        state = talker.Speak(match.group(1) + item[COLUMN_MESSAGE])
                        state.Wait()
                    else:
                        play(item[COLUMN_SOUND], play_volume)
                    break
