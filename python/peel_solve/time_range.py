from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import maya.cmds as m
from shiboken2 import wrapInstance
from peel_solve import time_util, roots, solve
import math






class TimeRangeWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        """ The initialization includes setting up the UI framework for the tool window, which asks the user
        for the c3d files, as well as the start and end frames."""

        super(TimeRangeWidget, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        self.ranges = QtWidgets.QTableWidget()
        self.ranges.setColumnCount(3)
        self.ranges.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ranges.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ranges.cellDoubleClicked.connect(self.select_event)

        layout.addWidget(self.ranges)

        low_bar = QtWidgets.QHBoxLayout()

        low_bar.addWidget(QtWidgets.QLabel("Start TC"))
        self.tc_start = QtWidgets.QLineEdit()
        low_bar.addWidget(self.tc_start)

        low_bar.addWidget(QtWidgets.QLabel("TC Rate"))
        self.tc_rate = QtWidgets.QLineEdit()
        low_bar.addWidget(self.tc_rate)

        low_bar.addWidget(QtWidgets.QLabel("Offset (sec)"))
        self.tc_offset = QtWidgets.QLineEdit()
        low_bar.addWidget(self.tc_offset)

        low_bar.addWidget(QtWidgets.QLabel("Start#"))
        self.frame_start = QtWidgets.QLineEdit()
        low_bar.addWidget(self.frame_start)

        self.solve_button = QtWidgets.QPushButton("Solve Selected")
        self.solve_button.pressed.connect(self.do_solve)
        low_bar.addWidget(self.solve_button)

        self.solve_all_button = QtWidgets.QPushButton("Solve All")
        self.solve_all_button.pressed.connect(self.do_solve_all)
        low_bar.addWidget(self.solve_all_button)

        low_bar.addStretch(1)

        layout.addItem(low_bar)

        self.setLayout(layout)

        self.resize(500, 250)

        self.populate()

    def clear(self):
        self.ranges.clear()

    def populate(self):
        self.ranges.clear()
        self.ranges.setRowCount(0)

        optical_root = roots.optical()
        if optical_root is None:
            self.tc_offset.setText("")
            self.tc_rate.setText("")
            self.tc_start.setText("")
            return
        self.frame_start.setText(str(time_util.c3d_start(optical_root)))

        tc_standard = m.getAttr(optical_root + ".C3dTimecodeStandard")
        offset = m.getAttr(optical_root + ".C3dFirstField")
        rate = m.getAttr(optical_root + ".C3dRate")
        self.tc_offset.setText("%.2f" % (offset / rate))
        self.tc_rate.setText(str(tc_standard))

        hh = m.getAttr(optical_root + ".C3dTimecodeH")
        mm = m.getAttr(optical_root + ".C3dTimecodeM")
        ss = m.getAttr(optical_root + ".C3dTimecodeS")
        ff = m.getAttr(optical_root + ".C3dTimecodeF")

        self.tc_start.setText("%02d:%02d:%02d:%02d" % (hh, mm, ss, ff))

    def add_range(self, name, start, end):
        row = self.ranges.rowCount()
        self.ranges.setRowCount(row+1)
        self.ranges.setItem(row, 0, QtWidgets.QTableWidgetItem(name))
        self.ranges.setItem(row, 1, QtWidgets.QTableWidgetItem(start))
        self.ranges.setItem(row, 2, QtWidgets.QTableWidgetItem(end))

    def get_range(self, row):
        tc_rate = float(self.tc_rate.text())

        c3d_start = time_util.c3d_start(roots.optical())

        start_tc = time_util.Timecode(str(self.ranges.item(row, 1).text()), tc_rate)
        end_tc = time_util.Timecode(str(self.ranges.item(row, 2).text()), tc_rate)

        print("Start:  " + start_tc.info())
        print("End:    " + end_tc.info())
        print("Offset: " + c3d_start.info())

        a = start_tc - c3d_start
        b = end_tc - c3d_start

        a.set_rate(time_util.fps())
        b.set_rate(time_util.fps())

        print("Start: " + a.info())
        print("End:   " + b.info())

        return a.frame(), b.frame()

    def select_event(self, row):
        start, end = self.get_range(row)

        m.playbackOptions(min=math.floor(start), max=math.ceil(end))

    def do_solve(self, all=False):
        for i in range(self.ranges.rowCount()):
            row = self.ranges.item(i, 0)
            if all is True or row.isSelected():
                start, end = self.get_range(i)
                solve.run(start=start, end=end)

    def do_solve_all(self):
        self.do_solve(all=True)



class TimeRanges(QtWidgets.QDialog):

    def __init__(self, parent=None):

        if parent is None:
            pointer = omui.MQtUtil.mainWindow()
            parent = wrapInstance(long(pointer), QtWidgets.QWidget)

        super(TimeRanges, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        self.table = TimeRangeWidget()
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.resize(500, 250)

INSTANCE = None

def show():
    """ Create the gui if it doesn't exist, or show if it does """
    global INSTANCE
    if not INSTANCE:
        INSTANCE = TimeRanges()
    INSTANCE.show()
    return INSTANCE
