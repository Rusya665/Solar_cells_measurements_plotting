import os
import pandas as pd
from tkinter import messagebox

from icecream import ic


class TimeLineProcessor:
    def __init__(self, path_to_check):
        """
        Initialize a TimeLineProcessor instance.

        :param path_to_check: The path of the file to check.
        """
        self.path = path_to_check

    def check_the_path(self):
        """
        Check the file extension and read data accordingly.
        """
        file_extension = os.path.splitext(self.path)[1].lower()

        try:
            match file_extension:
                case '.txt':
                    df = pd.read_csv(self.path, delimiter='\t')  # Assuming tab-delimited txt file
                case '.json':
                    df = pd.read_json(self.path)
                case '.csv':
                    df = pd.read_csv(self.path)
                case '.xlsx':
                    df = pd.read_excel(self.path)
                case _:
                    messagebox.showerror('Error', 'Unknown file type')
                    return None

            if df.shape[1] != 1:
                messagebox.showerror("Error", "The DataFrame must have only one column.")
            return df

        except Exception as e:
            messagebox.showerror('Error', str(e))
            return None
