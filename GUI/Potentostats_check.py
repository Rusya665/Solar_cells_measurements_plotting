import os
import chardet
import pandas as pd
from Data_Reader import IVDataReader


class PotentiostatFileChecker:
    """
    Class to check if a file matches one of the specified potentiostat types.
    """

    def __init__(self, parent, potentiostat_choice='All'):
        """
        Initialize PotentiostatFileChecker with a dictionary mapping file extensions to potentiostat types and their
         identifying characteristics.
        """
        self.parent = parent
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
                        sweeps_data = self.detect_iv_sweeps(file, potentiostat)
                        return True, self.encoding, potentiostat, sweeps_data

        # If we got this far, the file didn't match any potentiostat
        return False, self.encoding, None, None

    def detect_iv_sweeps(self, file, potentiostat):
        """
        Detect the number of IV sweeps and their direction based on sign changes in a column of a dataframe.
        :param file: Path to IV data
        :param potentiostat: Type of the potentiostat
        :return: Dictionary containing:
                 - "Counts": Dictionary with counts for:
                     - "Total Sweeps": Integer count of total sweeps
                     - "Forward Sweeps": Integer count of Forward sweeps
                     - "Reverse Sweeps": Integer count of Reverse sweeps
                 - "Data": Dictionary with:
                     - "1_Forward": Data for the first detected forward sweep
                     - "2_Reverse": Data for the first detected reverse sweep
                     - "3_Forward": Data for the second detected forward sweep
                     - "4_Reverse": Data for the second detected reverse sweep
                     - (and so on...)
        """
        df, unit = IVDataReader(self, file, potentiostat, self.encoding).read()

        if len(df) < 2:
            return {"Counts": {"Total Sweeps": 0, "Forward Sweeps": 0, "Reverse Sweeps": 0}, "Data": {}}

        sweeps_data = []
        current_sweep_data = [{'V': df['V'].iloc[0], 'I': df['I'].iloc[0]}]

        # Determine the initial direction based on first two data points
        current_direction = "increasing" if df['V'].iloc[1] > df['V'].iloc[0] else "decreasing"

        for idx in range(1, len(df)):
            current_v = df['V'].iloc[idx]
            previous_v = df['V'].iloc[idx - 1]

            # Determine the "local" direction
            local_direction = "increasing" if current_v > previous_v else "decreasing"

            if local_direction != current_direction:
                sweeps_data.append(pd.DataFrame(current_sweep_data))
                current_sweep_data = [{'V': current_v, 'I': df['I'].iloc[idx]}]
                current_direction = local_direction
            else:
                current_sweep_data.append({'V': current_v, 'I': df['I'].iloc[idx]})

        # Append the final sweep
        sweeps_data.append(pd.DataFrame(current_sweep_data))

        forward_count = sum(1 for df in sweeps_data if df['V'].iloc[1] > df['V'].iloc[0])
        reverse_count = len(sweeps_data) - forward_count

        counts = {
            "Total Sweeps": forward_count + reverse_count,
            "Forward Sweeps": forward_count,
            "Reverse Sweeps": reverse_count
        }
        data = {}
        forward_counter = 1
        reverse_counter = 2

        for segment in sweeps_data:
            if segment['V'].iloc[1] > segment['V'].iloc[0]:  # Current sweep is forward
                key = f"{forward_counter}_Forward"
                data[key] = segment
                forward_counter += 2
            else:  # Current sweep is reverse
                key = f"{reverse_counter}_Reverse"
                data[key] = segment
                reverse_counter += 2
        # data = {str(idx): segment for idx, segment in enumerate(sweeps_data, start=1)}
        # self.check_data_integrity(df, {"Counts": counts, "Data": data}, file)
        return {"Counts": counts, "Data": data, 'Unit': unit}

    # def check_data_integrity(self, df, result,  file):
    #     """
    #     #     Check if the total number of rows in the initial dataframe matches the sum of the rows from
    #     the divided segments.
    #     """
    #     # Get the divided segments
    #     sweeps_data = [data for _, data in result["Data"].items()]
    #
    #     # Compute the total number of rows in the divided segments
    #     total_rows_in_segments = sum(segment.shape[0] for segment in sweeps_data)
    #     print(f'For {Path(file).stem} the total length is {df.shape[0]} and the sweeps all together are
    #     {total_rows_in_segments}')
