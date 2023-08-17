import pandas as pd
import numpy as np
from instruments import axis_crossing
from icecream import ic


class DeviceDetector:
    """
    Class to detect and filter devices and/or pixels.
    """

    def __init__(self, data_dict):
        self.data = data_dict
        self.print_nested_dict(self.data)
    def print_nested_dict(self, d, indent=0):
        for key, value in d.items():
            print('  ' * indent + str(key))
            if isinstance(value, dict):
                self.print_nested_dict(value, indent + 1)
            else:
                print('  ' * (indent + 1) + str(value))


    def detector(self):

        for device, specs in self.data.items():
            print(device)


    def divide_sweeps(self, data_frame):
        current_values = data_frame['current']
        voltage_values = data_frame['voltage']

        crossing_index = axis_crossing(data_frame, 'voltage')

        if crossing_index is None:  # Only one sweep
            if voltage_values.iloc[-1] > voltage_values.iloc[0]:  # Forward sweep
                return voltage_values, current_values, None, None
            else:  # Reverse sweep
                return None, None, voltage_values, current_values

        else:  # Two sweeps
            voltage_forward = voltage_values.iloc[:crossing_index]
            current_forward = current_values.iloc[:crossing_index]
            voltage_reverse = voltage_values.iloc[crossing_index:]
            current_reverse = current_values.iloc[crossing_index:]
            return voltage_forward, current_forward, voltage_reverse, current_reverse


