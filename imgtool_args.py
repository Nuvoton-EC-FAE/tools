import argparse

class CustomHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if action.option_strings:
            return ', '.join(action.option_strings)
        return super()._format_action_invocation(action)
    
class ImgToolArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Nuvoton Image Tool For Binary File.',
            formatter_class=CustomHelpFormatter
        )
        self.add_arguments()

    def add_arguments(self):
        
        self.parser.add_argument('--resize', nargs=3, metavar=('INPUT_FILE', 'OUTPUT_FILE', 'SIZE'),
                                 help='Resize a binary file to a specific size with alignment.')
        
        self.parser.add_argument('--append', nargs=4, metavar=('INPUT_FILE_A', 'INPUT_FILE_B', 'OUTPUT_FILE', 'OFFSET'),
                                 help='Append file B to file A at a specified offset.')
        
        self.parser.add_argument('--merge', nargs=4, metavar=('INPUT_FILE_A', 'INPUT_FILE_B', 'OUTPUT_FILE', 'OFFSET'),
                                 help='Merge file B into file A at a specified offset.')

        self.parser.add_argument('--replace', nargs=4, metavar=('INPUT_FILE_A', 'INPUT_FILE_B', 'OUTPUT_FILE', 'OFFSET'),
                             help='Replace the content of file A with file B starting at a specified offset.')

        self.parser.add_argument('--sign', nargs='+', metavar='ARG',
                                 help='Calculate signature (BYTE(x8)/CRC32) for input file.\n'
                                      'Usage: --sign INPUT_FILE SIGNATURE_TYPE [append].\n'
                                      'Option: If append is provided, append the signed to the file.')



        self.parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output for debugging.')
        self.parser.add_argument('-a', '--align', type=int, default=16, help='Alignment value (default: 16 bytes).')
        self.parser.add_argument('-c', '--pad_byte', default='0x00', help='Padding byte (default: 0x00).')

    def parse_args(self):
        return self.parser.parse_args()

# if __name__ == "__main__":
#     args = ImgToolArgs().parse_args()
#     print(args)  # This will display parsed arguments when this module is executed directly
