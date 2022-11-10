import datetime
import glob
import io
import json
import logging
import openvr
import os
import re
import requests
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
        return f"STATUS {enable_server_silent}"

    srv.run(host=host, port=port)


class Discord_controller:
    record_url = None
    notification_url = None
    headers = {"Content-Type": "application/json"}

    def record(self, text):
        if self.record_url:
            self.post(self.record_url, "vrc_joined_bell_record", text)

    def notification(self, text):
        if self.notification_url:
            self.post(self.notification_url, "vrc_joined_bell_notification", text)

    def post(self, url, name, text):
        body = {
            "username": name,
            "content": text,
        }
        requests.post(url, json.dumps(body), headers=self.headers)


class Hmd_controller:
    # たぶんHMD
    hmd_id = 0
    vr_system = None

    def __init__(self):
        if openvr.isHmdPresent() and openvr.isRuntimeInstalled():
            self.vr_system = openvr.init(openvr.VRApplication_Utility)
            # 認識しているHMDがIndexか，SteamVR起動してないと''が返ってくるはず
            if (
                self.vr_system.getStringTrackedDeviceProperty(
                    self.hmd_id, openvr.Prop_ModelNumber_String
                )
                != "Index"
            ):
                logger.info("afk_detect only support IndexHMD")
                self.vr_system = None
            else:
                logger.info("IndexHMD detected!")

    def isHmdIdle(self):
        if not self.vr_system:
            return False
        # https://github.com/ValveSoftware/openvr/blob/08de3821dfd3aa46f778376680c68f33b9fdcb6c/headers/openvr_driver.h#L971-L976
        # 0: Idle HMDつけてないとき HMD持って動かしてるときもこれ
        # 1: Active HMDつけてるとき
        # 3: Idle for at least 5sec HMDが動かずに5秒立ったとき
        return self.vr_system.getTrackedDeviceActivityLevel(self.hmd_id) == 3


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
    with open("notice.yml", "r") as conf:
        config = yaml.load(conf, Loader=yaml.SafeLoader)

    data = {}
    logger.info("events")
    for notice in config["notices"]:
        data[notice["event"]] = ["", re.compile(notice["event"]), notice["sound"]]
        logger.info(f"  {notice['event']}: {notice['sound']}")
        if "message" in notice:
            data[notice["event"]].append(notice["message"])
            logger.info(f"        {notice['message']}")

    if config["silent"]["toggle_server"]:
        try:
            thread = threading.Thread(
                target=toggle_server,
                args=(config["silent"]["host"], config["silent"]["port"]),
                daemon=True,
            )
            thread.start()
        except:
            import traceback

            traceback.print_exc()

    start = datetime.datetime.strptime(
        config["silent"]["time"]["start"], "%H:%M:%S"
    ).time()
    end = datetime.datetime.strptime(config["silent"]["time"]["end"], "%H:%M:%S").time()
    logger.info("sleep time {} {} {}".format(start, "-", end))

    enableCevio = False
    if "cevio" in config:
        import clr

        try:
            sys.path.append(os.path.abspath(config["cevio"]["dll"]))

            logger.info(f"CeVIO dll: {config['cevio']['dll']}")
            clr.AddReference("CeVIO.Talk.RemoteService")
            import CeVIO.Talk.RemoteService as cs

            cs.ServiceControl.StartHost(False)
            talker = cs.Talker()
            talker.Cast = config["cevio"]["cast"]
            talker.Volume = 100
            enableCevio = True
            logger.info(f"cast: {config['cevio']['cast']}")
        except:
            import traceback

            traceback.print_exc()

    record_url = None
    notification_url = None
    hc = None
    dc = Discord_controller()
    if "webhook" in config:
        logger.info("webhook")
        if "record_url" in config["webhook"]:
            logger.info("  use record webhook")
            dc.record_url = config["webhook"]["record_url"]
        if "notification" in config["webhook"]:
            logger.info("  use notification webhook")
            dc.notification_url = config["webhook"]["notification"]["notification_url"]
            if config["webhook"]["notification"]["afk_detect"]:
                logger.info("    use AFKDetect")
                hc = Hmd_controller()

    vrcdir = f"{os.environ['USERPROFILE']}\\AppData\\LocalLow\\VRChat\\VRChat\\"
    logfiles = glob.glob(f"{vrcdir}output_log_*.txt")
    logfiles.sort(key=os.path.getctime, reverse=True)

    with open(logfiles[0], "r", encoding="utf-8") as f:
        open_text = f"open logfile : {logfiles[0]}"
        logger.info(open_text)
        dc.record(open_text)
        loglines = tail(f)
        timereg = re.compile(
            "([0-9]{4}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) .*"
        )
        terminatereg = re.compile(".*?VRCApplication: OnApplicationQuit at .*")

        for line in loglines:
            logtime = timereg.match(line)
            if not logtime:
                continue
            # おわり
            if terminatereg.match(line):
                logger.info(line)
                dc.record(line)
                return

            for pattern, item in data.items():
                match = item[COLUMN_EVENT_PATTERN].match(line)
                if not match:
                    continue
                logger.info(line)
                dc.record(line)
                if hc and hc.isHmdIdle() and not enable_server_silent:
                    dc.notification(line)
                if logtime.group(1) != item[COLUMN_TIME]:
                    item[COLUMN_TIME] = logtime.group(1)
                    group = ""
                    if len(match.groups()) > 0:
                        group = match.group(1)

                    if is_silent(config, group):
                        break

                    if enableCevio and len(item) == 4:
                        group = re.sub(r"[-―]", "", group)
                        if (
                            len(talker.GetPhonemes(group)) != 0
                            and len(talker.GetPhonemes(group))
                            <= config["cevio"]["max_phonemes"]
                        ):
                            state = talker.Speak(group + item[COLUMN_MESSAGE])
                            state.Wait()
                            break

                    play(item[COLUMN_SOUND], 1)
                    break


if __name__ == "__main__":
    main()
