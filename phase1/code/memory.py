
import os
import argparse
from utils import BinaryConverter
MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.
#initialize the instruction memory
class InsMem:
    # Constructor and method to read instruction memory
    def __init__(self, name, iodir):
        self.identifier = name
        self.filePath = iodir
        with open(self.filePath + os.sep + "imem.txt") as im:
            self.InstrMemory = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        # read instruction memory
        # return 32 bit hex val
        return "".join(self.InstrMemory[ReadAddress - ReadAddress % 4 : ReadAddress - ReadAddress % 4 + 4])


class DataMem:
    # Constructor and methods to read and write data memory
    def __init__(self, name, iodir):
        self.identifier = name
        self.filePath = iodir
        with open(self.filePath + os.sep + "dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

        self.DMem.extend(['00000000' for i in range(MemSize - len(self.DMem))])

    def readDataMem(self, ReadAddress):
        # read data memory
        # return 32 bit hex val
        return int("".join(self.DMem[ReadAddress - ReadAddress % 4 : ReadAddress - ReadAddress % 4 + 4]), 2)

    def writeDataMem(self, address, WriteData):
        # write data into byte addressable memory
        WriteData = BinaryConverter().toBinaryString(WriteData, 32)
        for i in range(4):
            self.DMem[address - address % 4 + i] = WriteData[8 * i:8 * i + 8]
        pass

    def outputDataMem(self):
        #resPath = os.path.join(self.opDir)
        resPath = os.path.join(self.filePath, self.identifier + "_DMEMResult.txt")

        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])