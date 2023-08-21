import os
import json
import openpyxl
from difflib import SequenceMatcher


class ActiveAreaDetector:
    """
    A class to detect files in a directory containing active area information for solar cell devices.

    Attributes:
    -----------
    path : str
        Path to the directory where the files are located.
    processors : dict
        Dictionary mapping file extensions to respective processing methods.
    active_area_data : dict
        Processed active area data from the valid files in the directory.
    """

    def __init__(self, path):
        """
        Initialize the ActiveAreaDetector with a path.

        :param path: Path to the directory to scan for active area files.
        """
        self.path = path
        self.filepath = ''
        self.processors = {
            '.txt': self.process_txt,
            '.json': self.process_json,
            '.xlsx': self.process_xlsx
        }
        # self.active_area_data = self.check_directory()

    @staticmethod
    def similar(a, b):
        """
        Determine how similar two strings are.

        :param a: First string to compare.
        :param b: Second string to compare.
        :return: Similarity ratio between 0 and 1.
        """
        return SequenceMatcher(None, a, b).ratio()

    def check_directory(self):
        """
        Check the directory for files containing active area information.

        :return: Dictionary of device names and their corresponding active areas or None if no data found.
        """
        valid_files = [file for file in os.listdir(self.path)
                       if file.endswith(tuple(self.processors.keys()))
                       and self.similar("Active area", file) > 0.6]  # 0.6 is a threshold, can be adjusted

        result_dict = {}

        for file in valid_files:
            self.filepath = os.path.join(self.path, file)
            extension = os.path.splitext(file)[-1]
            result_dict.update(self.processors[extension]())

        return result_dict if result_dict else None

    def process_txt(self):
        """
        Process .txt files to extract active area data.

        :return: Extracted active area data.
        """
        data_dict = {}
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                device, active_area = line.strip().split()  # Assuming space separated
                data_dict[device] = float(active_area)
        return data_dict

    def process_json(self):
        """
        Process .json files to extract active area data.

        :return: Extracted active area data.
        """
        with open(self.filepath, 'r') as f:
            return json.load(f)

    def process_xlsx(self):
        """
        Process .xlsx files to extract active area data.

        :return: Extracted active area data.
        """
        data_dict = {}
        workbook = openpyxl.load_workbook(self.filepath, read_only=True)
        sheet = workbook.active
        for row in sheet.iter_rows(values_only=True):
            device, active_area = row
            data_dict[device] = float(active_area)
        return data_dict

