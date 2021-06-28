# Copyright (c) 2021 Alastair Macleod
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import maya.cmds as m
import maya.OpenMaya as om
import math
import json
import subprocess
import os.path

def fps():
    second = om.MTime(1.0, om.MTime.kSeconds)
    return second.asUnits(om.MTime().uiUnit())


def sel_range():
    return [ m.playbackOptions(q=True, min=True), m.playbackOptions(q=True, max=True) ]


def anm_range():
    return [ m.playbackOptions(q=True, ast=True), m.playbackOptions(q=True, aet=True) ]


def as_frames(value):
    """ Converts the values to (int) frames.

    Input can be timecode (string), or float (seconds) or int (frames)

    If value is None, None is returned.

    Throws a TypeError for all other data types.
    """

    if isinstance(value, basestring):
        # this method works best for data from shotgun
        return int(tcode.TCode(value, 30, 120).raw_seconds * fps())

    if isinstance(value, float):
        # seconds
        return int(math.floor(value * fps()))

    if isinstance(value, int):
        return value

    if value is None:
        return None

    raise TypeError("Unknown type for value: " + str(value) + "  type:" + str(type(value)))


def set_range(dot):

    trial_in, trial_out, ast, aet = [as_frames(i) for i in (dot.trial_in, dot.trial_out, dot.range_in, dot.range_out)]

    if trial_in is not None:
        m.playbackOptions(min=trial_in)
        m.currentTime(tc_in)

    if trial_out is not None:
        m.playbackOptions(max=trial_out)

    if ast is not None:
        m.playbackOptions(ast=ast)

    if aet is not None:
        m.playbackOptions(aet=aet)


def c3d_start(optical_root):

    # Get the timecode value
    hh = m.getAttr(optical_root + ".C3dTimecodeH")
    mm = m.getAttr(optical_root + ".C3dTimecodeM")
    ss = m.getAttr(optical_root + ".C3dTimecodeS")
    ff = m.getAttr(optical_root + ".C3dTimecodeF")

    # Get the first field offset
    first_field = m.getAttr(optical_root + ".C3dFirstField")
    c3d_rate = m.getAttr(optical_root + ".C3dRate")
    tc_standard = m.getAttr(optical_root + ".C3dTimecodeStandard")

    start = int(ff) + int(ss) * tc_standard + int(mm) * 60 * tc_standard + int(hh) * 60 * 60 * tc_standard
    print("C3D start frame: %02d:%02d:%02d:%02d" % (hh, mm, ss, ff))
    print("First Field: %d " % first_field)
    print("Start frame: %d @ %d fps" % (start, tc_standard))
    offset = first_field * tc_standard / c3d_rate
    print("Offset: %d" % offset)
    print("   = %d * %d / %d" % (first_field, tc_standard, c3d_rate))
    return start + first_field * tc_standard / c3d_rate, tc_standard


def mov_start(file_path, rate=None):

    if not os.path.isfile(file_path):
        raise RuntimeError("Could not find: " + file_path)

    cmd = ["M:\\bin\\ffprobe.exe", "-print_format", "json", "-show_streams", file_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    data = json.loads(out)
    tc = None

    if 'streams' not in data:
        print(json)
        raise RuntimeError("Invalid file: " + str(file_path))

    for i in data['streams']:
        if 'tags' not in i: continue
        if 'timecode' not in i['tags']: continue
        if rate is None and 'r_frame_rate' in i and i['r_frame_rate'] != "0/0":
            rate = i['r_frame_rate']
            if '/' in rate:
                sp = rate.split('/')
                if sp[1] != "0":
                    rate = float(sp[0]) / float(sp[1])

        tc = i['tags']['timecode']

    if tc is None:
        raise RuntimeError("No timecode")

    hh, mm, ss, ff = tc.split(':')

    current = int(ff) + int(ss) * rate + int(mm) * rate * 60 + int(hh) * 60 * 60 * rate
    print("Video Timcode:     %s at %s" % (tc, rate))
    print("Video start frame: %d at %s" % (current, rate))

    return current, rate


def timecode(value):

    """ get the timecode for a given frame# at 30fps """

    fps = None
    time_mode = m.currentUnit(time=True, q=True)
    if time_mode == "120fps": fps = 120
    if time_mode == "ntscf": fps = 60
    if fps is None:
        raise RuntimeError("Invalid FPS - only 120 or 60 supported")

    frames = float(value) % fps
    value = int(value)

    if time_mode == "120fps":
        frames /= 4
    else:
        frames /= 2

    value = int(((value - frames) / fps))
    secs = value % 60
    value = int(((value - secs) / 60))
    mins = value % 60
    hours = int(((value - mins) / 60))

    return hours, mins, secs, frames

    # return "%02d:%02d:%02d:%02d" % (hours, mins, secs, frames)


def tc_node():

    """ Creates a timecode node in the scene based on the current frame range """

    if m.objExists("TIMECODE"):
        m.delete("TIMECODE")

    tc = m.group(name="TIMECODE", em=True)

    st = m.playbackOptions(q=True, min=True)
    en = m.playbackOptions(q=True, max=True)

    for i in range(int(st), int(en)):
        hh, mm, ss, ff = timecode(i)
        m.setKeyframe(tc, at="tx", v=hh, t=(i))
        m.setKeyframe(tc, at="ty", v=mm, t=(i))
        m.setKeyframe(tc, at="tz", v=ss, t=(i))
        m.setKeyframe(tc, at="rx", v=ff, t=(i))


def frame(timecode, fps=30):
    sp = timecode.split(':')
    hh, mm, ss, ff = [int(i) for i in sp]
    return hh * 60 * 60 * fps + mm * 60 * fps + ss * fps + ff
