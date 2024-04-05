from functools import reduce
from typing import Any, List, Dict

import numpy as np
import pandas as pd
from icecream import ic


class PixelMerger:
    def __init__(self, data: Dict[str, Any], substrates: Dict[str, List[str]], parent):
        """
        Initialize the PixelMerger class.

        :param parent: An instance of the main ctk app, used for integration with a custom tkinter interface.
        :param data: A dictionary containing pixel data.
        :param substrates: A dictionary where each key is a substrate name, and its value is a list of pixel names.
        """
        self.parent = parent
        self.data = data
        self.substrates = substrates
        self.merged_data = {}
        self.stat = self.parent.stat
        self.merge_substrates()

    def average_parameters(self, parameter_dicts: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate the average and various error metrics (standard deviation, mean absolute error, mean squared error,
        root mean squared error, mean absolute percentage error, median absolute deviation) for parameters across a set
        of pixels.

        :param parameter_dicts: A list of dictionaries, all containing parameters of a pixel.
        :return: A dictionary containing the averages and their corresponding errors. Error metrics include:
                 - Standard Deviation ('std_dev')
                 - Mean Absolute Error ('mae')
                 - Mean Squared Error ('mse')
                 - Root Mean Squared Error ('rmse')
                 - Mean Absolute Percentage Error ('mape')
                 - Median Absolute Deviation ('mad')
        """
        param_values = {key: [] for key in parameter_dicts[0]}
        for param_dict in parameter_dicts:
            for key, value in param_dict.items():
                param_values[key].append(value)

        calculated_params = {}
        for key, values in param_values.items():
            values = np.array(values)
            mean_value = np.mean(values)
            calculated_params[key] = mean_value

            if self.stat == 'std_dev':
                error_value = np.std(values, ddof=1)  # Sample standard deviation
            elif self.stat == 'mae':
                error_value = np.mean(np.abs(values - mean_value))  # Mean Absolute Error
            elif self.stat == 'mse':
                error_value = np.mean((values - mean_value) ** 2)  # Mean Squared Error
            elif self.stat == 'rmse':
                error_value = np.sqrt(np.mean((values - mean_value) ** 2))  # Root Mean Squared Error
            elif self.stat == 'mape':
                # Handle division by zero and potential NaN values
                with np.errstate(divide='ignore', invalid='ignore'):
                    error_value = np.mean(np.abs((values - mean_value) / values)) * 100
                    error_value = np.nan_to_num(error_value)  # Convert NaN to 0
            elif self.stat == 'mad':
                error_value = np.median(np.abs(values - np.median(values)))  # Median Absolute Deviation
            else:
                raise ValueError(f"Unknown stat: {self.stat}")

            error_key = f'{key} {self.stat}'
            calculated_params[error_key] = error_value
        return calculated_params

    @staticmethod
    def check_consistency(key: str, pixels: List[Dict[str, Any]]) -> Any:
        """
        Check if a key has consistent values across all given pixels.

        :param key: The key to check.
        :param pixels: The list of pixel data dictionaries.
        :return: The consistent value of the key.
        """
        values = set(pixel[key] for pixel in pixels if key in pixel)
        if len(values) > 1:
            raise ValueError(f"Inconsistent values for '{key}' across pixels.")
        return values.pop()

    def merge_pixels(self, folder_name: str, substrate_pixels: List[str]) -> Dict[str, Any]:
        """
        Merge all pixel data for a given substrate.

        :param folder_name: The date (usually) string which represents the top-level key in data.
        :param substrate_pixels: A list of pixel names that belong to the same substrate.
        :return: A dictionary containing merged data for the substrate.
        """
        merged = {'Parameters': {}, 'data': {}}
        keys_to_check = [
            'Active area (cm²)', 'Distance to light source (mm)',
            'Light intensity (W/cm²)', 'encoding', 'measurement device', 'unit'
        ]

        # Access the data at the correct level (date then pixel).
        date_data = self.data[folder_name]

        # Aggregate sweeps data by averaging parameters.
        sweep_types = ['Forward', 'Reverse', 'Average']
        for sweep_type in sweep_types:
            parameters = [date_data[pixel_name]['Parameters'][sweep_type] for pixel_name in substrate_pixels if
                          sweep_type in date_data[pixel_name]['Parameters']]
            merged['Parameters'][sweep_type] = self.average_parameters(parameters)

        # Check for consistency in certain keys.
        for key in keys_to_check:
            merged[key] = self.check_consistency(key, [date_data[pixel_name] for pixel_name in substrate_pixels])

        # Aggregate 'H-index' by averaging.
        h_index_values = [date_data[pixel_name]['H-index'] for pixel_name in substrate_pixels if
                          'H-index' in date_data[pixel_name]]
        merged['H-index'] = sum(h_index_values) / len(h_index_values) if h_index_values else None

        # Determine sweep types dynamically
        all_sweep_types = set()
        for pixel_name in substrate_pixels:
            all_sweep_types.update(self.data[folder_name][pixel_name]['data'].keys())

        # Process and average IV data for each sweep type
        for sweep_type in all_sweep_types:
            sweep_data_frames = []
            for pixel_name in substrate_pixels:
                pixel_data = self.data[folder_name][pixel_name]
                if sweep_type in pixel_data['data']:
                    sweep_data_frames.append(pixel_data['data'][sweep_type])
            ic(sweep_type)
            if sweep_data_frames:

                # Check if the lengths of 'V' are different
                lengths = [len(df) for df in sweep_data_frames]
                if len(set(lengths)) != 1:
                    # Find the index of the DataFrame with the longest 'V'
                    longest_df_index = lengths.index(max(lengths))
                    v_values = sweep_data_frames[longest_df_index]['V']
                else:
                    # If all lengths are the same, use 'V' from the first DataFrame
                    v_values = sweep_data_frames[0]['V']

                # Create a new DataFrame with the longest 'V'
                merged['data'][sweep_type] = pd.DataFrame({'V': v_values})
                average_i_values = []

                # Iterate over each index of the longest 'V' series
                for index in range(len(v_values)):
                    i_values = []

                    # Collect 'I' values for this index from all DataFrames, if available
                    for df in sweep_data_frames:
                        if index < len(df):
                            i_values.append(df.iloc[index]['I'])

                    # Compute the average of 'I' values, if available
                    if i_values:
                        average_i_values.append(np.mean(i_values))
                    else:
                        average_i_values.append(np.nan)  # Append NaN if no 'I' values are found

                # Assign the average 'I' values to the merged DataFrame
                merged['data'][sweep_type]['I'] = average_i_values
        # # Assuming 'V' is the same in all DataFrames
                # merged['data'][sweep_type] = pd.DataFrame()
                # merged['data'][sweep_type]['V'] = sweep_data_frames[0]['V']
                #
                # # Compute the average for the 'I' column across all DataFrames
                # merged['data'][sweep_type]['I'] = sum(df['I'] for df in sweep_data_frames) / len(sweep_data_frames)




                # # Check if all data frames have the same length
                # lengths = [len(df) for df in sweep_data_frames]
                # common_v = sweep_data_frames[0]['V']
                # if len(set(lengths)) != 1:  # If lengths vary, then apply the rounding
                #     ic('Applying tolerance because of varying lengths')
                #     tolerance = 1e-3  # Set a tolerance level
                #
                #     # Round 'V' values to the nearest multiple of tolerance
                #     for df in sweep_data_frames:
                #         df['V'] = np.round(df['V'] / tolerance) * tolerance
                #
                #     # Deduplicate 'V' values and keep the first occurrence
                #     for i, df in enumerate(sweep_data_frames):
                #         df = df[~df.duplicated('V')]
                #         sweep_data_frames[i] = df
                #
                #     # After rounding, find the common 'V' values across all DataFrames
                #     common_v = reduce(np.intersect1d, (df['V'] for df in sweep_data_frames))
                # ic(common_v)
                # # Sort common_v to match the original order of the first DataFrame
                # # common_v_sorted = sweep_data_frames[0][sweep_data_frames[0]['V'].isin(common_v)]['V']
                # # Determine the sorting order based on the sweep type
                # if "Forward" in sweep_type:
                #     common_v_sorted = sorted(common_v, reverse=True)
                # elif "Reverse" in sweep_type:
                #     common_v_sorted = sorted(common_v)
                # ic(common_v_sorted)
                # # Assuming 'V' is consistent across all DataFrames now, create a DataFrame with the sorted 'V'
                # merged['data'][sweep_type] = pd.DataFrame({'V': common_v_sorted})
                #
                # # Compute the average for the 'I' column across all DataFrames
                # i_values = [df.set_index('V')['I'].reindex(common_v_sorted).values for df in sweep_data_frames]
                # merged['data'][sweep_type]['I'] = np.nanmean(i_values, axis=0)




                # # Check if all data frames have the same length
                # lengths = [len(df) for df in sweep_data_frames]
                # common_v = sweep_data_frames[0]['V']
                # if len(set(lengths)) != 1:  # If lengths vary, then apply the rounding
                #     ic('omg')
                #     tolerance = 1e-3  # Set a tolerance level
                #     # Round 'V' values to the nearest multiple of tolerance
                #     for df in sweep_data_frames:
                #         df['V'] = np.round(df['V'] / tolerance) * tolerance
                #
                #     # After rounding, we can assume that 'V' values are consistent across data frames
                #     # Find the common 'V' values across all DataFrames
                #     common_v = reduce(np.intersect1d, (df['V'] for df in sweep_data_frames))
                #
                # # Filter and align DataFrames to the common 'V' values
                # # aligned_data_frames = [df[df['V'].isin(common_v)] for df in sweep_data_frames]
                #
                # # Assuming 'V' is consistent across all DataFrames now, we can take any 'V' column
                # merged['data'][sweep_type] = pd.DataFrame({'V': common_v})
                #
                # # Compute the average for the 'I' column across all DataFrames
                # merged['data'][sweep_type]['I'] = sum(df['I'] for df in sweep_data_frames) / len(sweep_data_frames)

        # Merge 'Used files' into a list, ensuring no duplicates.
        used_files = [date_data[pixel_name]['Used files'] for pixel_name in substrate_pixels if
                      'Used files' in date_data[pixel_name]]
        merged['Used files'] = list(set(used_files))
        return merged

    def merge_substrates(self) -> None:
        """
        Merge pixels according to the predefined substrates and retain unmerged pixels.
        """
        # Iterate through the folders
        for folder_name, devices in self.data.items():
            merged_for_date = {}
            for substrate_name, pixel_group in self.substrates.items():
                substrate_pixels = {name: devices[name] for name in pixel_group if name in devices}
                if substrate_pixels:
                    merged_for_date[substrate_name] = self.merge_pixels(folder_name, list(substrate_pixels.keys()))

            # Iterate through the devices in each folder
            for device_name, device_data in devices.items():
                if all(device_name not in group for group in self.substrates.values()):
                    merged_for_date[device_name] = device_data

            self.merged_data[folder_name] = merged_for_date

    def return_merged_data(self):
        return self.merged_data
