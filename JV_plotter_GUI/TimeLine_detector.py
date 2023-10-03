import os
import pandas as pd
from tkinter import messagebox


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
            if file_extension == '.txt':
                df = pd.read_csv(self.path, delimiter='\t')  # Assuming tab-delimited txt file
            elif file_extension == '.json':
                df = pd.read_json(self.path)
            elif file_extension == '.csv':
                df = pd.read_csv(self.path)
            elif file_extension == '.xlsx':
                df = pd.read_excel(self.path)
            else:
                messagebox.showerror('Error', 'Unknown file type')
                return None

            if df.shape[1] != 1:
                messagebox.showerror("Error", "The DataFrame must have only one column.")
                return None
            return df

        except Exception as e:
            messagebox.showerror('Error', str(e))
            return None
