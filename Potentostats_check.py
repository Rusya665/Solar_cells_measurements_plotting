import os
import chardet


class PotentiostatFileChecker:
    """
    Class to check if a file matches one of the specified potentiostat types.
    """

    def __init__(self,  potentiostat_choice='All'):
        """
        Initialize PotentiostatFileChecker with a dictionary mapping file extensions to potentiostat types and their
         identifying characteristics.
        """
        self.potentiostat_dict = {
            '.DTA': {
                'Gamry': "CURVE1\tTABLE",
                # To add a new potentiostat with '.dta' extension:
                # 'new_potentiostat': "new text to find",
            },
            '.csv': {'PalmSens4': "Cyclic Voltammetry: CV i vs E"},
            '.txt': {'SMU': "[0, 0, 0]"},
            # To add a new file extension, add a new entry like this:
            # '.new_extension': {'new_potentiostat': "new text to find"},
        }
        self.potentiostat_choice = potentiostat_choice

    def check_file(self, file):
        """
        Checks a file to determine if it matches one of the potentiostat types.

        :param file: The file to check.
        :return: If the file is identified, a tuple with (True, encoding_used, potentiostat_type).
                 If the file is not identified, a tuple with (False, encoding_used, None).
        """
        filename, file_extension = os.path.splitext(file)
        if self.potentiostat_choice != 'All':
            # Skip files that do not have an extension corresponding to the chosen potentiostat
            file_extensions = [ext for ext, pots in self.potentiostat_dict.items() if self.potentiostat_choice in pots]
            if file_extension not in file_extensions:
                return False, None, None

        if file_extension not in self.potentiostat_dict:
            return False, None, None  # Skip files with non-matching extensions

        # Detect encoding using chardet
        with open(file, 'rb') as f:
            result = chardet.detect(f.read(4096))  # Check encoding of the first 4096  bytes
        encoding = result['encoding']
        for potentiostat, target_text in self.potentiostat_dict[file_extension].items():
            with open(file, 'r', encoding=encoding) as f:
                for i, line in enumerate(f):
                    if i >= 100:  # limit number of lines read to 100
                        break
                    if target_text in line:
                        return True, encoding, potentiostat

        # If we got this far, the file didn't match any potentiostat
        return False, encoding, None
