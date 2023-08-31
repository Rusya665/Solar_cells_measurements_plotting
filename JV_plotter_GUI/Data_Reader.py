from pathlib import Path
from tkinter import messagebox

import pandas as pd
from datetime import timedelta

from JV_plotter_GUI.instruments import flip_data_if_necessary


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
                    try:
                        start_of_data_index = next(i for i, line in enumerate(lines) if
                                                   line.strip() == "Pt\tT\tVf\tIm\tVu\tSig\tAch\tIERange\tOver\tTemp")
                    except StopIteration:
                        print(f"The file {self.path} does not contain the expected start marker.")
                        return None
                    units_line = lines[start_of_data_index + 1].strip()
                    units = units_line.split('\t')
                    current_unit = units[3]  # Assuming the current unit is in the 4th column (0-indexed)
                df = pd.read_csv(self.path, engine='python',
                                 header=None, skiprows=start_of_data_index + 2, encoding=self.encoding, sep='\t')
                df.drop(df.columns[[0, 2, 5, 6, 7, 8, 9, 10]], axis=1,
                        inplace=True)  # Drop unnecessary columns.
                df.columns = ['Pt', 'V', 'I']  # Keep the "Pt" column for further filtering
                df = df[df["Pt"].str.contains(r'^\d+$')].reset_index()  # Filter the df by "Pt" column
                # Drop unnecessary columns
                df.drop(['Pt', 'index'], axis=1, inplace=True)
                df = self.convert_current(current_unit, df)

            case "PalmSens4":
                #  Encoding UTF-16
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

            case "SP-150e":
                #  Encoding ISO-8859-1
                i_values, v_values, time_values = [], [], []
                num_header_lines, i_index, v_index, time_index, current_unit = None, None, None, None, None
                preconditioning_time = None

                with open(self.path, 'r', encoding=self.encoding) as file:
                    for line_number, line in enumerate(file, start=1):
                        line = line.strip()

                        if "Nb header lines" in line:
                            num_header_lines = int(line.split(":")[1].strip())
                            continue

                        if line.startswith("ti (h:m:s)"):
                            time_str = line.split("ti (h:m:s)")[1]
                            hours, minutes, seconds = map(float, time_str.split(':'))
                            preconditioning_time = timedelta(hours=hours, minutes=minutes,
                                                             seconds=seconds).total_seconds()
                            continue

                        if num_header_lines is None:
                            continue

                        values = line.split("\t")
                        if line_number == num_header_lines:
                            i_index, v_index = values.index(next(h for h in values if "<I>" in h)), values.index(
                                next(h for h in values if "Ewe" in h))
                            # Check if the time column exists
                            time_index = next((i for i, h in enumerate(values) if "time" in h), None)
                            current_unit = values[i_index].split("/")[-1]  # Extracting the current unit
                        elif line_number > num_header_lines and time_index is not None:
                            time_str = values[time_index].split(' ')[1]
                            hours, minutes, seconds = map(float, time_str.split(':'))
                            total_seconds = timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
                            time_values.append(float(total_seconds))
                            i_values.append(float(values[i_index]))
                            v_values.append(float(values[v_index]))

                # Creating a DataFrame with the I, V, and time values
                df = pd.DataFrame({'I': i_values, 'V': v_values, 'Time': time_values})
                # Creating a mask that checks if the 'Time' value is higher than the first 'Time'
                # value plus preconditioning_time
                mask = df['Time'] > preconditioning_time + df['Time'].iloc[0]
                # Use the mask to filter the DataFrame
                df = df[mask].drop(columns=['Time']).reset_index(drop=True)
                # Convert current to appropriate unit
                df.fillna(0)
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
        df['I'] = df['I'].astype(float)
        if current_unit in ['A', 'I']:
            pass  # Current is already in A, so no conversion needed
        elif current_unit in ['mA', 'Im']:
            df['I'] = df['I'].divide(10 ** 3)  # Current from mA to A
        elif current_unit in ['µA', 'Iµ']:
            df['I'] = df['I'].divide(10 ** 6)  # Converting from µA to A
        else:
            messagebox.showerror(title=f"Unexpected current unit!",
                                 message=f"This current unit {current_unit} for {self.path} was detected.\n"
                                         f" Expected one of ['A', 'mA', 'µA']")
            self.parent.parent.exit()
        return df
