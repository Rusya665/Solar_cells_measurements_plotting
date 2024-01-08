import customtkinter as ctk
from typing import Any, List, Dict, Optional


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

    def filter1(self):
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

    def filter2(self, device_list: List[str]):
        """
        Filter to identify and potentially remove erroneous measurement points for each device.
        It collects the average efficiency for each device across all dates and then applies
        logic to identify erroneous measurements.

        :param device_list: List of available devices.
        """
        device_efficiencies = {device: [] for device in device_list}

        # Collect average efficiencies for each device across all dates
        for device in device_list:
            for folder_name, devices in self.data.items():
                if device in devices:
                    device_data = devices[device]
                    avg_efficiency = device_data['Parameters']['Average']['Efficiency (%)']
                    device_efficiencies[device].append(avg_efficiency)

        # Apply logic to identify and handle erroneous measurements
        for device, efficiencies in device_efficiencies.items():
            self._identify_erroneous_measurements(device, efficiencies)

        return self.data

    def _identify_erroneous_measurements(self, folder_name: str, device_name: str, efficiencies: List[float]):
        """
        Identifies and handles erroneous measurement points for a given device.

        :param folder_name: Name of the folder where the measurement is located.
        :param device_name: Name of the device.
        :param efficiencies: List of average efficiencies for the device.
        """
        erroneous_points = []
        for i in range(len(efficiencies) - 1):
            current_eff = efficiencies[i]
            next_eff = efficiencies[i + 1]

            if current_eff < 0.01 and next_eff >= 0.01:
                erroneous_points.append(i)

        # Logic to remove erroneous points
        # This will depend on how you want to handle the removal in your data structure
        for point in erroneous_points:
            # Implement the removal of the erroneous point
            del self.data[folder_name][device_name]
