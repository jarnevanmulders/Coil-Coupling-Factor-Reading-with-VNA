# Reading coupling factor automatically with R&S VNA ZVL
# SCPI script reads S-parameters and convert results to coupling factor k between the two coils

from rohdeschwarz.instruments.vna import Vna
import numpy as np
import skrf as rf
import math as m
import cmath


# Connect
vna = Vna()
vna.open_tcp('10.128.52.19')

# Parse ID String
# Example:
#     "Rohde-Schwarz,ZNBT8-16Port,1318700624100104,2.70"
#     Manufacturer [0]: Rohde-Schwarz
#     Model        [1]: ZNBT8-16Port
#     Serial No    [2]: 1318700624100104
#     Firmware Ver [3]: 2.70
[manufacturer, model, serial_no, firmware_ver] = vna.query("*IDN?").split(",")

print(f"Manufacturer: {manufacturer}")
print(f"Model: {model}")
print(f"Serial_no: {serial_no}")
print(f"Firmware_ver: {firmware_ver}")

# Query number of physical ports
scpi  = ":INST:PORT:COUN?"
ports = int(vna.query(scpi)) # => 16
print("Ports:    {0}".format(ports))

def design_screen():
    vna.write("*RST")
    vna.write("*CLS")
    vna.write("SYSTEM:DISPLAY:UPDATE ON")
    vna.query("*IDN?")

    # define stimulus frequency sweep range
    vna.write("FREQ:CENT 6.78MHz")
    vna.write("FREQ:SPAN 100kHz")
    vna.write("")

    # set screen for S11
    vna.write("CALCulate1:PARameter:SDEFine 'TRC1', 'S11'")
    vna.write("CALCulate1:FORMat SMITH")
    vna.write("DISPlay:WINDow1:STATe ON")
    vna.write("DISPlay:WINDow1:TRACe:FEED 'TRC1'")

    # set screen for S12
    vna.write("CALCulate1:PARameter:SDEFine 'TRC2', 'S12'")
    vna.write("CALCulate1:FORMat MLOG")
    vna.write("DISPlay:WINDow2:STATe ON")
    vna.write("DISPlay:WINDow2:TRACe:FEED 'TRC2'")

    # set screen for S21
    vna.write("CALCulate1:PARameter:SDEFine 'TRC3', 'S21'")
    vna.write("CALCulate1:FORMat MLOG")
    vna.write("DISPlay:WINDow3:STATe ON")
    vna.write("DISPlay:WINDow3:TRACe:FEED 'TRC3'")

    # set screen for S22
    vna.write("CALCulate1:PARameter:SDEFine 'TRC4', 'S22'")
    vna.write("CALCulate1:FORMat SMITH")
    vna.write("DISPlay:WINDow4:STATe ON")
    vna.write("DISPlay:WINDow4:TRACe:FEED 'TRC4'")

def read_data():
    # set to single sweep and perform a measurement
    vna.write("INIT:CONT OFF")
    vna.write("INIT")
    print(vna.query("*OPC?"))

    # Read trace 1 S11
    vna.write("CALC1:PAR:SEL 'TRC1'")
    s11_results = np.asarray(vna.query("CALC1:DATA? SDAT").split(","), dtype=float).reshape(201, 2)
    s11 = complex(s11_results[101][0], s11_results[101][1])
    # print(s11)

    # Read trace 2 S12
    vna.write("CALC1:PAR:SEL 'TRC2'")
    s12_results = np.asarray(vna.query("CALC1:DATA? SDAT").split(","), dtype=float).reshape(201, 2)
    s12 = complex(s12_results[101][0], s12_results[101][1])
    # print(s12)

    # Read trace 3 S21
    vna.write("CALC1:PAR:SEL 'TRC3'")
    s21_results = np.asarray(vna.query("CALC1:DATA? SDAT").split(","), dtype=float).reshape(201, 2)
    s21 = complex(s21_results[101][0], s21_results[101][1])
    # print(s21)

    # Read trace 4 S22
    vna.write("CALC1:PAR:SEL 'TRC4'")
    s22_results = np.asarray(vna.query("CALC1:DATA? SDAT").split(","), dtype=float).reshape(201, 2)
    s22 = complex(s22_results[101][0], s22_results[101][1])
    # print(s22)

    return s11, s12, s21, s22


# Read s-parameters
S11, S12, S21, S22 = read_data()

vna.close()

# Convert s-parameters to z-parameters
f = np.array([1, 2, 3, 4])  # in GHz
s = np.zeros((len(f), 2, 2), dtype=complex)

s[:, 0, 0] = S11
s[:, 0, 1] = S12
s[:, 1, 0] = S21
s[:, 1, 1] = S22

s = np.array(s)
z = rf.s2z(s, z0=50)

k = z[0][0][1].imag / m.sqrt(z[0][0][0].imag * z[0][1][1].imag)
print(k)
