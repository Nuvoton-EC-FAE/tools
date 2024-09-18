import sys

def parse_config_line(line, debug=False):
    """Parses a config line and returns the corresponding C header format."""
    if "=" not in line:
        if debug:
            print(f"Skipping line (no '=' found): {line}")
        return None

    # Strip comments and split key and value
    line = line.split("#")[0].strip()
    if not line:
        if debug:
            print(f"Skipping empty line or comment: {line}")
        return None

    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()

    if debug:
        print(f"Parsing line: {key} = {value}")

    # Handle boolean values
    if value == "y":
        return f"#define {key} ENABLE"
    elif value == "n":
        return f"#define {key} DISABLE"


    # Handle numeric and hexadecimal values
    try:
        if value.startswith('"') and value.endswith('"'):
            return f"#define {key} {value}"
        elif value.startswith("0x"):  # Hexadecimal values
            return f"#define {key} {value}"
        elif value.isdigit():  # Decimal values
            return f"#define {key} {value}"
    except ValueError:
        print(f"Error parsing value: {value}")

    return None

def convert_prj_to_header(prj_conf_path, output_header_path, debug=False):
    """Converts a prj.conf file to a C header file."""
    config_counter = 0
    try:
        with open(prj_conf_path, 'r') as prj_conf_file, open(output_header_path, 'w') as header_file:
            # Write header guards and initial macros
            header_file.write("#ifndef _PRJ2HEADER_H_\n")
            header_file.write("#define _PRJ2HEADER_H_\n\n")
            header_file.write("#define ENABLE 1\n")
            header_file.write("#define DISABLE 0\n\n")

            # Process each line in the prj.conf file
            for line in prj_conf_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip empty lines and comments

                # Convert and write the line to the header file
                converted_line = parse_config_line(line, debug)
                if converted_line:
                    header_file.write(converted_line + "\n")
                    config_counter += 1
                elif debug:
                    print(f"Skipping line (not valid config): {line}")

            # Close the header guard
            header_file.write("\n#endif // _PRJ2HEADER_H_\n")

        print(f"Header file generated successfully at: {output_header_path}, conter: {config_counter}")
    except FileNotFoundError:
        print(f"Error: The file '{prj_conf_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script.py <prj.conf path> <output header path> [--debug]")
    else:
        debug = '--debug' in sys.argv
        convert_prj_to_header(sys.argv[1], sys.argv[2], debug)
