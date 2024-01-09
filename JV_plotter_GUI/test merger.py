import json
from typing import Any, List, Dict

import numpy as np
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
        self.stat = 'std_dev'
        # self.stat = 'mae'
        self.merge_substrates()

    @staticmethod
    def average_parameters1(parameter_dicts: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Average the parameters across a set of pixels.

        :param parameter_dicts: A list of dictionaries, each containing parameter of a pixel.
        :return: A dictionary containing averaged parameters.
        """
        averaged_params = {}
        count = len(parameter_dicts)
        for param_dict in parameter_dicts:
            for key, value in param_dict.items():
                averaged_params[key] = averaged_params.get(key, 0) + value / count
        ic(averaged_params)
        return averaged_params

    def average_parameters(self, parameter_dicts: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate the average and error (standard deviation or mean absolute error) for parameters across a set of pixels.

        :param parameter_dicts: A list of dictionaries, all containing parameters of a pixel.
        :return: A dictionary containing the averages and their corresponding errors.
        """
        param_values = {key: [] for key in parameter_dicts[0]}
        for param_dict in parameter_dicts:
            for key, value in param_dict.items():
                param_values[key].append(value)

        calculated_params = {}
        for key, values in param_values.items():
            mean_value = np.mean(values)
            calculated_params[key] = mean_value

            if self.stat == 'std_dev':
                error_value = np.std(values, ddof=1)  # Sample standard deviation
            elif self.stat == 'mae':
                error_value = np.mean(np.abs(values - mean_value))  # Mean Absolute Error
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
        # all_sweep_types = set()
        # for pixel_name in substrate_pixels:
        #     all_sweep_types.update(self.data[folder_name][pixel_name]['data'].keys())
        # ic(all_sweep_types)

        # # Process and average IV data for each sweep type
        # for sweep_type in all_sweep_types:
        #     sweep_data_frames = []
        #     for pixel_name in substrate_pixels:
        #         pixel_data = self.data[folder_name][pixel_name]
        #         if sweep_type in pixel_data['data']:
        #             sweep_data_frames.append(pixel_data['data'][sweep_type])
        #
        #     if sweep_data_frames:
        #         # Assuming 'V' is the same in all DataFrames
        #         merged['data'][sweep_type] = pd.DataFrame()
        #         merged['data'][sweep_type]['V'] = sweep_data_frames[0]['V']
        #
        #         # Compute the average for the 'I' column across all DataFrames
        #         merged['data'][sweep_type]['I'] = sum(df['I'] for df in sweep_data_frames) / len(sweep_data_frames)

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


def helper(suffix, data):
    # Accumulate efficiencies for each pixel across devices
    pixel_efficiencies = {}
    for device_name, device_data in data.items():
        for pixel_name, pixel_info in device_data.items():
            if suffix == 'before':
                name = 'scanCVivsE-11R-1'
            elif suffix == 'after':
                name = 'scanCVivsE-11R'
            if ('Parameters' in pixel_info and 'Average' in
                    # pixel_info['Parameters'] and pixel_name == 'scanCVivsE-10R-2'):
                    pixel_info['Parameters'] and pixel_name == name):
                efficiency = pixel_info['Parameters']['Average'].get('Efficiency (%)')
                if efficiency is not None:
                    if pixel_name not in pixel_efficiencies:
                        pixel_efficiencies[pixel_name] = []
                    pixel_efficiencies[pixel_name].append([device_name, efficiency])
    ic(suffix, pixel_efficiencies)


if __name__ == "__main__":
    path = (r'D:/OneDrive - O365 Turun yliopisto/Documents/Aging tests/2023 Carbon revival/'
            r'3. New thing, dark storage/Measurememnts separated/Mahboubeh/2024-01-09 Mahboubeh IV data.json')
    path2 = (r'D:/OneDrive - O365 Turun yliopisto/Documents/Aging tests/2023 Carbon revival/'
             r'3. New thing, dark storage/Measurememnts separated/Mahboubeh/2024-01-09 Mahboubeh pixels sorted.json')
    with open(path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    with open(path2, 'r', encoding='utf-8') as file:
        sub_data = json.load(file)
    helper('before', json_data)
    instance = PixelMerger(data=json_data, substrates=sub_data, parent=None)
    json_data = instance.return_merged_data()
    helper('after', data=json_data)
    ic(json_data)
