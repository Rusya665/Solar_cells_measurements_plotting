import xlsxwriter
from icecream import ic
import pandas as pd
from instruments import create_folder
import os
import time
from datetime import date


class DevicePlotter:
    def __init__(self, parent, matched_devices: dict):
        self.matched_devices = matched_devices
        self.parent = parent
        ic(self.matched_devices)
        # Initializing other attributes required for the class

        # Assuming you want to keep a similar structure for an Excel file as above
        self.workbook = None  # This will be our xlsx writer workbook

        self.save_data_to_excel()

    def create_workbook(self):
        """
        Creating new xlsx doc and/or folder for it
        :return: Workbook
        """
        xlsx_name = self.parent.file_directory + str(date.today()) + ' ' + os.path.basename(os.path.dirname(self.parent.file_directory)) + ' ' + "JV plots and " \
                                                                                                "calculations.xlsx"
        self.workbook = xlsxwriter.Workbook(xlsx_name, {'strings_to_numbers': True})
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