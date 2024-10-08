from datetime import timedelta
from pathlib import Path
from typing import List

import pandas as pd
from CTkMessagebox import CTkMessagebox

from JV_plotter_GUI.instruments import flip_data_if_necessary, remove_non_monotonic_last_value


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
        if self.potentiostat == "SMU":
            df = pd.read_csv(self.path, sep='\t', engine='python', header=None, encoding=self.encoding,
                             names=['V', 'I'], skiprows=2)
            current_unit = 'I'
            df = self.convert_current('I', df)

        elif self.potentiostat == "Gamry":
            with open(self.path, 'r', encoding=self.encoding) as file:
                lines = file.readlines()

            curve_indices = []
            for i, line in enumerate(lines):
                # Detect all the CURVE in the file
                if "CURVE" in line and "TABLE" in line:
                    units_line = lines[i + 2].strip()
                    units = units_line.split('\t')
                    current_unit_tmp = units[3]  # Assuming the current unit is in the 4th column (0-indexed)
                    curve_indices.append(i)
                    if current_unit is None:
                        current_unit = current_unit_tmp
                    else:
                        if current_unit != current_unit_tmp:
                            CTkMessagebox(title="Perhaps the file is corrupted",
                                          message=f"The Gamry's DTA file {self.path}\n"
                                                  f"Contains more than 1 CV data\n"
                                                  f"and these CV's having different current unit",
                                          icon="warning", option_1='Okay, fascinating')
            # Adding the end of the file as the end index for the last curve
            curve_indices.append(len(lines))
            curve_dfs = []

            for i in range(0, len(curve_indices) - 1):
                curve_df = self.gamry_process_curve(lines, curve_indices[i], curve_indices[i + 1])
                if len(curve_df) > 1:
                    curve_dfs.append(curve_df)
            if len(curve_dfs) > 1:
                CTkMessagebox(title="Perhaps the file is corrupted",
                              message=f"The Gamry's DTA file {self.path}\n"
                                      f"Contains more than 1 CV data",
                              icon="warning", option_1='Okay, fascinating')
                # Merging data from all curves into a single DataFrame
            final_df = pd.concat(curve_dfs).reset_index(drop=True)

            df1 = self.convert_current(current_unit, final_df)
            df = remove_non_monotonic_last_value(df1)

        elif self.potentiostat == "PalmSens4":
            # Encoding UTF-16
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

        elif self.potentiostat == "SP-150e":
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
            CTkMessagebox(title="Unexpected current unit!",
                          message=f"This current unit {current_unit} for {self.path} was detected.\n"
                                  f" Expected one of ['A', 'mA', 'µA']",
                          icon="cancel")
            self.parent.parent.exit()
        return df

    @staticmethod
    def gamry_process_curve(lines: List[str], start: int, end: int) -> pd.DataFrame:
        """
        Processes a segment of lines from a Gamry `.DTA` file to extract voltage (V) and current (I) data.

        This function extracts the IV curve data for a single curve segment, converts the raw string data into a
        pandas DataFrame,
        handles inconsistent formatting (such as commas in decimal places), and returns a cleaned DataFrame containing
        the relevant columns.

        :param lines: List of strings, where each string represents a line from the `.DTA` file.
        :param start: The starting line index of the curve segment within `lines`.
        :param end: The ending line index of the curve segment within `lines`.

        :return: A pandas DataFrame containing two columns:
            - 'V': Voltage values extracted from the 'Vf' column of the file.
            - 'I': Current values extracted from the 'Im' column of the file.
            If no valid data is found between `start` and `end`, an empty DataFrame is returned.
        """

        # Check if curve data is present
        if end <= start + 3:
            print(f"No data lines between {start} and {end}. Returning empty DataFrame.")
            return pd.DataFrame(columns=['V', 'I'])

        # Extract the header line for columns
        header_line = lines[start + 1].strip().split('\t')

        # Extract data for the curve, skipping two lines for header and units
        curve_data = lines[start + 3:end]
        if not curve_data:
            print(f"No curve data found between lines {start} and {end}. Returning empty DataFrame.")
            return pd.DataFrame(columns=['V', 'I'])

        # Handle extra spaces and inconsistent formatting in numeric data
        curve_data = [line.replace(',', '.').replace(' ', '').split() for line in curve_data]
        # Convert to DataFrame
        df = pd.DataFrame(curve_data)

        # Ensure the header line matches the number of columns in the DataFrame
        if len(header_line) != df.shape[1]:
            df.columns = header_line[:df.shape[1]]  # Assign columns up to the available data
        else:
            df.columns = header_line

        # Naming columns and selecting relevant ones (Vf -> 'V' and Im -> 'I')
        if 'Vf' not in header_line or 'Im' not in header_line:
            print(f"Expected columns 'Vf' and 'Im' not found in header. Check file format.")
            return pd.DataFrame(columns=['V', 'I'])

        # Rename columns and select only the 'V' (voltage) and 'I' (current) columns
        df = df[['Vf', 'Im']].rename(columns={'Vf': 'V', 'Im': 'I'})

        # Convert data to numeric values after replacing commas and aligning precision
        df['V'] = pd.to_numeric(df['V'], errors='coerce')
        df['I'] = pd.to_numeric(df['I'], errors='coerce')
        df.dropna(inplace=True)

        return df
