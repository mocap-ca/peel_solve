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


def set_roots(root_nodes):

    """ Sets the root nodes in the scene (list) """

    # Set solve params
    if not m.objExists("peelSolveOptions"):
        m.createNode("peelSolveOptions", name="peelSolveOptions")
    m.setAttr("peelSolveOptions.rootNodes", len(root_nodes), *root_nodes, typ="stringArray")


def ls(extend=True):
    """ returns a list of the skeleton root nodes as defined in peelSolveOptions node.
     If extend is true, the roots for all peelsolve nodes will be returned """

    if extend:
        ret = set()
        for i in m.ls(type='peelSolveOptions'):
            try:
                ret.update(set(m.getAttr(i + ".rootNodes")))
            except Exception as e:
                print(str(e))

        return list(ret)
    else:
        if not m.objExists("peelSolveOptions"):
            return []
        return m.getAttr('peelSolveOptions.rootNodes')


def consolidate_roots():

    """ combine the roots in multiple option nodes in to the first """

    all_roots = ls(extend=True)

    for i in m.ls(type='peelSolveOptions'):
        if i != 'peelSolveOptions':
            m.delete(i)

    if len(all_roots) > 0:

        if not m.objExists('peelSolveOptions'):
            m.createNode('peelSolveOptions', name='peelSolveOptions')

        m.setAttr('peelSolveOptions.rootNodes', len(all_roots), *list(all_roots), type='stringArray')


def find_optical_root():

    """ Returns the best guess for the mocap (optical) root """

    # Moving forward this should be the authority.  The other techniques are fallbacks only for old scenes.
    root_shapes = m.ls(type="peelOpticalRoot")
    if root_shapes:
        return m.listRelatives(root_shapes[0], parent=True)[0]

    # look for the most common parent of peelSquareLocator nodes
    root = find_root_from_parenting()
    if root:
        return root

    # look for what the active markers are connected to
    root = find_root_from_active()
    if root:
        return root

    return None


def find_root_from_active():
    """ returns the top node of the mocap data (optical root) """
    for loc in m.ls(type='peelLocator'):
        transform = m.listRelatives(loc, p=True)[0]
        if m.objExists(transform + ".peelTarget"):
            con = m.listConnections(transform + ".peelTarget")
            if not con:
                continue
            for marker in con:
                parent = m.listRelatives(marker, parent=True)
                if parent is not None:
                    return parent[0]

    return None


def find_root_from_parenting():
    """ return the most common parent of peelSquareLocator nodes """
    res = []
    for loc in m.ls(type='peelSquareLocator'):
        parent1 = m.listRelatives(loc, p=True)
        parent2 = m.listRelatives(parent1[0], p=True)
        if parent2:
            res.append(parent2[0])

    if len(res) == 0:
        return None

    return max(set(res), key=res.count)


def skel_root(extend=True):
    """ Returns the first root node, or None """
    r = ls(extend=extend)
    if not r:
        return None
    return r[0]
