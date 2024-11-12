import os
import argparse
from utils import BinaryConverter
from state import State

class RegisterFile:
    # Constructor and methods to read and write register file
    def __init__(self, iodir, identifier):
        # self.outputFile = opDir + identifier +"RFResult.txt"
        self.outputFile = os.path.join(iodir, identifier + "RFResult.txt")
        self.Registers = ["".join(["0" for x in range(32)]) for i in range(32)]

    def readRF(self, Reg_addr):
        return int(self.Registers[Reg_addr], 2)

    def writeRF(self, Reg_addr, Wrt_reg_data):
        if Reg_addr == 0:
            return
        self.Registers[Reg_addr] = BinaryConverter().toBinaryString(Wrt_reg_data, 32)
        pass

    def outputRF(self, cycle):
        op = ["-" * 70 + "\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend([str(val) + "\n" for val in self.Registers])
        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class Core():
    # Constructor and core functionalities
    def __init__(self, filePath, imem, dmem, identifier):
        self.myRF = RegisterFile(filePath, identifier)
        self.cycle = 0
        self.halted = False
        self.filePath = filePath
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem
        self.state.IF["nop"] = False
        self.pipelinereg = PipelineRegisters()
        self.hazarddetect = HazardDetector()


class SingleStageCore(Core):
    # Constructor and methods for single-stage core operations
    def __init__(self, filePath, imem, dmem, identifier):
        super(SingleStageCore, self).__init__(filePath, imem, dmem, identifier)
        self.opFilePath = filePath + "/StateResult_SS.txt"

    def InstructionFetch(self):

        self.state.ID["Instr"] = self.ext_imem.readInstr(self.state.IF["PC"])
        instructionReverse = self.state.ID["Instr"][::-1]
        opcode = instructionReverse[0:7]

        if opcode == "1111111":
            self.nextState.IF["PC"] = self.state.IF["PC"]
            self.nextState.IF["nop"] = True

        else:
            self.nextState.IF["nop"] = False
            self.nextState.IF["PC"] = self.state.IF["PC"] + 4
            self.state.ID["nop"] = False

    def InstructionDecode(self):
        self.state.EX["nop"] = self.state.ID["nop"]

        if not self.state.ID["nop"]:
            instructionReverse = self.state.ID["Instr"][::-1]
            opcode = instructionReverse[0:7]

            # R-type instruction
            if opcode == "1100110":
                rs1 = instructionReverse[15:20][::-1]
                rs2 = instructionReverse[20:25][::-1]
                rd = instructionReverse[7:12][::-1]
                func7 = instructionReverse[25:32][::-1]
                func3 = instructionReverse[12:15][::-1] + func7[1]

                aluContol = {"0000": "0010", "0001": "0110", "1110": "0000", "1100": "0001", "1000": "0011"}
                self.state.EX = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                 "Read_data2": self.myRF.readRF(int(rs2, 2)),
                                 "imm": "X", "Rs": 0, "Rt": 0, "pcJump": 0,
                                 "is_I_type": False, "rd_mem": 0, "aluSource": 0, "aluControl": aluContol[func3],
                                 "alu_op": "10",
                                 "Wrt_reg_addr": int(rd, 2), "wrt_mem": 0, "registerWrite": 1, "branch": 0, "memReg": 0}

            # I-type instruction
            if opcode == "1100100":
                rs1 = instructionReverse[15:20][::-1]
                imm = instructionReverse[20:32][::-1]
                rd = instructionReverse[7:12][::-1]
                func3 = instructionReverse[12:15][::-1]

                aluContol = {"000": "0010", "111": "0000", "110": "0001", "100": "0011"}
                self.state.EX = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)), "Read_data2": 0,
                                 "imm": BinaryConverter().binaryToTwosComplement(imm, 12), "Rs": 0, "Rt": 0, "pcJump": 0,
                                 "is_I_type": True, "rd_mem": 0, "aluSource": 1, "aluControl": aluContol[func3],
                                 "alu_op": "00",
                                 "Wrt_reg_addr": int(rd, 2), "wrt_mem": 0, "registerWrite": 1, "branch": 0, "memReg": 0}

            # I-type instruction
            if opcode == "1100000":
                rs1 = instructionReverse[15:20][::-1]
                imm = instructionReverse[20:32][::-1]
                rd = instructionReverse[7:12][::-1]

                self.state.EX = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)), "Read_data2": 0,
                                 "imm": BinaryConverter().binaryToTwosComplement(imm, 12), "Rs": 0, "Rt": 0, "pcJump": 0,
                                 "is_I_type": False, "rd_mem": 1, "aluSource": 1, "aluControl": "0010", "alu_op": "00",
                                 "Wrt_reg_addr": int(rd, 2), "wrt_mem": 0, "registerWrite": 1, "branch": 0, "memReg": 1}

            # S-type instruction
            if opcode == "1100010":
                rs1 = instructionReverse[15:20][::-1]
                rs2 = instructionReverse[20:25][::-1]
                imm = instructionReverse[7:12] + instructionReverse[25:32]
                imm = imm[::-1]

                self.state.EX = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                 "Read_data2": self.myRF.readRF(int(rs2, 2)),
                                 "imm": int(imm, 2), "Rs": 0, "Rt": 0, "pcJump": 0,
                                 "is_I_type": False, "rd_mem": 0, "aluSource": 1, "aluControl": "0010", "alu_op": "00",
                                 "Wrt_reg_addr": "X", "wrt_mem": 1, "registerWrite": 0, "branch": 0, "memReg": "X"}

                # SB-type instruction
            if opcode == "1100011":
                rs1 = instructionReverse[15:20][::-1]
                rs2 = instructionReverse[20:25][::-1]
                imm = "0" + instructionReverse[8:12] + instructionReverse[25:31] + instructionReverse[7] + \
                      instructionReverse[31]  # check
                imm = imm[::-1]
                func3 = instructionReverse[12:15][::-1]

                self.state.EX = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                 "Read_data2": self.myRF.readRF(int(rs2, 2)),
                                 "imm": "X", "Rs": 0, "Rt": 0, "pcJump": BinaryConverter().binaryToTwosComplement(imm, 13),
                                 "is_I_type": False, "rd_mem": 0, "aluSource": 0, "aluControl": "0110", "alu_op": "01",
                                 "Wrt_reg_addr": "X", "wrt_mem": 0, "registerWrite": 0, "branch": 1, "memReg": "X",
                                 "func3": func3}
            # UJ-type instruction
            if opcode == "1111011":
                rs1 = instructionReverse[15:20][::-1]
                rd = instructionReverse[7:12][::-1]
                imm = "0" + instructionReverse[21:31] + instructionReverse[20] + instructionReverse[12:20] + \
                      instructionReverse[31]  # check
                imm = imm[::-1]

                self.state.EX = {"nop": False, "Read_data1": self.state.IF['PC'], "Read_data2": 4,
                                 "imm": "X", "Rs": 0, "Rt": 0, "pcJump": BinaryConverter().binaryToTwosComplement(imm, 21),
                                 "is_I_type": False, "rd_mem": 0, "aluSource": 1, "aluControl": "0010", "alu_op": "10",
                                 "Wrt_reg_addr": int(rd, 2), "wrt_mem": 0, "registerWrite": 1, "branch": 1, "memReg": 0,
                                 "func3": "X"}

    def InstructionExecute(self):
        self.state.MEM["nop"] = self.state.EX["nop"]
        if not self.state.EX["nop"]:
            if self.state.EX["imm"] != "X":
                op2 = self.state.EX["imm"]
            else:
                op2 = self.state.EX["Read_data2"]

            # addition
            if self.state.EX["aluControl"] == "0010":
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] + op2

            # subtraction
            if self.state.EX["aluControl"] == "0110":
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] - op2

            # and operation
            if self.state.EX["aluControl"] == "0000":
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] & op2

            # or operation
            if self.state.EX["aluControl"] == "0001":
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] | op2

            # xor operation
            if self.state.EX["aluControl"] == "0011":
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] ^ op2

            # branch
            if self.state.EX["branch"]:
                if self.state.EX["func3"] == "000" and self.state.MEM["ALUresult"] == 0:
                    self.nextState.IF["PC"] = self.state.IF["PC"] + (self.state.EX["pcJump"])
                    self.nextState.IF["nop"] = False
                    self.state.MEM["nop"] = True

                elif self.state.EX["func3"] == "001" and self.state.MEM["ALUresult"] != 0:
                    self.nextState.IF["PC"] = self.state.IF["PC"] + (self.state.EX["pcJump"])
                    self.nextState.IF["nop"] = False
                    self.state.MEM["nop"] = True

                elif self.state.EX["func3"] == "X":
                    self.nextState.IF["nop"] = False
                    self.nextState.IF["PC"] = self.state.IF["PC"] + (self.state.EX["pcJump"])

            self.state.MEM["rd_mem"] = self.state.EX["rd_mem"]
            self.state.MEM["wrt_mem"] = self.state.EX["wrt_mem"]

    def LoadStore(self):
        self.state.WB["nop"] = self.state.MEM["nop"]
        if not self.state.MEM["nop"]:
            if self.state.MEM["wrt_mem"]:
                writeData = self.state.EX["Read_data2"]
                writeAddress = self.state.MEM["ALUresult"]
                self.ext_dmem.writeDataMem(writeAddress, writeData)
            if self.state.MEM["rd_mem"]:
                readAddress = self.state.MEM["ALUresult"]
                self.state.MEM["Wrt_data"] = self.ext_dmem.readDataMem(readAddress)
            self.state.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
            self.state.WB["registerWrite"] = self.state.EX["registerWrite"]
            self.state.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
        else:
            self.state.WB["nop"] = True

    def WriteBack(self):
        if not self.state.WB["nop"]:
            if self.state.WB["registerWrite"]:
                Reg_addr = self.state.WB["Wrt_reg_addr"]
                if self.state.EX["memReg"]:
                    Wrt_reg_data = self.state.MEM["Wrt_data"]
                else:
                    Wrt_reg_data = self.state.MEM["ALUresult"]
                self.myRF.writeRF(Reg_addr, Wrt_reg_data)

    def step(self):

        # Your implementation
        self.InstructionFetch()
        self.InstructionDecode()
        self.InstructionExecute()
        self.LoadStore()
        self.WriteBack()

        if self.state.IF["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)
        self.printState(self.nextState, self.cycle)

        self.state = self.nextState
        self.nextState = State()
        self.cycle += 1

        return self.cycle

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

#A class for pipeline
class PipelineRegisters:

    def __init__(self):
        self.fetchToDecode = {"PC": 0, "rawInstruction": 0}
        self.decodeToExecute = {"PC": 0, "instruction": 0, "source1": 0, "source2": 0}
        self.executeToMemory = {"PC": 0, "instruction": 0, "aluResult": 0, "source2": 0}
        self.memoryToWriteBack = {"PC": 0, "instruction": 0, "writeData": 0, "aluResult": 0, "source2": 0}

# Define a class to detect pipeline hazards
class HazardDetector():
    # Methods to detect various hazard types
    def detectRegWriteHazard(self, pipelineState: PipelineRegisters, sourceReg):
        return sourceReg != 0 and pipelineState.memoryToWriteBack["instruction"] and \
            pipelineState.memoryToWriteBack["instruction"]["registerWrite"] and \
            pipelineState.memoryToWriteBack["instruction"]["Wrt_reg_addr"] == sourceReg

    def detectLoadHazard(self, pipelineState: PipelineRegisters, srcReg1, srcReg2):
        return pipelineState.decodeToExecute["instruction"] and pipelineState.decodeToExecute["instruction"]["rd_mem"] and \
            (pipelineState.decodeToExecute["instruction"]["Wrt_reg_addr"] == int(srcReg1, 2) or \
             pipelineState.decodeToExecute["instruction"]["Wrt_reg_addr"] == int(srcReg2, 2))

    def detectMemoryHazard(self, pipelineState: PipelineRegisters, sourceReg):
        return pipelineState.memoryToWriteBack["instruction"] and pipelineState.memoryToWriteBack["instruction"]["registerWrite"] and \
            pipelineState.memoryToWriteBack["instruction"]["Wrt_reg_addr"] != 0 and \
            pipelineState.memoryToWriteBack["instruction"]["Wrt_reg_addr"] == sourceReg

    def detectEXHazard(self, pipelineState: PipelineRegisters, sourceReg):
        return pipelineState.executeToMemory["instruction"] and pipelineState.executeToMemory["instruction"]["registerWrite"] and \
            not pipelineState.executeToMemory["instruction"]["rd_mem"] and \
            pipelineState.executeToMemory["instruction"]["Wrt_reg_addr"] != 0 and \
            pipelineState.executeToMemory["instruction"]["Wrt_reg_addr"] == sourceReg


class FiveStageCore(Core):

    def __init__(self, filePath, imem, dmem, identifier):
        super(FiveStageCore, self).__init__(filePath, imem, dmem, identifier)
        self.opFilePath = filePath + "/StateResult_FS.txt"

    #IF
    def InstructionFetch(self):
        self.nextState.ID["nop"] = self.state.IF["nop"]

        if not self.state.IF["nop"]:
            self.pipelinereg.fetchToDecode["rawInst"] = self.ext_imem.readInstr(self.state.IF["PC"])
            self.pipelinereg.fetchToDecode["PC"] = self.state.IF["PC"]
            instructionReverse = self.pipelinereg.fetchToDecode["rawInst"][::-1]

            opcode = instructionReverse[0:7]
            if opcode == "1111111":
                self.nextState.ID["nop"] = self.state.IF["nop"] = True

            else:
                self.nextState.IF["nop"] = False
                self.nextState.IF["PC"] = self.state.IF["PC"] + 4

                if self.hazarddetect.detectLoadHazard(self.pipelinereg, instructionReverse[15:20][::-1],
                                                instructionReverse[20:25][::-1]):
                    self.nextState.ID["nop"] = True
                    self.nextState.IF["PC"] = self.state.IF["PC"]

    #ID
    def InstructionDecode(self):
        self.nextState.EX["nop"] = self.state.ID["nop"]

        if not self.state.ID["nop"]:
            instructionReverse = self.pipelinereg.fetchToDecode["rawInst"][::-1]
            self.pipelinereg.decodeToExecute["PC"] = self.pipelinereg.fetchToDecode["PC"]
            pc = self.pipelinereg.fetchToDecode["PC"]
            opcode = instructionReverse[0:7]

            # R-type instruction
            if opcode == "1100110":
                rs1 = instructionReverse[15:20][::-1]
                rs2 = instructionReverse[20:25][::-1]
                rd = instructionReverse[7:12][::-1]
                func7 = instructionReverse[25:32][::-1]
                func3 = instructionReverse[12:15][::-1] + func7[1]

                aluContol = {"0000": "0010", "0001": "0110", "1110": "0000", "1100": "0001", "1000": "0011"}
                self.pipelinereg.decodeToExecute["instruction"] = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                                         "Read_data2": self.myRF.readRF(int(rs2, 2)),
                                                         "imm": "X", "pcJump": 0, "Rs": int(rs1, 2), "Rt": int(rs2, 2),
                                                         "Wrt_reg_addr": int(rd, 2), "is_I_type": False, "rd_mem": 0,
                                                         "aluSource": 0, "aluControl": aluContol[func3],
                                                         "wrt_mem": 0, "alu_op": "10", "registerWrite": 1, "branch": 0,
                                                         "memReg": 0}

            # I-type instruction
            if opcode == "1100100":
                rs1 = instructionReverse[15:20][::-1]
                imm = instructionReverse[20:32][::-1]
                rd = instructionReverse[7:12][::-1]
                func3 = instructionReverse[12:15][::-1]

                aluContol = {"000": "0010", "111": "0000", "110": "0001", "100": "0011"}
                self.pipelinereg.decodeToExecute["instruction"] = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                                         "Read_data2": 0,
                                                         "imm": BinaryConverter().binaryToTwosComplement(imm, 12), "pcJump": 0,
                                                         "Rs": int(rs1, 2),
                                                         "Rt": 0,
                                                         "Wrt_reg_addr": int(rd, 2), "is_I_type": True, "rd_mem": 0,
                                                         "aluSource": 1, "aluControl": aluContol[func3],
                                                         "wrt_mem": 0, "alu_op": "00", "registerWrite": 1, "branch": 0,
                                                         "memReg": 0}

            # I-type instruction
            if opcode == "1100000":
                rs1 = instructionReverse[15:20][::-1]
                imm = instructionReverse[20:32][::-1]
                rd = instructionReverse[7:12][::-1]
                func3 = instructionReverse[12:15][::-1]

                self.pipelinereg.decodeToExecute["instruction"] = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                                         "Read_data2": 0,
                                                         "imm": BinaryConverter().binaryToTwosComplement(imm, 12), "pcJump": 0,
                                                         "Rs": int(rs1, 2),
                                                         "Rt": 0,
                                                         "Wrt_reg_addr": int(rd, 2), "is_I_type": False, "rd_mem": 1,
                                                         "aluSource": 1, "aluControl": "0010",
                                                         "wrt_mem": 0, "alu_op": "00", "registerWrite": 1, "branch": 0,
                                                         "memReg": 1}

            # S-type instruction
            if opcode == "1100010":
                rs1 = instructionReverse[15:20][::-1]
                rs2 = instructionReverse[20:25][::-1]
                imm = instructionReverse[7:12] + instructionReverse[25:32]
                imm = imm[::-1]

                self.pipelinereg.decodeToExecute["instruction"] = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                                         "Read_data2": self.myRF.readRF(int(rs2, 2)),
                                                         "imm": int(imm, 2), "Rs": int(rs1, 2), "Rt": int(rs2, 2),
                                                         "pcJump": 0,
                                                         "is_I_type": False, "rd_mem": 0, "aluSource": 1,
                                                         "aluControl": "0010", "alu_op": "00",
                                                         "Wrt_reg_addr": "X", "wrt_mem": 1, "registerWrite": 0,
                                                         "branch": 0, "memReg": "X"}

            # SB-type instruction
            if opcode == "1100011":
                rs1 = instructionReverse[15:20][::-1]
                rs2 = instructionReverse[20:25][::-1]
                imm = "0" + instructionReverse[8:12] + instructionReverse[25:31] + instructionReverse[7] + \
                      instructionReverse[31]
                imm = imm[::-1]
                func3 = instructionReverse[12:15][::-1]

                self.pipelinereg.decodeToExecute["instruction"] = {"nop": False, "Read_data1": self.myRF.readRF(int(rs1, 2)),
                                                         "Read_data2": self.myRF.readRF(int(rs2, 2)),
                                                         "imm": "X", "Rs": int(rs1, 2), "Rt": int(rs2, 2),
                                                         "pcJump": BinaryConverter().binaryToTwosComplement(imm, 13),
                                                         "is_I_type": False, "rd_mem": 0, "aluSource": 0,
                                                         "aluControl": "0110", "alu_op": "01",
                                                         "Wrt_reg_addr": "X", "wrt_mem": 0, "registerWrite": 0,
                                                         "branch": 1, "memReg": "X", "func3": func3}

            # UJ-type instruction
            if opcode == "1111011":
                rs1 = instructionReverse[15:20][::-1]
                imm = "0" + instructionReverse[21:31] + instructionReverse[20] + instructionReverse[12:20] + \
                      instructionReverse[31]
                imm = imm[::-1]
                rd = instructionReverse[7:12][::-1]

                self.pipelinereg.decodeToExecute["instruction"] = {"nop": False, "Read_data1": pc, "Read_data2": 4,
                                                         "imm": "X", "Rs": 0, "Rt": 0,
                                                         "pcJump": BinaryConverter().binaryToTwosComplement(imm, 21),
                                                         "is_I_type": False, "rd_mem": 0, "aluSource": 1,
                                                         "aluControl": "0010", "alu_op": "10",
                                                         "Wrt_reg_addr": int(rd, 2), "wrt_mem": 0, "registerWrite": 1,
                                                         "branch": 1, "memReg": 0, "func3": "X"}

            if self.hazarddetect.detectRegWriteHazard(
                    self.pipelinereg, self.pipelinereg.decodeToExecute["instruction"]["Rs"]
            ):
                self.pipelinereg.decodeToExecute["instruction"]["Read_data1"] = self.pipelinereg.memoryToWriteBack["Wrt_data"]

            if self.hazarddetect.detectRegWriteHazard(
                    self.pipelinereg, self.pipelinereg.decodeToExecute["instruction"]["Rt"]
            ):
                self.pipelinereg.decodeToExecute["instruction"]["Read_data2"] = self.pipelinereg.memoryToWriteBack["Wrt_data"]

            self.pipelinereg.decodeToExecute["Rs1"] = self.pipelinereg.decodeToExecute["instruction"]["Rs"]
            self.pipelinereg.decodeToExecute["Rs2"] = self.pipelinereg.decodeToExecute["instruction"]["Rt"]

            if self.hazarddetect.detectEXHazard(
                    self.pipelinereg, self.pipelinereg.decodeToExecute["Rs1"]
            ):
                self.pipelinereg.decodeToExecute["instruction"]["Read_data1"] = self.pipelinereg.executeToMemory["ALUresult"]

            elif self.hazarddetect.detectMemoryHazard(
                    self.pipelinereg, self.pipelinereg.decodeToExecute["Rs1"]
            ):
                self.pipelinereg.decodeToExecute["instruction"]["Read_data1"] = self.pipelinereg.memoryToWriteBack["Wrt_data"]

            if self.pipelinereg.decodeToExecute["instruction"]["imm"] == "X":
                if self.hazarddetect.detectEXHazard(self.pipelinereg, self.pipelinereg.decodeToExecute["Rs2"]):
                    self.pipelinereg.decodeToExecute["instruction"]["Read_data2"] = self.pipelinereg.executeToMemory["ALUresult"]

                elif self.hazarddetect.detectMemoryHazard(self.pipelinereg, self.pipelinereg.decodeToExecute["Rs2"]):
                    self.pipelinereg.decodeToExecute["instruction"]["Read_data2"] = self.pipelinereg.memoryToWriteBack["Wrt_data"]

            if self.pipelinereg.decodeToExecute["instruction"]["branch"]:
                if self.pipelinereg.decodeToExecute["instruction"]["func3"] == "000" and self.pipelinereg.decodeToExecute["instruction"][
                    "Read_data1"] - self.pipelinereg.decodeToExecute["instruction"]["Read_data2"] == 0:
                    self.nextState.IF["nop"] = False
                    self.nextState.IF["PC"] = pc + (self.pipelinereg.decodeToExecute["instruction"]["pcJump"])
                    self.state.IF["nop"] = self.nextState.EX["nop"] = self.nextState.ID["nop"] = True

                elif self.pipelinereg.decodeToExecute["instruction"]["func3"] == "001" and self.pipelinereg.decodeToExecute["instruction"][
                    "Read_data1"] - self.pipelinereg.decodeToExecute["instruction"]["Read_data2"] != 0:
                    self.nextState.IF["nop"] = False
                    self.nextState.IF["PC"] = pc + (self.pipelinereg.decodeToExecute["instruction"]["pcJump"])
                    self.state.IF["nop"] = self.nextState.EX["nop"] = self.nextState.ID["nop"] = True

                elif self.pipelinereg.decodeToExecute["instruction"]["func3"] == "X":
                    self.nextState.IF["nop"] = False
                    self.nextState.IF["PC"] = pc + (self.pipelinereg.decodeToExecute["instruction"]["pcJump"])
                    self.state.IF["nop"] = self.nextState.ID["nop"] = True

                else:
                    self.nextState.EX["nop"] = True

        else:
            self.pipelinereg.decodeToExecute = {"PC": 0, "instruction": 0, "rs": 0, "rt": 0}

    #EX
    def InstructionExecute(self):

        self.nextState.MEM["nop"] = self.state.EX["nop"]

        if not self.state.EX["nop"]:
            pc = self.pipelinereg.decodeToExecute["PC"]
            instruction = self.pipelinereg.decodeToExecute["instruction"]
            rs2 = self.pipelinereg.decodeToExecute["Rs2"]
            self.state.EX = self.pipelinereg.decodeToExecute["instruction"]

            if self.state.EX["imm"] != "X":
                op2 = self.state.EX["imm"]

            else:
                op2 = self.state.EX["Read_data2"]

            # addition
            if self.state.EX["aluControl"] == "0010":
                alu_result = self.state.EX["Read_data1"] + op2

            # subtraction
            if self.state.EX["aluControl"] == "0110":
                alu_result = self.state.EX["Read_data1"] - op2

            # and
            if self.state.EX["aluControl"] == "0000":
                alu_result = self.state.EX["Read_data1"] & op2

            # or
            if self.state.EX["aluControl"] == "0001":
                alu_result = self.state.EX["Read_data1"] | op2

            # xor
            if self.state.EX["aluControl"] == "0011":
                alu_result = self.state.EX["Read_data1"] ^ op2

            self.pipelinereg.executeToMemory["PC"] = pc
            self.pipelinereg.executeToMemory["instruction"] = instruction
            self.pipelinereg.executeToMemory["ALUresult"] = alu_result
            self.pipelinereg.executeToMemory["Rs2"] = rs2

    #MEM
    def LoadStore(self):

        self.nextState.WB["nop"] = self.state.MEM["nop"]

        if not self.state.MEM["nop"]:
            pc = self.pipelinereg.executeToMemory["PC"]
            instruction = self.pipelinereg.executeToMemory["instruction"]
            alu_result = self.pipelinereg.executeToMemory["ALUresult"]
            rs2 = self.pipelinereg.executeToMemory["Rs2"]

            if instruction["wrt_mem"]:
                writeData = self.myRF.readRF(rs2)
                writeAddress = alu_result
                self.ext_dmem.writeDataMem(writeAddress, writeData)

            if instruction["rd_mem"]:
                readAddress = alu_result
                wrt_mem_data = self.ext_dmem.readDataMem(readAddress)

            if instruction["memReg"] == 1:
                self.pipelinereg.memoryToWriteBack["Wrt_data"] = wrt_mem_data

            else:
                self.pipelinereg.memoryToWriteBack["Wrt_data"] = alu_result

            self.pipelinereg.memoryToWriteBack["PC"] = pc
            self.pipelinereg.memoryToWriteBack["instruction"] = instruction

    #WB
    def WriteBack(self):

        if not self.state.WB["nop"]:
            instruction = self.pipelinereg.memoryToWriteBack["instruction"]

            if instruction["registerWrite"]:
                Reg_addr = instruction["Wrt_reg_addr"]
                Wrt_reg_data = self.pipelinereg.memoryToWriteBack["Wrt_data"]
                self.myRF.writeRF(Reg_addr, Wrt_reg_data)

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------
        self.WriteBack()

        # --------------------- MEM stage --------------------
        self.LoadStore()

        # --------------------- EX stage ---------------------
        self.InstructionExecute()

        # --------------------- ID stage ---------------------
        self.InstructionDecode()

        # --------------------- IF stage ---------------------
        self.InstructionFetch()

        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and \
                self.state.WB["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)
        self.PrintState(self.pipelinereg, self.cycle)
        self.state = self.nextState
        self.nextState = State()
        self.cycle += 1

        return self.cycle

    def PrintState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["fetchToDecode" + key + ": " + str(val) + "\n" for key, val in state.fetchToDecode.items()])
        printstate.extend(["decodeToExecute" + key + ": " + str(val) + "\n" for key, val in state.decodeToExecute.items()])
        printstate.extend(["executeToMemory" + key + ": " + str(val) + "\n" for key, val in state.executeToMemory.items()])
        printstate.extend(["memoryToWriteBack" + key + ": " + str(val) + "\n" for key, val in state.memoryToWriteBack.items()])

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)