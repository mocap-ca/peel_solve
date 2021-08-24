import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
from peel_solve import matrix, dag


def getJoint(name):
	dp = dag.get_mdagpath(name)
	if dp is None: return None
	if not dp.hasFn(om.MFn.kJoint): return None
	return oma.MFnIkJoint(dp)

class PeelJoint:
	def __init__(self, name):

		joint = getJoint(name)
		if joint is None:
			return

		dp = dag.get_mdagpath(name)

		util=om.MScriptUtil()
		util.createFromList( [0.0, 0.0, 0.0], 3)
		double3 = util.asDoublePtr()

		# scale
		joint.getScale(double3)
		scale = om.MVector(double3)
		self.scale = scale

		# rotateOrient
		preOrientation = om.MQuaternion()
		joint.getScaleOrientation(preOrientation)
		self.preOrientation = preOrientation

		# prematrix = scale * preOrientation
		preMatrix = matrix.scaleMatrix(scale)
		preMatrix *= preOrientation.asMatrix()
		self.pre = preMatrix

		# rotation
		rotation = om.MEulerRotation()
		joint.getRotation(rotation)
		self.rotation = om.MEulerRotation(rotation)

		# orientation
		orientation = om.MQuaternion()
		joint.getOrientation(orientation)
		self.orientation = om.MQuaternion(orientation)

		# parent inverse scale
		self.postInverse = None

		if dp.length() > 1:
			dp.pop()
			if dp.hasFn(om.MFn.kJoint):
				parentJoint = oma.MFnIkJoint(dp)
				parentJoint.getScale(double3)
				x = om.MScriptUtil().getDoubleArrayItem(double3, 0)
				y = om.MScriptUtil().getDoubleArrayItem(double3, 1)
				z = om.MScriptUtil().getDoubleArrayItem(double3, 2)
				if x == 0 or y == 0 or z == 0 : raise ValueError("Zero Value for inverse scale")
				self.postInverse = om.MVector(1/x,1/y,1/z)
			
		# postMatrix = orientation * inverseScale
		postMatrix = orientation.asMatrix()
		if self.postInverse is not None:
			postMatrix *= matrix.scaleMatrix(self.postInverse)
		self.post = postMatrix

		# translation
		self.translation = om.MVector(joint.getTranslation(om.MSpace.kTransform))

	def __str__(self):
		x = ["Scale:         " + dag.show(self.scale),
             "PreOri:        " + dag.show(self.preOrientation),
			 "Pre:           ", dag.show(self.pre),
			 "Rotation:      " + dag.show(self.rotation),
			 "Orientation:   " + dag.show(self.orientation),
			 "Inverse Scale: " + dag.show(self.postInverse),
			 "Post:          ", dag.show(self.post),
			 "Translation:   " + dag.show(self.translation) ]

		return "\n".join(x)

	def asMatrix(self):
		m = self.pre  # scale, scaleOrient
		m *= self.rotation.asMatrix() 
		m *= self.post # jointOrient, parentInverseScale
		m *= matrix.translationMatrix(self.translation)
		return m
