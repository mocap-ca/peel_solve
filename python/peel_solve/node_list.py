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
from peel_solve import roots


def cameras():
    """ returns all animated cameras (generator) """
    for i in m.ls(type='camera'):
        transform = m.listRelatives(i, p=True)[0]
        keys = m.keyframe(transform, q=True)
        if keys:
            yield transform


def joints():
    """ returns a list of all the solving joints (passive transforms) """
    out = []
    for root in roots.ls():
        out += m.peelSolve(s=root, lp=True, ns=True)
    return out


def transforms():
    """ returns all transforms used by the solver """
    out = []
    for root in roots.ls():
        out += m.peelSolve(s=root, lt=True, ns=True)
    return out


def all_markers():
    """ returns a list of mocap markers in the scene (parent of peelSquareLocator) """

    mkr = m.ls(type='peelSquareLocator')
    mkr = [m.listRelatives(i, parent=True, f=True)[0] for i in mkr]
    return mkr


def active(use_solver=True):
    """
    :param use_solver: if true asks the solver to find them, otherwise searches the scene by node type
    :return: a list of all the active transforms
    """
    if use_solver:
        out = []
        for root in roots.ls():
            out += m.peelSolve(s=root, la=True, ns=True) or []
        return out
    else:
        shapes = m.ls(type="peelLocator", long=True)
        return [m.listRelatives(i, p=True, f=True)[0] for i in shapes]


def active_connections():
    """ returns the number of connected, number of disconnected active markers """
    connected = 0
    disconnected = 0
    for i in active():
        if m.listConnections(i + ".peelTarget", d=False, s=True):
            connected += 1
        else:
            disconnected += 1

    return connected, disconnected


def source(active_marker):

    """ returns the name of the marker driving the provided active marker name, or None """

    if not m.objExists(active_marker + ".peelTarget"):
        raise ValueError("Could not find peelTarget attribute - is this a active marker? " + str(active_marker))

    src = m.listConnections(active_marker + ".peelTarget")
    if len(src) == 0:
        return None
    else:
        return src[0]


def pairs():
    """ returns active markers and their connected source, or none """
    ret = []
    for i in active():
        src = m.listConnections(i + ".peelTarget")
        if len(src) == 0:
            ret.append((i, None))
        else:
            ret.append((i, src[0]))
    return ret


def options_node():
    on = m.objExists('peelSolveOptions')
    if on is not None: return 'peelSolveOptions'
    m.createNode('peelSolveOptions', n='peelSolveOptions')
    return 'peelSolveOptions'
