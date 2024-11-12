import os
import argparse
from memory import InsMem, DataMem
from single_and_five_stage import SingleStageCore, FiveStageCore
MemSize = 1000

class GenerateMetrics:
    def __init__(self, filePath, ss_cycle, fs_cycle):
        self.newFile = open(filePath + os.sep + "PerformanceMetrics_Result.txt", "w")

        self.newFile.write("Single Stage Core Performance Metrics-----------------------------\n")
        self.newFile.write("Number of cycles: " + str(ss_cycle) + "\n")

        with open(filePath + os.sep + "imem.txt", "r") as fp:
            x = len(fp.readlines()) / 4
        self.newFile.write("Total Number of Instructions: " + str(int(x)) + "\n")
        ss_CPI = ss_cycle / x
        ss_CPI = round(ss_CPI, 5)
        self.newFile.write("Cycles per instruction: " + str(ss_CPI) + "\n")

        ss_IPC = 1 / ss_CPI
        ss_IPC = round(ss_IPC, 6)
        self.newFile.write("Instructions per cycle: " + str(ss_IPC) + "\n")

        self.newFile.write("\nFive Stage Core Performance Metrics-----------------------------\n")
        self.newFile.write("Number of cycles: " + str(fs_cycle) + "\n")
        self.newFile.write("Total Number of Instructions: " + str(int(x)) + "\n")
        fs_CPI = fs_cycle / x
        fs_CPI = round(fs_CPI, 5)
        self.newFile.write("Cycles per instruction: " + str(fs_CPI) + "\n")

        fs_IPC = 1 / fs_CPI
        fs_IPC = round(fs_IPC, 6)
        self.newFile.write("Instructions per cycle: " + str(fs_IPC) + "\n")


# Main function to run the simulation
if __name__ == "__main__":
    # Setup and run the simulation for both single-stage and five-stage cores
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="./input/testcase1", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    filePath = args.iodir
    print("IO Directory:", filePath)

    imem = InsMem("imem", filePath)
    dmem_ss = DataMem("SS", filePath)
    dmem_fs = DataMem("FS", filePath)
    ssCore = SingleStageCore(filePath, imem, dmem_ss, 'SS_')
    fsCore = FiveStageCore(filePath, imem, dmem_fs, 'FS_')

    while 1:
        if not ssCore.halted:
            ss_cycle = ssCore.step()

        if not fsCore.halted:
            fs_cycle = fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    GenerateMetrics(filePath, ss_cycle, fs_cycle)

    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()