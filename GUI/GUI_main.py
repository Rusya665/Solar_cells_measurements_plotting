import time
from tkinter import ttk

import customtkinter as ctk

from Main_frame import SpecifyPath


class RGBMainRoot(ctk.CTk):
    screen_width, screen_height = 800, 680

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s = ttk.Style()
        self.s.configure('Treeview', rowheight=30)
        # Some variables
        self.data = None
        # window
        self.title("Average RGB value extractor.py")
        self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.minsize(700, 600)
        self.resizable(True, True)

        SpecifyPath(parent=self, get_data=self.get_data)

    def get_data(self, data=None, aging_mode=False):
        """
        Pass a data_dict from one Tkinter clss to another one
        :param data: Dict with data
        :param aging_mode: Activate aging mode (IV data locates in different folders)
        :return: None
        """
        all_instances = []
        temp_value = None
        self.data = data

        self.destroy()


if __name__ == "__main__":
    start_time = time.time()
    ctk.set_appearance_mode("dark")
    app_1 = RGBMainRoot()
    app_1.mainloop()
    print("\n", "--- %s seconds ---" % (time.time() - start_time))
