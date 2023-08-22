import xlsxwriter
from icecream import ic
from scipy.stats import linregress
import pandas as pd
from instruments import open_file, axis_crossing
import os
import time
from datetime import date
from xlsxwriter.utility import xl_rowcol_to_cell


class DevicePlotter:
    def __init__(self, parent, matched_devices: dict):
        self.data = matched_devices
        self.parent = parent
        self.xlsx_name = ''
        self.workbook = self.create_workbook()
        self.center = self.workbook.add_format({'align': 'center'})
        self.across_selection = self.workbook.add_format()
        self.across_selection.set_center_across()
        self.wb_main = self.workbook.add_worksheet('Total')
        self.wb_table = self.workbook.add_worksheet('Tabel_Total')
        if self.parent.aging_mode:
            self.aging_sheet = self.workbook.add_worksheet('Aging')

        self.set_worksheets()
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
        # self.wb_main.insert_chart(0, 1, self.add_all_together_plot())

        # Iterate through the folders
        for folder_name, devices in self.data.items():
            # Iterate through the devices in each folder
            for device_name, device_data in devices.items():
                # Create a worksheet for each device with the name "folder device"
                ws_name = f"{folder_name} {device_name}"
                ws = self.workbook.add_worksheet(ws_name)

                # Write the headers for I, V, and P
                col_start = 0
                ws.write(0, col_start, 'I', self.center)
                ws.write(0, col_start + 1, 'V', self.center)
                ws.write(0, col_start + 2, 'P', self.center)

                # Write the device name and parameters in column D
                ws.write(0, col_start + 3, device_name, self.center)
                ws.write(1, col_start + 3, 'Parameters')
                ws.write(2, col_start + 3, 'Isc, mA')
                ws.write(3, col_start + 3, 'Voc, mV')
                ws.write(4, col_start + 3, 'Ƞ')
                ws.write(5, col_start + 3, 'FF')
                ws.write(6, col_start + 3, 'Max power, W')
                ws.write(7, col_start + 3, 'Active area, mm²')
                ws.write(8, col_start + 3, 'Light Intensity, W/cm²')

                ws.set_column(col_start + 3, col_start + 3, 19)
                # Write the "Values" header in column E
                ws.write(0, col_start + 4, 'Values', self.across_selection)
                ws.write_blank(0, col_start + 5, '', self.across_selection)
                ws.write_blank(0, col_start + 6, '', self.across_selection)

                # Write the "Reverse" and "Forward" headers in columns E and F
                ws.write(1, col_start + 4, 'Reverse', self.center)
                ws.write(1, col_start + 5, 'Forward', self.center)
                ws.write(1, col_start + 6, 'Average', self.center)

                # Write the active area value
                ws.write(7, col_start + 4, device_data['Active area'], self.across_selection)
                ws.write_blank(7, col_start + 5, '', self.across_selection)
                ws.write_blank(7, col_start + 6, '', self.across_selection)

                # Write the light intensity value
                ws.write(8, col_start + 4, device_data['Light Intensity'], self.across_selection)
                ws.write_blank(8, col_start + 5, '', self.across_selection)
                ws.write_blank(8, col_start + 6, '', self.across_selection)

                (reverse_isc_row, reverse_voc_row, forward_isc_row,
                 forward_voc_row, reverse_start_row, forward_start_row) = None, None, None, None, None, None
                # Iterate through the sweeps (Forward and Reverse) for each device
                row = 1
                for sweep_name, sweep_data in device_data['data'].items():
                    voltage_data = sweep_data['V']
                    current_data = sweep_data['I']

                    # Approximate Voc
                    voc_index = abs(current_data).idxmin()
                    voc_approx = voltage_data[voc_index]

                    # Linear fit for Isc
                    isc_indices_fit = abs(voltage_data) / voc_approx < 0.3
                    slope_isc, intercept_isc, _, _, _ = linregress(voltage_data[isc_indices_fit],
                                                                   current_data[isc_indices_fit])
                    isc = intercept_isc
                    rsh = -1 / slope_isc

                    # Linear fit for Voc
                    voc_indices_fit = [voc_index - 1, voc_index] if current_data[voc_index] < 0 else [voc_index,
                                                                                                      voc_index + 1]
                    slope_voc, intercept_voc, _, _, _ = linregress(voltage_data[voc_indices_fit],
                                                                   current_data[voc_indices_fit])
                    voc = -intercept_voc / slope_voc
                    rs = -1 / slope_voc

                    if sweep_name == '1_Forward':
                        forward_isc_row, forward_voc_row = isc, voc
                        forward_start_row = row + 1
                    elif sweep_name == '2_Reverse':
                        reverse_isc_row, reverse_voc_row = isc, voc
                        reverse_start_row = row + 1

                    # Write the data to the worksheet
                    for index, row_data in sweep_data.iterrows():
                        current = row_data['I']
                        voltage = row_data['V']
                        # power = current * voltage

                        ws.write(row, col_start, current)
                        ws.write(row, col_start + 1, voltage)
                        # ws.write_formula(row, col_start + 2, f'=A{row}*B{row}')
                        ws.write_formula(row, col_start + 2,
                                         f'={xl_rowcol_to_cell(row, col_start)}*{xl_rowcol_to_cell(row, col_start + 1)}')
                        row += 1

                # Write the Reverse and Forward values for Isc and Voc
                ws.write(2, col_start + 4, reverse_isc_row)
                ws.write(3, col_start + 4, reverse_voc_row)
                ws.write(2, col_start + 5, forward_isc_row)
                ws.write(3, col_start + 5, forward_voc_row)
                # Write the Reverse and Forward values for Isc and Voc as Excel formulas
                ws.write_formula(2, col_start + 6, f'=(E3+F3)/2')  # Average Isc
                ws.write_formula(3, col_start + 6, f'=(E4+F4)/2')  # Average Voc
                # Write the Max Power formulas for Reverse and Forward sweeps
                ws.write_formula(6, col_start + 4, f'=MAX(C{reverse_start_row}:C{row})')  # Reverse Max Power
                ws.write_formula(6, col_start + 5, f'=MAX(C{forward_start_row}:C{row})')  # Forward Max Power
                ws.write_formula(6, col_start + 6, '=(E7+F7)/2')  # Average Max Power

                # Efficiency for Reverse, Forward, and Average
                ws.write_formula(4, col_start + 4, '=100*E7/(E9*E8)')  # Reverse Efficiency
                ws.write_formula(4, col_start + 5, '=100*F7/(E9*E8)')  # Forward Efficiency
                ws.write_formula(4, col_start + 6, '=(E5+F5)/2')  # Average Efficiency

                # Fill Factor for Reverse, Forward, and Average
                ws.write_formula(5, col_start + 4, '=E7/(E3*E4)')  # Reverse Fill Factor
                ws.write_formula(5, col_start + 5, '=F7/(F3*F4)')  # Forward Fill Factor
                ws.write_formula(5, col_start + 6, '=(E6+F6)/2')  # Average Fill Factor

    def add_all_together_plot(self):
        """
        Here will be all-in-one plot implemented
        :return:
        """
        ...
