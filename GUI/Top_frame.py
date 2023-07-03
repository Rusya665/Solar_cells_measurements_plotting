import customtkinter as ctk
import tkinter as ttk
from idlelib.tooltip import Hovertip


class FirstFrame(ctk.CTkFrame):
    def __init__(self, parent, width=200, height=200, fg_color='transparent', *args, **kwargs):
        super().__init__(master=parent, width=width, height=height, fg_color=fg_color, *args, **kwargs)
        self.parent = parent

        self.potentiostat_combox = ctk.CTkComboBox(self, values=['All', 'Gamry', 'PalmSens4', 'SMU'], width=70,
                                                   command=self.parent.set_potentiostat)
        self.expand = ctk.CTkButton(self, text='Expand all', width=20,
                                    command=lambda: self.parent.expand_collapse())
        self.collapse = ctk.CTkButton(self, text='Collapse all', width=20,
                                      command=lambda: self.parent.expand_collapse(False))

        self.aging_mode_checkbox = ctk.CTkCheckBox(self, text='Aging mode', command=self.parent.aging_mode_activator, width=20)
        self.save_after_CheckBox = ctk.CTkCheckBox(self, text='SA', command=self.save_after)

        self.expand.grid(row=0, column=0, pady=15, padx=0)
        self.collapse.grid(row=0, column=1, pady=0, padx=7)
        self.potentiostat_combox.grid(row=0, column=2, pady=0, padx=10)
        self.aging_mode_checkbox.grid(row=0, column=3, pady=0, padx=7)
        self.save_after_CheckBox.grid(row=0, column=4, pady=0, padx=7)

        self.hovers()

    def hovers(self):
        hover_delay = 400
        hover_text_expand_all = 'Expand all folders'
        hover_text_collapse_all = 'Collapse all folders'
        hover_potentiostat_combox = 'Choose potentiostat to work with'

        hover_aging_mode_checkbox = 'Activate "Aging mode". Will detect the same devices in the multiple folders'
        hover_text_sa = 'Optional parameter.\nSave images with areas after completing all images chosen.\n' \
                        'Thus the annoying saving time will be only at the very end of working.'
        Hovertip(self.expand, hover_text_expand_all, hover_delay=hover_delay)
        Hovertip(self.collapse, hover_text_collapse_all, hover_delay=hover_delay)
        Hovertip(self.potentiostat_combox, hover_potentiostat_combox, hover_delay=hover_delay)

        Hovertip(self.aging_mode_checkbox, hover_aging_mode_checkbox, hover_delay=hover_delay)
        Hovertip(self.save_after_CheckBox, hover_text_sa, hover_delay=hover_delay)

    def save_after(self):
        self.parent.parent.save_after = self.save_after_CheckBox.get()
