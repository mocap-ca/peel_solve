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
from peel_solve import node_list, roots
import math


def ls():

    nodes = set()

    for i in m.ls(type="animCurveTA"):
        nodes.add(m.listConnections(i + ".o")[0])

    for i in m.ls(type="animCurveTL"):
        nodes.add(m.listConnections(i + ".o")[0])

    return list(nodes)


def time_range(sel=None):
    if sel is None:
        sel = ls()

    k = m.keyframe(sel, q=True)

    return min(k), max(k)


def clear_animation():
    """ Clear the animation off the solve skeleton root and below """
    m.delete(roots.ls(), channels=True, hierarchy="below")


def frame(sel=None):
    a, b = time_range(sel)
    m.playbackOptions(min=math.floor(a), max=math.ceil(b))


def cut_keys():
    """ remove all the keys on the peelsolve joints """
    m.cutKey(node_list.joints())


def offset_animation(value, prefix=None):

    """ moves all the joints and camera animation in the scene by value """

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    if isinstance(value, float):
        value = round(value)

    if prefix:
        j = m.ls(prefix + "*", typ='joint')
    else:
        j = ls()

    print("Offsetting %d nodes by %d" % (len(j), value))

    m.keyframe(j, tc=value, r=True)

    m.playbackOptions(min=start+value, max=end+value)


def trim_anim():

    """ remove all joint or camera animation outside of the playback min/max range """

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    a, b = time_range()

    if b > end:
        m.cutKey(j, time=(b, end))

    if a < start:
        m.cutKey(j, time=(a, start))


def zero_anim(first_frame=1, prefix=None):

    """ move the animation on all joints to first_frame (1) """

    if prefix:
        j = m.ls(prefix + "*", typ='joint')
    else:
        j = ls()

    if not j:
        if prefix:
            raise RuntimeError("Could not find anything to offset for: " + prefix)
        else:
            raise RuntimeError("Could not find anything to offset")

    keys = m.keyframe(j, q=True)

    offset = min(keys) * -1 + first_frame

    offset_animation(offset, prefix)




