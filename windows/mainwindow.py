__author__ = 'Patrick'

import sys
import os
import webbrowser
from PyQt4 import QtGui, uic, Qt
import PyQt4.Qwt5 as Qwt
from ui.items import CustomTreeItem
from ui.data import DataSet
import random
from helpers.serialHelpers import list_serial_ports
from PyQt4.Qwt5.anynumpy import *
from dataread.provant_serial import ProvantSerial
from ui.artificalHorizon import AttitudeIndicator
from ui.artificalRoll import RollIndicator
from ui.artificalPitch import PitchIndicator
from ui.artificalYaw import YawIndicator
from dataPersistency.csvRecorder import CsvRecorder
from windows.about import AboutSetup

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('windows/vant.ui', self)
        self.setupTreeWidget()
        self.setWindowIcon(QtGui.QIcon('favicon.ico'))
        self.show()
        self.setupPlot()
        self.dataSets = {}
        self.provantSerial = None
        #legend = Qwt.QwtLegend()
        #self.qwtPlot.insertLegend(legend, Qwt.QwtPlot.TopLegend)
        self.setupSerial()
        self.timerCounter =0

        self.horizon = AttitudeIndicator(self.frame_2)
        self.lay3.addWidget(self.horizon)

        self.attitudeRoll = RollIndicator(self.frame_2)
        self.lay4.addWidget(self.attitudeRoll)

        self.attitudePitch = PitchIndicator(self.frame_2)
        self.lay4.addWidget(self.attitudePitch)

        self.attitudeYaw = YawIndicator(self.frame_2)
        self.lay5.addWidget(self.attitudeYaw)
        self.setupMenu()

    def setupMenu(self):
        self.currentFile = None
        self.actionSave.setShortcut('Ctrl+S')
        self.actionSave.setStatusTip('Save new File')
        self.actionSave.triggered.connect(self.saveFile)
        self.actionSave_as.triggered.connect(self.saveFileAs)
        self.actionClose.triggered.connect(QtGui.QApplication.exit)
        self.actionAbout.triggered.connect(self.about)

    def saveFileAs(self):
        self.currentFile = None
        self.saveFile()

    def saveFile(self):
        writer = CsvRecorder()
        if not self.currentFile:
            self.currentFile = QtGui.QFileDialog.getSaveFileName(self, 'Save file','/home')
        try:
            writer.writeDataToFile(self.dataSets, self.currentFile)
            QtGui.QMessageBox.about(self, "","Success!")
        except Exception, e:
            self.currentFile = None
            QtGui.QMessageBox.about(self, "","Error!\n{0}".format(e))

    def about(self):
         self.aboutWindow = AboutSetup()

    def setupSerial(self):
        #assert isinstance(self.serialList,QtGui.QComboBox) #hint for pycharm code-completion
        actual = self.serialList.currentText()
        self.serialList.clear()
        self.serialList.addItem(actual)

        for serial in list_serial_ports():
            self.serialList.addItem(serial)
        self.serialConnect.clicked.connect(self.connectToSerial)

    def connectToSerial(self):
        try:
            self.setSerial(ProvantSerial(window= self,serial_name=str(self.serialList.currentText())))
            self.serialStatus.setText('OK!')
        except Exception, e:
            self.serialStatus.setText("ERROR!")
            print e


    def setSerial(self, ser):
        self.provantSerial = ser

    def addPoint(self, datasetName, y):
        if datasetName not in self.dataSets:
            self.dataSets[datasetName] = DataSet(self, datasetName)
            self.dataSets[datasetName].curve.attach(self.qwtPlot)
            self.addSingleData(datasetName)
            self.dataSets[datasetName].setColor(self.getColor(datasetName))
        self.dataSets[datasetName].addPoint(y)

    def addArray(self, datasetName, points,setnames = None):
        if setnames:
            datasetName_ = datasetName + setnames[0]
            if datasetName_ not in self.dataSets:
                self.addDataTree(datasetName, len(points),setnames)
                for i in range(len(points)):
                    datasetName_ = datasetName+setnames[i]
                    #print datasetName_
                    self.dataSets[datasetName_] = DataSet(self, datasetName_)
                    self.dataSets[datasetName_].curve.attach(self.qwtPlot)
                    self.dataSets[datasetName_].setColor(self.getColor(datasetName_))
            for i in range(len(points)):
                if points[i] != None:
                    self.dataSets[datasetName+setnames[i]].addPoint(points[i])
        else:
            datasetName_ = datasetName +  '['+str(0)+']'
            if datasetName_ not in self.dataSets:
                self.addDataTree(datasetName, len(points))
                for i in range(len(points)):
                    datasetName_ = datasetName + '['+str(i)+']'
                    self.dataSets[datasetName_] = DataSet(self, datasetName_)
                    self.dataSets[datasetName_].curve.attach(self.qwtPlot)
                    self.dataSets[datasetName_].setColor(self.getColor(datasetName_))
            for i in range(len(points)):
                if points[i]:
                    self.dataSets[datasetName + '['+str(i)+']'].addPoint(points[i])

    def setupPlot(self):
        self.startTimer(50)

    def getDataFromSerial(self):
        self.provantSerial.update()

    def updateData(self):
        self.getDataFromSerial()
        for namea, dataset in self.dataSets.items():
            dataset.update()
        self.qwtPlot.replot()
        self.lMotorSetpoint.setValue(self.provantSerial.motor.motor[0])
        self.rMotorSetpoint.setValue(self.provantSerial.motor.motor[1])
        self.lServo.setValue(self.provantSerial.servo.servo[4])
        self.rServo.setValue(self.provantSerial.servo.servo[5])

        self.horizon.setRoll(self.provantSerial.attitude.roll)
        self.horizon.setPitch(self.provantSerial.attitude.pitch)
        
        self.attitudeRoll.setRoll(self.provantSerial.attitude.roll)
        self.label_6.setText(str(self.provantSerial.attitude.roll))
        self.attitudePitch.setRoll(self.provantSerial.attitude.pitch)
        self.label_7.setText(str(self.provantSerial.attitude.pitch))
        self.attitudeYaw.setAngle(self.provantSerial.attitude.yaw)
        self.label_8.setText(str(self.provantSerial.attitude.yaw))

    def timerEvent(self, e):
        self.timerCounter += 1
        if self.provantSerial:
            self.updateData()
        elif (self.timerCounter % 100) == 1:
            self.setupSerial()


    def setupTreeWidget(self):
        #self.treeWidget.header().setResizeMode(3)
        self.treeWidget.header().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.treeWidget.header().setResizeMode(1, QtGui.QHeaderView.Fixed)
        self.treeWidget.header().setResizeMode(2, QtGui.QHeaderView.Fixed)
        self.treeWidget.header().setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        self.treeWidget.setColumnWidth(1, 30)

    def addDataTree(self, data, children_number,setnames = None):
        if setnames:
            parent = CustomTreeItem(self, self.treeWidget, data, self.treeWidget, color=False)
            for i in range(children_number):
                a = CustomTreeItem(self, parent, data+setnames[i])
                a.setText(0,setnames[i])
            self.treeWidget.resizeColumnToContents(2)
        else:
            parent = CustomTreeItem(self, self.treeWidget, data, self.treeWidget, color=False)
            for i in range(children_number):
                CustomTreeItem(self, parent, data + '['+str(i)+']')
            self.treeWidget.resizeColumnToContents(2)

    def addSingleData(self, name):
        CustomTreeItem(self, self.treeWidget, name, self.treeWidget)

    def disablePlot(self, name):
        self.dataSets[name].curve.detach()

    def enablePlot(self, name):
        self.dataSets[name].curve.attach(self.qwtPlot)

    def setPlotColor(self, name, color):
        #print color
        self.dataSets[name].setColor(color)

    def getColor(self, name):
        return self.findNode(name).colorChooser.color()

    def findNode(self, name, node=None):
        if not node:
            root = self.treeWidget.invisibleRootItem()
            node = root
        else:
            #print node.text(0)
            if node._name == name:
                return node
        for i in range(node.childCount()):
            if self.findNode(name, node.child(i)):
                return self.findNode(name, node.child(i))