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
import math

from maya import mel
import maya.cmds as m

from peel_solve import roots, node_list

""" Runs the maya peelsolver """


def load_plugin():
    """ Loads the PeelSolve plugin """

    if 'peelsolve' in ''.join(m.pluginInfo(q=True, ls=True)).lower():
        return

    ext = None
    os = m.about(os=True)
    if os == "mac":
        ext = "bundle"
    if os == "win":
        ext = "mll"

    if not ext:
        raise RuntimeError("Could not determine OS")

    ver = m.about(v=True)
    m.loadPlugin("peelsolve_" + ver + "_2540." + os)


def go_to_pref_action(sel, trans, rot):
    for j in sel:
        if m.objExists(j + '.peelType') and m.getAttr(j + '.peelType') > 0:
            continue

        if rot:
            for attr in ['X', 'Y', 'Z']:
                if not m.objExists(j + '.jointType' + attr):
                    continue
                if not m.getAttr(j + '.jointType' + attr):
                    continue
                if m.getAttr(j + '.rotateX', lock=True):
                    continue
                val = m.getAttr(j + '.preferredAngle' + attr)
                try:
                    m.setAttr(j + '.rotate' + attr, val)
                except:
                    pass

        if trans:
            for attr in ['X', 'Y', 'Z']:
                if not m.objExists(j + '.preferredTrans' + attr):
                    continue
                val = m.getAttr(j + '.preferredTrans')
                try:
                    m.setAttr(j + '.translate' + attr, val)
                except:
                    pass


def solve_args(solve_type):
    on = node_list.options_node()
    values = {}

    for val in ['start', 'end', 'increment', 'iterations', 'method', 'timeMode', 'debug',
                'reverse', 'statistics', 'rootNodes', 'readDirect', 'scale', 'bothways',
                'refine', 'quat', 'rootfirst', 'gradientSamples', 'threads']:
        values[val] = m.getAttr(on + '.' + val)

    if values['timeMode'] == 0:
        values['start'] = m.playbackOptions(q=True, min=True)
        values['end'] = m.playbackOptions(q=True, max=True)

    if values['scale'] < 0:
        values['scale'] = 1

    if solve_type == 'quick':
        values['refine'] = False
        values['method'] = 0
        values['iterations'] = 50

    if solve_type == 'refine':
        values['refine'] = True

    args = {'scl': values['scale'], 'i': values['iterations'], 'threads': values['threads']}

    if solve_type != 'single':
        args['st'] = values['start']
        args['end'] = values['end']
        args['inc'] = values['increment']

    if values['gradientSamples'] == 0: args['gs'] = 1
    if values['gradientSamples'] == 1: args['gs'] = 2
    if values['gradientSamples'] == 2: args['gs'] = 4

    for a, b in [('debug', 'debug'), ('statistics', 'stat'), ('reverse', 'r'), ('readDirect', 'rd'),
                 ('bothways', 'bw'), ('refine', 'ref'), ('rootfirst', 'rf'), ('quat', 'quat')]:
        if values[a]: args[b] = True

    if values['method'] >= 0 and values['method'] <= 3:
        args['m_cmds'] = values['method']

    return args


def solve(solve_type=None):
    """ Run a solve using the settings defined on the pref node """

    rn = roots.ls()

    if len(rn) == 0:
        m.error("No skeleton top node defined")
        return None

    solve_types = [None, 'quick', 'refine', 'single']
    if solve_type not in solve_types:
        valid_values = 'None,' + ','.join(solve_types[1:])
        msg = "Invalid solve type: %s, valid values: %s" % (str(solve_type), valid_values)
        raise RuntimeError(msg)

    if m.objExists('PEELSNAPLOC_*'):
        ret = m.confirmDialog(t='Confirm', m='The markers may be locked, do you want to continue',
                              b=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if ret == 'No':
            return None

    sels = m.ls(sl=True)

    args = solve_args(solve_type)

    transforms = m.peelSolve(s=rn, lt=True, ns=True)

    delete_keys = m.getAttr("peelSolveOptions.deleteKeys")
    pre_solve_root = m.getAttr("peelSolveOptions.preSolveRoot")
    pre_solve_pose = m.getAttr("peelSolveOptions.preSolvePose")

    if solve_type not in ['single', 'refine']:
        at = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
        if delete_keys == 2:
            m.delete(transforms, channels=True, unitlessAnimationCurves=False, hierarchy='none', at=at)
        elif delete_keys == 1:
            tr = (args['start'], args['end'])
            m.cutKey(transforms, clear=True, time=tr, option='keys', hierarchy='none', at=at)

    if pre_solve_root is True:
        m.peelSolve(s=rn, ro=True)

    if pre_solve_pose is True:
        go_to_pref_not_root()

    # args['e'] = True
    ret = m.peelSolve(s=rn, e=True, **args)

    if solve_type != 'single':
        chan = m.peelSolve(s=rn, ns=True, lc=True)
        m.filterCurve(chan, filter='euler')

    m.select(sels)


def run(iterations=500, inc=1, root_nodes=None, start=None, end=None):
    """
    :param iterations: passed to peelsolve
    :param inc: frame increment
    :param root_nodes: solve roots.  Uses the options node if none are provided.
    :param start: start frame for solve
    :param end: end frame for solve range
    Runs the solver with the specified arguments
    """

    if not root_nodes:
        root_nodes = roots.ls()

    # Run the solve
    m.refresh(su=True)
    try:
        if start is None:
            start = m.playbackOptions(q=True, min=True)
        if end is None:
            end = m.playbackOptions(q=True, max=True)
        root_flag = ' '.join(['-s ' + i for i in root_nodes])
        m.peelSolve(e=root_flag, st=start, end=end, inc=inc, i=iterations)
    finally:
        m.refresh(su=False)


def frame(iterations=500, root_nodes=None):
    """
    :param iterations: passed to peelsolve
    :param root_nodes: solve roots.  Uses the options node if none are provided.
    """

    if not root_nodes:
        root_nodes = roots.ls()

    root_flag = ' '.join(['-s ' + i for i in root_nodes])

    cmd = "peelSolve -e %s -scl 1 -i %d -threads 2 -gs 1 -quat -m_cmds 1;" \
          % (root_flag, iterations)

    print(cmd)
    mel.eval(cmd)

    # mel.eval("peelSolve2Run(4);")


def go_to_pref_not_root():
    rn = roots.ls()
    jnts = m.peelSolve(lp=True, ns=True, s=rn)
    sel = m.ls(sl=True)
    m.select(jnts)
    for r in rn: m.select(r, tgl=True)
    joints = m.ls(sl=True)
    go_to_pref_action(joints, True, True)
    m.select(sel)


def find_char_top():
    root = roots.skel_root()

    while 1:
        up = m.listRelatives(root, p=True)
        if not up:
            break
        root = up

    return root


def set_mocap_range():
    keys = m.keyframe(node_list.all_markers(), q=True)
    start = math.floor(min(keys))
    end = math.ceil(max(keys))
    m.playbackOptions(min=start, max=end, ast=start, aet=end)


def range_selected():
    sel = m.ls(sl=True)
    if sel is None or len(sel) == 0:
        m.confirmDialog(m="Nothing Selected")
        return

    keys = m.keyframe(sel, q=True)
    if keys is None or len(keys) == 0: return
    m.playbackOptions(min=math.floor(min(keys)), max=math.ceil(max(keys)))
