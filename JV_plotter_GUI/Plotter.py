import json
import math
import os
import time
from datetime import date, timedelta, datetime
from tkinter import messagebox

import xlsxwriter
from xlsxwriter.worksheet import Worksheet

from JV_plotter_GUI.Chart_creator import ChartsCreator
from JV_plotter_GUI.instruments import (open_file, row_to_excel_col, random_color, remove_data_key)
from JV_plotter_GUI.settings import settings


class DevicePlotter:
    """
        This class is designed for plotting and analyzing device measurements, specifically for photovoltaic devices.
    """

    def __init__(self, parent, matched_devices: dict):
        self.chart_fr_rw_row, self.chart_fr_rw_col = None, None
        self.chart_average_row, self.chart_average_col = None, None
        self.data = matched_devices
        self.check_data_sweeps_consistence()
        self.parent = parent
        self.unique_devices = self.parent.all_unique_devices
        self.stat = self.parent.stat
        self.sorted = self.parent.sorted
        self.name = self.__class__.__name__
        self.parameter_dict = settings['parameter_dict']
        self.set_settings()
        # Assuming the default cells height 20 pixels and width 64
        self.chart_horizontal_spacing = math.ceil((480 * settings[self.name]['chart_x_scale']) / 64) + 1
        self.chart_vertical_spacing = math.ceil((288 * settings[self.name]['chart_y_scale']) / 20) + 1
        self.chart_huge_horizontal_spacing = math.ceil((480 * settings[self.name]['all_in_one_chart_x_scale']) / 64) + 1
        self.chart_huge_vertical_spacing = math.ceil((288 * settings[self.name]['all_in_one_chart_y_scale']) / 20) + 1
        self.xlsx_name = ''
        self.warning_messages = []
        self.workbook = self.create_workbook()
        self.date_format = self.workbook.add_format({'num_format': 'yyyy-mm-dd'})
        self.base_date = datetime(1900, 1, 1)
        self.timeline_df = self.parent.timeline_df
        self.chart_creator = ChartsCreator(workbook=self.workbook, settings=settings[self.name], data=self.data,
                                           timeline_df=self.timeline_df, base_date=self.base_date)
        self.center = self.workbook.add_format({'align': 'center'})
        self.across_selection = self.workbook.add_format()
        self.across_selection.set_center_across()
        self.wb_main = self.workbook.add_worksheet('Total')
        # Main Worksheet
        self.wb_main.set_tab_color('#FFA500')  # Orange for the main worksheet
        if self.parent.aging_mode:
            self.aging_sheet = self.workbook.add_worksheet('Aging')
            self.aging_sheet.set_tab_color('#1E90FF')  # Dodger Blue
        self.wb_table = self.workbook.add_worksheet('Table_Total')
        self.wb_table.set_tab_color('#32CD32')  # Lime Green
        # Aging-Related Sheets
        if self.parent.aging_mode:
            self.aging_plots_forward_absolute = self.workbook.add_worksheet('Aging_plots_forward_raw')
            self.aging_plots_forward_absolute.set_tab_color('#4169E1')  # Royal Blue

            self.aging_plots_reverse_absolute = self.workbook.add_worksheet('Aging_plots_reverse_raw')
            self.aging_plots_reverse_absolute.set_tab_color('#4682B4')  # Steel Blue

            self.aging_plots_avg_absolute = self.workbook.add_worksheet('Aging_plots_avg_raw')
            self.aging_plots_avg_absolute.set_tab_color('#5F9EA0')  # Cadet Blue

            self.aging_plots_forward_relative = self.workbook.add_worksheet('Aging_plots_forward_normalized')
            self.aging_plots_forward_relative.set_tab_color('#20B2AA')  # Light Sea Green

            self.aging_plots_reverse_relative = self.workbook.add_worksheet('Aging_plots_reverse_normalized')
            self.aging_plots_reverse_relative.set_tab_color('#48D1CC')  # Medium Turquoise

            self.aging_plots_avg_relative = self.workbook.add_worksheet('Aging_plots_avg_normalized')
            self.aging_plots_avg_relative.set_tab_color('#40E0D0')  # Turquoise

        # Table-Related Sheets
        self.wb_table_forward = self.workbook.add_worksheet('Table_Forward')
        self.wb_table_forward.set_tab_color('#228B22')  # Forest Green

        self.wb_table_reverse = self.workbook.add_worksheet('Table_Reverse')
        self.wb_table_reverse.set_tab_color('#008000')  # Green

        self.wb_table_average = self.workbook.add_worksheet('Table_Average')
        self.wb_table_average.set_tab_color('#ADFF2F')  # Green Yellow

        self.set_worksheets()
        self.fill_tables()
        self.aging()

        self.wb_table.autofit()
        self.wb_table_forward.autofit()
        self.wb_table_reverse.autofit()
        self.wb_table_average.autofit()
        if self.parent.aging_mode:
            self.aging_sheet.autofit()

        print("\nWorksheets have been set.")
        print("--- %s seconds ---" % (time.time() - self.parent.start_time_workbook))
        print("\nCompressing the Excel file, hold on...")
        start_time = time.time()
        self.workbook.close()
        self.dump_json_data()
        if self.parent.open_wb:
            time.sleep(0.2)
            open_file(self.xlsx_name)
        print("--- %s seconds ---" % (time.time() - start_time))
        print(f"\nThe total time is {time.time() - self.parent.start_time}")
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
        self.workbook = xlsxwriter.Workbook(self.xlsx_name, {'strings_to_numbers': True, 'nan_inf_to_errors': True})
        return self.workbook

    def check_data_sweeps_consistence(self):
        ...

    def dump_json_data(self):
        """
        Dumping JSON data to a file. Handles nested dictionaries and excludes the 'data'
        key that contains non-serializable Pandas DataFrames.

        :return: None
        """

        if self.parent.dump_json:
            base_dir = os.path.basename(self.parent.file_directory)
            current_date = date.today()
            json_name = os.path.join(self.parent.file_directory,
                                     f"{current_date} {base_dir} IV data.json")

            # # Recursively remove 'data' key
            cleaned_data = remove_data_key(self.data)

            with open(json_name, 'w') as f:
                json.dump(cleaned_data, f, indent=4)

    def set_worksheets(self):
        folder_counter, device_counter = 0, -1

        # Generate a random color for each folder
        folder_colors = {folder_name: random_color() for folder_name in self.data.keys()}

        # Dictionary to store worksheet references and colors
        ws_color_dict = {}

        # Check if any name is too long
        long_name_found = any(
            len(f"{folder_name} {device_name}") > 31
            for folder_name, devices in self.data.items()
            for device_name in devices
        )
        # Iterate through the folders
        for folder_name, devices in self.data.items():
            folder_counter += 1

            # Determine color based on folder or device
            color = folder_colors[folder_name] if len(self.data) > 1 else None

            # Iterate through the devices in each folder
            for device_name, device_data in devices.items():
                device_counter += 1

                if color is None:
                    color = random_color()

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

                # Store worksheet reference and color in dictionary
                ws_color_dict[ws] = color
                # Reset color to None for the next device if there's only one folder
                if len(self.data) == 1:
                    color = None

                self.set_headers(ws=ws, device_name=device_name)
                # Iterate through the sweeps (Forward and Reverse) for each device
                row = 1
                for sweep_name, sweep_data in device_data['data'].items():
                    # Write the data to the worksheet
                    for _, row_data in sweep_data.iterrows():
                        ws.write(row, 1, row_data['V'])
                        power = row_data['I'] * row_data['V']
                        current_density = 1000 * row_data['I'] / device_data['Active area (cm²)']
                        ws.write(row, 2, power)
                        ws.write(row, 0, current_density)
                        row += 1

                self.write_parameters(ws, device_data)

                # Insert IV charts into devices' sheets
                ws.insert_chart(row=self.chart_average_row, col=self.chart_average_col,
                                chart=self.chart_creator.plot_iv(sheet_name=ws_name, data_start=2,
                                                                 data_end=row, name_suffix=None))
                ws.insert_chart(row=self.chart_fr_rw_row, col=self.chart_fr_rw_col,
                                chart=self.chart_creator.plot_iv(sheet_name=ws_name, data_start=2,
                                                                 data_end=len(data['1_Forward']) + 1,
                                                                 name_suffix='Forward'))
                ws.insert_chart(row=self.chart_fr_rw_row + self.chart_vertical_spacing, col=self.chart_fr_rw_col,
                                chart=self.chart_creator.plot_iv(sheet_name=ws_name,
                                                                 data_start=len(data['1_Forward']) + 2,
                                                                 data_end=row, name_suffix='Reverse'))
                # Write file name(s) being used to create this pixel/device data
                used_files_data = [device_data['Used files']] if isinstance(device_data['Used files'], str) else \
                    device_data['Used files']
                ws.write(0, self.chart_fr_rw_col + self.chart_horizontal_spacing, 'Used files', self.center)
                ws.write_column(1, self.chart_fr_rw_col + self.chart_horizontal_spacing, used_files_data)
                # Insert each devise plot separately into the main sheet
                self.wb_main.insert_chart(self.chart_huge_vertical_spacing,
                                          self.chart_horizontal_spacing * device_counter,
                                          self.chart_creator.plot_iv(sheet_name=ws_name,
                                                                     data_start=2,
                                                                     data_end=row, name_suffix=None))
                self.wb_main.insert_chart(self.chart_huge_vertical_spacing + self.chart_vertical_spacing,
                                          self.chart_horizontal_spacing * device_counter,
                                          self.chart_creator.plot_iv(sheet_name=ws_name,
                                                                     data_start=2,
                                                                     data_end=len(data['1_Forward']) + 2,
                                                                     name_suffix='Forward'))
                self.wb_main.insert_chart(self.chart_huge_vertical_spacing + self.chart_vertical_spacing * 2,
                                          self.chart_horizontal_spacing * device_counter,
                                          self.chart_creator.plot_iv(sheet_name=ws_name,
                                                                     data_start=len(data['1_Forward']) + 2,
                                                                     data_end=row,
                                                                     name_suffix='Reverse'))
        if self.parent.color_wb:
            # Apply colors to all worksheets
            for ws, color in ws_color_dict.items():
                ws.set_tab_color(color)
        # insert huge IV plots into the main sheet
        self.wb_main.insert_chart('A1', self.chart_creator.plot_all_sweeps(start_key='forward_start_row',
                                                                           end_key='all_data_length', name_suffix=''))
        self.wb_main.insert_chart(0, self.chart_huge_horizontal_spacing,
                                  self.chart_creator.plot_all_sweeps(start_key='forward_start_row',
                                                                     end_key='reverse_start_row',
                                                                     name_suffix='Forward'))
        self.wb_main.insert_chart(0, self.chart_huge_horizontal_spacing * 2,
                                  self.chart_creator.plot_all_sweeps(start_key='reverse_start_row',
                                                                     end_key='all_data_length', name_suffix='Reverse'))

    def set_headers(self, ws: Worksheet, device_name: str) -> None:
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
        if self.sorted:
            self.write_center_across_selection(ws, (0, 8), f'Selected error metric: {self.stat}', 3)
            ws.write(1, 8, f'Reverse', self.center)
            ws.write(1, 9, f'Forward', self.center)
            ws.write(1, 10, f'Average', self.center)

    def write_center_across_selection(self, ws: Worksheet, position: tuple[int, int], text: str,
                                      number_of_cells: int) -> None:
        """
        Write text into a cell and center it across a specified number of adjacent cells in the Excel worksheet.

        This method writes the given text into the cell specified by the 'position' parameter. It then leaves the
        adjacent cells empty but sets their format to 'center across selection', effectively centering the text
        across 'number_of_cells' cells.

        :param ws: The xlsxwriter worksheet object where the text is to be written and centered.
        :param position: A tuple specifying the row and column indices of the starting cell.
        :param text: The text to be written and centered.
        :param number_of_cells: The number of cells across which the text will be centered.
        :return: None
        """
        row, col = position
        ws.write(row, col, text, self.across_selection)
        for i in range(1, number_of_cells):
            ws.write_blank(row, col + i, '', self.across_selection)

    def write_parameters(self, ws: Worksheet, device_data: dict) -> None:
        # Write the main parameters for Forward, Reverse and Average cases.
        sweeps_list = ['Reverse', 'Forward', 'Average']

        # Iterate through values 3 to 15 (inclusive) in self.parameter_dict
        for row, value in enumerate(list(self.parameter_dict.values())[2:15], start=2):
            for col, sweep in enumerate(sweeps_list, start=5):
                if row >= 11 and col == 5:  # For rows beyond 11th and first column
                    self.write_center_across_selection(ws, (row, col), device_data[value], 3)
                elif row < 11:
                    ws.write(row, col, device_data['Parameters'][sweep][value])
                if self.sorted and row < 11 and device_data['Parameters'][sweep].get(
                        f'{value} {self.stat}') is not None:
                    ws.write(row, col + len(sweeps_list), device_data['Parameters'][sweep][f'{value} {self.stat}'])

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

    def write_table_headers(self, ws: Worksheet) -> None:
        for i, header in self.parameter_dict.items():
            ws.write(0, i - 1, header, self.center)

    def write_table_rows(self, ws: Worksheet, row_index: int, sheet_name: str, sweep_direction: str) -> None:
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
        ws.write_formula(row_index, 11, f"='{sheet_name}'!F12")  # H-index
        ws.write_formula(row_index, 12, f"='{sheet_name}'!F13")  # Active area
        ws.write_formula(row_index, 13, f"='{sheet_name}'!F14")  # Light intensity
        ws.write_formula(row_index, 14, f"='{sheet_name}'!F15")  # Distance to a light source
        ws.write(row_index, [k for k, v in self.parameter_dict.items() if v == 'Device order'][0] - 1, row_index)

    def aging(self) -> None:
        if not self.parent.aging_mode:
            return
        # Write header to the Aging sheet
        self.aging_sheet.write(0, 0, 'TimeLine, h', self.center)  # Writing the header

        # Write the DataFrame values to the Aging sheet
        for row_num, value in enumerate(self.timeline_df[self.timeline_df.columns[0]]):
            self.aging_sheet.write(row_num + 1, 0, value)  # +1 to skip the header
            # Write the aging hours values in the datetime format, so area chart can display them properly.
            date_time = self.base_date + timedelta(days=value)
            self.aging_sheet.write_datetime(row_num + 2 + len(self.timeline_df), 0, date_time, self.date_format)

        keys_to_exclude = [key for key in self.parameter_dict.keys() if key >= 12]
        headers = [value for key, value in self.parameter_dict.items() if key not in keys_to_exclude]
        headers_final = headers[:]  # Copy the "headers" list
        headers_final.extend(
            [f"{header}_relative" for header in headers[2:]])  # Assuming the first two headers are not parameters
        if self.sorted:
            headers_final.extend([f"{header}_{self.stat}_lower" for header in headers[2:]])
            headers_final.extend([f"{header}_{self.stat}_upper" for header in headers[2:]])

        for i, header in enumerate(headers_final, 2):
            self.aging_sheet.write(0, i, header, self.center)

        sweeps = ['Forward', 'Reverse', 'Average']

        unique_devices_folders = {}
        for folder_name in self.data.keys():
            for device_name in self.unique_devices:
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
            area_chart = False
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
                        device_data = self.data[folder_name].get(device)
                        if not device_data:
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
                        if self.sorted and self.data[folder_name][device]['Parameters'][sweep].get(
                                f'{parameter} {self.stat}'):
                            area_chart = True
                            error_value = self.data[folder_name][device]['Parameters'][sweep][
                                f'{parameter} {self.stat}']
                            error_metric_lower = value - error_value
                            error_metric_upper = value + error_value
                            self.aging_sheet.write(current_row,
                                                   row + 1 + (len(self.parameter_dict) - len(keys_to_exclude)) * 2,
                                                   error_metric_lower)
                            self.aging_sheet.write(current_row,
                                                   row + 1 + (len(self.parameter_dict) - len(keys_to_exclude)) * 3,
                                                   error_metric_upper)

                    # Increment row index for the next iteration
                    current_row += 1

                data_end = current_row  # Track where data for this device ends
                data_start = data_end - len(folder_info_list) + 1

                # Plot charts here, outside the folder loop
                for row, parameter in self.parameter_dict.items():
                    if row in keys_to_exclude:  # Exclude non-parameter key
                        continue
                    # + 2 is to adjust for initial columns (TimeLine, Label, Scan Direction)
                    excel_col_abs = row_to_excel_col(row + 2)
                    # for relative values
                    value_type_shift = len(self.parameter_dict) - len(keys_to_exclude)
                    excel_col_rel = row_to_excel_col(row + 2 + value_type_shift)
                    chart_iv_absolute = self.chart_creator.plot_aging(device_name=device, sweep=sweep,
                                                                      param=parameter,
                                                                      param_column=excel_col_abs,
                                                                      data_start=data_start,
                                                                      data_end=data_end,
                                                                      shaded_error_bar=area_chart,
                                                                      value_type_shift=value_type_shift,
                                                                      row=row)
                    chart_iv_relative = self.chart_creator.plot_aging(device_name=device, sweep=sweep,
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

    def set_settings(self):
        self.chart_average_col = settings[self.name]['chart_average_col']
        self.chart_average_row = len(self.parameter_dict) + 1
        self.chart_fr_rw_col = settings[self.name]['chart_fr_rw_col'] + 3 if self.sorted else settings[self.name][
            'chart_fr_rw_col']
        self.chart_fr_rw_row = 0
