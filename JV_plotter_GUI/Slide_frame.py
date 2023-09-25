from idlelib.tooltip import Hovertip

import customtkinter as ctk


class SettingsPanel(ctk.CTkFrame):
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
        self.aging_mode_label = ctk.CTkLabel(self, text='Aging mode region')
        self.aging_mode_label.cget("font").configure(size=20)
        self.time_label = ctk.CTkLabel(self, text='Aging time: undefined.\n Specify the path')
        self.timeline_detector_button = ctk.CTkButton(self, text='Choose the TimeLine', state='disabled',
                                                      command=lambda: self.parent.specify_timeline())
        self.identical_areas_CheckBox = ctk.CTkCheckBox(self, text='Identical AA',
                                                        command=self.parent.identical_active_areas_activator)
        self.identical_areas_CheckBox.select()

        self.read_from_file = ctk.CTkButton(self, text='Read AA from file', command=self.parent.list_files)
        self.restore_cache_values = ctk.CTkButton(self, text='Cache values',
                                                  command=self.parent.table_frame.update_entries_from_cache)

        self.additional_settings = ctk.CTkButton(self, text='Additional settings',
                                                 command=self.parent.additional_settings.animate_additional_settings)
        self.slide_panel_label.pack(pady=10)
        self.potentiostat_combox_label.pack(pady=5)
        self.potentiostat_combox.pack(pady=5)
        widgets = [
            self.identical_areas_CheckBox,
            self.read_from_file,
            self.restore_cache_values,
            self.aging_mode_label,
            self.aging_mode_checkbox,
            self.time_label,
            self.timeline_detector_button,
            self.additional_settings
        ]
        for widget in widgets:
            widget.pack(pady=10)
        self.hovers()

    def hovers(self):
        hover_delay = 400
        hover_potentiostat_combox = "  Pick your potentiostat!  \n  Your magical device! 🎛️  "
        hover_text_sa = "  Twinsies! Identical  \n  active areas! 👯  "
        hover_text_read_from = "  Grab active areas  \n  from a secret file! 📁  "
        hover_text_cached = "  Cache me if you can!  \n  Restore NOT in \"Identical\"! 🔄  "
        hover_aging_mode_region = ("  Welcome, Adventurer!  🌟  \n"
                                   "  You\'re stepping into the aging  \n"
                                   "  Rollercoaster ride ahead!  🎢  \n"
                                   "  Unlock aging mysteries!  🔍  \n"
                                   "  Accelerated aging tests!  🕒  \n"
                                   "  See ever-changing colors!  🌈  \n"
                                   "  Good luck, daring friend!  🍀  \n"
                                   "  Your next click: big discovery?  🚀  ")
        hover_aging_mode_checkbox = "  Activate \"Aging Mode\"!  \n  Time-travel in folders! ⏳  "
        hover_aging_timeline = "  Max timeline time! 🕒  \n  Shows if readable! 🤓  "
        hover_choose_the_timeline = "  Point to your timeline! 🗺️  \n  Specify the path! 🛣️  "
        hover_additional_settings = ("  Dive Deeper! 🐠  \n"
                                     "  Uncover more customization options  \n"
                                     "  to fine-tune your experience! 🔧  ")

        Hovertip(self.potentiostat_combox, hover_potentiostat_combox, hover_delay=hover_delay)
        Hovertip(self.identical_areas_CheckBox, hover_text_sa, hover_delay=hover_delay)
        Hovertip(self.read_from_file, hover_text_read_from, hover_delay=hover_delay)
        Hovertip(self.restore_cache_values, hover_text_cached, hover_delay=hover_delay)
        Hovertip(self.aging_mode_label, hover_aging_mode_region, hover_delay=hover_delay)
        Hovertip(self.aging_mode_checkbox, hover_aging_mode_checkbox, hover_delay=hover_delay)
        Hovertip(self.time_label, hover_aging_timeline, hover_delay=hover_delay)
        Hovertip(self.timeline_detector_button, hover_choose_the_timeline, hover_delay=hover_delay)
        Hovertip(self.additional_settings, hover_additional_settings, hover_delay=hover_delay)

    def animate(self, step=0.03):
        if self.in_start_pos:  # If the frame is about to be shown
            self.parent.bind("<Button-1>", self.hide_if_clicked_outside)  # Bind the event
            self.parent.table_frame.files_table.bind("<Button-1>", self.hide_if_clicked_outside)
            self.parent.table_frame.active_areas_scrollable_frame.bind("<Button-1>", self.hide_if_clicked_outside)
        if not self.parent.additional_settings.in_start_pos:
            self.parent.additional_settings.animate_additional_settings()
        target_pos = self.end_pos if self.in_start_pos else self.start_pos
        step = -1 * step if self.in_start_pos else step
        self.animate_to_target(target_pos, step)
        self.in_start_pos = not self.in_start_pos

    def animate_to_target(self, target_pos, step):
        if (step < 0 and self.pos > target_pos) or (step > 0 and self.pos < target_pos):
            self.pos += step
            self.place(relx=self.pos, rely=self.rely, relwidth=self.width, relheight=self.relative_height)
            self.lift()  # Bring the frame to the top
            self.after(10, lambda: self.animate_to_target(target_pos, step))
        else:
            if self.in_start_pos:  # If the frame is fully hidden
                self.parent.unbind("<Button-1>")  # Unbind the event
                self.parent.table_frame.files_table.unbind("<Button-1>")  # Unbind the event
                self.parent.table_frame.active_areas_scrollable_frame.unbind("<Button-1>")  # Unbind the event

    def hide_if_clicked_outside(self, event):
        x, y, _, _ = self.bbox("insert")
        if event.x < x or event.x > x + self.winfo_width() or event.y < y or event.y > y + self.winfo_height():
            self.animate()  # Assuming you have a method to hide the slide frame
