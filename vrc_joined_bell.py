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


if __name__ == "__main__":
    with open("notice.yml", "r") as conf:
        notices = yaml.load(conf, Loader=yaml.SafeLoader)
    print("load config")
    data = {}
    for pattern, soundfile in notices.items():
        data[pattern] = ["", re.compile(pattern.encode()), soundfile]
        print("  " + pattern + ": " + soundfile)

    vrcdir = os.environ["USERPROFILE"] + "\\AppData\\LocalLow\\VRChat\\VRChat\\"
    logfiles = glob.glob(vrcdir + "output_log_*.txt")
    logfiles.sort(key=os.path.getctime, reverse=True)

    with open(logfiles[0], "rb") as f:
        print("open logfile : ", logfiles[0])
        loglines = tail(f)

        timereg = re.compile(
            "([0-9]{4}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) .*".encode()
        )

        for line in loglines:
            for pattern, item in data.items():
                logtime = timereg.match(line)
                if logtime and logtime.group(1) != item[0] and item[1].match(line):
                    print(line)
                    item[0] = logtime.group(1)
                    with open(item[2], "rb") as f:
                        sound = f.read()
                    winsound.PlaySound(sound, winsound.SND_MEMORY)
