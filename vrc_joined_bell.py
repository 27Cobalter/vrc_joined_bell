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
    for k, v in notices.items():
        print("  " + k + ": " + v)

    vrcdir = os.environ["USERPROFILE"] + "\\AppData\\LocalLow\\VRChat\\VRChat\\"
    logfiles = glob.glob(vrcdir + "output_log_*.txt")
    logfiles.sort(key=os.path.getctime, reverse=True)

    with open(logfiles[0], "rb") as f:
        print("open logfile : ", logfiles[0])
        loglines = tail(f)
        for line in loglines:
            for pattern, soundfile in notices.items():
                if re.match(pattern.encode(), line):
                    print(line)
                    with open(soundfile, "rb") as f:
                        data = f.read()
                    winsound.PlaySound(data, winsound.SND_MEMORY)
