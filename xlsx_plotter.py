import os
import time
import xlsxwriter
import instruments
from datetime import date

from read_iv import ReadData


class PlotIV(ReadData):
    """
    XLSX workbook constructor. Inherits from ReadIv
    :param path_file: the highest path to create a xlsx file
    :param folder_name: optional parameter for nested folder
    :param open_wb: optional parameter to open the workbook if True
    """
    xlsx_location = None
    xlsx_name = None

    def __init__(self, path_file: str, folder_name='', open_wb=True):
        super().__init__(path_file)

        self.folder_name = folder_name
        self._indicator = os.path.basename(os.path.dirname(self.path_file))  # See scratch.txt. "indicator" here stands
        # for the experiment name

        self.workbook = self.create_workbook()
        self.center = self.workbook.add_format({'align': 'center'})
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
        # self.test_name.append(self.xlsx_location)  # Check this line
        self.xlsx_name = self.xlsx_location + str(date.today()) + ' ' + self._indicator + ' ' + "JV plots and " \
                                                                                                "calculations.xlsx"
        self.workbook = xlsxwriter.Workbook(self.xlsx_name, {'strings_to_numbers': True})
        return self.workbook

    def set_worksheets(self):
        for row_index in range(1, len(self.data) + 1):
            ws = self.workbook.add_worksheet(f"{self.data[f'{row_index}']['File name']}")
            ws.write(0, 0, 'I', self.center)
            ws.write(0, 1, 'V', self.center)
            for JV_val in range(len(self.data[f'{row_index}']['IV'].index)):
                ws.write_row(JV_val + 1, 0, self.data[f'{row_index}']['IV'].loc[JV_val])

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
