import os


def get_filenames(directory):
    """
    Get a list of filenames in the given directory.

    :param directory: Path to the directory
    :return: List of filenames in the directory
    """
    return os.listdir(directory)


# Example usage
directory_path = r'D:/OneDrive - O365 Turun yliopisto/IV_plotting_project/Input'
filenames = get_filenames(directory_path)
print(filenames)
