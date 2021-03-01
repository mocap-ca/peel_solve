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

from maya import mel
import maya.cmds as m


def create():

    main_window = mel.eval("string $s = $gMainWindow")
    anim_menu = mel.eval("string $sa[]= $gAnimationMenus")

    m.setParent(main_window)

    ps = "import peel_solve.solve as ps;"
    loc = "import peel_solve.locator as loc;"
    sel = "import peel_solve.select as sel;"

    level = m.peelSolve(level=True)

    menu_index = None

    for i, item in enumerate(anim_menu):
        if item.endswith("PeelSolve2"):
            menu_index = i
            break

    if menu_index is None:
        new_menu = m.menu("PeelSolve", label="PeelSolve", tearOff=True, allowOptionBoxes=True)
        mel.eval('$gAnimationMenus[%d]="%s"' % (len(anim_menu), new_menu))

        m.menuItem(label="Set Root", command=loc + "loc.connect(1)")
        m.menuItem(label="Reconnect Mocap Root", command=loc + "loc.connect_markers()")
        m.menuItem(d=True)
        m.menuItem(label="Solve Single Frame", command=ps + "ps.frame()")
        m.menuItem(label="Solve All Frames", command=ps + "ps.solve()")
        m.menuItem(label="Refine All Frames", command=ps + "ps.solve('refine')")
        m.menuItem(d=True)
        m.menuItem(label="Select", command=sel + "sel.select()")
        m.menuItem(ob=True, command=sel + "sel.options()")
        m.menuItem(label="Select By", subMenu=True)
        m.menuItem(label="Select All", command=sel + "sel.select(1)")
        m.menuItem(label="Select Active", command=sel + "sel.select(2)")
        m.menuItem(label="Select Passive", command=sel + "sel.select(3)")
        m.menuItem(label="Select Rigidbodies", command=sel + "sel.select(4)")
        m.menuItem(label="Select RB Nodes", command=sel + "sel.select(5)")
        m.setParent("..", menu=True)

        m.menuItem(label="Set Selected", subMenu=True)
        m.menuItem(label="Passive", command=loc + "loc.add_attributes(0)")
        m.menuItem(label="Position", command=loc + "loc.add_attributes(1)")
        if level > 99:
            m.menuItem(label="Rotation", command=loc + "loc.add_attributes(2)")
            m.menuItem(label="Both", command=loc + "loc.add_attributes(3)")
            m.menuItem(label="Slide", command=loc + "loc.add_attributes(4)")
            m.menuItem(label="Aim", command=loc + "loc.add_attributes(5)")
        m.setParent("..", menu=True)

        m.menuItem(label="Normalize Marker Display", command=loc + "loc.normalize_display()")
        m.menuItem(label="Set Marker Properties", stp="mel", command="peelSolve2SetMarkerSize();")
        m.menuItem(label="Refresh Marker Attributes", stp="mel", command="peelSolve2RefreshMarkers();")
        m.menuItem(label="Lock Markers", stp="mel", command="peelSolve2LockMarkers();")
        m.menuItem(label="Unlock Markers", stp="mel", command="peelSolve2UnLockMarkers();")
        m.menuItem(label="Reset Markers", stp="mel", command="peelSolve2ResetMarkers();")

        m.menuItem(d=1)
        m.menuItem(label="Set Default Pose", stp="mel", command="peelSolve2SetPref();")
        m.menuItem(label="Go to Default Pose", stp="mel", command="peelSolve2GoToPref();")
        m.menuItem(ob=True, stp="mel", command="peelSolve2GoToPrefOp();")
        m.menuItem(label="Graph Errors", stp="mel", command="peelSolve2Graph();")

        m.menuItem(label="Filter", command="peelFilterRun()")
        m.menuItem(ob=True, command="peelFilterOp()")

        m.menuItem(d=1)

        m.menuItem(ob=True, command="peelSolve2RunOp()")

        mnu = "import peel_solve.menu as mnu"
        m.menuItem(label="Recreate Shelf", command=mnu + "mnu.shelf()")
        m.menuItem(label="About", command="peelSolve2About();")

    if m.shelfLayout("peelSolve2", exists=True):
        m.addNewShelfTab("PeelSolve2")

    top_level = mel.eval("string $s = $gShelfTopLevel")

    children = m.shelfLayout(top_level + "|PeelSolve2", q=True, ca=True)
    if len(children) > 0:
        m.deleteUI(children)

    m.shelfButton(l="Make joint active: position", c=loc+"loc.connect(1)", i1="peelSolvePos.xpm", p="PeelSolve2")
    if level > 99:
        m.shelfButton(l="Make joint active: orientation", c=loc+"loc.connect(2)", i1="peelSolveOri.xpm", p="PeelSolve2")
        m.shelfButton(l="Make joint active: both", c=loc+"loc.connect(3)", i1="peelSolveBoth.xpm", p="PeelSolve2")
        m.shelfButton(l="Make joint active: slide", c=loc+"loc.connect(4)", i1="peelSolveSlide.xpm", p="PeelSolve2")
        m.shelfButton(l="Make joint active: aim", c=loc+"loc.connect(5)", i1="peelSolveAim.xpm", p="PeelSolve2")

    m.shelfButton(l="Connect Active Transform", c=loc+"loc.connect_active()", i1="peelSolveLink.xpm", p="PeelSolve2")

    m.shelfButton("Make joint passive",            c=loc + "loc.add_attributes(0)",  i1="peelSolveJointAttr.xpm",     p="PeelSolve2")
    m.shelfButton("Select affected Joints",     stp="mel",   c="peelSolve2Select()",           i1="peelSolveJointSel.xpm",      p="PeelSolve2")
    m.shelfButton("Set default pose",            stp="mel",  c="peelSolve2SetPref()",          i1="peelSolveSetDefault.xpm",    p="PeelSolve2")
    m.shelfButton("Move selected to default pose", stp="mel",c="peelSolve2GoToPref()",         i1="peelSolveGetDefault.xpm",    p="PeelSolve2")
    m.shelfButton("Create rigidbody",           stp="mel", c="peelSolve2RigidBody())",          i1="peelSolveRigidBody.xpm",     p="PeelSolve2")
    m.shelfButton("Lock markers",                stp="mel",c="peelSolve2LockMarkers()",         i1="peelSolveLockMarkers.xpm",   p="PeelSolve2")
    m.shelfButton("Unlock markers",             stp="mel", c="peelSolve2UnLockMarkers()",       i1="peelSolveUnLockMarkers.xpm", p="PeelSolve2")
    m.shelfButton("Remove marker offsets",     stp="mel",  c="peelSolve2ResetMarkers()",        i1="peelSolveResetMarkers.xpm",  p="PeelSolve2")
    m.shelfButton("Set transform root",        stp="mel",  c="peelSolve2RootNodeSelector()",    i1="peelSolveSetSkeleton.xpm",   p="PeelSolve2")
    m.shelfButton("Solve single frame",        c=ps+"ps.frame()",          i1="peelSolveFrame.xpm",         p="PeelSolve2")
    m.shelfButton("Preview solve frame range", c=ps+"ps.solve('quick')",   i1="peelSolveRunPreview.xpm",    p="PeelSolve2")
    m.shelfButton("Solve frame range",         c=ps+"ps.solve()",   i1="peelSolveRun.xpm",           p="PeelSolve2")
    m.shelfButton("Refine previous solve",     c=ps+"ps.solve('refine')",  i1="peelSolveRunRefine.xpm",     p="PeelSolve2")
    m.shelfButton("Solver Options",            stp="mel",  c="peelSolve2RunOp()",               i1="peelSolveOptions.xpm",       p="PeelSolve2")
    m.shelfButton("Script Job On",             stp="mel",  c="peelSolve2ScriptJobOn()",         i1="peelSolveOn.xpm",            p="PeelSolve2")
    m.shelfButton("Script Job Off",            stp="mel",  c="peelSolve2ScriptJobOff()",        i1="peelSolveOff.xpm",           p="PeelSolve2")






