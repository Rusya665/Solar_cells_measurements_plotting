import os
from tkinter import messagebox

import pandas as pd
from fuzzywuzzy import fuzz


class DeviceDetector:
    """
    The DeviceDetector class processes and filters device-related data based on specific rules and matching criteria.

    Attributes:
    - data: A dictionary containing the device data.

    Methods:
    - print_nested_dict: Recursively prints keys and values of a nested dictionary.
    - detect_and_filter: Detects and filters devices based on predefined criteria.
    - find_fuzzy_pair: Finds a matching file name for a given file using fuzzy matching.
    - combine_data: Combines data from two matching files.
    - combine_sweeps: Combines sweeps data.

    """

    def __init__(self, data_dict):
        """
        Initializes the DeviceDetector class with a data dictionary and JV_plotter_GUI object.

        :param data_dict: Dictionary containing device-related data.
        """
        self.data = data_dict

    def detect_and_filter(self):
        """
        Detects and filters devices based on the following criteria:
        - If a device has 2 sweeps, both forward and reverse, it's directly added to the result.
        - If a device has 1 sweep, tries to find its matching pair.
          If a match is found, their data is combined.
        - If a device has more than 2 sweeps, the sweeps are combined based on their V values.

        :return: Dictionary of processed data.
        """

        result_data = {}

        # Iterate through folders and then files
        for folder_name, folder_data in self.data.items():
            single_sweep_files = {}
            processed_files = set()
            result_data[folder_name] = {}  # Initialize the folder in the result

            # Handle devices with both sweeps
            for filename, details in folder_data.items():
                fw_sweeps = details['Sweeps']['Forward Sweeps']
                rv_sweeps = details['Sweeps']['Reverse Sweeps']

                # Directly add files with both sweeps to result
                if fw_sweeps + rv_sweeps == 2 and fw_sweeps == rv_sweeps:
                    result_data[folder_name][filename] = details
                    result_data[folder_name][filename]['Used files'] = filename

                # Collect single sweep files for later processing
                elif fw_sweeps + rv_sweeps == 1:
                    direction = "Forward" if fw_sweeps == 1 else "Reverse"
                    single_sweep_files[filename] = direction

            # Pair devices with single sweeps
            for filename, direction in single_sweep_files.items():
                if filename in processed_files:
                    continue
                matched_file = self.find_fuzzy_pair(filename, single_sweep_files)
                # ic(filename, matched_file, single_sweep_files[matched_file], direction)
                # Pair found and they have complementary sweeps
                if matched_file and single_sweep_files[matched_file] != direction:
                    combined_data, used_files = self.combine_data(folder_data[filename], folder_data[matched_file])
                    # Adjust the key to represent the common device name with distinguishing suffixes
                    filename_key = self.adjust_filename(filename, matched_file)
                    result_data[folder_name][filename_key] = combined_data
                    result_data[folder_name][filename_key]['Used files'] = used_files

                    processed_files.add(filename)
                    processed_files.add(matched_file)

                else:
                    # Remove unmatched single sweep files
                    folder_data.pop(filename, None)
                    messagebox.showwarning('Unmatched file detected!',
                                           message=f'The file {filename} appears to be a file without a match')

            # Average out devices with multiple sweeps
            for filename, details in folder_data.items():
                fw_sweeps = details['Sweeps']['Forward Sweeps']
                rv_sweeps = details['Sweeps']['Reverse Sweeps']

                if fw_sweeps > 1 or rv_sweeps > 1:
                    averaged_data = self.combine_sweeps(details)
                    result_data[folder_name][filename] = averaged_data
                    result_data[folder_name][filename]['Used files'] = filename
        return self.adjust_keys(result_data)

    @staticmethod
    def adjust_keys(data_dict):
        """
        Processes a dictionary to remove file extensions from its keys.

        :param data_dict: Dictionary where keys might have file extensions.
        :return: Dictionary with keys adjusted (file extensions removed).
        """
        # Process keys and construct a new dictionary
        adjusted_dict = {}
        for folder_name, folder_data in data_dict.items():
            adjusted_folder_data = {os.path.splitext(key)[0]: value for key, value in folder_data.items()}
            adjusted_dict[folder_name] = adjusted_folder_data
        return adjusted_dict

    @staticmethod
    def find_fuzzy_pair(filename, single_sweep_files):
        """
        Find a fuzzy-matching filename for the given filename.

        :param filename: The filename to match.
        :param single_sweep_files: A dict of filenames with single sweeps.
        :return: The matching filename or None.
        """
        best_match = (None, 0)  # Tuple (filename, score)

        # Determine sweep direction and its opposite based on the filename
        sweep_direction = 'Forward' if 'fw' in filename.lower() else 'Reverse'
        opposite_direction = 'Reverse' if sweep_direction == 'Forward' else 'Forward'

        # Filter and score filenames with opposite direction
        candidates = [(other_filename, fuzz.ratio(filename, other_filename))
                      for other_filename, direction in single_sweep_files.items()
                      if direction == opposite_direction and other_filename != filename]

        # Find the best match if any
        if candidates:
            best_match = max(candidates, key=lambda x: x[1])

        return best_match[0] if best_match[1] > 80 else None

    @staticmethod
    def combine_data(data1, data2):
        """
        Combines data from two dictionaries.

        :param data1: The first data dictionary.
        :param data2: The second data dictionary.
        :return: The combined data dictionary and a list of contributing files.
        """
        combined_data = data1.copy()
        combined_data['Sweeps']['Total Sweeps'] += data2['Sweeps']['Total Sweeps']
        combined_data['Sweeps']['Forward Sweeps'] += data2['Sweeps']['Forward Sweeps']
        combined_data['Sweeps']['Reverse Sweeps'] += data2['Sweeps']['Reverse Sweeps']
        # Merging the dataframes
        for sweep_key in data2['data']:
            if sweep_key not in combined_data['data']:
                combined_data['data'][sweep_key] = data2['data'][sweep_key]
            else:
                # Check if the sweep is Forward or Reverse and assign it accordingly
                if 'Fw' in sweep_key:
                    combined_data['data']['1'] = data2['data'][sweep_key]
                elif 'Rv' in sweep_key:
                    combined_data['data']['2'] = data2['data'][sweep_key]
        used_files = data1['Used files'], data2['Used files']
        combined_data['Used files'] = used_files

        return combined_data, used_files

    @staticmethod
    def combine_sweeps(value_data):
        """
        Combines sweeps data based on their V values.
        Assumes each sweep has a 'V' column, and the values are averaged.

        :param value_data: Dictionary containing sweep data.
        :return: Dictionary with combined sweep data.
        """
        # Assuming each sweep has a 'V' column, and you want to average them.
        # This step is illustrative, and you might need to adjust based on the actual data format.
        # Placeholder for the combined sweeps
        combined_data = {}

        # Logic to combine the sweeps based on V column (Averaging I values for identical V values).
        # NOTE: This logic may need more refinement based on exact requirements.

        for sweep, df in value_data['data'].items():
            if sweep not in combined_data:
                combined_data[sweep] = df
            else:
                # Combining dataframes with identical V values and averaging the I values
                combined_df = pd.merge(combined_data[sweep], df, on='V', how='outer')
                combined_df['I'] = combined_df[['I_x', 'I_y']].mean(axis=1)
                combined_df.drop(columns=['I_x', 'I_y'], inplace=True)
                combined_data[sweep] = combined_df

        value_data['data'] = combined_data
        return value_data

    @staticmethod
    def adjust_filename(filename, matched_file):
        """
        Adjusts the given filename based on the common prefix and suffix
        found between the filename and matched_file.

        :param filename: The original filename to be adjusted.
        :param matched_file: The reference filename to determine common prefix and suffix.
        :return: Adjusted filename based on common elements with matched_file.
        """

        def find_common_prefix(s1, s2):
            """
            Finds the common prefix between two strings.

            :param s1: First string.
            :param s2: Second string.
            :return: Common prefix string.
            """
            i = 0
            while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
                i += 1
            return s1[:i]

        def find_common_suffix(s1, s2):
            """
            Finds the common suffix between two strings.

            :param s1: First string.
            :param s2: Second string.
            :return: Common suffix string.
            """
            i = -1
            while abs(i) <= len(s1) and abs(i) <= len(s2) and s1[i] == s2[i]:
                i -= 1
            return s1[i + 1:] if i != -1 else ''

        stripped_name = os.path.splitext(filename)[0]
        stripped_matched = os.path.splitext(matched_file)[0]

        # Find common prefix and suffix
        common_prefix = find_common_prefix(stripped_name, stripped_matched)
        common_suffix = find_common_suffix(stripped_name, stripped_matched)

        return f"{common_prefix}{common_suffix}"
