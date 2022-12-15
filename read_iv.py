import os.path
import pandas as pd

# Set pandas' console output width
# pd.set_option('display.max_rows', 500)
# pd.set_option('display.max_columns', 500)
# pd.set_option('display.width', 1000)


class ReadData:  # The main class for reading raw data
    data_files, raw_data = [], []

    def __init__(self, path_file: str):

        if not path_file.endswith('/'):  # Adding the '/' at the end of the given path if not there
            path_file = path_file + '/'

        self.path_file = path_file

        for file in os.listdir(self.path_file):
            if not file.startswith('Log'):
                if file.lower().endswith(('.txt', '.csv', '.dta')):
                    if self.potentiostat_check(os.path.join(self.path_file, file)):
                        ReadData.data_files.append(file)
                        # print(self.read_file(file))
                        ReadData.raw_data.append(self.read_file(os.path.join(self.path_file, file)))
        # print(ReadData.raw_data)
        # print(ReadData.data_files)
        for a, b in zip(ReadData.data_files, ReadData.raw_data):
            print(f'{a}\n {b}\n')

    @classmethod
    def potentiostat_check(cls, file):  # This method might be used to filter raw input dara for different potentiostats
        """
        This raw-data-checking methods is working.
        In future this method may return specific row-index for specific raw-date type
        """
        try:
            with open(file, 'r', encoding='utf-8') as f:  # Encoding for Gamry and SMU
                g = f.read().splitlines()
        except UnicodeDecodeError:
            with open(file, 'r', encoding='utf-16') as f:  # Special encoding for PalmSens4
                g = f.read().splitlines()
        if "CURVE1\tTABLE" in g:  # "Gamry"
            return True
        elif "Cyclic Voltammetry: CV i vs E" in g:  # "PalmSens4"
            return True
        elif '[0, 0, 0]' in g:  # "SMU"
            return True
        else:
            return False

    @classmethod
    def read_file(cls, file):

        if file.lower().endswith('.txt'):  # The source measurement unit case
            df = pd.read_csv(file, sep='\t', engine='python', header=None,
                             names=['V', 'I'], skiprows=2)
            df.name = file
            return df

        if file.lower().endswith('.dta'):  # The # Gamry case
            df = pd.read_csv(file, engine='python', header=None, skiprows=65, sep='\t')
            """
            A special note for future me. If the skiprows=65 is not gonna work anymore, add a method to actually 
            check the .DTA file before parsing. Love you. You are the best.
            """
            df.drop(df.columns[[0, 2, 5, 6, 7, 8, 9, 10]], axis=1, inplace=True)  # Drop unnecessary columns. Check the
            # Q3 from scratch.txt
            df.columns = ['Pt', 'V', 'I']  # Keep the "Pt" column for further filtering
            df = df[df["Pt"].str.contains(r'^\d+$')]  # Filter the df by "Pt" column
            df.drop('Pt', axis=1, inplace=True)  # Finally, drop that column
            df["I"] = df["I"].astype(float)  # Change var type from str to float
            # df['I'] = df['I'].divide(10 ** 3)  # Uniforming the result. Gamry saves the current in mA. Check the
            #             # Q3 from scratch.txt
            df.name = file
            return df

        if file.lower().endswith('.csv'):
            df = pd.read_csv(file, encoding='UTF-16', engine='python', header=None,
                             skiprows=6, keep_default_na=True, na_filter=False, names=['V', 'I'])
            df = df[df['I'].notna()]  # Picking only the data which is not "Nan" <- dropping the last raw
            df['I'] = df['I'].divide(10 ** 6)  # Uniforming the result. PalmSens saves the current in µA
            df.name = file
            return df
