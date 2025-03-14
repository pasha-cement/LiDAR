from scipy import interpolate
import numpy as np
import pandas as pd
import serial
import time
import libscrc
import logging

logging.basicConfig(level=logging.INFO)

class DevReader:
    def __init__(self, filename: str) -> None:
        self.__dev = pd.read_csv(filename, sep="\t")
        self.__angle_interpolator = interpolate.CubicSpline(self.__dev["Frequency"], self.__dev["Angle"])
        
    def get_freq_by_angle(self, angle: float) -> float:
        return self.__angle_interpolator.solve(angle)[1]
    
    def get_ampl_by_freq(self, freq: float) -> float:
        return np.interp(freq, self.__dev["Frequency"], self.__dev["Amplitude"])

class Deflector:
    def __init__(self, dev_filename: str, port: str) -> None:
        self.__dev_reader = DevReader(dev_filename)
        self.__serial = serial.Serial(port, baudrate=115200)
    
    def __make_command(self, type: int, data: list[int]) -> list[int]:
        buffer = [0xAA, len(data), type, *data, 0]
        buffer[-1] = self.calculate_crc8(buffer[:-1])
        return buffer
    
    def __send_command(self, buffer: list[int]) -> None:
            self.__serial.write(bytearray(buffer))
            time.sleep(0.01)

    def calculate_crc8(self, data: list[int]) -> int:
        return libscrc.hacker8(bytes(data), poly=0x31, init=0xFF)

    def start(self) -> None:
        preamp_on_command = self.__make_command(0xA2, [1])
        amp_on_command = self.__make_command(0xA3, [1])
        self.__send_command(preamp_on_command)
        self.__send_command(amp_on_command)
    
    def set_freq(self, freq:float) -> None:
        try:
            freq_bytes = int(freq * 100).to_bytes(2, 'little')
            set_freq_command = self.__make_command(0xA5, list(freq_bytes))
            self.__send_command(set_freq_command)
        except:
            self.stop()
            self.close()

    def set_angle(self, angle:float) -> None:
        freq = self.__dev_reader.get_freq_by_angle(angle)
        self.set_freq(freq)
    
    def set_ampl(self, ampl: float) -> None:
        try:
            ampl_bytes = int(ampl * 10).to_bytes(2, 'little')
            set_ampl_command = self.__make_command(0xA7, list(ampl_bytes))
            self.__send_command(set_ampl_command)
        except:
            self.stop()
            self.close()    
            
    def stop(self) -> None:
        preamp_off_command = self.__make_command(0xA2, [0])
        amp_off_command = self.__make_command(0xA3, [0])
        self.__send_command(preamp_off_command)
        self.__send_command(amp_off_command)
    
    def close(self) -> None:
        self.__serial.close()


if __name__ == "__main__":
    deflector = Deflector("AOD.dev", "COM31")
    deflector.start()
    for angle in np.linspace(-0.4, 0.4, 5):
        deflector.set_angle(angle)
        time.sleep(1)
    deflector.stop()
    deflector.close()

