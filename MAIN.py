from tkinter import ttk

import customtkinter as ctk

from JV_plotter_GUI.Main_frame import IVProcessingMainClass
from JV_plotter_GUI.settings import settings


class JVProcessorMAIN(ctk.CTk):
    screen_width, screen_height = settings['GUI_main']['screen_width'], settings['GUI_main']['screen_height']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s = ttk.Style()
        self.s.configure('Treeview', rowheight=30)
        self.title("JV processor")
        self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.minsize(700, 600)
        self.resizable(True, True)
        self.main_frame = IVProcessingMainClass(parent=self)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    jv_processor_app = JVProcessorMAIN()
    jv_processor_app.mainloop()
