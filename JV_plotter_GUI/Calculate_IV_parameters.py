from tkinter import messagebox

import numpy as np

from JV_plotter_GUI.settings import settings


class CalculateIVParameters:
    """
        This class is designed for analyzing device measurements, specifically for photovoltaic devices.
    """

    def __init__(self, parent, matched_devices: dict):
        self.data = matched_devices
        self.parent = parent
        self.warning_messages = []
        self.efficiency_forward, self.efficiency_reverse = None, None
        self.i_sc_forward, self.i_sc_reverse = None, None
        self.v_oc_forward, self.v_oc_reverse = None, None
        self.fill_factor_forward, self.fill_factor_reverse = None, None
        self.max_power_forward, self.max_power_reverse = None, None
        self.v_mpp_forward, self.v_mpp_reverse = None, None
        self.j_mpp_forward, self.j_mpp_reverse = None, None
        self.rs_forward, self.rs_reverse = None, None
        self.rsh_forward, self.rsh_reverse = None, None
        self.active_area, self.light_intensity, self.distance_to_light_source = None, None, None
        self.h_index = None
        self.parameter_dict = settings['parameter_dict']
        # self.parameter_dict = {
        #     1: 'Label',
        #     2: 'Scan direction',
        #     3: 'Efficiency (%)',
        #     4: 'Short-circuit current density (mA/cm²)',
        #     5: 'Open circuit voltage (V)',
        #     6: 'Fill factor',
        #     7: 'Maximum power (W)',
        #     8: 'Voltage at MPP (V)',
        #     9: 'Current density at MPP (mA/cm²)',
        #     10: 'Series resistance, Rs (ohm)',
        #     11: 'Shunt resistance, Rsh (ohm)',
        #     12: 'H-index',
        #     13: 'Active area, (cm²)',
        #     14: 'Light intensity (W/cm²)',
        #     15: 'Distance to light source (mm)',
        #     16: 'Device order',
        # }

        self.perform_calculation()
        if self.warning_messages:
            all_warnings = "\n".join(self.warning_messages)
            messagebox.showwarning("Warning!", f"Invalid data detected while calculating the\n"
                                               f"series resistance for the following devices:\n{all_warnings}\n"
                                               "This is likely due to bad JV data from a dead cell.")

    def perform_calculation(self):
        # Iterate through the folders
        for folder_name, devices in self.data.items():
            # Iterate through the devices in each folder
            for device_name, device_data in devices.items():
                self.active_area = device_data["Active area (cm²)"]
                self.light_intensity = device_data['Light intensity (W/cm²)']
                self.distance_to_light_source = device_data['Distance to light source (mm)']
                for sweep_name, sweep_data in device_data['data'].items():
                    power = sweep_data['I'] * sweep_data['V']
                    ind_mpp = np.argmax(power)
                    max_power = power[ind_mpp]
                    v_mpp = sweep_data['V'][ind_mpp]
                    j_mpp = sweep_data['I'][ind_mpp] / self.active_area
                    eff = 100 * max_power / (self.light_intensity * self.active_area)  # Efficiency in percentage

                    voc_approx, voc_index = self.calculate_voc_approx(sweep_data['V'], sweep_data['I'])
                    isc, rsh, b = self.calculate_isc_and_rsh(sweep_data['V'], sweep_data['I'], voc_approx)
                    voc, rs, b1 = self.calculate_voc_and_rs(sweep_data['V'], sweep_data['I'], voc_index,
                                                            device_name, folder_name)
                    ff = 0.0 if isc * voc == 0 else max_power / (isc * voc)  # Fill Factor
                    if sweep_name == '1_Forward':
                        self.i_sc_forward, self.v_oc_forward = isc, voc
                        self.rs_forward, self.rsh_forward = rs, rsh
                        self.max_power_forward, self.j_mpp_forward, self.v_mpp_forward = max_power, j_mpp, v_mpp
                        self.efficiency_forward, self.fill_factor_forward = eff, ff
                    elif sweep_name == '2_Reverse':
                        self.i_sc_reverse, self.v_oc_reverse = isc, voc
                        self.rs_reverse, self.rsh_reverse = rs, rsh
                        self.max_power_reverse, self.j_mpp_reverse, self.v_mpp_reverse = max_power, j_mpp, v_mpp
                        self.efficiency_reverse, self.fill_factor_reverse = eff, ff

                self.fill_dict_with_iv_parameters(device_data=device_data)
                device_data['H-index'] = self.h_index

    @staticmethod
    def calculate_voc_approx(voltage_data, current_data):
        voc_index = np.argmin(np.abs(current_data))
        return voltage_data[voc_index], voc_index

    @staticmethod
    def linfit_golden(x_data, y_data):
        """
        Linear fit using various methods.
        Uncomment the desired method.

        :param x_data: np.ndarray
            The x-values of the data points.
        :param y_data: np.ndarray
            The y-values of the data points.
        :return: tuple
            The slope and intercept of the best-fit line in the form (intercept, slope).

        Speed (Based on 1000 iterations):
        - The Least Squares Method: ~0.080 seconds
        - Direct Solve Method: ~0.020 seconds
        - Inverse Method: ~0.040 seconds
        """
        # Create design matrix
        design_matrix = np.vstack([np.ones(x_data.shape[0]), x_data]).T

        # Method 1: The Least Squares Method
        # Recommended as the golden choice.
        # More robust and can handle cases where the system of equations doesn't have a direct solution.
        # Slower but generally more reliable (~0.080 seconds).
        slope, intercept = np.linalg.lstsq(design_matrix, y_data, rcond=None)[0]

        # Method 2: Direct Solve Method (Uncomment to use)
        # Fastest method (~0.020 seconds).
        # May be less stable for ill-conditioned matrices.
        # slope, intercept = np.linalg.solve(design_matrix.T @ design_matrix, design_matrix.T @ y_data)

        # Method 3: Inverse Method (Uncomment to use)
        # Moderate speed (~0.040 seconds).
        # Involves direct matrix inversion, can be numerically unstable for ill-conditioned matrices.
        # slope, intercept = np.linalg.inv(design_matrix.T @ design_matrix) @ design_matrix.T @ y_data

        return intercept, slope

    def calculate_isc_and_rsh(self, voltage_data, current_data, voc_approx):
        isc_indices_fit = np.abs(voltage_data) / voc_approx < 0.3
        intercept, slope = self.linfit_golden(voltage_data[isc_indices_fit], current_data[isc_indices_fit])
        isc = slope
        rsh = 0.0 if intercept == 0 else -1 / intercept
        return isc, rsh, (slope, intercept)

    def calculate_voc_and_rs(self, voltage_data, current_data, voc_index, device_name, folder):
        voc_indices_fit = [voc_index - 1, voc_index - 0] if current_data[voc_index] < 0 else [voc_index - 1, voc_index]
        try:
            intercept, slope = self.linfit_golden(voltage_data[voc_indices_fit], current_data[voc_indices_fit])
        except KeyError:
            self.warning_messages.append(f"{device_name} in {folder}")
            # Handle the error as you see fit, perhaps setting intercept and slope to some default values
            intercept, slope = 0, 1e-9  # Setting to some default values
        voc = -slope / intercept if intercept != 0 else 0
        rs = 0.0 if intercept == 0 else -1 / intercept
        return voc, rs, (slope, intercept)

    def fill_dict_with_iv_parameters(self, device_data: dict) -> None:
        # https://doi.org/10.1021/acsenergylett.8b01627
        self.h_index = (self.efficiency_reverse - self.efficiency_forward) / self.efficiency_reverse
        device_data['Parameters'] = {}
        device_data['Parameters']['Forward'] = {
            self.parameter_dict[3]: self.efficiency_forward,
            self.parameter_dict[4]: 1000 * self.i_sc_forward / self.active_area,
            self.parameter_dict[5]: self.v_oc_forward,
            self.parameter_dict[6]: self.fill_factor_forward,
            self.parameter_dict[7]: self.max_power_forward,
            self.parameter_dict[8]: self.v_mpp_forward,
            self.parameter_dict[9]: 1000 * self.j_mpp_forward,
            self.parameter_dict[10]: self.rs_forward,
            self.parameter_dict[11]: self.rsh_forward,
        }
        device_data['Parameters']['Reverse'] = {
            self.parameter_dict[3]: self.efficiency_reverse,
            self.parameter_dict[4]: 1000 * self.i_sc_reverse / self.active_area,
            self.parameter_dict[5]: self.v_oc_reverse,
            self.parameter_dict[6]: self.fill_factor_reverse,
            self.parameter_dict[7]: self.max_power_reverse,
            self.parameter_dict[8]: self.v_mpp_reverse,
            self.parameter_dict[9]: 1000 * self.j_mpp_reverse,
            self.parameter_dict[10]: self.rs_reverse,
            self.parameter_dict[11]: self.rsh_reverse,
        }
        device_data['Parameters']['Average'] = {
            self.parameter_dict[3]: (self.efficiency_reverse + self.efficiency_forward) / 2,
            self.parameter_dict[4]: 1000 * (self.i_sc_forward / self.active_area + self.i_sc_reverse /
                                            self.active_area) / 2,
            self.parameter_dict[5]: (self.v_oc_reverse + self.v_oc_forward) / 2,
            self.parameter_dict[6]: (self.fill_factor_reverse + self.fill_factor_forward) / 2,
            self.parameter_dict[7]: (self.max_power_reverse + self.max_power_forward) / 2,
            self.parameter_dict[8]: (self.v_mpp_reverse + self.v_mpp_forward) / 2,
            self.parameter_dict[9]: 1000 * (self.j_mpp_reverse + self.j_mpp_forward) / 2,
            self.parameter_dict[10]: (self.rs_forward + self.rs_reverse) / 2,
            self.parameter_dict[11]: (self.rsh_reverse + self.rsh_forward) / 2,
        }
