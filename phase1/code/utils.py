class BinaryConverter:
    # Convert a number to a binary string with a specified number of bits
    def toBinaryString(self, n, bits):
        s = bin(n & int("1" * bits, 2))[2:]
        return ("{0:0>%s}" % (bits)).format(s)

    # Convert binary to two's complement representation
    def binaryToTwosComplement(self, bin, digit):
        while len(bin) < digit:
            bin = '0' + bin

        if bin[0] == '0':
            return int(bin, 2)
        else:
            return -1 * (int(''.join('1' if x == '0' else '0' for x in bin), 2) + 1)