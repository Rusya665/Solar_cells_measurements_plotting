import xlsxwriter
from icecream import ic
import pandas as pd
from instruments import open_file
import os
import time
from datetime import date


class DevicePlotter:
    def __init__(self, parent, matched_devices: dict):
        self.matched_devices = matched_devices
        self.parent = parent
        self.xlsx_name = ''
        self.workbook = self.create_workbook()
        self.center = self.workbook.add_format({'align': 'center'})
        self.wb_main = self.workbook.add_worksheet('Total')
        self.wb_table = self.workbook.add_worksheet('Tabel_Total')
        if self.parent.aging_mode:
            self.aging_sheet = self.workbook.add_worksheet('Aging')

        self.save_data_to_excel()
        self.workbook.close()
        if self.parent.open_wb:
            time.sleep(0.2)
            open_file(self.xlsx_name)

    def create_workbook(self):
        """
        Creating new xlsx doc and/or folder for it
        :return: Workbook
        """
        base_dir = os.path.dirname(self.parent.file_directory)
        base_name = os.path.basename(base_dir)
        self.xlsx_name = os.path.join(self.parent.file_directory,
                                      f"{date.today()} {base_name} JV plots and calculations.xlsx")
        self.workbook = xlsxwriter.Workbook(self.xlsx_name, {'strings_to_numbers': True})
        return self.workbook

    def save_data_to_excel(self):

        # Create a new Excel workbook
        workbook = xlsxwriter.Workbook('device_data.xlsx')

        # Add "Total" and "Table_total" sheets
        worksheet_total = workbook.add_worksheet('Total')
        worksheet_table_total = workbook.add_worksheet('Table_total')

        # For each device, create a separate sheet and fill data
        for device, details in self.matched_devices.items():

            # Add a new worksheet for the device
            worksheet = workbook.add_worksheet(device)

            # Write headers
            worksheet.write('A1', 'I')
            worksheet.write('B1', 'V')
            worksheet.write('C1', 'P')

            # Get data for I and V
            i_data = []
            v_data = []

            for sweep_type, df in details['data'].items():
                i_data.extend(df['I'].tolist())
                v_data.extend(df['V'].tolist())

            # Write the data to the worksheet
            for idx, (i, v) in enumerate(zip(i_data, v_data)):
                worksheet.write(idx + 1, 0, i)  # Write I data
                worksheet.write(idx + 1, 1, v)  # Write V data
                worksheet.write_formula(idx + 1, 2, f"A{idx + 2}*B{idx + 2}")  # Write P formula

        # Close the workbook
        workbook.close()
