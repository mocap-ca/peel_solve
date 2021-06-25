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

    """ Returns a list of of all animated nodes in the scene """

    nodes = set()

    for i in m.ls(type="animCurveTA"):
        nodes.add(m.listConnections(i + ".o")[0])

    for i in m.ls(type="animCurveTL"):
        nodes.add(m.listConnections(i + ".o")[0])

    return list(nodes)


def time_range(sel=None):

    """ Returns the current animated time range in the scene.
    @param sel: optional list of animated nodes to use for the time range """

    if sel is None:
        sel = ls()

    k = m.keyframe(sel, q=True)

    return min(k), max(k)


def clear_animation():
    """ Clear the animation off the solve skeleton root and below. Uses roots.ls() """
    m.delete(roots.ls(), channels=True, hierarchy="below")


def frame(sel=None):
    """ Set the playback options to frame the current animated range """
    a, b = time_range(sel)
    m.playbackOptions(min=math.floor(a), max=math.ceil(b))


def cut_keys():
    """ remove all the keys on the peelsolve joints - uses node_list.joint() """
    m.cutKey(node_list.joints())


def offset_animation(value, prefix=None):

    """ moves all animation in the scene by value.
     If prefix is provided it will look for joints with that prefix, otherwise all animation will be offset """

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


def trim_anim(nodes=None):

    """ remove all joint or camera animation outside of the playback min/max range """

    if nodes is None:
        nodes = ls()

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    a, b = time_range()

    if b > end:
        m.cutKey(nodes, time=(b, end))

    if a < start:
        m.cutKey(nodes, time=(a, start))


def zero_selected(first_frame=1):
    """ move the animation on the selected nodes to first_frame (1) """
    
    nodes = m.ls(sl=True)
    keys = m.keyframe(nodes, q=True)
    print min(keys), max(keys)
    
    value = round(min(keys))

    offset = min(keys) * -1 + first_frame
    
    print("Offsetting %d nodes by %d" % (len(nodes), value))

    m.keyframe(nodes, tc=offset, r=True)

    

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


def zero(nodes, first_frame=0):
    keys = m.keyframe(nodes, q=True)

    print min(keys), max(keys)

    offset = min(keys) * -1 + first_frame

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    if isinstance(offset, float):
        value = round(offset)

    if offset == 0:
        print("Zero offset, skipping")
        return

    print("Offsetting %d nodes by %d" % (len(nodes), offset))

    m.keyframe(nodes, tc=offset, r=True)

    m.playbackOptions(min=start + offset, max=end + offset)
    m.playbackOptions(ast=start + offset, aet=end + offset)




