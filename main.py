from log_creater import LogCreate


"""
Specify the path to the folder with raw data from potentiostat.
"""
# path = r"C:\Users\runiza.TY2206042\OneDrive - O365 Turun yliopisto\J-V\Input"  # Windows case
path = "/home/rusya665/OneDrive/IV_plotting_project/Input"  # Ubuntu case


def main():
    LogCreate(path)


if __name__ == "__main__":
    main()
