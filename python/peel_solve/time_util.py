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


class Timecode(object):
    def __init__(self, value=None, rate=None, fraction=0.0):
        self.h = None
        self.m = None
        self.s = None
        self.f = None
        self.fraction = fraction
        if rate is not None:
            self.rate = float(rate)
        else:
            self.rate = None

        if isinstance(value, Timecode):
            self.h = value.h
            self.m = value.m
            self.s = value.s
            self.f = value.f
            self.fraction = value.fraction
            self.rate = value.rate

        if rate is not None:
            self.rate = float(rate)
            if isinstance(value, str):
                self.set_timecode(value)

            if isinstance(value, float):
                self.set_frame(value)

    def set_timecode(self, value):

        if not isinstance(value, str):
            raise RuntimeError("Invalid value passed to set_timecode: " + str(value))

        if ':' not in value:
            raise ValueError("Invalid timecode string: " + value)
        sp = value.split(':')
        if len(sp) != 4:
            raise ValueError("Cannot parse timecode: " + value)

        self.h, self.m, self.s, self.f = [int(i) for i in sp]

    def set_frame(self, value):

        if not isinstance(value, float):
            raise RuntimeError("Invalid value passed to set_frame: " + str(value))

        self.f = value % self.rate
        value = (value - self.f) / self.rate
        self.s = value % 60
        value = (value - self.s) / 60
        self.m = value % 60
        self.h = (value - self.m) / 60

    def __str__(self):
        return "%02d:%02d:%02d:%02d" % (self.h, self.m, self.s, self.f)

    def info(self):
        ret = str(self) + "  Fps: " + str(self.rate)
        if self.fraction is not None:
            ret += "  Fraction: %f" % self.fraction
        ret += "   Frame: %d" % self.frame()
        return ret

    def frame(self):
        ret = self.f
        ret += self.s * self.rate
        ret += self.m * self.rate * 60
        ret += self.h * self.rate * 60 * 60
        return float(ret) + self.fraction

    def set_rate(self, rate):
        if rate == self.rate:
            return

        scaled = self.frame() * float(rate) / self.rate
        self.fraction = scaled % 1
        self.rate = rate
        self.set_frame(scaled // 1)

    def __add__(self, other):
        t = Timecode(other)
        t.set_rate(self.rate)
        t.set_frame(self.frame() + t.frame())
        return t

    def __sub__(self, other):
        t = Timecode(other)
        t.set_rate(self.rate)
        t.set_frame(self.frame() - t.frame())
        return t


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

    print(data)

    for i in data['streams']:
        if 'tags' not in i: continue
        if 'timecode' not in i['tags']: continue
        if rate is None and 'r_frame_rate' in i and i['r_frame_rate'] != "0/0":
            rate = i['r_frame_rate']
            if '/' in rate:
                sp = rate.split('/')
                if sp[1] != "0":
                    rate = float(sp[0]) / float(sp[1])

        tc = str(i['tags']['timecode'])

    if tc is None:
        raise RuntimeError("No timecode")

    if rate is None:
        raise RuntimeError("Could not determine frame rate for movie: " + str(file_path))

    print("TC: " + str(tc))

    return Timecode(tc, rate)


def tc_node():

    """ Creates a timecode node in the scene based on the current frame range """

    if m.objExists("TIMECODE"):
        m.delete("TIMECODE")

    tc = m.group(name="TIMECODE", em=True)

    st = m.playbackOptions(q=True, min=True)
    en = m.playbackOptions(q=True, max=True)

    for i in range(int(st), int(en)):
        t = Timecode(float(i), fps())
        m.setKeyframe(tc, at="tx", v=t.h, t=(i))
        m.setKeyframe(tc, at="ty", v=t.m, t=(i))
        m.setKeyframe(tc, at="tz", v=t.s, t=(i))
        m.setKeyframe(tc, at="rx", v=t.f, t=(i))


def timecode_start(optical_root):
    # Get the timecode value from the c3d
    # This is when the data was recorded, it may not be the first frame of data

    if optical_root is None:
        raise RuntimeError("Invalid optical root while getting timecode start")

    if not m.objExists(optical_root):
        raise RuntimeError("Root does not exist: " + optical_root + " while getting timecode start")

    t = Timecode()
    t.h = m.getAttr(optical_root + ".C3dTimecodeH")
    t.m = m.getAttr(optical_root + ".C3dTimecodeM")
    t.s = m.getAttr(optical_root + ".C3dTimecodeS")
    t.f = m.getAttr(optical_root + ".C3dTimecodeF")
    t.rate = m.getAttr(optical_root + ".C3dTimecodeStandard")
    return t


def c3d_start(optical_root):

    """ Get the start frame specified by the c3d file """

    start_tc = timecode_start(optical_root)

    # Get the first field offset (first field is 1 based)
    first_field = m.getAttr(optical_root + ".C3dFirstField")
    c3d_rate = m.getAttr(optical_root + ".C3dRate")

    return start_tc + Timecode(first_field, c3d_rate)


def now():
    return Timecode(m.currentTime(q=True), fps())


def now_alt(rate):
    t = Timecode()
    t.h = m.getAttr("TIMECODE.tx")
    t.m = m.getAttr("TIMECODE.ty")
    t.s = m.getAttr("TIMECODE.tz")
    t.f = m.getAttr("TIMECODE.rx")
    t.rate = rate
    return t
