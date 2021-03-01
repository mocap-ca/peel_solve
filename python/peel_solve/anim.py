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


def clear_animation():
    """ Clear the animation off the solve skeleton root and below """
    m.delete(roots.ls(), channels=True, hierarchy="below")


def frame_animation():
    """ Set the playback range to the min/max based on keys on joints """
    j = m.ls(typ='joint')
    keys = m.keyframe(j, q=True)
    m.playbackOptions(min=math.floor(min(keys)), max=math.ceil(max(keys)))


def cut_keys():
    """ remove all the keys on the peelsolve joints """
    m.cutKey(node_list.joints())


def offset_animation(value, prefix=None):

    """ moves all the joints and camera animation in the scene by value """

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    if isinstance(value, float):
        value = round(value)

    print("Offset: " + str(value))

    if prefix:
        j = m.ls(prefix + "*", typ='joint')
    else:
        j = m.ls(typ='joint')

    j += node_list.cameras()

    # remove keys from hidden channels.
    for i in j:
        for ch in ['tx', 'ty', 'tz']:
            if not m.getAttr(i + '.' + ch, k=True):
                m.cutKey(i + '.' + ch)

    m.playbackOptions(min=start+value, max=end+value)


def trim_anim():

    """ remove all joint or camera animation outside of the playback min/max range """

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    j = m.ls(type='joint') + [m.listRelatives(i, p=True)[0] for i in m.ls(type='camera')]
    k = m.keyframe(j, q=True)

    if max(k) > end:
        m.cutKey(j, time=(max(k), end))

    if min(k) < start:
        m.cutKey(j, time=(min(k), start))


def zero_anim(first_frame=1, prefix=None):

    """ move the animation on all joints to first_frame (1) """

    if prefix:
        j = m.ls(prefix + "*", typ='joint')
    else:
        j = m.ls(typ='joint')

    if not j:
        if prefix:
            raise RuntimeError("Could not find anything to offset for: " + prefix)
        else:
            raise RuntimeError("Could not find anything to offset")

    keys = m.keyframe(j, q=True)

    offset = min(keys) * -1 + first_frame

    offset_animation(offset, prefix)




