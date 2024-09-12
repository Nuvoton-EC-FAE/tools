import sys
import os
import struct
import logging
import argparse

# Define the header IDs and structures
COREDUMP_HDR_ID = b'ZE'
COREDUMP_HDR_VER = 1
LOG_HDR_STRUCT = "<ccHHBBI"
LOG_HDR_SIZE = struct.calcsize(LOG_HDR_STRUCT)

COREDUMP_ARCH_HDR_ID = b'A'
LOG_ARCH_HDR_STRUCT = "<cHH"
LOG_ARCH_HDR_SIZE = struct.calcsize(LOG_ARCH_HDR_STRUCT)

COREDUMP_MEM_HDR_ID = b'M'
COREDUMP_MEM_HDR_VER = 1
LOG_MEM_HDR_STRUCT = "<cH"
LOG_MEM_HDR_SIZE = struct.calcsize(LOG_MEM_HDR_STRUCT)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def parse_memory_section(data, offset, ptr_size):
    hdr = data[offset:offset+LOG_MEM_HDR_SIZE]
    _, hdr_ver = struct.unpack(LOG_MEM_HDR_STRUCT, hdr)

    if hdr_ver != COREDUMP_MEM_HDR_VER:
        logger.error(f"Memory block version: {hdr_ver}, expected {COREDUMP_MEM_HDR_VER}!")
        return None, offset

    ptr_fmt = "QQ" if ptr_size == 64 else "II"
    ptr_size_bytes = 8 if ptr_size == 64 else 4

    offset += LOG_MEM_HDR_SIZE
    addr_data = data[offset:offset+2*ptr_size_bytes]
    saddr, eaddr = struct.unpack(ptr_fmt, addr_data)

    size = eaddr - saddr

    offset += 2*ptr_size_bytes
    mem_data = data[offset:offset+size]

    mem = {"start": saddr, "end": eaddr, "size": size, "data": mem_data}
    
    return mem, offset + size

def analyze_coredump(input_file, output_file, verbose=False):
    try:
        with open(input_file, 'rb') as f:
            data = f.read()

        start_pos = data.find(COREDUMP_HDR_ID)
        if start_pos == -1:
            raise ValueError(f"COREDUMP_HDR_ID not found in {input_file}")

        header = struct.unpack(LOG_HDR_STRUCT, data[start_pos:start_pos+LOG_HDR_SIZE])
        ptr_size = 2 ** header[4]  # ptr_size is at index 4
        
        offset = start_pos + LOG_HDR_SIZE
        memory_regions = []

        while offset < len(data):
            section_id = data[offset:offset+1]
            
            # If we reach padding or unknown section ID, stop parsing
            if section_id == b'\x00':
                logger.info("Reached end or padding. Stopping parsing.")
                break
            
            if section_id == COREDUMP_ARCH_HDR_ID:
                arch_header = struct.unpack(LOG_ARCH_HDR_STRUCT, data[offset:offset+LOG_ARCH_HDR_SIZE])
                offset += LOG_ARCH_HDR_SIZE + arch_header[2]  # Skip ARCH data
            elif section_id == COREDUMP_MEM_HDR_ID:
                mem_data, offset = parse_memory_section(data, offset, ptr_size)
                if mem_data:
                    memory_regions.append(mem_data)
            else:
                logger.warning(f"Unknown section ID: {section_id}")
                break

        if verbose:
            logger.info(f"Main Header: {header}")
            logger.info(f"Pointer size: {ptr_size} bits")
            logger.info(f"ARCH Header: {arch_header}")
            logger.info("\nMemory Regions:")
            for i, region in enumerate(memory_regions, 1):
                logger.info(f"Region {i}:")
                logger.info(f"  Start address: 0x{region['start']:x}")
                logger.info(f"  End address: 0x{region['end']:x}")
                logger.info(f"  Size: {region['size']} bytes")
                logger.info(f"  Data (first 16 bytes): {region['data'][:16].hex()}")
                logger.info("")

        with open(output_file, 'wb') as f:
            f.write(data[start_pos:offset])

        logger.info(f"Processed coredump saved to {output_file}")

    except FileNotFoundError:
        logger.error(f"Error: The file '{input_file}' does not exist.")
    except ValueError as ve:
        logger.error(f"Error: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Analyze and strip coredump file")
    parser.add_argument("input_file", help="Input coredump file")
    parser.add_argument("output_file", nargs="?", help="Output file (optional)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--strip", action="store_true", help="Strip the coredump file (mandatory to execute the workflow)")

    args = parser.parse_args()

    # --strip must be specified to execute the workflow
    if not args.strip:
        parser.print_help()
        sys.exit(1)

    input_file = args.input_file
    if args.output_file:
        output_file = args.output_file
    else:
        base_name, ext = os.path.splitext(input_file)
        output_file = f"{base_name}_final{ext}"

    analyze_coredump(input_file, output_file, args.verbose)

if __name__ == "__main__":
    main()
