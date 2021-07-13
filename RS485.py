"""
Functions for connecting to USB-RS485 converter as well as all the slave devices. 
"""

import minimalmodbus
import time
import numpy as np
def connect_button_clicked_RS485(self):
    #COM Port (Look up in Device Manager)
    PORT='COM4' 

    #Set up USB-RS485 converter/tranceiver
    try: 
        RS485_conn = minimalmodbus.Instrument(PORT,1,mode=minimalmodbus.MODE_RTU)
        #RS485 protocol settings
        RS485_conn.serial.baudrate = 9600        # Baud
        RS485_conn.serial.bytesize = 8
        RS485_conn.serial.parity   = minimalmodbus.serial.PARITY_NONE
        RS485_conn.serial.stopbits = 1
        RS485_conn.serial.timeout  = 1          # seconds
        RS485_conn.mode = minimalmodbus.MODE_RTU
        #Good practice
        RS485_conn.close_port_after_each_call = True
        RS485_conn.clear_buffers_before_each_transaction = True
        print('Connected to USB-RS485 Converter')
    except:
        RS485_conn = None
        print('Cannot connect to USB-RS485 Converter')

    Pressures_Sensor_Names = ['PT22','PT12', 'PT21', 'PT11', 'PT23', 'PT13']
    Pressure_Sensor_Addresses = [1,2,3,4,5,6]
    Pressure_Sensor_Connections = {}

    #Set up connections to various slave devices
    for i,j in zip(Pressure_Sensor_Addresses,Pressures_Sensor_Names):
        try:
            conn = minimalmodbus.RS485_conn(PORT,i) # define connection to each slave device
            conn.read_register(30101-30001,0,4,True) # test pressure reading to decide if device is working
            Pressure_Sensor_Connections.update({j:conn})
            print('Connected to ' + j)
        except:
            conn = None
            Pressure_Sensor_Connections.update({j:conn})
            print('Could not connect to ' + j)


    return Pressure_Sensor_Connections



def update_Pressure(RS485_Connections):
    
    Pressures = {}

    for name,conn in RS485_Connections.items():
        try:
            p = conn.read_register(30101-30001,0,4,True)
            Pressures.update({name:p})
        except:
            Pressures.update({name:np.nan})

    return Pressures

