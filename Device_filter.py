import pandas as pd
import numpy as np
from instruments import axis_crossing


class DeviceDetector:
    """
    Class to detect and filter devices and/or pixels.
    """

    def __init__(self, data_dict):
        self.data = data_dict


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


