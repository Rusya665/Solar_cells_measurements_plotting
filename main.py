from read_iv import ReadData
from log_creater import LogCreate
import time

path = r"C:\Users\runiza.TY2206042\OneDrive - O365 Turun yliopisto\J-V\Input"


def main():
    start_time = time.time()
    ReadData(path)
    # LogCreate(path, start_time)


if __name__ == "__main__":
    main()
