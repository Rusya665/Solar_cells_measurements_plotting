import xlsxwriter
from icecream import ic
from scipy.stats import linregress
from instruments import open_file
from settings import settings
import math
import os
import time
from datetime import date
from xlsxwriter.utility import xl_rowcol_to_cell


class DevicePlotter:
    def __init__(self, parent, matched_devices: dict):
        self.data = matched_devices
        self.parent = parent
        self.name = self.__class__.__name__
        # Assuming the default cells height 20 pixels
        self.chart_vertical_spacing = math.ceil((288 * settings[self.name]['chart_y_scale']) / 20) + 1
        self.xlsx_name = ''
        self.workbook = self.create_workbook()
        self.center = self.workbook.add_format({'align': 'center'})
        self.across_selection = self.workbook.add_format()
        self.across_selection.set_center_across()
        self.wb_main = self.workbook.add_worksheet('Total')
        self.wb_table = self.workbook.add_worksheet('Tabel_Total')
        self.wb_table_forward = self.workbook.add_worksheet('Tabel_Forward')
        self.wb_table_reverse = self.workbook.add_worksheet('Tabel_Reverse')
        self.wb_table_average = self.workbook.add_worksheet('Tabel_Average')
        if self.parent.aging_mode:
            self.aging_sheet = self.workbook.add_worksheet('Aging')

        self.set_worksheets()
        self.fill_tables()
        self.workbook.close()
        if self.parent.open_wb:
            time.sleep(0.2)
            open_file(self.xlsx_name)

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
        folder_counter = 0

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
                # Decide the worksheet name based on whether a long name was found
                ws_name = (
                    f"{folder_counter} {device_name}" if long_name_found
                    else f"{folder_name} {device_name}"
                )

                if len(ws_name) > 31:  # In case the alternative naming is also too long
                    ws_name = ws_name[:31]

                if len(self.data) == 1:
                    ws_name = f'{device_name}'

                # Save the worksheet name to the corresponding device
                self.data[folder_name][device_name]['sheet_name'] = ws_name

                ws = self.workbook.add_worksheet(ws_name)

                self.set_headers(ws=ws, device_name=device_name, device_data=device_data)

                (reverse_isc_row, reverse_voc_row, forward_isc_row,
                 forward_voc_row, reverse_start_row, forward_start_row, rs_forward, rs_reverse,
                 rsh_forward, rsh_reverse) = None, None, None, None, None, None, None, None, None, None
                # Iterate through the sweeps (Forward and Reverse) for each device
                row = 1
                for sweep_name, sweep_data in device_data['data'].items():
                    voltage_data = sweep_data['V']
                    current_data = sweep_data['I']

                    voc_approx, voc_index = self.calculate_voc_approx(voltage_data, current_data)
                    isc, rsh = self.calculate_isc_and_rsh(voltage_data, current_data, voc_approx)
                    voc, rs = self.calculate_voc_and_rs(voltage_data, current_data, voc_index)

                    if sweep_name == '1_Forward':
                        forward_isc_row, forward_voc_row = isc, voc
                        forward_start_row = row + 1
                        rs_forward = rs
                        rsh_forward = rsh
                    elif sweep_name == '2_Reverse':
                        reverse_isc_row, reverse_voc_row = isc, voc
                        reverse_start_row = row + 1
                        rs_reverse = rs
                        rsh_reverse = rsh

                    # Write the data to the worksheet
                    for index, row_data in sweep_data.iterrows():
                        current = row_data['I']
                        voltage = row_data['V']
                        # power = current * voltage

                        ws.write(row, 0, current)
                        ws.write(row, 1, voltage)
                        ws.write_formula(row, 2,
                                         f'=0.001*{xl_rowcol_to_cell(row, 0)}*{xl_rowcol_to_cell(row, 1)}')
                        row += 1

                self.write_iv(ws, reverse_isc_row, reverse_voc_row, forward_isc_row, forward_voc_row)
                self.write_max_power(ws, reverse_start_row, forward_start_row, row)
                self.write_efficiency(ws)
                self.write_fill_factor(ws)
                self.write_short_circuit_current_density(ws)
                self.write_voltage_at_mpp(ws)
                self.write_current_density_at_mpp(ws)
                self.write_series_resistance(ws, rs_reverse, rs_forward)
                self.write_shunt_resistance(ws, rsh_reverse, rsh_forward)
                ws.insert_chart('D16', self.plot_iv(sheet_name=ws_name, data_start=2, data_end=row, name_suffix=None))
                ws.insert_chart(f"I1",
                                self.plot_iv(sheet_name=ws_name, data_start=forward_start_row,
                                             data_end=reverse_start_row,
                                             name_suffix='Forward'))
                ws.insert_chart(f"I{self.chart_vertical_spacing}",
                                self.plot_iv(sheet_name=ws_name, data_start=reverse_start_row, data_end=row,
                                             name_suffix='Reverse'))

    def set_headers(self, ws, device_name, device_data):
        # Write the headers for I, V, and P
        ws.write(0, 0, 'I', self.center)
        ws.write(0, 1, 'V', self.center)
        ws.write(0, 2, 'P', self.center)

        # Write the device name and parameters in column D
        ws.write(0, 3, device_name, self.center)
        ws.write(1, 3, 'Parameters', self.center)
        ws.write(2, 3, 'Isc, mA', self.center)
        ws.write(3, 3, 'Voc, V', self.center)
        ws.write(4, 3, 'Ƞ', self.center)
        ws.write(5, 3, 'FF', self.center)
        ws.write(6, 3, 'Max power, W', self.center)
        ws.write(7, 3, 'Short-circuit current density, mA/cm²)', self.center)
        ws.write(8, 3, 'Voltage at MPP (V)', self.center)
        ws.write(9, 3, 'Current density at MPP (mA/cm²)', self.center)
        ws.write(10, 3, 'Series resistance, Rs (ohm)', self.center)
        ws.write(11, 3, 'Shunt resistance, Rsh (ohm)', self.center)
        ws.write(12, 3, 'Active area, mm²', self.center)
        ws.write(13, 3, 'Light Intensity, W/cm²', self.center)

        ws.set_column(3, 3, 35)
        # Write the "Values" header in column E
        self.write_center_across_selection(ws, (0, 4), 'Values', 3)

        # Write the "Reverse" and "Forward" headers in columns E and F
        ws.write(1, 4, 'Reverse', self.center)
        ws.write(1, 5, 'Forward', self.center)
        ws.write(1, 6, 'Average', self.center)

        # Write the active area value
        self.write_center_across_selection(ws, (12, 4), device_data['Active area'], 3)

        # Write the light intensity value
        self.write_center_across_selection(ws, (13, 4), device_data['Light Intensity'], 3)

    def write_center_across_selection(self, ws, position, text, number_of_cells):
        row, col = position
        ws.write(row, col, text, self.across_selection)
        for i in range(1, number_of_cells):
            ws.write_blank(row, col + i, '', self.across_selection)

    @staticmethod
    def calculate_voc_approx(voltage_data, current_data):
        """
        Approximates the open-circuit voltage (Voc) by finding the voltage where the current is minimized.

        :param voltage_data: Array-like, voltage data points.
        :param current_data: Array-like, current data points corresponding to the voltage data.
        :return: Tuple containing the approximated Voc and the index where the current is minimized.
        """
        voc_index = abs(current_data).idxmin()
        return voltage_data[voc_index], voc_index

    @staticmethod
    def calculate_isc_and_rsh(voltage_data, current_data, voc_approx):
        """
        Calculates the short-circuit current (Isc) and shunt resistance (Rsh) by performing a linear regression
        on a subset of the voltage and current data.

        :param voltage_data: Array-like, voltage data points.
        :param current_data: Array-like, current data points.
        :param voc_approx: Float, approximated open-circuit voltage.
        :return: Tuple containing the calculated Isc and Rsh values.
        """
        isc_indices_fit = abs(voltage_data) / voc_approx < 0.3
        slope_isc, intercept_isc, _, _, _ = linregress(voltage_data[isc_indices_fit], current_data[isc_indices_fit])
        isc = intercept_isc
        rsh = -1 / slope_isc
        return isc, rsh

    @staticmethod
    def calculate_voc_and_rs(voltage_data, current_data, voc_index):
        """
        Calculates the open-circuit voltage (Voc) and series resistance (Rs) by performing a linear regression
        on the data near the Voc index.

        :param voltage_data: Array-like, voltage data points.
        :param current_data: Array-like, current data points.
        :param voc_index: Integer, index where the current is minimized.
        :return: Tuple containing the calculated Voc and Rs values.
        """
        voc_indices_fit = [voc_index - 1, voc_index] if current_data[voc_index] < 0 else [voc_index, voc_index + 1]
        slope_voc, intercept_voc, _, _, _ = linregress(voltage_data[voc_indices_fit], current_data[voc_indices_fit])
        voc = -intercept_voc / slope_voc
        rs = -1 / slope_voc
        return voc, rs

    @staticmethod
    def write_max_power(ws, reverse_start_row, forward_start_row, row):
        """
        Writes Excel formulas to calculate the maximum power for Reverse and Forward sweeps and their average.

        :param ws: Excel Worksheet object.
        :param reverse_start_row: Integer, start row for the Reverse sweep data.
        :param forward_start_row: Integer, start row for the Forward sweep data.
        :param row: Integer, end row for the data.
        :return: None.
        """
        ws.write_formula(6, 4, f'=MAX(C{reverse_start_row}:C{row})')  # Reverse Max Power
        ws.write_formula(6, 5, f'=MAX(C{forward_start_row}:C{row})')  # Forward Max Power
        ws.write_formula(6, 6, '=(E7+F7)/2')  # Average Max Power

    @staticmethod
    def write_efficiency(ws):
        """
        Writes Excel formulas to calculate the efficiency for Reverse, Forward, and Average sweeps.

        :param ws: Excel Worksheet object.
        :return: None.
        """
        ws.write_formula(4, 4, '=100*E7/(E14*E13)')  # Reverse Efficiency
        ws.write_formula(4, 5, '=100*F7/(E14*E13)')  # Forward Efficiency
        ws.write_formula(4, 6, '=(E5+F5)/2')  # Average Efficiency

    @staticmethod
    def write_fill_factor(ws):
        """
        Writes Excel formulas to calculate the fill factor for Reverse, Forward, and Average sweeps.

        :param ws: Excel Worksheet object.
        :return: None.
        """
        ws.write_formula(5, 4, '=E7/(E3*E4)')  # Reverse Fill Factor
        ws.write_formula(5, 5, '=F7/(F3*F4)')  # Forward Fill Factor
        ws.write_formula(5, 6, '=(E6+F6)/2')  # Average Fill Factor

    @staticmethod
    def write_short_circuit_current_density(ws):
        """
        Writes Excel formulas to calculate the short-circuit current density for Reverse, Forward, and Average sweeps.

        :param ws: Excel Worksheet object.
        :return: None.
        """
        ws.write_formula(7, 4, '=E3/E13')  # Reverse short circuit current density
        ws.write_formula(7, 5, '=F3/E13')  # Forward short circuit current density
        ws.write_formula(7, 6, '=G3/E13')  # Average short circuit current density

    @staticmethod
    def write_voltage_at_mpp(ws):
        """
         Writes Excel formulas to calculate the voltage at MPP for Reverse, Forward, and Average sweeps.

        :param ws: Excel Worksheet object.
        :return: None.
        """
        ws.write_formula(8, 4, '=INDEX(B:B,MATCH(E7,C:C,0))')  # Reverse Voltage at MPP
        ws.write_formula(8, 5, '=INDEX(B:B,MATCH(F7,C:C,0))')  # Forward Voltage at MPP
        ws.write_formula(8, 6, '=(E9+F9)/2')  # Average Voltage at MPP

    @staticmethod
    def write_current_density_at_mpp(ws):
        """
        Writes Excel formulas to calculate the current density at MPP for Reverse, Forward, and Average sweeps.

        :param ws: Excel Worksheet object.
        :return: None.
        """
        ws.write_formula(9, 4, '=INDEX(A:A,MATCH(E7,C:C,0))/E13')  # Reverse Current density at MPP
        ws.write_formula(9, 5, '=INDEX(A:A,MATCH(F7,C:C,0))/E13')  # Forward Current density at MPP
        ws.write_formula(9, 6, '=(E10+F10)/2')  # Average Current density at MPP

    @staticmethod
    def write_series_resistance(ws, rs_reverse, rs_forward):
        """
        Writes the series resistance (Rs) in the worksheet for Reverse, Forward, and Average cases.

        :param ws: Excel Worksheet object.
        :param rs_reverse: Series resistance in ohm for Reverse case.
        :param rs_forward: Series resistance in ohm for Forward case.
        :return: None.
        """
        ws.write(10, 4, rs_reverse)  # Reverse series resistance, Rs (ohm)
        ws.write(10, 5, rs_forward)  # Forward series resistance, Rs (ohm)
        ws.write_formula(10, 6, '=(E11+F11)/2')  # Average series resistance, Rs (ohm)

    @staticmethod
    def write_shunt_resistance(ws, rsh_reverse, rsh_forward):
        """
        Writes the shunt resistance (Rsh) in the worksheet for Reverse, Forward, and Average cases.

        :param ws: Excel Worksheet object.
        :param rsh_reverse: Shunt resistance in ohm for Reverse case.
        :param rsh_forward: Shunt resistance in ohm for Forward case.
        :return: None.
        """
        ws.write(11, 4, rsh_reverse)  # Reverse shunt resistance, Rsh (ohm)
        ws.write(11, 5, rsh_forward)  # Forward shunt resistance, Rsh (ohm)
        ws.write_formula(11, 6, '=(E12+F12)/2')  # Average shunt resistance, Rsh (ohm)

    @staticmethod
    def write_iv(ws, reverse_isc_row, reverse_voc_row, forward_isc_row, forward_voc_row):
        """
        Writes the values for the short-circuit current (Isc) and open-circuit voltage (Voc) for the
        Reverse and Forward sweeps, as well as calculates the Average Isc and Voc using Excel formulas.

        This method specifically targets the writing of Isc and Voc parameters to a given Excel worksheet.

        :param ws: Excel Worksheet object where the data will be written.
        :param reverse_isc_row: Short-circuit current (Isc) in amps for the Reverse sweep.
        :param reverse_voc_row: Open-circuit voltage (Voc) in volts for the Reverse sweep.
        :param forward_isc_row: Short-circuit current (Isc) in amps for the Forward sweep.
        :param forward_voc_row: Open-circuit voltage (Voc) in volts for the Forward sweep.
        :return: None.
        """
        # Write the Reverse and Forward values for Isc and Voc
        ws.write(2, 4, reverse_isc_row)
        ws.write(3, 4, reverse_voc_row)
        ws.write(2, 5, forward_isc_row)
        ws.write(3, 5, forward_voc_row)
        # Write the Reverse and Forward values for Isc and Voc as Excel formulas
        ws.write_formula(2, 6, f'=(E3+F3)/2')  # Average Isc
        ws.write_formula(3, 6, f'=(E4+F4)/2')  # Average Voc

    def fill_tables(self):
        table_type = {self.wb_table: ['F', 'E'],
                      self.wb_table_forward: ['F'],
                      self.wb_table_reverse: ['E'],
                      self.wb_table_average: ['G'],
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

            table.autofilter(0, 0, row_index, 11)  # Apply autofilter to the table

    @staticmethod
    def write_table_headers(ws):
        ws.write(0, 0, 'Label')
        ws.write(0, 1, 'Scan direction')
        ws.write(0, 2, 'Efficiency (%)')
        ws.write(0, 3, 'Short-circuit current density (mA/cm²)')
        ws.write(0, 4, 'Open circuit voltage (V)')
        ws.write(0, 5, 'Fill factor')
        ws.write(0, 6, 'Maximum power (W)')
        ws.write(0, 7, 'Voltage at MPP (V)')
        ws.write(0, 8, 'Current density at MPP (mA/cm²)')
        ws.write(0, 9, 'Series resistance, Rs (ohm)')
        ws.write(0, 10, 'Shunt resistance, Rsh (ohm)')
        ws.write(0, 11, 'Active area, (mm²)')

    @staticmethod
    def write_table_rows(ws, row_index, sheet_name, sweep_direction):
        col_letter = sweep_direction  # First letter of sweep direction (E, F, or G)
        ws.write(row_index, 0, sheet_name)  # Label
        ws.write_formula(row_index, 1, f"='{sheet_name}'!{col_letter}2")  # Scan direction
        ws.write_formula(row_index, 2, f"='{sheet_name}'!{col_letter}5")  # Efficiency
        ws.write_formula(row_index, 3, f"='{sheet_name}'!{col_letter}8")  # Short-circuit current density
        ws.write_formula(row_index, 4, f"='{sheet_name}'!{col_letter}4")  # Open circuit voltage
        ws.write_formula(row_index, 5, f"='{sheet_name}'!{col_letter}6")  # Fill factor
        ws.write_formula(row_index, 6, f"='{sheet_name}'!{col_letter}7")  # Maximum power
        ws.write_formula(row_index, 7, f"='{sheet_name}'!{col_letter}9")  # Voltage at MPP
        ws.write_formula(row_index, 8, f"='{sheet_name}'!{col_letter}10")  # Current density at MPP
        ws.write_formula(row_index, 9, f"='{sheet_name}'!{col_letter}11")  # Series resistance
        ws.write_formula(row_index, 10, f"='{sheet_name}'!{col_letter}12")  # Shunt resistance
        ws.write_formula(row_index, 11, f"='{sheet_name}'!E13")  # Active area

    def plot_iv(self, sheet_name, data_start, data_end, name_suffix):
        name_suffix = ' ' + name_suffix if name_suffix else ''
        chart_iv = self.workbook.add_chart({'type': 'scatter'})
        chart_iv.add_series({
            'categories': f'={sheet_name}!$A${data_start}:$A${data_end}',
            'values': f'={sheet_name}!$B${data_start}:$B${data_end}',
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
            'name': 'I, mA',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
            'major_tick_mark': 'outside',
        })
        chart_iv.set_chartarea({'border': {'none': True}})
        chart_iv.set_size({'x_scale': settings[self.name]['chart_x_scale'],
                           'y_scale': settings[self.name]['chart_y_scale']})

        return chart_iv
