
import os
import pymel.core as pm
import maya.cmds as cmds
from maya import mel
from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from . import file


class BatchSolve(QtWidgets.QDialog):
    def __init__(self):
        """ The initialization includes setting up the UI framework for the tool window, which asks the user
        for the c3d files, as well as the start and end frames."""
        pointer = omui.MQtUtil.mainWindow()
        parent = wrapInstance(long(pointer), QtWidgets.QWidget)
        super(BatchSolve, self).__init__(parent)

        # timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.setInterval(5000)
        self.timer.setSingleShot(False)
        self.progress = 0

        # data
        self.current_c3d = None
        self.c3d_files = []
        self.takes_table_headers = ["File", "In", "Out"]
        self.start_frame = None
        self.end_frame = None
        self.frame_range = []
        self.solve_obj = None

        # UI elements
        self.import_layout = QtWidgets.QGridLayout()
        self.takes_table = QtWidgets.QTableWidget()
        self.load_c3d_button = QtWidgets.QPushButton("Add C3D files")
        self.load_c3d_button.pressed.connect(self.load_c3d)
        self.clear_button = QtWidgets.QPushButton("Clear")
        self.clear_button.pressed.connect(self.clear_table)
        self.batch_solve_button = QtWidgets.QPushButton("Batch solve and Render")
        self.batch_solve_button.pressed.connect(self.batch_solve)
        self.setLayout(self.import_layout)

        # methods
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI layout for the tool"""
        self.import_layout.addWidget(self.load_c3d_button, 0, 0)
        self.import_layout.addWidget(self.clear_button, 0, 5)
        self.import_layout.addWidget(self.takes_table, 1, 0, 5, 10)
        self.import_layout.addWidget(self.batch_solve_button, 6, 0)

        # setup takes table
        column_count = len(self.takes_table_headers)
        self.takes_table.setColumnCount(column_count)
        self.takes_table.setHorizontalHeaderLabels(self.takes_table_headers)

        self.set_ui_style()

    def set_ui_style(self):
        """Sets the UI styling for the tool"""
        self.setMinimumWidth(340)
        header = self.takes_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

    def batch_solve(self):
        """Starts the timer for the batch processing. Using a timer ensures that there is a small pause between
        the different steps of the batch solve. Some actions in the peel tool only happen on still/idle time."""

        self.timer.start()  # Goes to tick()

    def tick(self):
        """This is where the main batch solve happens. It takes one c3d file at a time from the list, then imports it,
        solves it (after setting frame range and selecting the root), saves it and playblasts it."""

        if not self.c3d_files:
            print("All done!", self.c3d_files)
            self.timer.stop()
            return

        if self.progress == 0:
            # Find a c3d to work on
            self.current_c3d = self.c3d_files.pop(0)

            print("Now processing..............................................", self.current_c3d)
            # Import
            ImportData.import_file(self.current_c3d)
            print("Imported file..............................................: ", self.current_c3d)
            self.progress = 1
            # self.timer.stop()
            # return

        if self.progress == 1:

            # Select root
            root = self.select_root()  # For this to work, root name has to end with "c3d"
            if root is None:
                print("Root could not be found. Solve failed.")
                self.timer.stop()
                return

            # Set start and end frames on timeline
            self.frame_range = self.get_frame_range(self.current_c3d)
            if self.frame_range:
                pm.playbackOptions(minTime=self.frame_range[0], maxTime=self.frame_range[1])
            self.progress = 2

        # this separation is important! else, solve does not take the user-defined frame range. also, maya freezes.

        if self.progress == 2:
            print("Delete history set framerange..........................................: ", self.current_c3d)
            # Delete animation and history
            self.solve_obj = Solve()
            self.solve_obj.delete_prev_anim()
            self.solve_obj.delete_history()
            print("Now starting solve on..............................................: ", self.current_c3d)
            self.progress = 3

        if self.progress == 3:

            # Solve
            self.solve_obj.solve_c3d()
            print("Solve completed..............................................: ", self.current_c3d)
            self.progress = 4

        if self.progress == 4:

            # Save
            self.solve_obj.save_file(self.current_c3d)
            print("Saved...............................................................: ", self.current_c3d)
            self.progress = 5

        if self.progress == 5:

            # Playblast
            # Current_c3d eg: D:/CLIENTS/HOM/dog/outgoing/20210122_tracked_orders/0000233_B_edt.c3d
            # shot_name eg: 0000233
            shot_name = (((os.path.split(self.current_c3d)[1]).split(".")[0]).strip("_")).split("_")[0]
            print("shot name for playblast = ", shot_name)
            PlayBlast(shot_name)
            self.progress = 6

        if self.progress == 6:
            self.progress = 0

    @staticmethod
    def select_root():
        """selects the root in the scene (looks for transform object ending with 'c3d')"""
        for transform_object in pm.ls(transforms=True):
            if str(transform_object).endswith("c3d"):
                print("Selecting root:", transform_object)
                return transform_object  # eg: "0000246_edt_c3d"
        print("No root found")

    def get_frame_range(self, c3d_file):
        """Returns user-specified start and end frames if available."""
        user_frame_range = self.get_user_entered_range(c3d_file)
        if user_frame_range:
            return user_frame_range

    def get_user_entered_range(self, importing_file_name):
        """For the given c3d file, find the frame range from the UI /takes_table"""
        for row in range(0, self.takes_table.rowCount()):
            if not self.takes_table.item(row, 0):
                return None
            shot_name = self.takes_table.item(row, 0).text()
            importing_file_name_short = os.path.split(importing_file_name)[1]
            if shot_name == importing_file_name_short:
                if self.takes_table.item(row, 1) and self.takes_table.item(row, 2):
                    user_in_val = self.takes_table.item(row, 1).text()
                    user_out_val = self.takes_table.item(row, 2).text()
                    print(user_in_val, user_out_val)
                    return [user_in_val, user_out_val]
        return None

    def load_c3d(self):
        """Loads a dialog for selecting the c3d files. Called when the load button is pressed."""

        print("Loading c3d..")

        basic_filter = "*.c3d"
        last_directory = pm.optionVar(q="lastPeelC3dDir")

        # open file browser
        self.c3d_files = pm.fileDialog2(fm=4, fileFilter=basic_filter, dialogStyle=2, dir=last_directory)

        print("Found these c3d..", self.c3d_files)

        if self.c3d_files is None or len(self.c3d_files) == 0:
            return

        self.populate_c3d_table()

    def populate_c3d_table(self):
        """Populates the c3d table with the user-selected c3d files."""

        if self.c3d_files is None:
            print("No c3d files found. Could not populate table.")
            return

        row = 0
        for c3d_file in self.c3d_files:
            self.takes_table.insertRow(self.takes_table.rowCount())
            self.takes_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(os.path.split(c3d_file)[1])))
            row += 1

    def clear_table(self):
        """Clears the takes table and deletes the rows"""
        self.takes_table.setRowCount(0)
        self.takes_table.clearContents()


class ImportData:
    def __init__(self):
        self.file_browser()

    def file_browser(self):
        """ Opens a browser for user to select one c3d file. This method is used when import is done as a separate
        one-time operation. It is not used for the batch_solve"""

        basic_filter = "*.c3d"
        last_directory = pm.optionVar(q="lastPeelC3dDir")
        c3d_files = pm.fileDialog2(fm=1, fileFilter=basic_filter, dialogStyle=2, dir=last_directory)
        if c3d_files is None or len(c3d_files) == 0:
            raise RuntimeError("No c3d files selected for import")
        c3d_file = c3d_files[0]

        self.import_file(c3d_file)

    @staticmethod
    def import_file(c3d_file, merge=True, timecode=True, convert=False, debug=False):
        """Assigns values to attributes for peelC3D import, selects the root, imports and checks if the imported
        data pertains to the same dog as the previous data."""

        # Settings for peelC3d import
        pm.optionVar(sv=("lastPeelC3dDir", os.path.split(c3d_file)[0]))

        # print("loading c3d: %s  merge: %s   timecode: %s    convert: %s" %
        #       (str(c3d_file), str(merge), str(timecode), str(convert)))

        c3d_file = c3d_file.replace("\\", "/")

        # Check for root in scene.
        # roots = pm.ls(selection=True)  # returns an array
        #
        # if roots is None or len(roots) == 0:
        #     raise RuntimeError("Could not find mocap root in the scene - is the rig loaded and selected?")

        root = BatchSolve.select_root()  # ............................................................................................................................check

        dog_name = ImportData.get_dog_name(root)

        if merge:
            pm.select(root)
            pm.delete(root, channels=True, hierarchy='below')

        options = ";scale=1;unlabelled=0;nodrop=0;"
        options += "timecode=%d;" % int(bool(timecode))
        options += "convert=%d;" % int(bool(convert))
        options += "merge=%d;" % int(bool(merge))
        options += "debug=%d;" % int(bool(debug))
        import_cmd = 'file -import -type "peelC3D" -options "%s" "%s";' % (options, c3d_file)

        try:
            mel.eval(import_cmd)
        except RuntimeError:
            raise RuntimeError("Unable to load c3d - is the plugin loaded?")

        if merge:
            # rename the root
            root = pm.rename(root, '_' + str(os.path.split(c3d_file)[1]).replace('.', '_'))

        print("Checking if dogs match...")
        new_dog_name = ImportData.get_dog_name(root)
        if new_dog_name != dog_name:
            raise RuntimeError("Not the same dog. Imported but not solved. Please start over.")

        # Todo: Save file!

    @staticmethod
    def get_dog_name(root):
        children = pm.listRelatives(root)

        for child in children:
            if child.startswith("Tyrus"):
                return "Tyrus"
            if child.startswith("Sterling"):
                return "Sterling"
        print("Could not determine which dog.")
        return "No dog found"


class Solve:
    def __init__(self, save_file_path=r'D:\CLIENTS\HOM\dog\shots\auto_solves\solves\temp_saves\temp_save.c3d'):

        # data
        self.solves_folder = r'D:\CLIENTS\HOM\dog\shots\auto_solves\solves'

        # # methods
        # self.delete_prev_anim()
        # self.solve_c3d()
        # self.save_file_path = save_file_path

    @staticmethod
    def delete_prev_anim():
        """ Delete all animation"""

        # Delete all channels
        pm.delete(all=True, channels=True)

    @staticmethod
    def delete_history():
        """ Delete all history on joints"""

        # Select all passive, i.e. joints
        select_passive_cmd = "peelSolve2SelectType(3)"
        try:
            mel.eval(select_passive_cmd)
        except RuntimeError as e:
            print("Could not delete history on all joints")
            return

        # Delete history
        pm.delete(constructionHistory=True)

    @staticmethod
    def solve_c3d():
        """Solves the data for the range in timeline using PeelSolve"""

        solve_cmd = "peelSolve2Run(1)"
        try:
            mel.eval(solve_cmd)
        except RuntimeError as e:
            print("Could not solve due to following error:")
            print(str(e))
            return
        print("Solve completed.")

    def save_file(self, current_c3d=None):  # current c3d eg" D:/shots/20210122_tracked_orders/_0000224_B_edt.c3d
        """ Gets the file name and saves it """
        # if current_c3d:

        if not current_c3d:
            current_c3d = self.save_file_path  # r'D:\CLIENTS\HOM\dog\shots\auto_solves\solves\temp_saves\temp_save.c3d'

        shot_path = os.path.split(current_c3d)
        shot_name = (shot_path[1].strip("_")).split("_")[0]  # eg: _000246_edt_c3d
        # else:
        #     shot_name = BatchSolve.select_root()
        print("shot_name after split operation", shot_name)
        file_name = file.create_file_name(shot_name, self.solves_folder)
        pm.saveAs(file_name)
        print("File saved as: ", file_name)



INSTANCE = None


def batch_solve():
    """ Create the gui if it doesn't exist, or show if it does """
    global INSTANCE
    if not INSTANCE:
        INSTANCE = BatchSolve()
    INSTANCE.show()
    return INSTANCE


def import_data():
    ImportData()

def solve_data():
    Solve()

