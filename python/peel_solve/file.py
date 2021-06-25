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


from peel_solve import roots, node_list
import maya.cmds as m
from maya import mel
import os


def create_file_name(shot_name, solves_folder):
    """Returns the name the the solved MB file needs to be saved as"""
    versioned_file = get_latest_version_file(shot_name)
    return versioned_file  # eg: D:/shots/solves/000246/00246_solved_v02.mb


def get_latest_version_file(shot_name, solves_folder):  # Todo: some repetition with the other get_new_version method.
    """Find the latest file version for the shot in the solves folder, and returns the next version file name."""

    # if first version, create folder with shot name, return file name for saving
    if not os.path.isdir(os.path.join(solves_folder, shot_name)):
        os.mkdir(os.path.join(solves_folder, shot_name))
        first_version_file = os.path.join(solves_folder, shot_name, shot_name + "_solved_v001.mb")
        return first_version_file

    # if folder already exists. find latest file
    latest_version = 0
    for each_file in os.listdir(os.path.join(solves_folder, shot_name)):
        if not each_file.startswith(shot_name + "_solved_v"):
            continue
        version_part = each_file.replace((shot_name + "_solved_v"), "")[:-3]  # also removes the .mb part @ end
        if not version_part.isdigit():
            continue
        version = int(version_part)
        if version > latest_version:
            latest_version = version
    latest_version = str(latest_version + 1).zfill(3)  # Todo: what if more than 999 versions?
    return os.path.join(solves_folder, shot_name, shot_name + "_solved_v" + latest_version + ".mb")
    # return eg: "D:/shots/solves/000246/00246_solved_v02.mb"


def delete_mesh_below(node):

    mesh = m.listRelatives(node, typ='mesh', ad=True, f=True)
    if not mesh:
        return

    for i in mesh:
        m.delete(m.listRelatives(i, p=True, f=True))


def load_c3d(c3d_file=None, merge=True, timecode=True, convert=False, debug=False):

    if c3d_file is None:
        basic_filter = "*.c3d"
        d = m.optionVar(q="PeelLastC3dDir")
        c3d_files = m.fileDialog2(fileFilter=basic_filter, dialogStyle=2, fm=1, dir=d)
        if c3d_files is None or len(c3d_files) == 0:
            return
        c3d_file = c3d_files[0]
        m.optionVar(sv=("PeelLastC3dDir", os.path.split(c3d_file)[0]))

    print("loading c3d: %s   merge: %s   timecode: %s  convert: %s" % \
          (str(c3d_file), str(merge), str(timecode), str(convert)))

    # paths _must_ have forward slashes for maya's file command
    c3d_file = c3d_file.replace('\\', '/')

    root = roots.optical()

    if merge:
        if root is None:
            raise RuntimeError("Could not find mocap root in the scene - is the rig loaded?")
        m.select(root)
        m.delete(root, channels=True, hierarchy='below')

    options = ";scale=1;unlabelled=0;nodrop=0;"

    options += "timecode=%d;" % int(bool(timecode))
    options += "convert=%d;" % int(bool(convert))
    options += "merge=%d;" % int(bool(merge))
    options += "debug=%d;" % int(bool(debug))

    cmd = 'file -import -type "peelC3D" -options "%s" "%s";' % (options, c3d_file)
    print(cmd)
    try:
        mel.eval(cmd)
    except RuntimeError as e:
        print("Unable to load c3d - is the plugin loaded?")
        print(str(e))
        return

    if merge:
        # rename the root
        root = m.rename(root, '_' + os.path.split(c3d_file)[1].replace('.', '_'))


def load_fbx(fbxfile, subjects, merge=True):

    """ Loads an fbx file and creates a similar hierarchy to a c3d import """

    print("Loading FBX: " + str(fbxfile))

    time_mode = m.currentUnit(q=True, t=True)

    if not os.path.isfile(fbxfile):
        raise IOError("File does not exist: " + str(fbxfile))

    mel.eval('FBXImportMode -v "add";')
    mel.eval('FBXImport -f "%s" -t 1' % str(fbxfile))

    #m_cmds.file(fbxfile, i=True)

    topnode = None
    topname = '_' + os.path.split(fbxfile)[1].replace('.', '_')

    for actor in subjects:

        if merge:

            print("Moving keys for " + str(actor))

            for i in m.listRelatives(actor, c=True, typ='transform'):

                src_node = actor + "|" + i
                dst_node = actor + "_" + i

                if not m.objExists(dst_node):
                    print("Missing: " + str(dst_node))
                    continue

                if m.keyframe(src_node, q=True) is None:
                    print("No Animation: " + str(src_node))
                    continue

                m.cutKey(src_node)
                m.pasteKey(dst_node)

                # Rename the top node

                root = roots.optical()
                if root:
                    # rename the root
                    print("Renaming root node: " + str(root) + " to:  " + topname)
                    m.rename(roots.optical(), topname)

        else:
            for i in m.listRelatives(actor, s=False, c=True, type="transform"):
                shapes = m.listRelatives(i, s=True)
                if shapes:
                    m.delete(shapes)
                i = m.rename(i, actor + "_" + i)
                sh = m.createNode("peelSquareLocator", p=i, name=i + "Shape")
                m.setAttr(sh + ".displayMode", 1)
                m.setAttr(sh + ".size", 2)

                if not topnode:
                    # create a new top node
                    topnode = m.group(em=True, name=topname)

                m.parent(i, topnode)

            m.delete("|" + actor)

    print(time_mode)
    m.currentUnit(t=time_mode)


def save_fbx(outfile=None, force=False, reload=True, delete_mesh=True, unlock_joints=True):

    """
    Saves off a clean fbx file.
    Frames the keys on the joints, deletes any geo and exports joints, animated cameras and animated props
    """

    m.loadPlugin("fbxmaya")

    current_scene = m.file(q=True, sn=True)

    if not outfile:
        n = m.file(sn=True, q=True)
        print("Using current file name for fbx: " + str(os.path.splitext(n)))
        outfile = os.path.splitext(n)[0] + ".fbx"

        if not force and os.path.isfile(outfile):
            raise RuntimeError("File already exists: " + str(outfile))

    # save the joint list before deleting the markers
    j = node_list.joints()

    keys = m.keyframe(j, q=True)

    if not keys:
        raise RuntimeError("No keys on skeleton")

    m.playbackOptions(min=math.floor(min(keys)), max=math.ceil(max(keys)))

    # clean the scene

    if delete_mesh:
        for root in roots.ls():
            delete_mesh_below(root)

    if unlock_joints:
        # unlock all joints
        for i in m.ls(type='joint'):
            for ch in ['rx', 'ry', 'rz']:
                try:
                    m.setAttr(i + "." + ch, l=False)
                except Exception as e:
                    m.error("")

    mel.eval('peelSolve2SelectType(2)')
    m.delete()
    m.select(j)
    m.select(list(node_list.cameras()), add=True)
    m.select(node_list.props(), add=True)

    if m.objExists('|Timecode'):
        m.select('|Timecode', add=True)

    m.file(rn=outfile)

    print("Saving FBX: " + str(outfile))
    mel.eval('FBXExportUseSceneName -v true')
    mel.eval('FBXExport -f "%s" -s' % outfile.replace('\\', '/'))

    if reload:
        m.file(current_scene, o=True, f=True)
