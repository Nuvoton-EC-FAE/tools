# imgtools.py

import os
from pathlib import Path
from imgtool_args import ImgToolArgs
from tempfile import NamedTemporaryFile


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
    os.replace(temp_path, output_path)

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
    os.replace(temp_path, output_path)

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
    os.replace(temp_file_path, output_path)

    if imgtool_args.verbose:
        print(f"Replaced {base_path} with {replace_path} starting from offset {replace_offset}(0x{replace_offset:x}). Final size: {final_size + alignment_padding}(0x{(final_size + alignment_padding):x}) bytes.")


def main():
    args = ImgToolArgs().parse_args()

    if args.resize:
        resize_binary_file(args.resize[0], args.resize[1], args.resize[2], args)
    if args.append:
        append_to_file(args.append[0], args.append[1], args.append[2], args.append[3], args)
    if args.merge:
        merge_files(args.merge[0], args.merge[1], args.merge[2], args.merge[3], args)
    if args.replace:
        replace_file(args.replace[0], args.replace[1], args.replace[2], args.replace[3], args)


if __name__ == '__main__':
    main()
