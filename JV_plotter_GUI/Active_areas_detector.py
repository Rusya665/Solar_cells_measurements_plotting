import json
import os
from difflib import SequenceMatcher

import openpyxl


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

    def __init__(self, path, active_area_json=None):
        """
        Initialize the ActiveAreaDetector with a path.

        :param path: Path to the directory to scan for active area files.
        :param active_area_json: Path to the JSON file containing predefined active areas.
        """
        self.path = path
        self.filepath = ''
        self.active_area_json = active_area_json
        self.processors = {
            '.txt': self.process_txt,
            '.json': self.process_json,
            '.xlsx': self.process_xlsx
        }

    @staticmethod
    def similar(a, b):
        """
        Determine how similar the two strings are.

        :param a: First string to compare.
        :param b: Second string to compare.
        :return: Similarity ratio between 0 and 1.
        """
        return SequenceMatcher(None, a, b).ratio()

    def load_predefined_areas(self):
        """
        Load predefined active areas from a JSON file if provided.

        :return: Dictionary of predefined active areas or an empty dictionary.
        """
        if self.active_area_json and os.path.exists(self.active_area_json):
            return self.process_json(self.active_area_json)
        return {}

    def check_directory(self):
        """
        Check the directory for the best file containing active area information,
        with a preference for JSON files over TXT files if their similarity to "Active area" is close.

        :return: Dictionary of device names and their corresponding active areas or None if no data found.
        """
        valid_files = [file for file in os.listdir(self.path)
                       if file.endswith(tuple(self.processors.keys()))
                       and self.similar("Active area", file) > 0.6]  # 0.6 is a threshold, can be adjusted

        if not valid_files:
            return None

        # Sort files by similarity
        valid_files.sort(key=lambda file: self.similar("Active area", file), reverse=True)

        best_file = valid_files[0]
        best_similarity = self.similar("Active area", best_file)

        # Check if there's a JSON file close enough in similarity to the best file
        for file in valid_files:
            if file.endswith('.json') and abs(self.similar("Active area", file) - best_similarity) < 0.06:
                best_file = file
                break

        self.filepath = os.path.join(self.path, best_file)
        extension = os.path.splitext(best_file)[-1]
        return self.processors[extension]()

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

    def process_json(self, path_to_aa_json=None):
        """
        Process .json files to extract active area data.

        :return: Extracted active area data.
        """
        path = self.filepath if path_to_aa_json is None else path_to_aa_json
        with open(path, 'r') as f:
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
