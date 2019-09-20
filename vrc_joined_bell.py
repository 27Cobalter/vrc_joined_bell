import datetime
import time
import glob
import os
import re
import winsound
import yaml


def tail(thefile):
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line


def timerange(start, end):
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end


if __name__ == "__main__":
    with open("notice.yml", "r") as conf:
        config = yaml.load(conf, Loader=yaml.SafeLoader)

    data = {}
    print("events")
    for notice in config["notices"]:
        data[notice["event"]] = ["", re.compile(notice["event"]), notice["sound"]]
        print("  " + notice["event"] + ": " + notice["sound"])

    start = datetime.datetime.strptime(config["time"]["start"], "%H:%M:%S").time()
    end = datetime.datetime.strptime(config["time"]["end"], "%H:%M:%S").time()
    print("no notification time ", start, "-", end)

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
                if item[1].match(line) and logtime.group(1) != item[0]:
                    print(line.rstrip("\n"))
                    item[0] = logtime.group(1)

                    if not timerange(start, end):
                        with open(item[2], "rb") as f:
                            sound = f.read()
                        winsound.PlaySound(sound, winsound.SND_MEMORY)
                    break
