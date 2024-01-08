from typing import Any, List, Dict, Optional

import customtkinter as ctk


class FilterJVData:
    def __init__(self, parent: ctk.CTk, data: Dict[str, Any], substrates: Optional[Dict[str, List[str]]] = None):
        """
        Initialize the FilterJVData class.

        :param parent: An instance of the main ctk app.
        :param data: A dictionary containing raw device data.
        :param substrates: An optional dictionary where each key is a substrate name, and its value is a list of pixel
         names.
        """
        self.parent = parent
        self.data = data
        self.substrates = substrates
        pass

    def filter1(self) -> Dict:
        """
        Filter to remove dead pixels from the data. A pixel is considered dead if its average efficiency is less than
        0.01. If all pixels within a substrate are dead, one pixel is retained but its parameters (except IV data)
        are zeroed out.

        The method iterates through each folder and device in the data. For substrates with multiple pixels, it
        checks each pixel's efficiency. If a pixel is dead, it's removed unless all pixels in the substrate are dead.
        In that case, one pixel is retained with all its parameters (except 'data') set to zero.
        """
        # Iterate through the folders
        for folder_name, devices in self.data.items():
            # Iterate through the devices in each folder
            for device_name, device_data in devices.items():
                if device_name in self.substrates and len(self.substrates[device_name]) > 1:
                    dead_pixels = []
                    for pixel_name in self.substrates[device_name]:
                        pixel_data = device_data.get(pixel_name)
                        if pixel_data and pixel_data['Parameters']['Average']['Efficiency (%)'] < 0.01:
                            dead_pixels.append(pixel_name)

                    # If all pixels are dead, retain one pixel with zeroed parameters
                    if len(dead_pixels) == len(self.substrates[device_name]):
                        retained_pixel = self.substrates[device_name][0]
                        # Zero out H-index and all nested Parameters
                        device_data[retained_pixel] = {key: 0 for key in device_data[retained_pixel].keys()}
                        device_data[retained_pixel]['Parameters'] = {k: {p: 0 for p in v} for k, v in
                                                                     device_data[retained_pixel]['Parameters'].items()}
                        device_data[retained_pixel]['H-index'] = 0
                        device_data[retained_pixel]['data'] = device_data[retained_pixel][
                            'data']  # Preserve the IV data
                    else:
                        # Delete dead pixels
                        for dead_pixel in dead_pixels:
                            del device_data[dead_pixel]

        return self.data

    def filter2(self):
        """
         Updated filter to remove erroneous measurement points based on the new criteria.
        It checks the efficiency of each pixel in sequential measurements across devices and removes the entire pixel data
        if a pixel is dead (efficiency < 0.01) for one or more measurements and then comes back to life in a subsequent measurement.

        :return: Modified data with a list of deleted pixels and their respective folder names.
        """
        deleted_pixels = []

        # Accumulate efficiencies for each pixel across devices
        pixel_efficiencies = {}
        for device_name, device_data in self.data.items():
            for pixel_name, pixel_info in device_data.items():
                if 'Parameters' in pixel_info and 'Average' in pixel_info['Parameters']:
                    efficiency = pixel_info['Parameters']['Average'].get('Efficiency (%)')
                    if efficiency is not None:
                        if pixel_name not in pixel_efficiencies:
                            pixel_efficiencies[pixel_name] = []
                        pixel_efficiencies[pixel_name].append(efficiency)

        # Check for consecutive dead measurements followed by an alive one
        for pixel_name, efficiencies in pixel_efficiencies.items():
            was_dead = False
            for efficiency in efficiencies:
                if efficiency < 0.01:
                    was_dead = True
                elif was_dead and efficiency >= 0.01:
                    deleted_pixels.append(pixel_name)
                    break

        # Remove the entire pixel data for pixels that showed the dead-then-alive pattern
        for device_name, device_data in data.items():
            for pixel_name in deleted_pixels:
                if pixel_name in device_data:
                    del device_data[pixel_name]

        return data, deleted_pixels

    def updated_filter2(data):
        """
        Updated filter to remove erroneous measurement points based on the new criteria.
        It checks the efficiency of each pixel in sequential measurements across devices and removes the entire pixel data
        if a pixel is dead (efficiency < 0.01) for one or more measurements and then comes back to life in a subsequent measurement.

        :param data: The JSON data loaded from the file.
        :return: Modified data with a list of deleted pixels and their respective folder names.
        """
        deleted_pixels = []

        # Accumulate efficiencies for each pixel across devices
        pixel_efficiencies = {}
        for device_name, device_data in data.items():
            for pixel_name, pixel_info in device_data.items():
                if 'Parameters' in pixel_info and 'Average' in pixel_info['Parameters']:
                    efficiency = pixel_info['Parameters']['Average'].get('Efficiency (%)')
                    if efficiency is not None:
                        if pixel_name not in pixel_efficiencies:
                            pixel_efficiencies[pixel_name] = []
                        pixel_efficiencies[pixel_name].append(efficiency)

        # Check for consecutive dead measurements followed by an alive one
        for pixel_name, efficiencies in pixel_efficiencies.items():
            was_dead = False
            for efficiency in efficiencies:
                if efficiency < 0.01:
                    was_dead = True
                elif was_dead and efficiency >= 0.01:
                    deleted_pixels.append(pixel_name)
                    break

        # Remove the entire pixel data for pixels that showed the dead-then-alive pattern
        for device_name, device_data in data.items():
            for pixel_name in deleted_pixels:
                if pixel_name in device_data:
                    del device_data[pixel_name]

        return data, deleted_pixels
