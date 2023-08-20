import customtkinter as ctk
import tkinter as ttk
from idlelib.tooltip import Hovertip
from icecream import ic


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

        self.aging_mode_checkbox = ctk.CTkCheckBox(self, text='Aging mode', command=self.parent.aging_mode_activator,
                                                   width=20)
        self.identical_areas_CheckBox = ctk.CTkCheckBox(self, text='Identical AA',
                                                        command=self.parent.identical_active_areas_activator)
        self.identical_areas_CheckBox.select()

        self.read_from_file = ctk.CTkButton(self, text='Read AA from file', command=self.parent.list_files,
                                            width=10)
        self.restore_cache_values = ctk.CTkButton(self, text='Cache values',
                                                  command=self.parent.table_frame.update_entries_from_cache)

        self.expand.grid(row=0, column=0, pady=15, padx=0)
        self.collapse.grid(row=0, column=1, pady=0, padx=7)
        self.potentiostat_combox.grid(row=0, column=2, pady=0, padx=10)
        self.aging_mode_checkbox.grid(row=0, column=3, pady=0, padx=7)
        self.identical_areas_CheckBox.grid(row=0, column=4, pady=0, padx=7)
        self.read_from_file.grid(row=0, column=5, padx=5)
        self.restore_cache_values.grid(row=0, column=6)

        self.hovers()

    def hovers(self):
        hover_delay = 400
        hover_text_expand_all = 'Expand all folders'
        hover_text_collapse_all = 'Collapse all folders'
        hover_potentiostat_combox = 'Choose potentiostat to work with'

        hover_aging_mode_checkbox = 'Activate "Aging mode". Will detect the same devices in the multiple folders'
        hover_text_sa = 'Identical active areas'
        hover_text_read_from = 'Read given active areas from a file'
        hover_text_cached = ('Restore active are values from the previously typed cache in NOT\n'
                             ' the "Identical active areas" mode')
        Hovertip(self.expand, hover_text_expand_all, hover_delay=hover_delay)
        Hovertip(self.collapse, hover_text_collapse_all, hover_delay=hover_delay)
        Hovertip(self.potentiostat_combox, hover_potentiostat_combox, hover_delay=hover_delay)

        Hovertip(self.aging_mode_checkbox, hover_aging_mode_checkbox, hover_delay=hover_delay)
        Hovertip(self.identical_areas_CheckBox, hover_text_sa, hover_delay=hover_delay)
        Hovertip(self.read_from_file, hover_text_read_from, hover_delay=hover_delay)
        Hovertip(self.restore_cache_values, hover_text_cached, hover_delay=hover_delay)
