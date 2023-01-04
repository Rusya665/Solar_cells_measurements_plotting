import os
import sys
import time
import subprocess
import xlsxwriter
import instruments
import pandas as pd
from datetime import date

from read_iv import ReadData


class PlotIV:
    """
    XLSX workbook constructor.
    :param path_file: the highest path to create a xlsx file
    :param folder_name: optional parameter for nested folder
    :param open_wb: optional parameter to open the workbook if True
    """
    xlsx_location = None
    xlsx_name = None
    test_name = []

    def __init__(self, path_file: str, folder_name='', open_wb=None):

        # if not ReadData.data:
        #     raise IndexError('The data dict is empty')

        if not path_file.endswith('/'):  # Adding the '/' at the end of the given path if not there
            path_file = path_file + '/'

        self.folder_name = folder_name
        self.path_file = path_file
        self._indicator = os.path.basename(os.path.dirname(self.path_file))  # See scratch.txt. "indicator" here stands
        # for the experiment name

        self.workbook = self.create_workbook()
        self.wb_main = self.workbook.add_worksheet('Total')
        self.set_worksheets()
        # Keep this one the last
        self.workbook.close()
        if open_wb:
            time.sleep(0.2)
            instruments.open_file(self.xlsx_name)

    def create_workbook(self):
        """
        Creating new xlsx doc and/or folder for it
        :return: Workbook
        """
        self.xlsx_location = instruments.create_folder(self.path_file, self.folder_name)
        self.test_name.append(self.xlsx_location)  # Check this line
        self.xlsx_name = self.xlsx_location + str(date.today()) + ' ' + self._indicator + ' ' + "JV plots and " \
                                                                                                "calculations.xlsx"
        workbook = xlsxwriter.Workbook(self.xlsx_name, {'strings_to_numbers': True})
        return workbook

    def set_worksheets(self):
        for i in range(1, len(ReadData.data) + 1):
            ws = self.workbook.add_worksheet(f"{ReadData.data[f'{i}']['File name']}")
            print(ReadData.data[f'{i}']['File name'], len(ReadData.data[f'{i}']['IV'].index))
            for JV_val in range(len(f"{ReadData.data[f'{i}']['IV'].index}")):
                # ws.write(JV_val + 1, 0, ReadData.data[f'{i}']['IV'].at[JV_val, 'I'])
                # ws.write(JV_val + 1, 1, ReadData.data[f'{i}']['IV'].at[JV_val, 'V'])
                try:
                    ws.write_row(JV_val + 1, 0, ReadData.data[f'{i}']['IV'].loc[JV_val])
                except KeyError:
                    pass
    # def wb_main(self, worksheet_name: str):
    #     """
    #     Create new worksheet
    #     :param worksheet_name: Specify worksheet's name
    #     :return: Worksheet
    #     """
    #     return self.workbook.add_worksheet(worksheet_name)

    # def close_workbook(self):
    #     """
    #     Close workbook. Always do run it to save the data
    #     :return:
    #     """
    #     self.workbook.close()
