import os
import sys
import subprocess

def columns_swap(df, col1='V', col2='I'):
    """
    Swapping two columns in a PandasDataframe
    :param df: An initial dataframe
    :param col1: First column to swap
    :param col2: Second column to swap
    :return: A swapped dataframe
    """
    col_list = list(df.columns)
    x, y = col_list.index(col1), col_list.index(col2)
    col_list[y], col_list[x] = col_list[x], col_list[y]
    df = df[col_list]
    return df


def create_folder(path: str, suffix: str):  # Creating new folder for storing new data
    """
    Create a folder inside a given one.
    :param path: Given path
    :param suffix: Desired name of a new one
    :return: String with the folder's name (the folder has been created)
    """
    if suffix:
        if not suffix.endswith('/'):
            suffix = suffix + '/'
    if not os.path.exists(path + suffix):
        m = path + suffix
        os.makedirs(m)
        return m
    else:
        return str(path + suffix)


def open_file(path_to_file):
    """
    Run a file
    :param path_to_file: Path to a file
    :return:
    """
    if sys.platform == "win32":
        os.startfile(path_to_file)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path_to_file])
