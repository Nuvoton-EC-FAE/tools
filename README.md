# Tools

Nuvoton Tools For Zephyr

## Support Environments

* Windows: ECPAD.exe / imgtool
* Linux: imgtool

## Imgtool Usage

```
usage: imgtool.py [-h] 
                  [--resize INPUT_FILE OUTPUT_FILE SIZE] 
                  [--append INPUT_FILE_A INPUT_FILE_B OUTPUT_FILE OFFSET]
                  [--merge INPUT_FILE_A INPUT_FILE_B OUTPUT_FILE OFFSET] 
                  [--replace INPUT_FILE_A INPUT_FILE_B OUTPUT_FILE OFFSET]
                  [--sign ARG [ARG ...]] 
                  [-v] 
                  [-a ALIGN] 
                  [-c PAD_BYTE]

Nuvoton Image Tool For Binary File.

options:
  -h, --help      show this help message and exit
  --resize        Resize a binary file to a specific size with alignment.
  --append        Append file B to file A at a specified offset.
  --merge         Merge file B into file A at a specified offset.
  --replace       Replace the content of file A with file B starting at a specified offset.
  --sign          Calculate signature (CRC/CHECKSUM) for input file. Usage: --sign INPUT_FILE SIGNATURE_TYPE [OUTPUT_FILE] If
                  OUTPUT_FILE is provided, write the signed file.
  -v, --verbose   Enable verbose output for debugging.
  -a, --align     Alignment value (default: 16 bytes).
  -c, --pad_byte  Padding byte (default: 0x00).

```
