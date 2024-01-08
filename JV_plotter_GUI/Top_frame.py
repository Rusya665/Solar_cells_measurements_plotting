from idlelib.tooltip import Hovertip

import customtkinter as ctk


class TopmostFrame(ctk.CTkFrame):
    def __init__(self, parent, width=200, height=200, fg_color='transparent', *args, **kwargs):
        super().__init__(master=parent, width=width, height=height, fg_color=fg_color, *args, **kwargs)
        self.parent = parent

        self.expand = ctk.CTkButton(self, text='Expand all', width=20,
                                    command=lambda: self.parent.expand_collapse())
        self.collapse = ctk.CTkButton(self, text='Collapse all', width=20,
                                      command=lambda: self.parent.expand_collapse(False))
        self.settings_button = ctk.CTkButton(self, text='Settings', width=25, command=self.parent.slide_frame.animate)
        self.expand.grid(row=0, column=0, pady=15, padx=0)
        self.collapse.grid(row=0, column=1, pady=0, padx=7)
        self.settings_button.grid(row=0, column=2, pady=0, padx=7)

        self.hovers()

    def hovers(self):
        hover_delay = 400
        hover_text_expand_all = 'Expand all folders'
        hover_text_collapse_all = 'Collapse all folders'
        hover_text_settings = 'Show/hide the side panel with the additional settings'
        Hovertip(self.expand, hover_text_expand_all, hover_delay=hover_delay)
        Hovertip(self.collapse, hover_text_collapse_all, hover_delay=hover_delay)
        Hovertip(self.settings_button, hover_text_settings, hover_delay=hover_delay)
