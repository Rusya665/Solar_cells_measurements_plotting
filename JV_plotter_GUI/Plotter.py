import math
import os
import time
from datetime import date
from tkinter import messagebox

import numpy as np
import xlsxwriter

from JV_plotter_GUI.instruments import open_file, row_to_excel_col, custom_round
from JV_plotter_GUI.settings import settings


class DevicePlotter:
    """
        This class is designed for plotting and analyzing device measurements, specifically for photovoltaic devices.
    """

    def __init__(self, parent, matched_devices: dict):
        self.data = matched_devices
        self.parent = parent
        self.name = self.__class__.__name__
        # Assuming the default cells height 20 pixels and width 64
        self.chart_horizontal_spacing = math.ceil((480 * settings[self.name]['chart_x_scale']) / 64) + 1
        self.chart_vertical_spacing = math.ceil((288 * settings[self.name]['chart_y_scale']) / 20) + 1
        self.chart_huge_horizontal_spacing = math.ceil((480 * settings[self.name]['all_in_one_chart_x_scale']) / 64) + 1
        self.chart_huge_vertical_spacing = math.ceil((288 * settings[self.name]['all_in_one_chart_y_scale']) / 20) + 1
        self.xlsx_name = ''
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
        self.parameter_dict = {
            1: 'Label',
            2: 'Scan direction',
            3: 'Efficiency (%)',
            4: 'Short-circuit current density (mA/cm²)',
            5: 'Open circuit voltage (V)',
            6: 'Fill factor',
            7: 'Maximum power (W)',
            8: 'Voltage at MPP (V)',
            9: 'Current density at MPP (mA/cm²)',
            10: 'Series resistance, Rs (ohm)',
            11: 'Shunt resistance, Rsh (ohm)',
            12: 'Active area, (cm²)',
            13: 'Light intensity (W/cm²)',
            14: 'Distance to light source (mm)',
            15: 'Device order',
        }

        self.workbook = self.create_workbook()
        self.center = self.workbook.add_format({'align': 'center'})
        self.across_selection = self.workbook.add_format()
        self.across_selection.set_center_across()
        self.wb_main = self.workbook.add_worksheet('Total')

        if self.parent.aging_mode:
            self.aging_sheet = self.workbook.add_worksheet('Aging')

        self.wb_table = self.workbook.add_worksheet('Table_Total')

        if self.parent.aging_mode:
            self.timeline_df = self.parent.timeline_df
            self.aging_plots_forward_absolute = self.workbook.add_worksheet('Aging_plots_forward_raw')
            self.aging_plots_reverse_absolute = self.workbook.add_worksheet('Aging_plots_reverse_raw')
            self.aging_plots_avg_absolute = self.workbook.add_worksheet('Aging_plots_avg_raw')
            self.aging_plots_forward_relative = self.workbook.add_worksheet('Aging_plots_forward_normalized')
            self.aging_plots_reverse_relative = self.workbook.add_worksheet('Aging_plots_reverse_normalized')
            self.aging_plots_avg_relative = self.workbook.add_worksheet('Aging_plots_avg_normalized')

        self.wb_table_forward = self.workbook.add_worksheet('Table_Forward')
        self.wb_table_reverse = self.workbook.add_worksheet('Table_Reverse')
        self.wb_table_average = self.workbook.add_worksheet('Table_Average')

        self.set_worksheets()
        self.fill_tables()
        self.aging()

        self.wb_table.autofit()
        self.wb_table_forward.autofit()
        self.wb_table_reverse.autofit()
        self.wb_table_average.autofit()
        if self.parent.aging_mode:
            self.aging_sheet.autofit()

        self.workbook.close()
        if self.parent.open_wb:
            time.sleep(0.2)
            open_file(self.xlsx_name)
        if self.warning_messages:
            all_warnings = "\n".join(self.warning_messages)
            messagebox.showwarning("Warning!", f"Invalid data detected while calculating the\n"
                                               f"series resistance for the following devices:\n{all_warnings}\n"
                                               "This is likely due to bad JV data from a dead cell.")

    def create_workbook(self):
        """
        Creating new xlsx doc and/or folder for it
        :return: Workbook
        """
        base_dir = os.path.basename(self.parent.file_directory)
        self.xlsx_name = os.path.join(self.parent.file_directory,
                                      f"{date.today()} {base_dir} JV plots and calculations.xlsx")
        self.workbook = xlsxwriter.Workbook(self.xlsx_name, {'strings_to_numbers': True})
        return self.workbook

    def set_worksheets(self):
        folder_counter, device_counter = 0, -1

        # Check if any name is too long
        long_name_found = any(
            len(f"{folder_name} {device_name}") > 31
            for folder_name, devices in self.data.items()
            for device_name in devices
        )

        # Iterate through the folders
        for folder_name, devices in self.data.items():
            folder_counter += 1
            # Iterate through the devices in each folder
            for device_name, device_data in devices.items():
                device_counter += 1
                # Decide the worksheet name based on whether a long name was found
                ws_name = (
                    f"{folder_counter} {device_name}" if long_name_found
                    else f"{folder_name} {device_name}"
                )
                ws_name = f'{device_name}' if len(self.data) == 1 else ws_name
                ws_name = ws_name[:31] if len(ws_name) > 31 else ws_name
                data = self.data[folder_name][device_name]['data']
                self.data[folder_name][device_name].update({
                    'sheet_name': ws_name,
                    'sweep_indexes_data': {
                        'all_data_length': len(data['1_Forward']) + len(data['2_Reverse']) + 2,
                        'reverse_start_row': len(data['1_Forward']) + 2,
                        'forward_start_row': 2
                    }
                })
                ws = self.workbook.add_worksheet(ws_name)

                self.set_headers(ws=ws, device_name=device_name)
                self.active_area = device_data["Active area"]
                self.light_intensity = device_data['Light Intensity']
                self.distance_to_light_source = device_data['Distance to light source']
                # Iterate through the sweeps (Forward and Reverse) for each device
                row = 1
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
                    # Write the data to the worksheet
                    for _, row_data in sweep_data.iterrows():
                        # ws.write(row, 0, row_data['I'])
                        ws.write(row, 1, row_data['V'])
                        power = row_data['I'] * row_data['V']
                        current_density = 1000 * row_data['I'] / self.active_area
                        ws.write(row, 2, power)
                        ws.write(row, 0, current_density)
                        row += 1

                self.write_parameters(ws, device_data)

                # Insert IV charts into devices' sheets
                ws.insert_chart('E16', self.plot_iv(sheet_name=ws_name, data_start=2,
                                                    data_end=row, name_suffix=None))
                ws.insert_chart(f"J1", self.plot_iv(sheet_name=ws_name, data_start=2,
                                                    data_end=len(data['1_Forward']) + 1,
                                                    name_suffix='Forward'))
                ws.insert_chart(f"J{self.chart_vertical_spacing}", self.plot_iv(sheet_name=ws_name,
                                                                                data_start=len(data['1_Forward']) + 2,
                                                                                data_end=row, name_suffix='Reverse'))
                # Write file name(s) being used to create this pixel/device data
                used_files_data = [device_data['Used files']] if isinstance(device_data['Used files'], str) else \
                    device_data['Used files']
                ws.write(0, 8 + self.chart_horizontal_spacing, 'Used files', self.center)
                ws.write_column(1, 8 + self.chart_horizontal_spacing, used_files_data)
                # Insert each devise plot separately into the main sheet
                self.wb_main.insert_chart(self.chart_huge_vertical_spacing,
                                          self.chart_horizontal_spacing * device_counter,
                                          self.plot_iv(sheet_name=ws_name,
                                                       data_start=2,
                                                       data_end=row, name_suffix=None))
                self.wb_main.insert_chart(self.chart_huge_vertical_spacing + self.chart_vertical_spacing,
                                          self.chart_horizontal_spacing * device_counter,
                                          self.plot_iv(sheet_name=ws_name,
                                                       data_start=2,
                                                       data_end=len(data['1_Forward']) + 2,
                                                       name_suffix='Forward'))
                self.wb_main.insert_chart(self.chart_huge_vertical_spacing + self.chart_vertical_spacing * 2,
                                          self.chart_horizontal_spacing * device_counter,
                                          self.plot_iv(sheet_name=ws_name,
                                                       data_start=len(data['1_Forward']) + 2,
                                                       data_end=row,
                                                       name_suffix='Reverse'))
        # insert huge IV plots into the main sheet
        self.wb_main.insert_chart('A1', self.plot_all_sweeps(start_key='forward_start_row',
                                                             end_key='all_data_length', name_suffix=''))
        self.wb_main.insert_chart(0, self.chart_huge_horizontal_spacing,
                                  self.plot_all_sweeps(start_key='forward_start_row',
                                                       end_key='reverse_start_row', name_suffix='Forward'))
        self.wb_main.insert_chart(0, self.chart_huge_horizontal_spacing * 2,
                                  self.plot_all_sweeps(start_key='reverse_start_row',
                                                       end_key='all_data_length', name_suffix='Reverse'))

    def set_headers(self, ws, device_name):
        # Write the headers for I, V, and P
        ws.write(0, 0, 'J, mA/cm²', self.center)
        # ws.write(0, 0, 'I, mA', self.center)
        ws.write(0, 1, 'V, V', self.center)
        ws.write(0, 2, 'P, W', self.center)

        # Write the device name and parameters in column D
        ws.write(0, 4, device_name, self.center)
        ws.write(1, 4, 'Parameters', self.center)
        last_key = list(self.parameter_dict.keys())[-1]
        for i, value in self.parameter_dict.items():
            if i in [1, 2, last_key]:
                continue
            ws.write(i - 1, 4, value, self.center)
        ws.set_column(4, 4, 35)
        # Write the "Values" header in column E
        self.write_center_across_selection(ws, (0, 5), 'Values', 3)

        # Write the "Reverse" and "Forward" headers in columns E and F
        ws.write(1, 5, 'Reverse', self.center)
        ws.write(1, 6, 'Forward', self.center)
        ws.write(1, 7, 'Average', self.center)

    def write_center_across_selection(self, ws, position, text, number_of_cells):
        row, col = position
        ws.write(row, col, text, self.across_selection)
        for i in range(1, number_of_cells):
            ws.write_blank(row, col + i, '', self.across_selection)

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

    def write_parameters(self, ws, device_data):
        # Write the active area value
        self.write_center_across_selection(ws, (11, 5), self.active_area, 3)
        # Write the light intensity value
        self.write_center_across_selection(ws, (12, 5), self.light_intensity, 3)
        # Write the distance to the light source
        self.write_center_across_selection(ws, (13, 5), self.distance_to_light_source, 3)

        eff_avr = (self.efficiency_reverse + self.efficiency_forward) / 2
        ws.write(2, 5, self.efficiency_reverse)  # Reverse Efficiency
        ws.write(2, 6, self.efficiency_forward)  # Forward Efficiency
        ws.write(2, 7, eff_avr)  # Average Efficiency

        j = 1000 * (self.i_sc_forward + self.i_sc_reverse) / self.active_area
        ws.write(3, 5, 1000 * self.i_sc_reverse / self.active_area)  # Reverse short circuit current density
        ws.write(3, 6, 1000 * self.i_sc_forward / self.active_area)  # Forward short circuit current density
        ws.write(3, 7, j)  # Average short circuit current density

        v_oc_average = (self.v_oc_reverse + self.v_oc_forward) / 2
        ws.write(4, 5, self.v_oc_reverse)
        ws.write(4, 6, self.v_oc_forward)
        ws.write(4, 7, v_oc_average)

        ff = (self.fill_factor_reverse + self.fill_factor_forward) / 2
        ws.write(5, 5, self.fill_factor_reverse)  # Reverse Fill Factor
        ws.write(5, 6, self.fill_factor_forward)  # Forward Fill Factor
        ws.write(5, 7, ff)  # Average Fill Factor

        max_power_average = (self.max_power_reverse + self.max_power_forward) / 2
        ws.write(6, 5, self.max_power_reverse)  # Reverse Max Power
        ws.write(6, 6, self.max_power_forward)  # Forward Max Power
        ws.write(6, 7, max_power_average)  # Average Max Power

        v_mpp = (self.v_mpp_reverse + self.v_mpp_forward) / 2
        ws.write(7, 5, self.v_mpp_reverse)  # Reverse Voltage at MPP
        ws.write(7, 6, self.v_mpp_forward)  # Forward Voltage at MPP
        ws.write(7, 7, v_mpp)  # Average Voltage at MPP

        j_mpp = 1000 * (self.j_mpp_reverse + self.j_mpp_forward) / 2
        ws.write(8, 5, 1000 * self.j_mpp_reverse)  # Reverse Current density at MPP
        ws.write(8, 6, 1000 * self.j_mpp_forward)  # Forward Current density at MPP
        ws.write(8, 7, j_mpp)  # Average Current density at MPP

        rs = (self.rs_forward + self.rs_reverse) / 2
        ws.write(9, 5, self.rs_reverse)  # Reverse series resistance, Rs (ohm)
        ws.write(9, 6, self.rs_forward)  # Forward series resistance, Rs (ohm)
        ws.write(9, 7, rs)  # Average series resistance, Rs (ohm)

        rsh = (self.rsh_reverse + self.rsh_forward) / 2
        ws.write(10, 5, self.rsh_reverse)  # Reverse shunt resistance, Rsh (ohm)
        ws.write(10, 6, self.rsh_forward)  # Forward shunt resistance, Rsh (ohm)
        ws.write(10, 7, rsh)  # Average shunt resistance, Rsh (ohm)

        device_data['Parameters'] = {}
        device_data['Parameters']['Forward'] = {
            self.parameter_dict[3]: self.efficiency_forward,
            self.parameter_dict[4]: self.i_sc_forward / self.active_area,
            self.parameter_dict[5]: self.v_oc_forward,
            self.parameter_dict[6]: self.fill_factor_forward,
            self.parameter_dict[7]: self.max_power_forward,
            self.parameter_dict[8]: self.v_mpp_forward,
            self.parameter_dict[9]: self.j_mpp_forward,
            self.parameter_dict[10]: self.rs_forward,
            self.parameter_dict[11]: self.rsh_forward,
        }
        device_data['Parameters']['Reverse'] = {
            self.parameter_dict[3]: self.efficiency_reverse,
            self.parameter_dict[4]: self.i_sc_reverse / self.active_area,
            self.parameter_dict[5]: self.v_oc_reverse,
            self.parameter_dict[6]: self.fill_factor_reverse,
            self.parameter_dict[7]: self.max_power_reverse,
            self.parameter_dict[8]: self.v_mpp_reverse,
            self.parameter_dict[9]: self.j_mpp_reverse,
            self.parameter_dict[10]: self.rs_reverse,
            self.parameter_dict[11]: self.rsh_reverse,
        }
        device_data['Parameters']['Average'] = {
            self.parameter_dict[3]: eff_avr,
            self.parameter_dict[4]: j,
            self.parameter_dict[5]: v_oc_average,
            self.parameter_dict[6]: ff,
            self.parameter_dict[7]: max_power_average,
            self.parameter_dict[8]: v_mpp,
            self.parameter_dict[9]: j_mpp,
            self.parameter_dict[10]: rs,
            self.parameter_dict[11]: rsh,
        }

    def fill_tables(self):
        table_type = {self.wb_table: ['G', 'F'],
                      self.wb_table_forward: ['G'],
                      self.wb_table_reverse: ['F'],
                      self.wb_table_average: ['H'],
                      }
        for table, sweeps in table_type.items():
            self.write_table_headers(table)
            # Iterate through the folders
            row_index = 1
            for folder_name, devices in self.data.items():
                # Iterate through the devices in each folder
                for device_name, device_data in devices.items():
                    sheet_name = device_data['sheet_name']
                    for sweep in sweeps:
                        self.write_table_rows(table, row_index, sheet_name, sweep)
                        row_index += 1
            table.autofilter(0, 0, row_index, len(self.parameter_dict) - 1)  # Apply auto filter to the table

    def write_table_headers(self, ws):
        for i, header in self.parameter_dict.items():
            ws.write(0, i - 1, header, self.center)

    def write_table_rows(self, ws, row_index, sheet_name, sweep_direction):
        col_letter = sweep_direction  # First letter of the sweep direction (F, G, or H)
        ws.write(row_index, 0, sheet_name)  # Label
        ws.write_formula(row_index, 1, f"='{sheet_name}'!{col_letter}2")  # Scan direction
        ws.write_formula(row_index, 2, f"='{sheet_name}'!{col_letter}3")  # Efficiency
        ws.write_formula(row_index, 3, f"='{sheet_name}'!{col_letter}4")  # Short-circuit current density
        ws.write_formula(row_index, 4, f"='{sheet_name}'!{col_letter}5")  # Open circuit voltage
        ws.write_formula(row_index, 5, f"='{sheet_name}'!{col_letter}6")  # Fill factor
        ws.write_formula(row_index, 6, f"='{sheet_name}'!{col_letter}7")  # Maximum power
        ws.write_formula(row_index, 7, f"='{sheet_name}'!{col_letter}8")  # Voltage at MPP
        ws.write_formula(row_index, 8, f"='{sheet_name}'!{col_letter}9")  # Current density at MPP
        ws.write_formula(row_index, 9, f"='{sheet_name}'!{col_letter}10")  # Series resistance
        ws.write_formula(row_index, 10, f"='{sheet_name}'!{col_letter}11")  # Shunt resistance
        ws.write_formula(row_index, 11, f"='{sheet_name}'!F12")  # Active area
        ws.write_formula(row_index, 12, f"='{sheet_name}'!F13")  # Light intensity
        ws.write_formula(row_index, 13, f"='{sheet_name}'!F14")  # Distance to a light source
        ws.write(row_index, [k for k, v in self.parameter_dict.items() if v == 'Device order'][0] - 1, row_index)

    def plot_iv(self, sheet_name, data_start, data_end, name_suffix):
        name_suffix = ' ' + name_suffix if name_suffix else ''
        chart_iv = self.workbook.add_chart({'type': 'scatter'})
        chart_iv.add_series({
            'categories': f"='{sheet_name}'!$B${data_start}:$B${data_end}",
            'values': f"='{sheet_name}'!$A${data_start}:$A${data_end}",
            'line': {'width': 1.5, 'color': 'black'}, 'marker': {'type': 'none'},  # No markers
        })
        chart_iv.set_title({
            'name': f"{sheet_name + name_suffix}",
            'name_font': {'size': 14, 'italic': False, 'bold': False, 'name': 'Calibri (Body)'},
        })
        chart_iv.set_x_axis({
            'name': 'V, V',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_tick_mark': 'cross',
            'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
        })
        chart_iv.set_legend({'none': True})
        chart_iv.set_y_axis({
            'name': 'J, mA/cm²',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
            'major_tick_mark': 'outside',
        })
        chart_iv.set_chartarea({'border': {'none': True}})
        chart_iv.set_size({'x_scale': settings[self.name]['chart_x_scale'],
                           'y_scale': settings[self.name]['chart_y_scale']})

        return chart_iv

    def plot_all_sweeps(self, start_key, end_key, name_suffix):
        name_suffix = ' ' + name_suffix if name_suffix else ''
        chart_all_sweeps = self.workbook.add_chart({'type': 'scatter'})

        for folder_name, devices in self.data.items():
            for device_name, device_data in devices.items():
                ws_name = self.data[folder_name][device_name]['sheet_name']
                data_start = self.data[folder_name][device_name]['sweep_indexes_data'][start_key]
                data_end = self.data[folder_name][device_name]['sweep_indexes_data'][end_key]
                chart_all_sweeps.add_series({
                    'categories': f"='{ws_name}'!$B${data_start}:$B${data_end}",
                    'values': f"='{ws_name}'!$A${data_start}:$A${data_end}",
                    'line': {'width': 1.5}, 'marker': {'type': 'none'},  # No markers
                    'name': f"{ws_name}",
                })

        # Set other chart properties as needed
        chart_all_sweeps.set_title(
            {'name': f"IV plot{name_suffix}", 'name_font': {'size': 14, 'italic': False,
                                                            'bold': False, 'name': 'Calibri (Body)'}})
        chart_all_sweeps.set_x_axis({
            'name': 'V, V',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_tick_mark': 'cross',
            'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
        })
        chart_all_sweeps.set_legend({'none': False})
        chart_all_sweeps.set_y_axis({
            'name': 'J, mA/cm²',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
            'major_tick_mark': 'outside',
        })
        chart_all_sweeps.set_chartarea({'border': {'none': True}})
        chart_all_sweeps.set_size({'x_scale': settings[self.name]['all_in_one_chart_x_scale'],
                                   'y_scale': settings[self.name]['all_in_one_chart_y_scale']})

        return chart_all_sweeps

    def aging(self) -> None:
        if not self.parent.aging_mode:
            return
        # Write header to the Aging sheet
        self.aging_sheet.write(0, 0, 'TimeLine, h', self.center)  # Writing the header

        # Write the DataFrame values to the Aging sheet
        for row_num, value in enumerate(self.timeline_df[self.timeline_df.columns[0]]):
            self.aging_sheet.write(row_num + 1, 0, value)  # +1 to skip the header

        keys_to_exclude = [key for key in self.parameter_dict.keys() if key >= 12]
        headers = [value for key, value in self.parameter_dict.items() if key not in keys_to_exclude]

        headers.extend(
            [f"{header}_relative" for header in headers[2:]])  # Assuming the first two headers are not parameters

        for i, header in enumerate(headers, 2):
            self.aging_sheet.write(0, i, header, self.center)

        sweeps = ['Forward', 'Reverse', 'Average']

        unique_devices_folders = {}
        for folder_name, devices in self.data.items():
            for device_name, device_data in devices.items():
                if device_name not in unique_devices_folders:
                    unique_devices_folders[device_name] = []

                unique_devices_folders[device_name].append({
                    'folder_name': folder_name,
                })

        keys_to_exclude.extend([1, 2])
        first_values = {}  # To store the first value of each device-parameter combination
        current_row = 1  # starting row

        counter_counter = 0
        # Loop through each sweep
        for sweep in sweeps:
            if sweep == 'Forward':
                target_sheet_absolute = self.aging_plots_forward_absolute
                target_sheet_relative = self.aging_plots_forward_relative
            elif sweep == 'Reverse':
                target_sheet_absolute = self.aging_plots_reverse_absolute
                target_sheet_relative = self.aging_plots_reverse_relative
            else:
                target_sheet_absolute = self.aging_plots_avg_absolute
                target_sheet_relative = self.aging_plots_avg_relative
            # Loop through each device
            for device_counter, (device, folder_info_list) in enumerate(unique_devices_folders.items()):
                first_values[device] = {}  # Initialize for this device
                # Loop through each folder for the device
                for folder_info in folder_info_list:
                    folder_name = folder_info['folder_name']

                    self.aging_sheet.write(current_row, 2, device)
                    self.aging_sheet.write(current_row, 3, sweep)

                    # Loop through each parameter
                    for row, parameter in self.parameter_dict.items():
                        if row in keys_to_exclude:  # Exclude non-parameter key
                            continue
                        # Retrieve parameter value from self.data
                        value = self.data[folder_name][device]['Parameters'][sweep][parameter]

                        # Check if it's the first value for this parameter-device combination
                        if parameter not in first_values[device]:
                            first_values[device][parameter] = value
                        relative_value = value / first_values[device][parameter]

                        # Write the value into the Excel sheet
                        self.aging_sheet.write(current_row, row + 1, value)
                        self.aging_sheet.write(current_row, row + 1 + len(self.parameter_dict) - len(keys_to_exclude),
                                               relative_value)

                    # Increment row index for the next iteration
                    current_row += 1

                data_end = current_row  # Track where data for this device ends
                data_start = data_end - len(folder_info_list) + 1

                # Plot charts here, outside the folder loop
                for row, parameter in self.parameter_dict.items():
                    if row in keys_to_exclude:  # Exclude non-parameter key
                        continue
                    excel_col_abs = row_to_excel_col(
                        row + 2)  # 2 to adjust for initial columns (TimeLine, Label, Scan Direction)
                    # for relative values
                    excel_col_rel = row_to_excel_col(row + 2 + len(self.parameter_dict) - len(keys_to_exclude))
                    chart_iv_absolute = self.plot_aging(device_name=device, sweep=sweep,
                                                        param=parameter,
                                                        param_column=excel_col_abs,
                                                        data_start=data_start,
                                                        data_end=data_end)
                    chart_iv_relative = self.plot_aging(device_name=device, sweep=sweep,
                                                        param=parameter,
                                                        param_column=excel_col_rel,
                                                        data_start=data_start,
                                                        data_end=data_end)
                    counter_counter += 1
                    # Insert the chart
                    target_sheet_absolute.insert_chart(device_counter * self.chart_vertical_spacing,
                                                       (row - 3) * self.chart_horizontal_spacing,
                                                       chart_iv_absolute)
                    target_sheet_relative.insert_chart(device_counter * self.chart_vertical_spacing,
                                                       (row - 3) * self.chart_horizontal_spacing,
                                                       chart_iv_relative)

    def plot_aging(self, device_name, sweep, param, param_column, data_start, data_end):
        max_value = self.timeline_df.iloc[:, 0].max()
        next_rounded_value = custom_round(max_value)
        name_suffix = f"{device_name} {param} {sweep}"
        chart_iv = self.workbook.add_chart({'type': 'scatter'})
        chart_iv.add_series({
            'categories': f"='Aging'!$A$2:$A${self.timeline_df.shape[0] + 1}",
            'values': f"='Aging'!${param_column}${data_start}:${param_column}${data_end}",
            'line': {'width': 1.5, 'color': 'black'},
            'marker': {
                'type': 'circle',
                'size': 5,
                'border': {'color': 'black'},
                'fill': {'color': 'white'}}
        })
        chart_iv.set_title({
            'name': name_suffix,
            'name_font': {'size': 14, 'italic': False, 'bold': False, 'name': 'Calibri (Body)'},
        })
        chart_iv.set_x_axis({
            'name': 'Time, h',
            'min': 0,
            'max': next_rounded_value,
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_tick_mark': 'cross',
            'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': False},
            'minor_gridlines': {'visible': False},
            # 'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
        })
        chart_iv.set_legend({'none': True})
        chart_iv.set_y_axis({
            'name': param,
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            # 'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
            'major_gridlines': {'visible': False},
            'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        chart_iv.set_chartarea({'border': {'none': True}})
        chart_iv.set_size({'x_scale': settings[self.name]['chart_x_scale'],
                           'y_scale': settings[self.name]['chart_y_scale']})

        return chart_iv
