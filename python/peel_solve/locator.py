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
from peel_solve import roots, node_list


def line(position, parent, attr_type=1):

    """ Create a line locator at the location of position and parent it to parent
    returns (transform, shape) """

    if len(position) == 0:
        raise ValueError("Invalid source node for line locator")

    if not m.objExists(parent):
        raise ValueError("Could not find parent: " + str(parent))

    node = position
    if ':' in node:
        node = node.split(':')[-1]

    if '|' in node:
        node = node.split('|')[-1]

    if len(node) == 0:
        raise ValueError("Invalid source node for line locator: " + str(position))

    node = node + "_Marker"
    shape = node + "Shape"

    # create the node

    ll_transform = m.createNode("transform", n=node, parent=parent)
    ll_shape = m.createNode("peelLocator", n=shape, p=ll_transform)

    if m.nodeType(ll_shape).startswith("unknown"):
        m.delete(ll_shape)
        m.delete(ll_transform)
        raise RuntimeError("Could not create line locator, is the plugin loaded?")

    matrix = m.xform(position, q=True, ws=True, m=True)
    m.xform(ll_transform, ws=True, m=matrix)

    size = None
    if m.ls(position, st=True) == "transform":
        shape = m.listRelatives(position, shapes=True)
        if shape:
            ttype = m.ls(shape[0], st=True)
            if ttype == "peelSquareLocator" and m.objExists(shape[0] + ".size"):
                matrix = m.getAttr(position + ".worldMatrix")
                mag = (matrix[0] + matrix[5] + matrix[10]) / 3
                size = m.getAttr(position + ".size") * 1.1 * mag

    if size is None:
        # use the radius of the joint the marker is being attached to
        if m.ls(parent, st=True) == "joint" and m.objExists(parent + ".radius"):
            size = m.getAttr(parent + ".radius")

    if size <= 0:
        size = 1

    m.setAttr(ll_shape + ".size", size)

    tw = 0.0
    rw = 0.0

    if attr_type is not None:

        add_type_attr(ll_transform, attr_type)

        if attr_type in [1, 3, 4, 5]:
            tw = 1.0

        if attr_type in [2, 3]:
            rw = 1.0

        add_matrix_attr(ll_transform, "peelTarget")
        add_attr(ll_transform, "translationWeight", tw)
        add_attr(ll_transform, "rotationWeight", rw)

        m.connectAttr(ll_transform + ".translationWeight", ll_shape + ".tWeight")
        m.connectAttr(ll_transform + ".rotationWeight", ll_shape + ".rWeight")

        m.connectAttr(position + ".worldMatrix", node + ".peelTarget")

    m.select(ll_transform, r=True)
    return ll_transform, ll_shape


def add_attr(obj, attr, value, at=None, dt=None):

    if at is None and dt is None:
        if isinstance(value, str):
            at = "string"
        if isinstance(value, float):
            at = "double"
        if isinstance(value, bool):
            at = "bool"

    if at is None and dt is None:
        raise ValueError("Could not determine type for attribute")

    if not m.objExists(obj + "." + attr):
        if at:
            m.addAttr(obj, k=True, ln=attr, at=at)
        if dt:
            m.addAttr(obj, k=True, ln=attr, dt=dt)
        m.setAttr(obj + "." + attr, value)
    else:
        m.setAttr(obj + "." + attr, lock=0)


def add_vector_attr(obj, attr, x, y, z):
    if not m.objExists(obj + "." + attr):
        m.addAttr(obj, ln=attr, at="double3")
        m.addAttr(obj, ln=attr + "X", at="double", p=attr)
        m.addAttr(obj, ln=attr + "Y", at="double", p=attr)
        m.addAttr(obj, ln=attr + "Z", at="double", p=attr)
        m.setAttr(obj + "." + attr + "X", x)
        m.setAttr(obj + "." + attr + "Y", y)
        m.setAttr(obj + "." + attr + "Z", z)
    else:
        m.setAttr(obj + "." + attr, lock=False)
        m.setAttr(obj + "." + attr + "X", lock=False)
        m.setAttr(obj + "." + attr + "Y", lock=False)
        m.setAttr(obj + "." + attr + "Z", lock=False)


def add_type_attr(obj, value):
    values = ["passive", "activeTrans", "activeRot", "activeBoth", "sliding", "aim", "line"]
    add_enum_attr(obj, "peelType", values, value)
    m.setAttr(obj + ".peelType", value)


def add_enum_attr(obj, attr, values, value):
    if m.objExists(obj + "." + attr):
        return

    m.addAttr(obj, k=True, ln=attr, at="enum", enumName=":".join(values))
    m.setAttr(obj + "." + attr, value)


def add_matrix_attr(obj, attr):
    if not m.objExists(obj + "." + attr):
        m.addAttr(obj, ln=attr, at="fltMatrix")
    else:
        m.setAttr(obj + "." + attr, lock=False)


def remove_attr(obj, attr):
    if m.objExists(obj + "." + attr):
        m.setAttr(obj + "." + attr, lock=False)
        m.deleteAttr(obj, at=attr)


def add_joint_attributes(joint=None):

    if joint is None:
        selection = m.ls(sl=True)
        if len(selection) != 1:
            raise RuntimeError("Select one thing to add the attributes")

        node = selection[0]

    if not m.objExists(joint):
        raise RuntimeError("Could not find joint: " + str(joint))

    d_attr = ["rotStab", "rotStiff", "lendof", "lengthStiff", "transStiff", "rotShareVal",
              "rotShared", "rotationError", "stabilityError", "translationStiffnessError",
              "rotationStiffnessError", "lengthStiffnessError"]

    # Check if this is a root node
    root = joint in roots.ls()

    add_type_attr(joint, 0)

    tx = m.getAttr(joint + ".translateX")
    ty = m.getAttr(joint + ".translateY")
    tz = m.getAttr(joint + ".translateZ")

    add_vector_attr(joint, "lengthAxis", tx, ty, tz)
    add_attr(joint, "dofX", root)
    add_attr(joint, "doxY", root)
    add_attr(joint, "dofZ", root)
    add_vector_attr(joint, "preferredTrans", tx, ty, tz)

    remove_attr(joint, "peelTarget")
    remove_attr(joint, "translationWeight")
    remove_attr(joint, "rotationWeight")


def transform_attr(attr_type=1):

    """ Adds the transform attributes to a node, or connects if more than one item is selected """

    selection = m.ls(sl=True, l=True)

    if len(selection) == 0:
        raise RuntimeError("Nothing selected")
    if len(selection) == 1:
        add_attributes(attr_type)
    else:
        connect(attr_type, selection)


def connect(attr_type, *selection):

    if len(selection) == 0:
        selection = m.ls(sl=True, l=True)

    if len(selection) < 2:
        raise RuntimeError("Not enough items to create connection %d" % len(selection))

    joint = selection[-1]

    for node in selection[:-1]:

        locator, shape = line(node, joint)
        add_attributes(attr_type, locator)
        m.connectAttr(node + ".worldMatrix[0]", locator + ".peelTarget", f=True)
        if m.objExists(locator + ".translationWeight"):
            m.connectAttr(locator + ".translationWeight", shape + ".tWeight")
        if m.objExists(locator + ".rotationWeight"):
            m.connectAttr(locator + ".rotationWeight", shape + ".rWeight")


def connect_active(source=None, dest=None):

    if source is None or dest is None:
        selection = m.ls(sl=True, l=True)
        if len(selection) != 2:
            raise RuntimeError("Select two things to connect")
        source = selection[0]
        dest = selection[1]

    if not m.objExists(dest + ".peelTarget"):
        raise RuntimeError(dest + " does not have peel attributes")

    if m.getAttr(dest + ".peelTarget", l=True):
        raise RuntimeError(dest + " has locked attributes - cannot connect")

    try:
        m.connectAttr(source + ".worldMatrix[0]", dest + ".peelTarget")
    except RuntimeError as e:
        print("Could not connect: " + str(e))


def select(node_type=None):
    if node_type is None:
        node_type = m.optionVar(q="ov_peelSolveOp_Select")

    root_nodes = roots.ls()

    if node_type == 1:
        m.select(m.peelSolve(s=root_nodes, lt=True, ns=True))

    if node_type == 2:
        m.select(m.peelSolve(s=root_nodes, la=True, ns=True))

    if node_type == 3:
        m.select(m.peelSolve(s=root_nodes, lp=True, ns=True))

    if node_type == 4:
        m.select(m.ls(type="rigidbodyLocator"))
        m.pickWalk(d="up")

    if node_type == 5:
        m.select(m.ls(type="rigidbodyNode"))


def connect_markers():
    """ connects active transforms by name """

    ret = []
    for transform in node_list.active():
        name = transform
        if '|' in name:
            name = name.split('|')[-1]
        if ':' in name:
            name = name.split(':')[-1]

        if '_Marker' not in name:
            print("Skipping node that does not have the suffix _Marker: " + transform)
            continue

        src = name[:name.find('_Marker')]
        con = m.listConnections(transform + ".peelTarget")
        if con and src in con:
            # already connected.
            continue

        if m.objExists(src + ".worldMatrix"):
            m.connectAttr(src + ".worldMatrix", transform + ".peelTarget", f=True)
            print("Connecting: " + str(src) + " to " + str(transform))
            continue

        if '_' in src:
            src = src[src.find('_') + 1:]
            if m.objExists(src + ".worldMatrix"):
                m.connectAttr(src + ".worldMatrix", transform + ".peelTarget", f=True)
                print("Connecting: " + str(src) + " to " + str(transform))
                continue

        print("Skipping, could not find: " + src + " for marker: " + transform)
        ret.append(transform)

    return ret


def normalize_display():

    vals = []

    for locator in m.ls(type="peelLocator", l=True):

        if m.objExists(locator + ".tw"):
            vals.append(m.getAttr(locator + ".tw"))
        if m.objExists(locator + ".rw"):
            vals.append(m.getAttr(locator + ".rw"))

    maxval = max(vals)

    for locator in m.ls(type="peelLocator", l=True):
        m.setAttr(locator + ".normal", maxval)





