import os

import pandas as pd
from CTkMessagebox import CTkMessagebox
from fuzzywuzzy import fuzz


class TimeLineProcessor:
    def __init__(self, folder_path=None, hardcore_timeline=None, path_to_check=None):
        """
        Initialize a TimeLineProcessor instance.

        :param folder_path: The path of the folder to check.
        :param hardcore_timeline: Specific timeline file to look for.
        :param path_to_check: The path of the file to check.
        """
        self.folder_path = folder_path
        self.hardcore_timeline = hardcore_timeline
        self.path = path_to_check

    def find_timeline_file(self):
        """
        Search for the file with 'Timeline' in its name within the folder
        """
        if self.hardcore_timeline is not None:
            return os.path.join(self.folder_path, self.hardcore_timeline)
        highest_score = 0
        timeline_file = None

        for filename in os.listdir(self.folder_path):
            score = fuzz.partial_ratio("Timeline", filename)
            if score > highest_score:
                highest_score = score
                timeline_file = filename

        if timeline_file:
            return os.path.join(self.folder_path, timeline_file)
        else:
            CTkMessagebox(title='Error', message='No Timeline file found', icon="cancel")
            return None

    def check_the_path(self, auto_detect=True):
        """
        Check the file extension and read data accordingly.
        """
        if auto_detect and self.folder_path:
            self.path = self.find_timeline_file()

        if not self.path:
            return None

        file_extension = os.path.splitext(self.path)[1].lower()

        try:
            if file_extension == '.txt':
                df = pd.read_csv(self.path, delimiter='\t')  # Assuming tab-delimited txt file
            elif file_extension == '.json':
                df = pd.read_json(self.path)
            elif file_extension == '.csv':
                df = pd.read_csv(self.path)
            elif file_extension == '.xlsx':
                df = pd.read_excel(self.path)
            else:
                CTkMessagebox(title="Error", message='Unknown timeline file type', icon="cancel")
                return None

            if df.shape[1] != 1:
                CTkMessagebox(title="Error", message="The DataFrame must have only one column.", icon="cancel")
                return None
            return df

        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")
            return None
