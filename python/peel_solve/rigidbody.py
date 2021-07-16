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


from __future__ import print_function
import maya.cmds as m
from peel_solve import vector, locator
import json
import os.path

def create(nodes=None):

    """ Creates a rigidbody from nodes, or the current selection if nodes is None
    @returns: transform, node, [locators]
    """

    if nodes is None:
        nodes = m.ls(sl=True, l=True)

    if len(nodes) < 2:
        raise RuntimeError("Please select at least two nodes, three or more is best")

    v = vector.VectorList([vector.Vector(i) for i in nodes])

    rbt = m.group(em=True, n="rigidBodyLocator")
    rbt = '|' + rbt
    rb_shape = m.createNode("rigidbodyLocator", p=rbt, n="rigidBodyLocator_shape")
    v.average().apply(rbt)

    rbn = m.createNode("rigidbodyNode", n="rbn")

    locators = []

    for i, node in enumerate(nodes):

        line_locator, line_locator_shape = locator.line(node, rbt)
        rbn_name = line_locator
        if '|' in rbn_name:
            rbn_name = rbn_name.split('|')[-1]
        line_locator = m.rename(line_locator, "RB_" + rbn_name)
        locators.append(line_locator)
        m.addAttr(line_locator, ln="weight", at="double")
        m.setAttr(line_locator + ".weight", e=True, keyable=True)
        m.setAttr(line_locator + ".weight", 1)
        m.connectAttr(line_locator + ".translate", rbn + ".local[%d]" % i, f=True)
        m.connectAttr(line_locator + ".weight", rbn + ".weight[%d]" % i, f=True)
        m.connectAttr(node + ".worldMatrix", rbn + ".input[%d]" % i, f=True)
        m.connectAttr(line_locator + ".translate", rb_shape + ".points[%d]" % i, f=True)
        m.connectAttr(line_locator + ".weight", line_locator + ".tWeight", f=True)

    m.connectAttr(rbn + ".OutputTranslation", rbt + ".translate")
    m.connectAttr(rbn + ".OutputRotation", rbt + ".rotate")

    m.refresh()

    return rbt, rbn, locators


def ls(all=False):

    """ Returns unbaked rigidbodies """
    
    if all:
        # For each rididbody shape node, find the transform
        nodes = []
        for shape in m.ls(type="rigidbodyLocator", l=True):
            yield m.listRelatives(shape, p=True, f=True)[0]
    
    for rigidbody in m.ls(type="rigidbodyNode"):
        con = m.listConnections(rigidbody + ".OutputTranslation", d=True, s=False)
        if con:
            yield con[0]


def serialize():

    ret = {}

    for rb in ls(all=True):
        points = []
        for child in m.listRelatives(rb, f=True, c=True, type="transform"):
            name = child.split('|')[-1]
            if name.startswith("RB_") and name.endswith("_Marker"):
                tr = m.getAttr(child + ".t")[0]
                w = m.getAttr(child + ".weight")
                source = name[3:-7]

                points.append((child, tr, w, source))
        rb_name = rb
        if '|' in rb_name:
            rb_name = rb_name.split('|')[-1]
        ret[rb_name] = points

    return ret


def save(file_path=None):

    if file_path is None:
        sn = m.file(sn=True, q=True)
        file_path = sn[:sn.rfind('.')] + ".peel"

    data = serialize()

    fp = open(file_path, "w")
    json.dump({'rigidbodies': data}, fp, indent=4)
    fp.close()

    print(file_path.replace("/", "\\"))




def from_active(active_node):

    """ return the rigidbody node associated with the rigidbody active node """

    driven_by = m.listConnections(active_node + ".t", s=True, d=False)
    if driven_by is None or len(driven_by) == 0:
        return None

    if m.nodeType(driven_by[0]) == 'rigidbodyNode':
        return driven_by[0]

    return None


def source_name(rb_local):

    """ based on the given rigidbody locator, guess the source name """

    if '|' in rb_local:
        rb_local = rb_local.split('|')[-1]

    if rb_local.startswith("RB_"):
        rb_local = rb_local[3:]

    if rb_local.endswith("_Marker"):
        rb_local = rb_local[:-7]

    if not m.objExists(rb_local) and ':' in rb_local:
        rb_local = rb_local.split(':')[-1]

    if rb_local.startswith("RB_"):
        rb_local = rb_local[3:]

    return rb_local


def connect():

    """ Reconnect the rigidbody to the mocap data, by name """

    for rigidbody in m.ls(type="rigidbodyNode"):

        for index in m.getAttr(rigidbody + ".input", mi=True):
            ch = "[%d]" % index
            rb_source = m.listConnections(rigidbody + ".input" + ch, s=True, d=False)
            if rb_source:
                print("Skipping connected: " + str(rb_source))
                print("    to: " + str(rb_source))
                continue

            rb_local = m.listConnections(rigidbody + ".local" + ch, s=True, d=False)[0]

            source = source_name(rb_local)

            if m.objExists(source):
                print("Connecting: " + source + " to " + rigidbody + ".input" + ch)
                m.connectAttr(source + ".worldMatrix[0]", rigidbody + ".input" + ch)
            else:
                print("Cannot find source for: " + str(rb_local))


def unbake(nodes=None):

    """ Reconnects the rigidbody markers to the source data """

    if nodes is None:
        nodes = []
        # For each rididbody shape node, find the transform
        for shape in m.ls(type="rigidbodyLocator", l=True):
            nodes.append(m.listRelatives(shape, p=True, f=True)[0])
        if not nodes:
            print("No rigidbodies found")
            return
    elif isinstance(nodes, basestring):
            nodes = [nodes]

    for rbt in nodes:

        src = m.listConnections(rbt + ".t")
        if src:
            for i in src:
                print(i, m.nodeType(i))
                if m.nodeType(i) == "rigidbodyNode":
                    m.delete(i)

        m.delete(rbt, channels=True)

        if not m.listConnections(rbt + ".t"):

            rbn = m.createNode("rigidbodyNode", n="rbn")

            i = 0

            for c in m.listRelatives(rbt, c=True, type="transform", f=True):
                if not c.endswith("_Marker"):
                    print("Not a node: " + c)
                    continue

                source = source_name(c)

                if m.objExists(source):
                    print("connecting " + str(source) + " to " + c)

                    m.connectAttr(c + ".translate", rbn + ".local[%d]" % i, f=True)
                    m.connectAttr(c + ".weight", rbn + ".weight[%d]" % i, f=True)
                    m.connectAttr(source + ".worldMatrix", rbn + ".input[%d]" % i, f=True)
                    i += 1

                else:
                    print("Could not find source for marker: " + c)

            m.connectAttr(rbn + ".OutputTranslation", rbt + ".translate")
            m.connectAttr(rbn + ".OutputRotation", rbt + ".rotate")


def fetch(rbn):
    if not m.objExists(rbn):
        raise RuntimeError("Object does not exist: " + rbn)

    if not m.nodeType(rbn) != 'rigidbodyLocator':
        raise RuntimeError("Object is not a rigidbody: " + rbn)

    # inputs and weights
    src = []
    sz = m.getAttr(rbn + ".input", s=True)
    for i in range(sz):
        c = m.listConnections(rbn + ".input[%d]" % i)

        if c is None or len(c) == 0:
            continue

        w = m.getAttr(rbn + ".weight[%d]" % i)

        src.append((c[0], w))

    return src


def bake():

    """ Bakes all the rigidbodies in the scene """

    locs = ls()

    if not locs:
        return

    for i in m.ls(type="imagePlane"):
        m.setAttr(i + ".displayMode", 0)

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    try:
        m.refresh(suspend=True)
        m.bakeResults(locs, sm=True, t=(start, end), sb=1, dic=True, pok=True, sac=False,
                      at=('rx', 'ry', 'rz', 'tx', 'ty', 'tz'))
    finally:
        m.refresh(suspend=False)

    m.delete(m.ls(type="rigidbodyNode"))
