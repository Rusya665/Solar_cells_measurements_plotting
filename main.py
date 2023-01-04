from read_iv import ReadData
from log_creater import LogCreate
from xlsx_plotter import PlotIV
import time
from tester import do_smth


"""
Specify the path to the folder with raw data from potentiostat.
"""
# path = r"C:\Users\runiza.TY2206042\OneDrive - O365 Turun yliopisto\J-V\Input"  # Windows case
path = "/home/rusya665/OneDrive/IV_plotting_project/Input"  # Ubuntu case


def main():
    start_time = time.time()
    ReadData(path)
    do_smth()
    PlotIV(path, open_wb=1)
    LogCreate(path, start_time)
    print("\n", "--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    main()
