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
from peel_solve import solve, locator, roots, rigidbody, file

import os.path
import os


def scale_hips():

    s = m.getAttr(roots.find_optical_root() + ".sx")
    m.scaleKey(roots.skel_root(), valueScale=1 / s, at=["tx", "ty", "tz"])


def reconnect():
    roots.consolidate_roots()
    locator.connect_markers()
    rigidbody.connect()
    solve.frame()


def find_template(basedir, actor):

    res = []

    actor_dir = os.path.join(basedir, actor)

    for i in os.listdir(actor_dir):
        if i.lower().startswith(actor.lower()):
            res.append(i)

    if len(res) == 0:
        return None

    return os.path.join(actor_dir, sorted(res)[-1])


def build_solve(src_path, template_dir, actors=None):

    """
    :param src_path:     Path to the c3d or fbx file to load the mocap data from
    :param template_dir: Where to find actor templates
    :param actors:       List of actors names to build for.

    called by task_maya.BuildSolve
    called by maya.flux.Gui.build_rot()

    Loads the c3d or fbx file, connects the markers, runs the solve and saves the file

    The actor name must be the prefix of the optical data and also the template file name.  Spaces are converted
    to underscores.

    See find_template() for how the template is found
    """

    solve.load_plugin()

    m.loadPlugin("fbxmaya")

    has_rig = False

    if actors:
        for name in actors:
            t = find_template(template_dir, name.replace(' ', '_'))
            if t:
                if has_rig:
                    m.file(t, i=True)
                else:
                    # Open it so we can get the fps settings, etc
                    m.file(t, o=True)
                    has_rig = True
            else:
                print("Could not find template for: " + name)
                print("Dir: " + template_dir)
    else:
        raise RuntimeError("Not implemented yet")

    if src_path.lower().endswith('.c3d'):
        file.load_c3d(src_path, merge=False)
    elif src_path.lower().endswith('.fbx'):
        file.load_fbx(src_path, [i.replace(' ', '_') for i in actors], merge=False)
    else:
        raise ValueError("Invalid source file: " + src_path)

    if has_rig:
        locator.connect_markers()


def move_to_origin(prefix, hips):

    """ move the optical root so the character is over the origin """

    start = m.playbackOptions(q=True, min=True)
    end = m.playbackOptions(q=True, max=True)

    m.currentTime( start + (end-start) / 2)

    root = roots.find_optical_root()
    m.setAttr(root + ".t", 0, 0, 0)
    m.setAttr(root + ".r", 0, 0, 0)

    rb = rigidbody.create([prefix + i for i in ['RFWT', 'LFWT', 'RBWT', 'LBWT']])

    solve.frame()
    ry = m.getAttr(hips + ".ry")
    m.setAttr(root + ".ry", -ry)

    tx = m.getAttr(root + ".tx") - m.getAttr(rb + ".tx")
    tz = m.getAttr(root + ".tz") - m.getAttr(rb + ".tz")
    m.setAttr(root + ".t", tx, 0, tz)

    m.delete(rb)


def set_range():

    root = roots.find_optical_root()
    if not root:
        print("Could not find root when setting range")
        return None, None

    if not m.objExists(root + ".C3dTimecodeOffset") or not m.objExists(root + ".C3dFrames"):
        print("Could not find attributes when setting range")
        return None, None

    start = m.getAttr(root + ".C3dTimecodeOffset")

    end = start + m.getAttr(root + ".C3dFrames")

    m.playbackOptions(min=start)
    m.playbackOptions(max=end)

    return start, end