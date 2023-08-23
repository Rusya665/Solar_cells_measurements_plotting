from pathlib import Path
from tkinter import messagebox

import pandas as pd
from icecream import ic

from GUI.instruments import columns_swap, flip_data_if_necessary


class IVDataReader:
    """
    Class to read IV data
    """

    def __init__(self, parent, path, potentiostat, encoding):
        self.parent = parent
        self.path = path
        self.potentiostat = potentiostat
        self.encoding = encoding

    def read(self):
        df = None
        current_unit = None
        match self.potentiostat:
            case "SMU":
                df = pd.read_csv(self.path, sep='\t', engine='python', header=None, encoding=self.encoding,
                                 names=['V', 'I'], skiprows=2)
                current_unit = 'I'
                df = self.convert_current('I', df)

            case "Gamry":
                # Open the file and read the line containing the units
                with open(self.path, 'r', encoding=self.encoding) as file:
                    lines = file.readlines()
                    curve1_index = lines.index("CURVE1\tTABLE\n")
                    units_line = lines[curve1_index + 1].strip()
                    units = units_line.split('\t')
                    current_unit = units[3]  # Assuming the current unit is in the 4th column (0-indexed)
                df = pd.read_csv(self.path, engine='python', header=None, skiprows=65, encoding=self.encoding, sep='\t')
                """
                A special note for future me. If the skiprows=65 is not gonna work anymore, add a method to actually 
                check the .DTA file before parsing. Love you. You are the best.
                """
                df.drop(df.columns[[0, 2, 5, 6, 7, 8, 9, 10]], axis=1,
                        inplace=True)  # Drop unnecessary columns. Check the
                # Q3 from scratch.txt
                df.columns = ['Pt', 'V', 'I']  # Keep the "Pt" column for further filtering
                df = df[df["Pt"].str.contains(r'^\d+$')].reset_index()  # Filter the df by "Pt" column
                df.drop('Pt', axis=1, inplace=True)  # Drop that column
                df.drop('index', axis=1, inplace=True)  # Finally, drop a column created by reset_index()
                df = self.convert_current(current_unit, df)

            case "PalmSens4":
                # Open the file and read the line containing the units
                with open(self.path, 'r', encoding=self.encoding) as file:
                    # Skip the lines until reaching the line containing units
                    line = file.readline().strip()
                    while not line.startswith('V,'):
                        line = file.readline().strip()

                # Split the line to get the units
                units = line.split(',')
                # voltage_unit = units[0].split()[-1]  # The unit for voltage
                current_unit = units[1]  # The unit for current

                df = pd.read_csv(self.path, engine='python', header=None, encoding=self.encoding,
                                 skiprows=6, keep_default_na=True, na_filter=False, names=['V', 'I'])
                df = df[df['I'].notna()]  # Picking only the data which is not "Nan" <- dropping the last raw
                df = self.convert_current(current_unit, df)

        if df is not None:
            df.name = Path(self.path).stem
            # return columns_swap(df)
            return flip_data_if_necessary(df), current_unit
        else:
            raise ValueError(f"No matching potentiostat found for path: {self.path}")

    def convert_current(self, current_unit, df):
        """
        Convert the current to milli-amps (mA) based on the detected unit
        """
        if current_unit in ['A', 'I']:
            df['I'] = df['I'].multiply(10 ** 3)  # Converting from A to mA
        elif current_unit in ['mA', 'Im']:
            pass  # Current is already in mA, so no conversion needed
        elif current_unit in ['µA', 'Iµ']:
            df['I'] = df['I'].divide(10 ** 3)  # Converting from µA to mA
        else:
            messagebox.showerror(title=f"Unexpected current unit!",
                                 message=f"This current unit {current_unit} for {self.path} was detected.\n"
                                         f" Expected one of ['A', 'mA', 'µA']")
            self.parent.parent.exit()
        return df
