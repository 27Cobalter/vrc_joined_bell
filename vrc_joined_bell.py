import datetime
import glob
import io
import logging
import os
import psutil
import re
import sys
import threading
import time
import wave
import yaml

from flask import Flask

# disable pygame version log
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame


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


def is_silent(config, group):
    if (
        "toggle_server" in config["silent"]
        and config["silent"]["toggle_server"]
        and enable_server_silent
    ):
        return True

    start = datetime.datetime.strptime(
        config["silent"]["time"]["start"], "%H:%M:%S"
    ).time()
    end = datetime.datetime.strptime(config["silent"]["time"]["end"], "%H:%M:%S").time()

    if not is_silent_time(start, end):
        return False

    if "match_group" in config["silent"]["exclude"] and is_silent_exclude_event(
        config["silent"]["exclude"]["match_group"], group
    ):
        return False

    if "days_of_week" in config["silent"]["exclude"] and is_silent_exclude_days_of_week(
        config["silent"]["exclude"]["days_of_week"]
    ):
        return False

    return True


def is_silent_exclude_event(match_groups, group):
    for match_group in match_groups:
        if match_group == group:
            return True

    return False


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


enable_server_silent = False
logger = logging.getLogger(__name__)
log_io = io.StringIO()


def toggle_server(host, port):
    srv = Flask(__name__)
    log = logging.getLogger("werkzeug")
    log.disabled = True
    srv.logger.disabled = True

    logger.info("start toggle server")

    @srv.route("/log")
    def log():
        value = log_io.getvalue().replace("\n", "<br>")
        return f"{value}"

    @srv.route("/toggle")
    def toggle():
        global enable_server_silent
        enable_server_silent = not enable_server_silent

        logger.info(f"silent mode status change to {enable_server_silent} ")

        return f"STATUS {enable_server_silent}"

    @srv.route("/state")
    def show():
        global enable_server_silent

        logger.info(f"silent mode status: {enable_server_silent} ")

        return f"STATUS {enable_server_silent}"

    srv.run(host=host, port=port)


def process_kill_by_name(name):
    pid = os.getpid()
    for p in psutil.process_iter(attrs=["pid", "name"]):
        if p.info["name"] == name and p.pid != pid:
            p.terminate()


COLUMN_TIME = 0
COLUMN_EVENT_PATTERN = 1
COLUMN_SOUND = 2
COLUMN_MESSAGE = 3


def main():
    logger.setLevel(level=logging.INFO)
    std_handler = logging.StreamHandler(stream=sys.stdout)
    handler = logging.StreamHandler(stream=log_io)
    std_handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(std_handler)
    logger.addHandler(handler)
    process_kill_by_name("vrc_joined_bell.exe")
    with open("notice.yml", "r") as conf:
        config = yaml.load(conf, Loader=yaml.SafeLoader)

    data = {}
    logger.info("events")
    for notice in config["notices"]:
        data[notice["event"]] = ["", re.compile(notice["event"]), notice["sound"]]
        logger.info("  " + notice["event"] + ": " + notice["sound"])
        if "message" in notice:
            data[notice["event"]].append(notice["message"])
            logger.info("        " + notice["message"])

    if config["silent"]["toggle_server"]:
        try:
            thread = threading.Thread(
                target=toggle_server,
                args=(config["silent"]["host"], config["silent"]["port"]),
            )
            thread.start()
        except:
            import traceback

            traceback.print_exc()

    start = datetime.datetime.strptime(
        config["silent"]["time"]["start"], "%H:%M:%S"
    ).time()
    end = datetime.datetime.strptime(config["silent"]["time"]["end"], "%H:%M:%S").time()
    behavior = config["silent"]["behavior"]
    volume = config["silent"]["volume"]
    logger.info("sleep time behavior ", behavior, start, "-", end)

    enableCevio = False
    if "cevio" in config:
        import clr

        try:
            sys.path.append(os.path.abspath(config["cevio"]["dll"]))

            logger.info("CeVIO dll:", config["cevio"]["dll"])
            clr.AddReference("CeVIO.Talk.RemoteService")
            import CeVIO.Talk.RemoteService as cs

            cs.ServiceControl.StartHost(False)
            talker = cs.Talker()
            talker.Cast = config["cevio"]["cast"]
            talker.Volume = 100
            enableCevio = True
            logger.info("cast:", config["cevio"]["cast"])
        except:
            import traceback

            traceback.print_exc()

    vrcdir = os.environ["USERPROFILE"] + "\\AppData\\LocalLow\\VRChat\\VRChat\\"
    logfiles = glob.glob(vrcdir + "output_log_*.txt")
    logfiles.sort(key=os.path.getctime, reverse=True)

    with open(logfiles[0], "r", encoding="utf-8") as f:
        logger.info("open logfile : ", logfiles[0])
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
                    logger.info(line)
                    item[COLUMN_TIME] = logtime.group(1)
                    group = ""
                    if len(match.groups()) > 0:
                        group = match.group(1)
                    silent_time = is_silent(config, group)

                    if behavior == "ignore" and silent_time:
                        break

                    if behavior == "volume_down" and silent_time:
                        play_volume = volume
                    else:
                        play_volume = 1.0

                    if enableCevio and len(item) == 4:
                        talker.Volume = play_volume * 100
                        group = re.sub(r"[-―]", "", group)
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


if __name__ == "__main__":
    main()
