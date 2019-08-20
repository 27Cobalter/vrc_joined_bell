import time
import glob
import os
import re
import winsound

soundfile = "sound.wav"


def tail(thefile):
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line


if __name__ == "__main__":
    with open(soundfile, "rb") as f:
        data = f.read()

    vrcdir = os.environ["USERPROFILE"] + "\\AppData\\LocalLow\\VRChat\\VRChat\\"
    logfiles = glob.glob(vrcdir + "output_log_*.txt")
    logfiles.sort(key=os.path.getctime, reverse=True)

    with open(logfiles[0], "rb") as f:
        loglines = tail(f)
        for line in loglines:
            pattern = ".*?[NetworkManager] OnPlayerJoined.*"
            if re.match(pattern, line):
                print(line)
                winsound.PlaySound(data, winsound.SND_MEMORY)
