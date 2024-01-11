import inspect
import os
from datetime import datetime
from typing import Any, Dict, Optional, List


class FilterJVData:
    def __init__(self, parent=None):
        """
        Initialize the FilterJVData class.


        :param parent: (Optional) An instance of the main ctk app, used for integration with a custom tkinter interface.

        """
        self.parent = parent
        self.log = []

    def filter1(self, data: Dict[str, Any], substrates: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Removes dead pixels from the data unless all pixels in a substrate are dead.
        A pixel is considered dead if its average efficiency is less than 0.01.
        If all pixels within a substrate are dead, none are deleted.

        Iterates through each folder and device, checking each pixel's efficiency.
        Dead pixels are removed only if at least one pixel in the same substrate is alive.

        :param substrates: A dictionary where each key is a substrate name, and its value is a list of
                           pixel names.
                           This is used for more advanced filtering based on substrates.
        :param data: A dictionary containing raw device data.
                     The data is expected to be structured with folder names as keys and devices as values.
        :return: A tuple containing the modified data and a list of logs detailing the deletions.
        """
        current_frame = inspect.currentframe()
        method_name = inspect.getframeinfo(current_frame).function
        self.log.append(f"{method_name} is activated\n")
        log_counter = 0
        pixels_to_delete = {}

        # Populate lists of dead and alive pixels
        for folder_name, devices in data.items():
            for device_name, device_data in devices.items():
                if device_name in substrates:
                    dead_pixels = []
                    alive_pixels = []

                    # Check each pixel's efficiency
                    for pixel_name in substrates[device_name]:
                        pixel_data = devices.get(pixel_name)
                        if pixel_data and pixel_data['Parameters']['Average']['Efficiency (%)'] < 0.01:
                            dead_pixels.append(pixel_name)
                        else:
                            alive_pixels.append(pixel_name)

                    # Add dead pixels to the "delete" list if at least one pixel in the substrate is alive
                    if alive_pixels:
                        for dead_pixel in dead_pixels:
                            pixels_to_delete[(folder_name, dead_pixel)] = True

        # Perform deletion based on the populated list
        for (folder_name, dead_pixel) in pixels_to_delete:
            if dead_pixel in data[folder_name]:
                del data[folder_name][dead_pixel]
                log_counter += 1
                self.log.append(f"{log_counter}. Deleted dead pixel: {dead_pixel} in folder: {folder_name}")

        if log_counter == 0:
            self.log.append('No device was filtered out')
        self.log.append('\n')
        return data

    def filter2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Removes specific erroneous measurement points from the data.
        It targets measurements where a device is dead (efficiency < 0.01) and then comes back to life
        (efficiency >= 0.01) in subsequent measurements.
        Iterates through each device's measurements, identifying and marking dead-then-alive patterns.
        Such measurements are then deleted from the data.

        :param data: A dictionary containing raw device data.
        The data is expected to be structured with folder names as keys and devices as values.
        :return: A tuple containing the modified data and a list of logs detailing the deletions.
        """
        current_frame = inspect.currentframe()
        method_name = inspect.getframeinfo(current_frame).function
        self.log.append(f"{method_name} is activated\n")
        log_counter = 0
        device_efficiencies = {}
        # Accumulate efficiencies for each device
        for folder_name, devices in data.items():
            for device_name, device_data in devices.items():
                if 'Parameters' in device_data and 'Average' in device_data['Parameters']:
                    efficiency = device_data['Parameters']['Average'].get('Efficiency (%)')
                    if device_name not in device_efficiencies:
                        device_efficiencies[device_name] = []
                    device_efficiencies[device_name].append([folder_name, efficiency])

        # Identify and delete erroneous measurements
        for device, measurements in device_efficiencies.items():
            to_delete = []
            first_dead_index = None

            for measurement_index, (date, efficiency) in enumerate(measurements):
                if efficiency < 0.01 and first_dead_index is None:
                    first_dead_index = measurement_index
                elif efficiency >= 0.01 and first_dead_index is not None:
                    to_delete.extend(range(first_dead_index, measurement_index))
                    first_dead_index = None
            for measurement in to_delete:
                folder_name = measurements[measurement][0]
                del data[folder_name][device]
                log_counter += 1
                self.log.append(f"{log_counter}. Deleted dead device in the folder: {folder_name}, device: {device}")
        if log_counter == 0:
            self.log.append('Non device was filtered out')
        self.log.append('\n')
        return data

    def dump_log(self, filename: Optional[str] = None):
        """
        Dumps the log to a specified file.
        If no filename is provided, a default name with a timestamp is used.

        :param filename: The (optional) name of the file to write the log to.
        """
        if self.log:
            if not filename:
                base_dir = os.path.basename(self.parent.file_directory)
                today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
                log = f'Filter_log_{today}_for_{base_dir}.txt'
                filename = os.path.join(self.parent.file_directory, log)

            with open(filename, 'w') as f:
                for entry in self.log:
                    f.write(entry + '\n')
