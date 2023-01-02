import os
import sys
import time
import subprocess
from datetime import datetime

from read_iv import ReadData


class LogCreate:
    def __init__(self, path: str, start_time: float):
        if not path.endswith('/'):  # Adding the '/' at the end of the given path if not there
            path = path + '/'
        self.main_path = path
        self.start_time = start_time
        self._indicator = os.path.basename(os.path.dirname(self.main_path))  # See scratch.txt
        self.log_folder = self.create_folder()
        self.log()

    def create_folder(self):  # Creating new folder for storing new data
        if not os.path.exists(self.main_path + 'Log/'):
            m = self.main_path + 'Log/'
            os.makedirs(m)
            return m
        else:
            return str(self.main_path + 'Log/')

    @classmethod
    def open_file(cls, path_to_file):
        if sys.platform == "win32":
            os.startfile(path_to_file)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, path_to_file])

    def log(self):
        today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
        log_path = f"{self.log_folder}Log for {self._indicator}, {today}.txt"
        with open(log_path, "w") as log:
            log.write(f"Log for {self._indicator}\n\n")
            log.write(f"Date: {today}\n\n")
            log.write(f"Source folder: {self.main_path}\n")
            log.write(f'Source folder contained:\n')
            if not len(ReadData.data_files) == 0:
                for i, j in enumerate(zip(ReadData.data_files, ReadData.encoding_list, ReadData.potentiostat)):
                    log.write(f"{i + 1}. {j[0]}\t{j[2]}\tencoding={j[1]}\n")
            else:
                log.write('The given directory contained no applicable files\n')
            # # print(f'Skipped list: {skipped_img_index}')
            # if skipped_img_index:
            #     log.write(f'\nErrors\n')
            #     for w in range(len(skipped_img_index)):
            #         log.write(f'Skipped images: {skipped_img_index[w]}. {error_list[w]}\n')
            # log.write(f'\nParameters being used\n')
            # log.write(f'Number of background erasing cycles: {cycles}\n')
            # log.write(f'Did film was created: {film}\n')
            # if film == 'y':
            #     log.write(f'Ageing video: {video_name}\n')
            #     log.write(f'Frame rate: {frame_rate}\n')
            #     log.write(f'Frame size: {img_shape(cropped[0])[0:2]}\n')
            log.write(f'\nTotal analyzing and plotting time: \t{time.time() - self.start_time} sec')
        self.open_file(log_path)




