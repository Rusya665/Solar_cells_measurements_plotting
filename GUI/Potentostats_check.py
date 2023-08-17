import os
import chardet
import numpy as np
import pandas as pd
from Data_Reader import IVDataReader


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
        self.encoding = None
        self.potentiostat_choice = potentiostat_choice

    def check_file(self, file):
        """
        Checks a file to determine if it matches one of the potentiostat types.

        :param file: The file to check.
        :return: If the file is identified, a tuple with (True, encoding_used, potentiostat_type, number of sweeps).
                 If the file is not identified, a tuple with (False, encoding_used, None, None).
        """
        filename, file_extension = os.path.splitext(file)
        if self.potentiostat_choice != 'All':
            # Skip files that do not have an extension corresponding to the chosen potentiostat
            file_extensions = [ext for ext, pots in self.potentiostat_dict.items() if self.potentiostat_choice in pots]
            if file_extension not in file_extensions:
                return False, None, None, None

        if file_extension not in self.potentiostat_dict:
            return False, None, None, None  # Skip files with non-matching extensions

        # Detect encoding using chardet
        with open(file, 'rb') as f:
            result = chardet.detect(f.read(4096))  # Check encoding of the first 4096  bytes
        self.encoding = result['encoding']
        for potentiostat, target_text in self.potentiostat_dict[file_extension].items():
            with open(file, 'r', encoding=self.encoding) as f:
                for i, line in enumerate(f):
                    if i >= 100:  # limit number of lines read to 100
                        break
                    if target_text in line:
                        sweeps_data = self.detect_iv_sweeps(file, potentiostat, 'V')
                        return True, self.encoding, potentiostat, sweeps_data

        # If we got this far, the file didn't match any potentiostat
        return False, self.encoding, None, None

    def detect_iv_sweeps(self, file, potentiostat, col_name='V'):
        """
        Detect the number of IV sweeps and their direction based on sign changes in a column of a dataframe.
        :param file: Path to IV data
        :param potentiostat: Type of the potentiostat
        :param col_name: Name of the column to check
        :return: Dictionary containing:
                 - "Counts": Dictionary with counts for:
                     - "Total Sweeps": Integer count of total sweeps
                     - "Forward Sweeps": Integer count of Forward sweeps
                     - "Reverse Sweeps": Integer count of Reverse sweeps
                 - "Data": Dictionary with:
                     - "1": Data for the first detected sweep (either Forward or Reverse)
                     - "2": Data for the second detected sweep
                     - (and so on...)
        """
        df = IVDataReader(file, potentiostat, self.encoding).read()

        forward_data = []
        reverse_data = []

        for idx in range(1, len(df)):
            current_v = df[col_name].iloc[idx]
            previous_v = df[col_name].iloc[idx - 1]

            # Forward sweep
            if current_v > previous_v:
                if not forward_data:
                    forward_data.append({'V': previous_v, 'I': df['I'].iloc[idx - 1]})
                forward_data.append({'V': current_v, 'I': df['I'].iloc[idx]})

            # Reverse sweep
            elif current_v < previous_v:
                if not reverse_data:
                    reverse_data.append({'V': previous_v, 'I': df['I'].iloc[idx - 1]})
                reverse_data.append({'V': current_v, 'I': df['I'].iloc[idx]})

        sweeps_data = []
        if forward_data:
            sweeps_data.append(pd.DataFrame(forward_data))
        if reverse_data:
            sweeps_data.append(pd.DataFrame(reverse_data))

        forward_count = 1 if forward_data else 0
        reverse_count = 1 if reverse_data else 0

        counts = {
            "Total Sweeps": forward_count + reverse_count,
            "Forward Sweeps": forward_count,
            "Reverse Sweeps": reverse_count
        }

        data = {str(idx): segment for idx, segment in enumerate(sweeps_data, start=1)}
        print(self.check_data_integrity(df, {"Counts": counts, "Data": data}))
        return {"Counts": counts, "Data": data}

    def check_data_integrity(self, df, result, col_name='V'):
        """
        Check if the total number of rows in the initial dataframe matches the sum of the rows from the divided segments.
        """
        # Retrieve the initial dataframe

        # Get the divided segments
        sweeps_data = [data for _, data in result["Data"].items()]

        # Compute the total number of rows in the divided segments
        total_rows_in_segments = sum(segment.shape[0] for segment in sweeps_data)

        # Check if the counts match
        return df.shape[0] == total_rows_in_segments
