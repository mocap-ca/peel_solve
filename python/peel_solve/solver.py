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


from peel.core import joint as pj, matrix as pm

import maya.cmds as m


def child_markers(joint):
    """ returns a generator of (transform, shape, connected marker """
    for i in m.listRelatives(joint, c=True, f=True):
        for j in m.listRelatives(i, c=True, f=True):
            if m.nodeType(j) == "peelLocator":
                con = m.listConnections(i + ".peelTarget", s=True, d=False)
                if con:
                    yield i, j, con[0]


class Solver(object):
    def __init__(self, node_name="PeelSolve"):
    
        """ Creates a peel solve node  """
        
        self.solver = m.createNode("PeelSolve", name=node_name)
        m.setAttr(self.solver + ".iterations", 400)
        self.items = []
        self.dict = {}
        self.current_id = 0

    def add_v2_joint(self, joint, parent_id, doft=False, dofr=True):

        jid = self.add_joint(joint, parent_id, doft, dofr)

        for transform, shape, source in child_markers(joint):
            m.setAttr(shape + ".type", 0)
            xid = self.add_locator(transform, jid)
            self.connect_constraint(xid, shape)
            m.connectAttr(source + ".worldMatrix", shape + ".target", f=True)

        return jid

    def add_joint(self, joint_name, parent_id, doft=False, dofr=True):
    
        """ creates the dag connections from joint_name to the solver node, returns the id

         The following attributes are set:

             solver.inputs[#].pre  = jnt.pre translation matrix
             solver.inputs[#].post = jnt.post translation matrix
             solver.inputs[#].dt   = jnt.translation
             solver.inputs[#].dr   = jnt.rotation

        The following connections are made (i.e. the outputs of the solve)

            solver.translation[#] -> joint_name.t
            solver.rotation[#]    -> joint_name.r

        """
        
        jnt = pj.peelJoint(joint_name)
        node_id = self.add_item(joint_name, parent_id, doft, dofr)
        self.current_id = self.current_id + 1
        pm.setAttr(self.solver + ".inputs[%d].pre" % node_id, jnt.pre)
        pm.setAttr(self.solver + ".inputs[%d].post" % node_id, jnt.post)
        m.setAttr(self.solver + ".inputs[%d].dt" % node_id, jnt.translation.x, jnt.translation.y, jnt.translation.z)
        m.setAttr(self.solver + ".inputs[%d].dr" % node_id, jnt.rotation.x, jnt.rotation.y, jnt.rotation.z)
        m.connectAttr(self.solver + ".translation[%d]" % node_id, joint_name + ".t", f=True)
        m.connectAttr(self.solver + ".rotation[%d]"  % node_id, joint_name + ".r", f=True)
        return node_id

    def add_locator(self, locator_name, parent_id):
    
        """ creates the dag connections from the locator (t/r) and returns the id

        The following attributes are set:
            solver.inputs[#].dt = locator_name.translate
            solver.inputs[#].dr = locator_name .rotate

        """
        
        tr = m.getAttr(locator_name + ".translate")[0]
        ro = m.getAttr(locator_name + ".rotate")[0]

        print "Adding locator: " + locator_name
        node_id = self.add_item(locator_name, parent_id, False, False)
        m.setAttr(self.solver + ".inputs[%d].dt" % node_id, *tr)
        m.setAttr(self.solver + ".inputs[%d].dr" % node_id, *ro)
        #m_cmds.connectAttr( locatorName + ".t", self.solver + ".inputs[%d].dt" % id )
        #m_cmds.connectAttr( locatorName + ".r", self.solver + ".inputs[%d].dr" % id )
        return node_id

    def add_item(self, item_name, parent_id, doft=True, dofr=False) :
    
        """ Adds the node to the system.  This can be a joint or a local definition of a marker.  Constraints
            are then added to tell the solver to generate error

        :param item_name:  name of the node in maya to add, can be a full dag path
        :param parent_id:  the id of the parent, or -1 for a root
        :param doft:  translation dof.  Bool, or (Bool, Bool, Bool)
        :param dofr:  rotation dof.  Bool, or (Bool, Bool, Bool)
        :return: the id of this item

        The following connections are made:
           item.message -> solver.inputs[#].ref

        The following attributes are set:
           solver.inputs[#].parentId = parent_id
           solver.inputs[#].name     = name
           solver.inputs[#].doftX    = doft
           solver.inputs[#].dofrX    = dofr

        """
        
        node_id = len(self.items)
        m.connectAttr(item_name + ".message", self.solver + ".inputs[%d].ref" % node_id)
        
        ch = self.solver + ".inputs[%d]" % node_id

        print "Setting : ", ch + ".parentId", parent_id
        m.setAttr(ch + ".parentId", parent_id)
        
        print "Setting",  ch + ".name", " to ", item_name
        m.setAttr(ch + ".name", item_name, type="string")

        print "Setting doft"
        if isinstance(doft, bool):
            m.setAttr(ch + ".var.doftx", int(doft))
            m.setAttr(ch + ".var.dofty", int(doft))
            m.setAttr(ch + ".var.doftz", int(doft))
        elif isinstance(doft, tuple) or isinstance(doft, list):
            m.setAttr(ch + ".var.doftx", int(doft[0]))
            m.setAttr(ch + ".var.dofty", int(doft[1]))
            m.setAttr(ch + ".var.doftz", int(doft[2]))
        else:
            raise ValueError("Invalid type for doft: " + str(type(doft)))

        print "Setting dofr"
        if isinstance(doft, bool):
            m.setAttr(ch + ".var.dofrx", int(dofr))
            m.setAttr(ch + ".var.dofry", int(dofr))
            m.setAttr(ch + ".var.dofrz", int(dofr))
        elif isinstance(dofr, tuple) or isinstance(dofr, list):
            m.setAttr(ch + ".var.dofrx", int(dofr[0]))
            m.setAttr(ch + ".var.dofry", int(dofr[1]))
            m.setAttr(ch + ".var.dofrz", int(dofr[2]))
        else:
            raise ValueError("Invalid type for doft: " + str(type(doft)))

        self.items.append(item_name)
        self.dict[item_name] = node_id
        return node_id

    def constraint_node(self, target_name, parent_name, constraint_type=0, weight=1.0, snap=True):
    
        """
         creates a constraint node and connects it to the solver.
                parentName is the
                type is the type of constraint
                weight is the

        :param target_name: the target for the constraint, e.g. a marker or transform
        :param parent_name: name of joint to parent the constraint to
        :param constraint_type:    0 = position,  1 = orientation,  2 = both,  3 = aim
        :param weight: constraint weight
        :param snap: if true, will position the constraint at the target
        :return: the name of the transform object

        sets the following attributes:

            constraint.type = constraint_type
            constraint.tWeight = weight

        makes the following connections:

            target_name.worldMatrix -> constraint.target
            constraint.type   -> solver.inputs[#node].con[#constraint].ct
            constraint.weight -> solver.inputs[#node].con[#constraint].weight
            constraint.target -> solver.inputs[#node].con[#constraint].matrix
                """
        
        # create a constraint node and parent it in
        transform = m.createNode("transform", parent=parent_name, name="PeelConstraint")
        const = m.createNode("peelLocator", parent=transform, name="PeelConstraintShape")

        m.addAttr(const, ln="target", at="fltMatrix")
        m.addAttr(const, ln="type", at="long")

        # snap to the position (must be done before adding)
        if snap:
            tr = m.xform(target_name, q=True, ws=True, t=True)
            m.xform(transform, t=tr, ws=True)

        if parent_name not in self.dict:
            print "The parent is not in the solver: " + str(parent_name)
            return None

        # add the constraint locator to the solver 
        node_id = self.add_locator(transform, self.dict[parent_name])

        m.connectAttr(target_name + ".worldMatrix", const + ".target")
        m.setAttr(const + ".type", constraint_type) # !! this is different from the old transforms peelType
        m.setAttr(const + ".tWeight", weight)
        m.setAttr(const + ".rWeight", 0.0, l=True)

        self.connect_constraint(node_id, const)

    def connect_constraint(self, node_id, source):

        # connect the target world matrix to the solver, drives the constraints
        sz = m.getAttr(self.solver + ".inputs[%d].con" % node_id, size=True)
        m.connectAttr(source + ".type",    self.solver + ".inputs[%d].con[%d].ct"     % (node_id, sz))
        m.connectAttr(source + ".tWeight", self.solver + ".inputs[%d].con[%d].weight" % (node_id, sz))
        m.connectAttr(source + ".target",  self.solver + ".inputs[%d].con[%d].matrix" % (node_id, sz))

    def dump(self):

        """ dumps all the data on the solver node """

        if not m.objExists(self.solver):
            raise RuntimeError("Node does not exist")

        ins  = m.getAttr(self.solver + ".i", size=True)
        outs = m.getAttr(self.solver + ".t", size=True)
        print "Inputs", ins
        for i in range(ins):
            ch = "%s.inputs[%d]" % (self.solver, i )
            print ch
            print "  Name       ", m.getAttr(ch + ".name")
            print "  Parent     ", m.getAttr(ch + ".pid")
            print "  preMatrix  ", m.getAttr(ch + ".pre")
            print "  postMatrix ", m.getAttr(ch + ".post")
            print "  defaultT   ", m.getAttr(ch + ".dt")
            print "  defaultR   ", m.getAttr(ch + ".dr")
            print "  constraints ", m.getAttr(ch + ".constraints", s=True)
            for j in range(m.getAttr(ch + ".constraints", s=True)):
                cch = "%s.constraints[%d]" % (ch, j)
                print "      type    ", m.getAttr(cch + ".type")
                print "      weight  ", m.getAttr(cch + ".weight")
                print "      matrix  ", m.getAttr(cch + ".matrix")
            print "  variables"
            print "     tx       ", m.getAttr(ch + ".var.doftx")
            print "     ty       ", m.getAttr(ch + ".var.dofty")
            print "     tz       ", m.getAttr(ch + ".var.doftz")
            print "     rx       ", m.getAttr(ch + ".var.dofrx")
            print "     ry       ", m.getAttr(ch + ".var.dofry")
            print "     rz       ", m.getAttr(ch + ".var.dofrz")
            print "     len.en   ", m.getAttr(ch + ".var.en")
            print "     len.axis ", m.getAttr(ch + ".var.axis")
            
        print "Output", outs



