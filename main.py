from read_iv import ReadData
from log_creater import LogCreate

path = r"C:\Users\runiza.TY2206042\OneDrive - O365 Turun yliopisto\J-V\Input"


def main():
    ReadData(path)
    LogCreate(path)


if __name__ == "__main__":
    main()
