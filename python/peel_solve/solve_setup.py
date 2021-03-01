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
from maya import mel
import solve
from peel_solve import locator, roots, rigidbody

""" Collection of utilities for creating a solve setup"""


def four_points(joint, rb):

    """ Constrain a joint to a rigibody by using 4 markers """

    def name(node):
        if ':' in node: node = node.split(':')[-1]
        if '|' in node: node = node.split('|')[-1]
        return node

    rb_name = name(rb)
    east = m.spaceLocator(name=rb_name + "_east")[0]
    m.parent(east, joint)
    m.setAttr(east + ".tx", 0)
    m.setAttr(east + ".ty", 0)
    m.setAttr(east + ".tz", 20)

    west = m.spaceLocator(name=rb_name + "_west")[0]
    m.parent(west, joint)
    m.setAttr(west + ".tx", 0)
    m.setAttr(west + ".ty", 0)
    m.setAttr(west + ".tz", -20)

    north = m.spaceLocator(name=rb_name + "_north")[0]
    m.parent(north, joint)
    m.setAttr(north + ".tx", 20)
    m.setAttr(north + ".ty", 0)
    m.setAttr(north + ".tz", 0)

    south = m.spaceLocator(name=rb_name + "_south")[0]
    m.parent(south, joint)
    m.setAttr(south + ".tx", -20)
    m.setAttr(south + ".ty", 0)
    m.setAttr(south + ".tz", 0)

    for i in [north, south, east, west]:
        m.parent(i, rb)
        m.select([i, joint])
        mel.eval("peelSolve2TransformAttr(1);")


def midpoint(nodes, prefix=""):
    #res = [m_cmds.getAttr(prefix + i + ".t")[0] for i in nodes]
    res = [m.xform(prefix + i, q=True, ws=True, t=True) for i in nodes]
    res = [sum(i) for i in zip(*res)]
    return [i / len(nodes) for i in res]


def move_to_origin(prefix):
    # TODO: This doesn't work with scaled data
    global HIPS
    oroot = roots.ls()
    m.setAttr(oroot + ".t", 0, 0, 0)
    n = midpoint(HIPS, prefix)
    m.setAttr(oroot + ".t", -n[0], 0, -n[2])


def fit_legs(skel, marker):

    m.setAttr(skel + 'Hips.t', l=True)
    for i in ['Hips', 'RightLeg', 'RightFoot', 'LeftLeg', 'LeftFoot']:
        m.setAttr(skel + i + '.r', l=True)

    mkr = []

    ret = locator.connect(1, marker + "RTOE", skel + "RightFoot")
    m.setAttr(ret + '.t', 18, -7, 0)
    mkr.append(ret)

    ret = locator.connect(1, marker + "RHEL", skel + "RightFoot")
    m.setAttr(ret + '.t', -7, 3.5, 0)
    mkr.append(ret)

    ret = locator.connect(1, marker + "LTOE", skel + "LeftFoot")
    m.setAttr(ret + '.t', 18, -7, 0)
    mkr.append(ret)

    ret = locator.connect(1, marker + "LHEL", skel + "LeftFoot")
    m.setAttr(ret + '.t', -7, 3.5, 0)
    mkr.append(ret)

    solve.frame(root_nodes=[skel + 'Hips'])

    m.setAttr(skel + 'Hips.t', l=False)
    for i in ['Hips', 'RightLeg', 'RightFoot', 'LeftLeg', 'LeftFoot']:
        m.setAttr(skel + i + '.r', l=False)

    m.delete(mkr)


def strip_left(source, value):
    """ if source is prefixed with value, return value with that prefix removed, otherwise return value """
    if value is None or not source.startswith(value):
        return source
    return source[len(value):]


def data(root, strip_marker=None, strip_joint=None):
    """ serialize the solve settings for the given root node """

    all_data = {}

    active_list = []
    all_data['active'] = active_list

    # Active Markers

    for activeMarker in m.peelSolve(s=root, la=True):

        marker_name = activeMarker
        if '|' in marker_name: marker_name = marker_name.split('|')[-1]
        if ':' in marker_name: marker_name = marker_name.split(':')[-1]

        source = m.listConnections(activeMarker + ".peelTarget", s=True, d=False)
        if source is None or len(source) == 0:
            # marker is not connected - this may because we are parsing a template file
            m.warning("unconnected marker: " + str(activeMarker))
            source = marker_name
            if source.endswith('_Marker'):
                source = source[:-7]
        else:
            source = source[0]

        parent = m.listRelatives(activeMarker, p=True)[0]

        data = {'marker': strip_left(marker_name, strip_marker),
                'marker_raw': marker_name,
                'source': strip_left(source, strip_marker),
                'source_raw': source,
                'parent': strip_left(parent, strip_joint),
                'parent_raw': parent,
                'peelType': m.getAttr(activeMarker + ".peelType"),
                'tWeight': m.getAttr(activeMarker + ".translationWeight"),
                'rWeight': m.getAttr(activeMarker + ".rotationWeight")}

        if m.objExists(source):
            rigidbody_node = rigidbody.from_active(source)

            if rigidbody_node:
                # the marker is connect to a rigidbody - get the details for that

                rbdata = []
                for index in m.getAttr(rigidbody_node + ".input", mi=True):

                    # for each marker in the rigidbody_node
                    ch = "[%d]" % index
                    rb_source = m.listConnections(rigidbody_node + ".input" + ch, s=True, d=False)
                    if rb_source is None or len(rb_source) == 0:
                        rb_local = m.listConnections(rigidbody_node + ".local" + ch, s=True, d=False)
                        if rb_local is None or len(rb_local) == 0:
                            raise RuntimeError("Disconnected local rigidbody: " + str(rigidbody_node))
                        rb_source = rb_local[0]
                        if rb_source.endswith('_Marker'):
                            rb_source = rb_source[:-7]
                        m.warning("Disconnected rigidbody: " + str(rigidbody_node))

                    rb_weight = m.getAttr(rigidbody_node + ".weight" + ch)
                    rb_source_stripped = strip_left(rb_source[0], strip_marker)
                    rbdata.append((rb_source_stripped, rb_weight))
                data['rigidbody'] = rbdata

        active_list.append(data)

    # Rotation stiffness (passive markers)

    rotstiff = {}
    for passiveTransform in m.peelSolve(s=root, lp=True, ns=True):
        if m.objExists(passiveTransform + ".rotStiff"):
            marker_name = passiveTransform
            if '|' in marker_name: marker_name = marker_name.split('|')[-1]
            if ':' in marker_name: marker_name = marker_name.split(':')[-1]
            stiff = m.getAttr(passiveTransform + ".rotStiff")
            px = m.getAttr(passiveTransform + '.preferredAngleX')
            py = m.getAttr(passiveTransform + '.preferredAngleY')
            pz = m.getAttr(passiveTransform + '.preferredAngleZ')
            rotstiff[marker_name] = (stiff, px, py, pz)

    all_data['rotstiff'] = rotstiff

    return all_data


def findTransform( name ):

    """ returns the node skipping, hik joints """

    ret = []
    for node in m.ls(name)  :
        if m.nodeType(node) == 'hikFKJoint': continue
        ret.append(node)
    return ret


def connect(src, dst, peelType, tWeight, rWeight):
    """ connect a marker to a target """

    lineLoc = mel.eval('peelSolve2CreateLineLocator("%s", "%s")' % (src, dst))
    mel.eval('peelSolve2CreateTransform({"%s"}, %d)' % (lineLoc[0], peelType))

    m.connectAttr(src + ".worldMatrix[0]", lineLoc[0] + ".peelTarget")

    if m.objExists(lineLoc[0] + ".translationWeight"):
        m.connectAttr(lineLoc[0] + ".translationWeight", lineLoc[1] + ".tWeight")
        m.setAttr(lineLoc[0] + ".translationWeight", tWeight)

    if m.objExists(lineLoc[0] + ".rotationWeight"):
        m.connectAttr(lineLoc[0] + ".rotationWeight", lineLoc[1] + ".rWeight")
        m.setAttr(lineLoc[0] + ".rotationWeight", rWeight)

    print("Connected: %s to %s  type: %d  tw: %f  rw: %f" % (src, dst, peelType, tWeight, rWeight))

    return lineLoc


def connect_data(data, prefix='', namespace=''):
    """ Reconnect the serialized data - see data() """

    if len(namespace) > 0 and namespace[-1] != ':':
        namespace += ":"

    for active in data['active']:
        if 'rigidbody' in active:
            m.select([prefix + i[0] for i in active['rigidbody']])
            rbn = mel.eval("peelSolve2RigidBody();")
            rbt = m.listConnections(rbn + ".OutputTranslation", s=False, d=True)[0]
            src = rbt
        else:

            src = findTransform(prefix + active['source'])
            if not src:
                print("Could not find source for : " + prefix + active['source'])
                continue
            src = src[0]
        dst = findTransform(namespace + active['parent'])
        if not dst:
            raise RuntimeError("Cannot find: " + namespace + active['parent'])
        connect(src, dst[0], active['peelType'], active['tWeight'], active['rWeight'])


def create_setup(marker_prefix, skeleton_prefix):
    """ 
    :param marker_prefix: The prefix to the markers
    :param skeleton_prefix: The prefix to the joints
    Connect the markers to the joints using the global CONNECTIONS relationships
    TODO: use a json file instead
    """
    import maya.mel as mel

    for k, v in CONNECTIONS.iteritems():
        markers = [marker_prefix + i for i in v if m.objExists(marker_prefix + i)]
        m.select(*(markers + [skeleton_prefix + k]))
        mel.eval('peelSolve2TransformAttr(1);')

    ps.set_roots([ skeleton_prefix + "Hips"])
