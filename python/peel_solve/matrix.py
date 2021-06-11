import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import maya.cmds as m
import dag
import sys


def asArray(matrix):
    if type(matrix) is om.MTransformationMatrix: matrix = matrix.asMatrix()
    if not type(matrix) is om.MMatrix:
        return "not a matrix error, type is : " + str(type(matrix))

    ret = []
    for u in range(0, 4):
        for v in range(0, 4):
            ret.append(om.MScriptUtil.getDoubleArrayItem(matrix[u], v))

    return ret


def setAttr(chan, matrix):
    m.setAttr(chan, asArray(matrix), type="matrix")


def getValues(vals):
    if type(vals) is list and len(vals) == 3:
        return vals
    elif type(vals) is om.MVector:
        return [vals.x, vals.y, vals.z]
    else:
        raise TypeError("Expected array[3] or MVector, got " + str(type(vals)))


def scaleMatrix(vals):
    v = getValues(vals)
    util = om.MScriptUtil()
    util.createFromList([v[0], 0, 0, 0,
                         0, v[1], 0, 0,
                         0, 0, v[2], 0,
                         0, 0, 0, 1], 4 * 4)
    return om.MMatrix(util.asDouble4Ptr())


def translationMatrix(vals):
    v = getValues(vals)
    util = om.MScriptUtil()
    util.createFromList([1, 0, 0, 0,
                         0, 1, 0, 0,
                         0, 0, 1, 0,
                         v[0], v[1], v[2], 1], 4 * 4)
    return om.MMatrix(util.asDouble4Ptr())


def getTransformMatrix(item):
    dp = dag.get_mdagpath(item)
    if dp is None: return None
    trans = om.MFnTransform(dp)
    return trans.transformation()


def setTransformMatrix(item, matrix):
    dp = dag.get_mdagpath(item)
    if dp is None: return None
    trans = om.MFnTransform(dp)
    transmat = om.MTransformationMatrix(matrix)
    trans.set(transmat)
    return True


def createLocator(name, matrix, parent=None):
    """ Create a locator and transform it by the matrix """
    tmatrix = None
    if type(matrix) is om.MMatrix: tmatrix = om.MTransformationMatrix(matrix)
    if type(matrix) is om.MTransformationMatrix: tmatrix = matrix
    if tmatrix is None: raise TypeError("Expected Matrix object")

    if parent is not None:
        trans = m.createNode("transform", name=name, parent=parent)
    else:
        trans = m.createNode("transform", name=name)

    m.createNode("locator", name=name + "Shape", parent=trans)
    dloc = dag.get_mdagpath(trans)
    tloc = om.MFnTransform(dloc.transform())
    tloc.set(tmatrix)


def show(m):
    vals = asArray(m)
    for i in range(0, 16):
        sys.stdout.write("%04.4f   " % vals[i])
        if i % 4 == 3: sys.stdout.write("\n");
