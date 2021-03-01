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



