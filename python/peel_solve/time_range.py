from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import maya.cmds as m
from shiboken2 import wrapInstance
from peel_solve import time_util, roots

class SolveTemplates(QtWidgets.QDialog):
    def __init__(self):
        """ The initialization includes setting up the UI framework for the tool window, which asks the user
        for the c3d files, as well as the start and end frames."""
        pointer = omui.MQtUtil.mainWindow()
        parent = wrapInstance(long(pointer), QtWidgets.QWidget)
        super(SolveTemplates, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        self.ranges = QtWidgets.QTableWidget()
        self.ranges.setColumnCount(4)
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

        low_bar.addStretch(1)

        layout.addItem(low_bar)

        self.setLayout(layout)

        self.resize(700, 400)

        self.populate(435)

    def populate(self, shot=None):
        optical_root = roots.optical()
        self.frame_start.setText(str(time_util.c3d_start(optical_root)))

        tc_standard = m.getAttr(optical_root + ".C3dTimecodeStandard")
        offset = m.getAttr(optical_root + ".C3dFirstField")
        rate = m.getAttr(optical_root + ".C3dRate")
        self.tc_offset.setText(str(offset / rate))
        self.tc_rate.setText(str(tc_standard))

        hh = m.getAttr(optical_root + ".C3dTimecodeH")
        mm = m.getAttr(optical_root + ".C3dTimecodeM")
        ss = m.getAttr(optical_root + ".C3dTimecodeS")
        ff = m.getAttr(optical_root + ".C3dTimecodeF")

        self.tc_start.setText("%02d:%02d:%02d:%02d" % (hh, mm, ss, ff))

        row = 0
        with open(r'M:\CLIENTS\HOM\dog\outgoing\20210629_tracked_orders\ranges.txt') as f:
            for line in f:
                print(line)
                sp = line.rstrip().split('\t')
                if len(sp) == 4:
                    if shot is not None and int(sp[0]) != shot:
                        continue
                    self.ranges.setRowCount(row + 1)
                    for col, val in enumerate(sp):
                        self.ranges.setItem(row, col, QtWidgets.QTableWidgetItem(val))
                    row += 1

                else:
                    print(len(sp), sp)

    def select_event(self, row):
        tc_rate = float(self.tc_rate.text())
        first = time_util.frame(str(self.tc_start.text()), tc_rate)
        start = time_util.frame(str(self.ranges.item(row, 2).text()), tc_rate)
        end = time_util.frame(str(self.ranges.item(row, 3).text()), tc_rate)

        offset = float(self.tc_offset.text()) * tc_rate


        print(first, start, end)
        print((start - first - offset) * 4, (end - first - offset) * 4)







INSTANCE = None

def show():
    """ Create the gui if it doesn't exist, or show if it does """
    global INSTANCE
    if not INSTANCE:
        INSTANCE = SolveTemplates()
    INSTANCE.show()
    return INSTANCE
