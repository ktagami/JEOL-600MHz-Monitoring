from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import time
from datetime import date
import threading
import psutil
import os
import os.path as path
import pyqtgraph as pg
import numpy as np
import scipy as sp
import scipy.interpolate
import csv as csv
import serial


import RS485
import TCPIP
import u12

class GUI(QWidget):

    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        grid = QGridLayout()
        
        grid.addWidget(self.Layout_Controller_Connect(), 0, 0)
        grid.addWidget(self.Layout_Logging(), 1, 0)
        grid.addWidget(self.Layout_Pressure(), 0, 1)
        grid.addWidget(self.Layout_Temperature(), 1, 1)
        #grid.addWidget(self.Layout_MAS(), 0, 2)
        #grid.addWidget(self.Layout_Other(), 1, 2)
        
        self.setLayout(grid)

        self.setWindowTitle("600MHz Readings")
        self.resize(400, 300)


######################################################################################   

    def Layout_Controller_Connect(self):
        self.GB = QGroupBox("Connect to Measurement Devices")
        layout = QGridLayout()

        #Button for connecting to all serial/TCP devices
        self.connect_button = QPushButton('Connect',self)
        layout.addWidget(self.connect_button, 0, 0, 1, 2)
        #self.connect_button.clicked.connect(RS485.connect_button_clicked_RS485)
        #self.connect_button.clicked.connect(TCPIP.connect_button_clicked_TCP)
        self.connect_button.clicked.connect(self.connect_button_clicked)

        #Button for starting data acquisition
        self.start_button = QPushButton('Start Acquisition',self)
        layout.addWidget(self.start_button, 1, 0, 1, 2)
        self.start_button.clicked.connect(self.start_button_clicked)

        #Button for stopping data acquisition
        self.stop_button = QPushButton('Stop Acquisition',self)
        layout.addWidget(self.stop_button, 2, 0, 1, 2)
        self.stop_button.clicked.connect(self.stop_button_clicked)

        #Status box for data acquisition

        self.data_status = QLineEdit(self)
        layout.addWidget(self.data_status, 4, 0, 1, 2)
        self.data_status.setReadOnly(True)
        self.data_status.setText('Data Acquisition Status: Idle')
        self.data_status.setStyleSheet("background-color: orange;")


        #Define timer for periodically reading and updating measurement values
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        #self.timer.timeout.connect(RS485.update_RS485) # This timer connects to the 'timer_update' function and will call this function every time interval once started
        #self.timer.timeout.connect(TCPIP.update_TCP)


        self.GB.setLayout(layout)
        return self.GB


######################################################################################       

    def Layout_Logging(self):
        self.GB = QGroupBox("Log and Save Data")
        layout = QGridLayout()


        #Input box for setting log file name
        self.log_name = QLabel('Log File Name:',self)
        layout.addWidget(self.log_name, 0, 0)

        self.log_filename = QLineEdit(self)
        layout.addWidget(self.log_filename, 0, 1)
        self.log_filename.setText(time.strftime('%Y%m%d') + '.log')
        #self.log_filename.clicked.connect(log_filename_changed)

        #Button for starting to save data to log file
        self.start_log_button = QPushButton('Start Logging',self)
        layout.addWidget(self.start_log_button, 2, 0, 1, 2)
        self.start_log_button.clicked.connect(self.start_log_button_clicked)

        #Button for stopping save data to log file
        self.stop_log_button = QPushButton('Stop Logging',self)
        layout.addWidget(self.stop_log_button, 3, 0, 1, 2)
        self.stop_log_button.clicked.connect(self.stop_log_button_clicked)

        #Status box for logging status
        self.log_status = QLineEdit(self)
        layout.addWidget(self.log_status, 4, 0, 1, 2)
        self.log_status.setReadOnly(True)
        self.log_status.setText('Data Logging Status: Idle')
        self.log_status.setStyleSheet("background-color: orange;")



        self.logtimer = pg.QtCore.QTimer()
        self.logtimer.timeout.connect(self.update_log) 

        self.GB.setLayout(layout)
        return self.GB
######################################################################################  
    def Layout_Pressure(self):
        self.GB = QGroupBox("Pressure and Flow")
        layout = QGridLayout()

        Bearing_Pressure_Sensor_Names = ['PT22','PT21', 'PT23']
        Drive_Pressure_Sensor_Names = ['PT12','PT11','PT13']
        Flow_Sensor_Names = ['MFCU2', 'MFCU1']
        self.Pressure_Displays = {}
        self.Flow_Displays = {}

        #Bearing
        self.Bearing_Plable = QLabel('Bearing ',self)
        layout.addWidget(self.Bearing_Plable, 0, 0)

        for ind,i in enumerate(Bearing_Pressure_Sensor_Names):
            Label = QLabel('%s:' % i)
            layout.addWidget(Label,ind+1,0)

            Bar = QProgressBar()
            layout.addWidget(Bar,ind+1,1)
            Bar.setStyleSheet("QProgressBar::chunk ""{""background-color: orange;""}")
            Bar.setFormat('Idle') 
            Bar.setAlignment(Qt.AlignCenter)
            Bar.setValue(100)
            self.Pressure_Displays.update({i:Bar})

        #Drive
        self.Drive_Plable = QLabel('Drive ',self)
        layout.addWidget(self.Drive_Plable, 0, 2)


        for ind,i in enumerate(Drive_Pressure_Sensor_Names):
            Label = QLabel('%s:' % i)
            layout.addWidget(Label,ind+1,2)

            Bar = QProgressBar()
            layout.addWidget(Bar,ind+1,3)
            Bar.setStyleSheet("QProgressBar::chunk ""{""background-color: orange;""}")
            Bar.setFormat('Idle') 
            Bar.setAlignment(Qt.AlignCenter)
            Bar.setValue(100)
            self.Pressure_Displays.update({i:Bar})

        #Flow
        Label = QLabel('MFCU2:')
        layout.addWidget(Label,4,0)

        MFCU2 = QProgressBar()
        layout.addWidget(MFCU2,4,1)
        MFCU2.setStyleSheet("QProgressBar::chunk ""{""background-color: orange;""}")
        MFCU2.setFormat('Idle') 
        MFCU2.setAlignment(Qt.AlignCenter)
        MFCU2.setValue(100)
        self.Flow_Displays.update({'MFCU2':MFCU2})

        Label = QLabel('MFCU1:')
        layout.addWidget(Label,4,2)

        MFCU1 = QProgressBar()
        layout.addWidget(MFCU1,4,3)
        MFCU1.setStyleSheet("QProgressBar::chunk ""{""background-color: orange;""}")
        MFCU1.setFormat('Idle') 
        MFCU1.setAlignment(Qt.AlignCenter)
        MFCU1.setValue(100)
        self.Flow_Displays.update({'MFCU1':MFCU1})



        self.GB.setLayout(layout)
        return self.GB
######################################################################################   
    def Layout_Temperature(self):
        self.GB = QGroupBox("Temperature")
        layout = QGridLayout()
        Temp_Sensor_Names = ['T12','T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11']
        Drive_Temp_Sensor_Names = Temp_Sensor_Names[1:5]
        Bearing_Temp_Sensor_Names = Temp_Sensor_Names[5:9]
        Return_Temp_Sensor_Names = Temp_Sensor_Names[9:12]
        Probe_Temp_Sensor_Names = Temp_Sensor_Names[12:]

        #Bearing
        self.Bearing_Plable = QLabel('Bearing ',self)
        layout.addWidget(self.Bearing_Plable, 0, 0)

        self.Bearing_Temp_Sensor_Funcs = []
        self.Bearing_Temp_Sensor_Labels = []
        for ind,i in enumerate(Bearing_Temp_Sensor_Names):
            Label = QLabel('%s:' % i)
            self.Bearing_Temp_Sensor_Labels.append(Label)
            layout.addWidget(Label,ind+1,0)

            LineEdit = QLineEdit()
            layout.addWidget(LineEdit,ind+1,1)
            LineEdit.setText('Idle')
            LineEdit.setReadOnly(True)
            LineEdit.setStyleSheet("background-color: orange;")
            self.Bearing_Temp_Sensor_Funcs.append(LineEdit)

        #Drive
        self.Bearing_Plable = QLabel('Drive ',self)
        layout.addWidget(self.Bearing_Plable, 0, 2)

        self.Drive_Temp_Sensor_Funcs = []
        self.Drive_Temp_Sensor_Labels = []
        for ind,i in enumerate(Drive_Temp_Sensor_Names):
            Label = QLabel('%s:' % i)
            layout.addWidget(Label,ind+1,2)

            LineEdit = QLineEdit()
            self.Drive_Temp_Sensor_Funcs.append(LineEdit)
            layout.addWidget(LineEdit,ind+1,3)
            LineEdit.setText('Idle')
            LineEdit.setReadOnly(True)
            LineEdit.setStyleSheet("background-color: orange;")
            self.Drive_Temp_Sensor_Labels.append(Label)


        #Return
        self.Return_Plable = QLabel('Return ',self)
        layout.addWidget(self.Return_Plable, 0, 4)

        self.Return_Temp_Sensor_Funcs = []
        self.Return_Temp_Sensor_Labels = []
        for ind,i in enumerate(Return_Temp_Sensor_Names):
            Label = QLabel('%s:' % i)
            self.Return_Temp_Sensor_Labels.append(Label)
            layout.addWidget(Label,ind+1,4)

            LineEdit = QLineEdit()
            layout.addWidget(LineEdit,ind+1,5)
            LineEdit.setText('Idle')
            LineEdit.setReadOnly(True)
            LineEdit.setStyleSheet("background-color: orange;")
            self.Return_Temp_Sensor_Funcs.append(LineEdit)


        #Probe/lakeshore
        lakeshore_names = ['Sample', 'Bearing', 'Drive']
        self.lakeshore_displays = {}
        self.Probe_Plable = QLabel('Probe',self)
        layout.addWidget(self.Probe_Plable, 0, 6)

        for ind,i in enumerate(lakeshore_names):
            Label = QLabel('%s:' % i)
            layout.addWidget(Label,ind+1,6)

            LineEdit = QLineEdit()
            layout.addWidget(LineEdit,ind+1, 7)
            LineEdit.setText('Idle')
            LineEdit.setReadOnly(True)
            LineEdit.setStyleSheet("background-color: orange;")
            self.lakeshore_displays.update({i:LineEdit})       



        self.GB.setLayout(layout)
        return self.GB
######################################################################################   
#Functions for device connection and data acquisition window


    def start_button_clicked(self):
        global time0
        time0 = time.time()
        #Try to start timer (timer is started by this RS485 file and not the corresponding TCP file)
        try:
            self.timer.start(1000) # Timer set to update once every seconds
        except:
            print('Could not start timer')

    def stop_button_clicked(self):
        try:
            self.timer.stop()
            self.data_status.setText('Data Acquisition Status: Idle')
            self.data_status.setStyleSheet("background-color: orange;")
        except:
            print('Could not stop timer')


    def connect_button_clicked(self):
        try:
            self.RS485_Connections = RS485.connect_button_clicked_RS485()
        except:
            print('Could not connect to RS485 Devices')

        try:
            self.DAC = u12.U12()
        except:
            print('Could not connect to Labjack U12 DAC/ADC')

        try:
            self.lakeshore = serial.Serial('COM31',57600, parity=serial.PARITY_ODD, bytesize = 7)
        except:
            print('Could not connect to Lakeshore Temperature Controller')

        try:
            self.TCP_Connections = TCPIP.connect_button_clicked_TCP()
        except:
            print('Could not connect to TCP Devices')



    def update_data(self):
        self.data_status.setText('Data Acquisition Status: Acquiring')
        self.data_status.setStyleSheet("background-color: lightgreen;")
        #Pressure
        try:

            self.Pressure_Data = RS485.update_Pressure(self.RS485_Connections)
            for name,disp in self.Pressure_Displays.items():
                try:
                    if name == 'PT22' or 'PT12': # Select Low pressure
                        dat = self.Pressure_Data[name]
                        disp.setStyleSheet("QProgressBar::chunk ""{""background-color: lightgreen;""}")
                        disp.setFormat('%s kPa' % dat) 
                        disp.setAlignment(Qt.AlignCenter)
                        disp.setValue((dat/70)*100)
                    else: # Select High pressure
                        dat = self.Pressure_Data[name]
                        disp.setStyleSheet("QProgressBar::chunk ""{""background-color: lightgreen;""}")
                        disp.setFormat('%s kPa' % dat) 
                        disp.setAlignment(Qt.AlignCenter)
                        disp.setValue((dat/70)*270)
                except:
                        disp.setStyleSheet("QProgressBar::chunk ""{""background-color: red;""}")
                        disp.setFormat('NaN') 
                        disp.setAlignment(Qt.AlignCenter)
                        disp.setValue(100)
        except:
            print('Pressure Read Failed')

        #Flow
        try:
            self.Flow_Data = {'MFCU2': self.DAC.eAnalogIn(channel=1, gain=0)['voltage']}
            self.Flow_Data.update({'MFCU1': self.DAC.eAnalogIn(channel=3, gain=0)['voltage']})
            for name,disp in self.Flow_Displays.items():
                try:
                    volt = self.Flow_Data[name]
                    flow = 100*(volt/5) #Assume full scale flow rate is 0-100l/min and 0-5V
                    disp.setStyleSheet("QProgressBar::chunk ""{""background-color: lightgreen;""}")
                    disp.setFormat('%.1f l/min' % flow) 
                    disp.setAlignment(Qt.AlignCenter)
                    disp.setValue(flow)
                except:
                    disp.setStyleSheet("QProgressBar::chunk ""{""background-color: red;""}")
                    disp.setFormat('NaN') 
                    disp.setAlignment(Qt.AlignCenter)
                    disp.setValue(100)                    
        except:
            print('Flow Read Failed')
        
        #Lakeshore Temp
        try:
            lakeshore_handles = {'Sample':'A', 'Bearing':'B', 'Drive':'C'}
            self.lakeshore_Data = {}
            for name, disp in self.lakeshore_displays.items():
                self.lakeshore.write(b'KRDG? %s\n' % lakeshore_handles[name])
                time.sleep(0.06)
                temp1 = float(ser.readline()[0:7])
                self.la
        except:
            print('Lakeshore Read Failed')


######################################################################################   
#Functions for Data Logging window
    def start_log_button_clicked(self):
        try:
            self.logtimer.start(10000) # Timer set to update once every 10 seconds
        except:
            print('Could not start log timer')
        if path.exists(self.log_filename.text()):
            with open(self.log_filename.text(), 'w') as logfile: #Create the csv log file 
                writer = csv.writer(logfile)
                writer.writerow(["Time", "PT22", "PT12", "PT21", "PT11", "PT23", "PT13"])
        else:
            print("Log file already exists. Data will be appended to existing file.")

    def stop_log_button_clicked(self):
        try:
            self.logtimer.stop()
        except:
            print('Could not stop log timer')
     
    def update_log(self):
        try:
            with open(self.log_filename.text(), 'a', newline='') as logfile:
                writer = csv.writer(logfile)
                writer.writerow([time.time(),"PT22", "PT12", "PT21", "PT11", "PT23", "PT13"])
                self.log_status.setText('Data Logging Status: Active')
                self.log_status.setStyleSheet("background-color: lightgreen;")
        except:
            print('Could not update log')
            self.log_status.setText('Data Logging Status: Error')
            self.log_status.setStyleSheet("background-color: red;")


######################################################################################  


if __name__ == '__main__':

    app = QApplication(sys.argv)
    G = GUI()
    G.show()
    sys.exit(app.exec_())

def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    if including_parent:
        parent.kill()

me = os.getpid()
kill_proc_tree(me)
