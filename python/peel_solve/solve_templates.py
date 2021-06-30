from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance

class SolveTemplates(QtWidgets.QDialog):
    def __init__(self):
        """ The initialization includes setting up the UI framework for the tool window, which asks the user
        for the c3d files, as well as the start and end frames."""
        pointer = omui.MQtUtil.mainWindow()
        parent = wrapInstance(long(pointer), QtWidgets.QWidget)
        super(SolveTemplates, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        self.templates = QtWidgets.QListView()

        layout.addWidget(self.templates)

