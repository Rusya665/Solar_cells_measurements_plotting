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
                        number_of_sweeps = self._get_number_of_sweeps(file, potentiostat)
                        return True, self.encoding, potentiostat, number_of_sweeps

        # If we got this far, the file didn't match any potentiostat
        return False, self.encoding, None, None

    def _get_number_of_sweeps(self, file, potentiostat):
        df = IVDataReader(file, potentiostat, self.encoding).read()
        # return axis_crossing(df, 'V')
        return detect_iv_sweeps(df, 'V')

    def detect_iv_sweeps(df, col_name):
        """
        Detect the number of IV sweeps and their direction based on sign changes in a column of a dataframe.
        :param df: DataFrame
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
        df_sign_changes = df[col_name].loc[np.sign(df[col_name]).diff().ne(0)]

        if df_sign_changes.index[0] == 0:  # To handle the edge case where the first row is 0
            df_sign_changes.drop(df_sign_changes.index[0], inplace=True)

        forward_count = 0
        reverse_count = 0
        sweeps_data = []  # List to store data associated with each sweep

        # Start with the first data point
        start_idx = 0

        for idx in df_sign_changes.index:
            end_idx = idx
            if df[col_name].iloc[idx - 1] < df[col_name].iloc[idx]:
                forward_count += 1
            else:
                reverse_count += 1
            sweeps_data.append(df.iloc[start_idx:end_idx])
            start_idx = idx

        # Final sweep after the last sign change
        sweeps_data.append(df.iloc[start_idx:])

        counts = {
            "Total Sweeps": forward_count + reverse_count,
            "Forward Sweeps": forward_count,
            "Reverse Sweeps": reverse_count
        }

        data = {str(idx): segment for idx, segment in enumerate(sweeps_data, start=1)}

        return {"Counts": counts, "Data": data}
