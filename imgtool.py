# imgtools.py

import os
import shutil
from pathlib import Path
from imgtool_args import ImgToolArgs
from tempfile import NamedTemporaryFile
import struct
import zlib

# Sign mode related values
SIGN_CRC = "crc"
SIGN_CHECKSUM = "checksum"
SIGN_RSA_2048 = "rsa2048"
SIGN_RSA_3072 = "rsa3072"
SIGN_SIGN_OFF = "off"
SIGN_RESERVED_VALUE = 0


def parse_hexadecimal(value):
    """Convert hexadecimal string (starting with '0x') or decimal string to integer."""
    try:
        return int(value, 16) if value.lower().startswith('0x') else int(value)
    except ValueError:
        raise ValueError(f"Invalid numeric value: {value}")


def resize_binary_file(input_path, output_path, target_size, imgtool_args):
    """Resize a binary file to a specified size and apply alignment."""
    target_size = parse_hexadecimal(target_size)
    current_size = Path(input_path).stat().st_size
    PAD_BYTE = bytes([int(imgtool_args.pad_byte, 16)])

    if imgtool_args.verbose:
        print(f"Resizing to: {target_size} bytes (0x{target_size:x}).")

    if current_size > target_size:
        raise ValueError(f"Current size {current_size}(0x{current_size:x}) bytes is larger than the target size {target_size}(0x{target_size:x}) bytes.")

    padding_size = target_size - current_size
    alignment_padding = (imgtool_args.align - (target_size % imgtool_args.align)) % imgtool_args.align

    with open(output_path, "wb") as file_out:
        with open(input_path, "rb") as file_in:
            file_out.write(file_in.read())
        file_out.write(PAD_BYTE * padding_size)
        file_out.write(PAD_BYTE * alignment_padding)

    if imgtool_args.verbose:
        print(f"File resized and aligned to {imgtool_args.align}-byte boundary, final size: {target_size + alignment_padding}(0x{(target_size + alignment_padding):x}) bytes.")


def append_to_file(base_path, append_path, output_path, offset, imgtool_args):
    """Append content of one file to another at a specified offset and apply alignment, handling same input and output paths safely."""
    offset = parse_hexadecimal(offset)
    base_size = Path(base_path).stat().st_size
    PAD_BYTE = bytes([int(imgtool_args.pad_byte, 16)])

    if offset < base_size:
        raise ValueError(f"Offset {offset}(0x{offset:x}) bytes must be larger than the base file size {base_size}(0x{base_size:x}) bytes.")

    with NamedTemporaryFile(delete=False) as temp_file:
        with open(base_path, 'rb') as file_base:
            temp_file.write(file_base.read())  # Write the entire base file to temp
            temp_file.write(PAD_BYTE * (offset - base_size))  # Pad to the specified offset

        with open(append_path, 'rb') as file_append:
            temp_file.write(file_append.read())  # Append the additional file content

        temp_path = temp_file.name

    final_size = Path(temp_path).stat().st_size
    alignment_padding = (imgtool_args.align - (final_size % imgtool_args.align)) % imgtool_args.align

    with open(temp_path, 'ab') as file_out:
        file_out.write(PAD_BYTE * alignment_padding)

    # Replace the original file with the temporary file
    shutil.move(temp_path, output_path)

    if imgtool_args.verbose:
        print(f"Appended {append_path} to {base_path} at offset {offset}(0x{offset:x}), aligned to {imgtool_args.align}-byte boundary. Final size: {final_size + alignment_padding}(0x{(final_size + alignment_padding):x}) bytes.")


def merge_files(base_path, insert_path, output_path, merge_offset, imgtool_args):
    """Merge one file into another at specified offset and align the final output, handling same input and output paths safely."""
    merge_offset = parse_hexadecimal(merge_offset)
    base_size = Path(base_path).stat().st_size
    insert_size = Path(insert_path).stat().st_size
    PAD_BYTE = bytes([int(imgtool_args.pad_byte, 16)])

    if base_size < merge_offset:
        raise ValueError(f"Base file {base_size}(0x{base_size:x}) bytes must be larger than the insert file {merge_offset}(0x{merge_offset:x}) offset.")

    with NamedTemporaryFile(delete=False) as temp_file:
        with open(base_path, 'rb') as file_base, open(insert_path, 'rb') as file_insert:
            temp_file.write(file_base.read(merge_offset))  # Write up to the merge offset
            temp_file.write(file_insert.read())  # Insert the new file content
            file_base.seek(merge_offset)  # Skip the replaced part in the original
            temp_file.write(file_base.read())  # Continue writing the rest

        temp_path = temp_file.name

    final_size = Path(temp_path).stat().st_size
    alignment_padding = (imgtool_args.align - (final_size % imgtool_args.align)) % imgtool_args.align

    with open(temp_path, 'ab') as file_out:
        file_out.write(PAD_BYTE * alignment_padding)

    # Replace the original file with the temporary file
    shutil.move(temp_path, output_path)

    if imgtool_args.verbose:
        print(f"Merged {insert_path} into {base_path} at offset {merge_offset}(0x{merge_offset:x}). Final size: {final_size + alignment_padding}(0x{(final_size + alignment_padding):x}) bytes.")


def replace_file(base_path, replace_path, output_path, replace_offset, imgtool_args):
    """Replace a portion of the base file with the replace file starting from the specified offset. Handles same input and output paths safely."""
    replace_offset = parse_hexadecimal(replace_offset)
    base_size = Path(base_path).stat().st_size
    replace_size = Path(replace_path).stat().st_size
    PAD_BYTE = bytes([int(imgtool_args.pad_byte, 16)])

    if base_size < replace_offset + replace_size:
        raise ValueError(f"Base file {base_size}(0x{base_size:x}) bytes must be larger than the sum of replace offset {replace_offset}(0x{replace_offset:x}) and replace file size {replace_size}(0x{replace_size:x}).")

    # Use a temporary file to safely handle when base_path and output_path are the same
    with NamedTemporaryFile(delete=False) as temp_file:
        with open(base_path, 'rb') as file_base, open(replace_path, 'rb') as file_replace:
            # Write base file content up to the replace offset to the temp file
            temp_file.write(file_base.read(replace_offset))
            # Write the replace file content
            temp_file.write(file_replace.read())
            # Move file pointer past the replaced portion
            file_base.seek(replace_offset + replace_size)
            # Write the remaining base file content
            temp_file.write(file_base.read())

        temp_file_path = temp_file.name

    # Compute final size and alignment
    final_size = base_size
    alignment_padding = (imgtool_args.align - (final_size % imgtool_args.align)) % imgtool_args.align

    # Add alignment padding and finalize the temporary file
    with open(temp_file_path, 'ab') as file_out:
        file_out.write(PAD_BYTE * alignment_padding)

    # Replace the original file with the temporary file
    shutil.move(temp_file_path, output_path)

    if imgtool_args.verbose:
        print(f"Replaced {base_path} with {replace_path} starting from offset {replace_offset}(0x{replace_offset:x}). Final size: {final_size + alignment_padding}(0x{(final_size + alignment_padding):x}) bytes.")



def calculate_crc32(data):
    """Calculate CRC32 of the given data."""
    return zlib.crc32(data) & 0xFFFFFFFF

def calculate_checksum(data):
    """Calculate simple checksum of the given data."""
    return sum(data) & 0xFFFFFFFF

def sign_file(input_path, signature_type, opt_append, imgtool_args):
    with open(input_path, 'rb') as file:
        data = file.read()

    signatures = {}
    if signature_type.lower() == 'all':
        signatures['crc32'] = calculate_crc32(data)
        signatures['byte(x8)'] = calculate_checksum(data)  # Assuming checksum returns byte(x8) checksum
    elif signature_type.lower() == 'crc32':
        signatures['crc32'] = calculate_crc32(data)
    elif signature_type.lower() == 'byte':
        signatures['byte(x8)'] = calculate_checksum(data)
    else:
        raise ValueError(f"Unsupported signature type: {signature_type}")

    for sig_type, sig_value in signatures.items():
        signature_name = sig_type.upper()
        signature_bytes = struct.pack('<I', sig_value)  # Adjust format as necessary


        if str(opt_append).lower() == 'append':
            base_name, ext = os.path.splitext(input_path)
            modified_output_path = f"{base_name}_{sig_type}{ext}"
            with open(modified_output_path, 'wb') as file:
                file.write(data)
                file.write(signature_bytes)  # Append 4-byte signature in little-endian format

        if imgtool_args.verbose:
            print(f"Signature value for {signature_name}: 0x{sig_value:08X}")
            if opt_append:
                print(f"Signed file written to: {modified_output_path}")
                print(f"Original size: {len(data)} bytes: {hex(len(data))}")
                print(f"Final size: {len(data) + 4} bytes {hex(len(data)+4)}")


def main():
    args = ImgToolArgs().parse_args()

    if args.resize:
        resize_binary_file(args.resize[0], args.resize[1], args.resize[2], args)
    elif args.append:
        append_to_file(args.append[0], args.append[1], args.append[2], args.append[3], args)
    elif args.merge:
        merge_files(args.merge[0], args.merge[1], args.merge[2], args.merge[3], args)
    elif args.replace:
        replace_file(args.replace[0], args.replace[1], args.replace[2], args.replace[3], args)
    elif args.sign:
        if len(args.sign) < 2 or len(args.sign) > 3:
            print("Invalid number of arguments for --sign option.")
            print("Usage: --sign INPUT_FILE SIGNATURE_TYPE [append]")
            print("Supported SIGNATURE_TYPE: byte(x8), crc32")
            return

        input_file = args.sign[0]
        signature_type = args.sign[1]
        opt_append = args.sign[2] if len(args.sign) == 3 else None

        sign_file(input_file, signature_type, opt_append, args)



if __name__ == '__main__':
    main()
