from typing import Any, List, Dict


class PixelMerger:
    def __init__(self, data: Dict[str, Any], substrates: Dict[str, List[str]]):
        """
        Initialize the PixelMerger class.

        :param data: A dictionary containing pixel data.
        :param substrates: A dictionary where each key is a substrate name and its value is a list of pixel names.
        """
        self.data = data
        self.substrates = substrates
        self.merged_data = {}
        self.merge_substrates()

    @staticmethod
    def average_parameters(parameter_dicts: List[Dict[str, Any]]) -> Dict[str, float]:
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
        return averaged_params

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

    def merge_pixels(self, substrate_pixels: List[str]) -> Dict[str, Any]:
        """
        Merge all pixel data for a given substrate.

        :param substrate_pixels: A list of pixel names that belong to the same substrate.
        :return: A dictionary containing merged data for the substrate.
        """
        merged = {'Parameters': {}, 'data': []}
        keys_to_check = [
            'Active area (cm²)', 'Distance to light source (mm)',
            'Light intensity (W/cm²)', 'encoding', 'measurement device', 'unit'
        ]

        # Aggregate sweeps data by averaging parameters.
        sweep_types = ['Forward', 'Reverse', 'Average']
        for sweep_type in sweep_types:
            parameters = [self.data[pixel_name]['Parameters'][sweep_type] for pixel_name in substrate_pixels if
                          sweep_type in self.data[pixel_name]['Parameters']]
            merged['Parameters'][sweep_type] = self.average_parameters(parameters)

        # Check for consistency in certain keys.
        for key in keys_to_check:
            merged[key] = self.check_consistency(key, [self.data[pixel_name] for pixel_name in substrate_pixels])

        # Aggregate 'H-index' by averaging.
        h_index_values = [self.data[pixel_name]['H-index'] for pixel_name in substrate_pixels if
                          'H-index' in self.data[pixel_name]]
        merged['H-index'] = sum(h_index_values) / len(h_index_values)

        # Merge IV 'data' by concatenating all data lists.
        for pixel_name in substrate_pixels:
            if 'data' in self.data[pixel_name]:
                merged['data'].extend(self.data[pixel_name]['data'])

        # Merge 'Used files' into a list, ensuring no duplicates.
        used_files = [self.data[pixel_name]['Used files'] for pixel_name in substrate_pixels if
                      'Used files' in self.data[pixel_name]]
        merged['Used files'] = list(set(used_files))

        return merged

    def merge_substrates(self) -> Dict[str, Dict[str, Any]]:
        """
        Merge pixels according to the predefined substrates.

        :return: A dictionary with substrate names as keys and merged data as values.
        """
        for substrate_name, pixel_group in self.substrates.items():
            self.merged_data[substrate_name] = self.merge_pixels(pixel_group)
        return self.merged_data
