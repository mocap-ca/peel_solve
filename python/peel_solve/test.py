import maya.cmds as m
from peel_solve import locator

def load():
    p = r'E:/git/amazon/peelsolve/build_2020/peelsolve2020/Debug/peelsolve2020d.mll'
    m.loadPlugin(p)

def unload():
    m.unloadPlugin("peelsolve2020d.mll");

def simple():

    m.file(f=True, new=True)

    m1 = m.spaceLocator(name="m1")[0]
    m2 = m.spaceLocator(name="m2")[0]
    m3 = m.spaceLocator(name="m3")[0]
    m4 = m.spaceLocator(name="m4")[0]

    m.setAttr(m1 + ".tx", 3)
    m.setAttr(m1 + ".ty", 3)
    m.setAttr(m2 + ".tx", -4)
    m.setAttr(m2 + ".ty", 4)
    m.setAttr(m3 + ".tx", 4)
    m.setAttr(m3 + ".ty", -4)
    m.setAttr(m4 + ".tx", -4)
    m.setAttr(m4 + ".ty", -4)

    m.select(cl=True)
    root = m.joint(name="root")

    locator.line(m1, root, attr_type=5)
    locator.line(m2, root)
    locator.line(m3, root)
    locator.line(m4, root)

    m.setAttr(root + ".tx", 1)
    m.setAttr(root + ".ty", 1)
    m.setAttr(root + ".tz", 1)

    m.setAttr(root + ".rx", 45)
    m.setAttr(root + ".ry", 40)
    m.setAttr(root + ".rz", 45)

    m.setAttr(m1 + ".tx", 4)
    m.setAttr(m1 + ".ty", 4)

    #m.peelSolve(s=root)


def lendof():

    m.file(f=True, new=True)

    j1 = m.joint(name="j1")
    j2 = m.joint(name="j2")

    m.setAttr(j2 + ".tx", 4)

    m1 = m.spaceLocator(name="m1")[0]
    m2 = m.spaceLocator(name="m2")[0]

    m.setAttr(l2 + ".tx", 4)

    locator.line(m1, j1, 3)
    locator.line(m2, j2, 3)

    m.setAttr(m2 + ".tx", 6)


