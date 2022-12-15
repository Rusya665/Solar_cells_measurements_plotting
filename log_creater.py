from read_iv import ReadData
import os
from pathlib import Path
from datetime import datetime
import time


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

    def log(self):
        today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
        log_path = f"{self.log_folder}Log for {self._indicator}, {today}.txt"
        with open(log_path, "w") as log:
            log.write(f"Log for {self._indicator}\n\n")
            log.write(f"Date: {today}\n\n")
            log.write(f"Source folder: {self.main_path}\n")
            log.write(f'Source folder contained:\n')
            for i, j in enumerate(ReadData.data_files):
                log.write(f"{i + 1}. {j}\n")

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
        os.startfile(log_path)


