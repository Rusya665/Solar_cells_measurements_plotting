import csv
import os.path
import pandas as pd


class ReadData:  # The main class for reading raw data
    data_files = []

    def __init__(self, path_file: str):

        if not path_file.endswith('/'):  # Adding the '/' at the end of the given path if not there
            path_file = path_file + '/'

        self.path_file = path_file

        for file in os.listdir(self.path_file):
            if not file.startswith('Log'):
                ReadData.data_files.append(file)
                self._read_file(file)
        print(ReadData.data_files)

    def _read_file(self, file):
        # print(os.path.join(self.path_file, file))
        if file.endswith('.txt'):  # The source measurement unit case
            df = pd.read_csv(os.path.join(self.path_file, file), sep='\t', engine='python', header=None,
                             names=['Vm', 'Im'], skiprows=2)
        return df
