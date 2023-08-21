import pandas as pd
from pathlib import Path
from GUI.instruments import columns_swap


class IVDataReader:
    """
    Class to read IV data
    """

    def __init__(self, path, potentiostat, encoding):
        self.path = path
        self.potentiostat = potentiostat
        self.encoding = encoding

    def read(self):
        df = None

        match self.potentiostat:
            case "SMU":
                df = pd.read_csv(self.path, sep='\t', engine='python', header=None, encoding=self.encoding,
                                 names=['V', 'I'], skiprows=2)

            case "Gamry":
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

            case "PalmSens4":
                df = pd.read_csv(self.path, engine='python', header=None, encoding=self.encoding,
                                 skiprows=6, keep_default_na=True, na_filter=False, names=['V', 'I'])
                df = df[df['I'].notna()]  # Picking only the data which is not "Nan" <- dropping the last raw
                df['I'] = df['I'].divide(10 ** 6)  # Uniforming the result. PalmSens saves the current in µA
        if df is not None:
            df.name = Path(self.path).stem
            return columns_swap(df)
        else:
            raise ValueError(f"No matching potentiostat found for path: {self.path}")
