import customtkinter as ctk
from idlelib.tooltip import Hovertip


class SlidePanel(ctk.CTkFrame):
    def __init__(self, parent, start_pos, end_pos):
        super().__init__(master=parent)
        self.parent = parent
        # general attributes
        self.start_pos = start_pos + 0.04
        self.end_pos = end_pos - 0.03
        self.width = abs(start_pos - end_pos)

        # animation logic
        self.pos = self.start_pos
        self.in_start_pos = True
        self.rely = 0.05
        self.relative_height = 0.85
        # layout
        self.place(relx=self.start_pos, rely=self.rely, relwidth=self.width, relheight=self.relative_height)

        self.slide_panel_label = ctk.CTkLabel(self, text="Settings")
        self.slide_panel_label.cget("font").configure(size=20)
        self.potentiostat_combox_label = ctk.CTkLabel(self, text="Choose potentiostat")
        self.potentiostat_combox = ctk.CTkComboBox(self, values=['All', 'Gamry', 'PalmSens4', 'SMU', 'SP-150e'],
                                                   width=110,
                                                   command=self.parent.set_potentiostat)

        self.aging_mode_checkbox = ctk.CTkCheckBox(self, text='Aging mode', command=self.parent.aging_mode_activator,
                                                   width=20)
        self.identical_areas_CheckBox = ctk.CTkCheckBox(self, text='Identical AA',
                                                        command=self.parent.identical_active_areas_activator)
        self.identical_areas_CheckBox.select()

        self.read_from_file = ctk.CTkButton(self, text='Read AA from file', command=self.parent.list_files)
        self.restore_cache_values = ctk.CTkButton(self, text='Cache values',
                                                  command=self.parent.table_frame.update_entries_from_cache)
        self.open_wb_checkbox = ctk.CTkCheckBox(self, text='Open WB', command=self.parent.open_wb_activator)
        self.open_wb_checkbox.select()
        self.slide_panel_label.pack(pady=10)
        self.potentiostat_combox_label.pack(pady=5)
        self.potentiostat_combox.pack(pady=5)
        widgets = [
            self.aging_mode_checkbox,
            self.identical_areas_CheckBox,
            self.read_from_file,
            self.restore_cache_values,
            self.open_wb_checkbox
        ]
        for widget in widgets:
            widget.pack(pady=10)

        self.hovers()

    def hovers(self):
        hover_delay = 400
        hover_potentiostat_combox = 'Choose potentiostat to work with'

        hover_aging_mode_checkbox = 'Activate "Aging mode". Will detect the same devices in the multiple folders'
        hover_text_sa = 'Identical active areas'
        hover_text_read_from = 'Read given active areas from a file'
        hover_text_cached = ('Restore active are values from the previously typed cache in NOT\n'
                             ' the "Identical active areas" mode')
        hover_text_open_wb = 'Open resulting workbook after the code is complete'
        Hovertip(self.potentiostat_combox, hover_potentiostat_combox, hover_delay=hover_delay)

        Hovertip(self.aging_mode_checkbox, hover_aging_mode_checkbox, hover_delay=hover_delay)
        Hovertip(self.identical_areas_CheckBox, hover_text_sa, hover_delay=hover_delay)
        Hovertip(self.read_from_file, hover_text_read_from, hover_delay=hover_delay)
        Hovertip(self.restore_cache_values, hover_text_cached, hover_delay=hover_delay)
        Hovertip(self.open_wb_checkbox, hover_text_open_wb, hover_delay=hover_delay)

    def animate(self):
        target_pos = self.end_pos if self.in_start_pos else self.start_pos
        step = -0.03 if self.in_start_pos else 0.03
        self.animate_to_target(target_pos, step)
        self.in_start_pos = not self.in_start_pos

    def animate_to_target(self, target_pos, step):
        if (step < 0 and self.pos > target_pos) or (step > 0 and self.pos < target_pos):
            self.pos += step
            self.place(relx=self.pos, rely=self.rely, relwidth=self.width, relheight=self.relative_height)
            self.lift()  # Bring the frame to the top
            self.after(10, lambda: self.animate_to_target(target_pos, step))
