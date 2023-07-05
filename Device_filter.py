from icecream import ic
import pandas as pd
import numpy as np


class DeviceDetector:
    """
    Class to detect and filter devices and/or pixels.
    """

    def __init__(self, data_dict):
        self.smu_ones = None
        self.data = data_dict
        # ic(self.data)

    def detector(self):
        self.smu_ones = []
        for device, specs in self.data.items():
            print(device)
            for spec, value in specs.items():
                if spec == 'measurement device' and value == 'SMU':
                    self.smu_ones.append(device)
        self.smu_case()

    def smu_case(self):
        if not self.smu_ones:
            return
        else:
            pass

    def axis_crossing(self, df, col_name):
        df = df[col_name].loc[np.sign(df[col_name]).diff().ne(0)]
        if df.index[0] == 0:  # .diff() always detects the first row as True. Drop that result
            df.drop(df.index[0], inplace=True)
        if len(df.index) == 0:  # If no sign-changes was found return None
            return None
        return df.index[0]

    def divide_sweeps(self, data_frame):
        current_values = data_frame['current']
        voltage_values = data_frame['voltage']

        crossing_index = self.axis_crossing(data_frame, 'voltage')

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


