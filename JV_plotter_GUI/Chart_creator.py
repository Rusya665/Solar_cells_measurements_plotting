from datetime import timedelta

from xlsxwriter import Workbook
from xlsxwriter.workbook import ChartScatter

from JV_plotter_GUI.instruments import row_to_excel_col, custom_round


class ChartsCreator:
    def __init__(self, workbook: Workbook, data: dict, settings: dict, timeline_df, base_date):
        """
        Initialize ChartsCreator class.

        :param workbook: A xlsxwriter Workbook object where plots are to be added.
        :param data: A dictionary which contains the raw data.
        :param settings: A dictionary with the settings
        :param base_date: A datetime representation of the zero in the horizontal axis
        """
        self.workbook = workbook
        self.data = data
        self.settings = settings
        self.timeline_df = timeline_df
        self.base_date = base_date

    def plot_iv(self, sheet_name: str, data_start: int, data_end: int,
                name_suffix: str or None) -> ChartScatter:
        name_suffix = ' ' + name_suffix if name_suffix else ''
        chart = self.workbook.add_chart({'type': 'scatter'})
        chart.add_series({
            'categories': f"='{sheet_name}'!$B${data_start}:$B${data_end}",
            'values': f"='{sheet_name}'!$A${data_start}:$A${data_end}",
            'line': {'width': 1.5, 'color': 'black'}, 'marker': {'type': 'none'},  # No markers
        })
        chart.set_title({
            'name': f"{sheet_name + name_suffix}",
            'name_font': {'size': 14, 'italic': False, 'bold': False, 'name': 'Calibri (Body)'},
        })
        chart.set_x_axis({
            'name': 'V, V',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_tick_mark': 'cross',
            'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
        })
        chart.set_legend({'none': True})
        chart.set_y_axis({
            'name': 'J, mA/cm²',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
            'major_tick_mark': 'outside',
        })
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.settings['chart_x_scale'],
                        'y_scale': self.settings['chart_y_scale']})

        return chart

    def plot_all_sweeps(self, start_key, end_key, name_suffix):
        name_suffix = ' ' + name_suffix if name_suffix else ''
        chart_all_sweeps = self.workbook.add_chart({'type': 'scatter'})

        for folder_name, devices in self.data.items():
            for device_name, device_data in devices.items():
                ws_name = self.data[folder_name][device_name]['sheet_name']
                data_start = self.data[folder_name][device_name]['sweep_indexes_data'][start_key]
                data_end = self.data[folder_name][device_name]['sweep_indexes_data'][end_key]
                chart_all_sweeps.add_series({
                    'categories': f"='{ws_name}'!$B${data_start}:$B${data_end}",
                    'values': f"='{ws_name}'!$A${data_start}:$A${data_end}",
                    'line': {'width': 1.5}, 'marker': {'type': 'none'},  # No markers
                    'name': f"{ws_name}",
                })

        # Set other chart properties as needed
        chart_all_sweeps.set_title(
            {'name': f"IV plot{name_suffix}", 'name_font': {'size': 14, 'italic': False,
                                                            'bold': False, 'name': 'Calibri (Body)'}})
        chart_all_sweeps.set_x_axis({
            'name': 'V, V',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_tick_mark': 'cross',
            'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
        })
        chart_all_sweeps.set_legend({'none': False})
        chart_all_sweeps.set_y_axis({
            'name': 'J, mA/cm²',
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
            'major_tick_mark': 'outside',
        })
        chart_all_sweeps.set_chartarea({'border': {'none': True}})
        chart_all_sweeps.set_size({'x_scale': self.settings['all_in_one_chart_x_scale'],
                                   'y_scale': self.settings['all_in_one_chart_y_scale']})

        return chart_all_sweeps

    def plot_aging(self, device_name, sweep, param, param_column, data_start, data_end, shaded_error_bar=False,
                   value_type_shift=None, row=None):
        max_value = self.timeline_df.iloc[:, 0].max()
        next_rounded_value = custom_round(max_value)
        major_unit = 500
        minor_unit = 100
        name_suffix = f"{device_name} {param} {sweep}"
        chart_type = 'area' if shaded_error_bar else 'scatter'
        chart = self.workbook.add_chart({'type': chart_type})
        categories = f"='Aging'!$A$2:$A${self.timeline_df.shape[0] + 1}"
        categories_dates = f"='Aging'!$A${self.timeline_df.shape[0] + 3}:$A${self.timeline_df.shape[0] * 2 + 1 * 2}"

        if not shaded_error_bar:
            chart.add_series({
                'categories': categories,
                'values': f"='Aging'!${param_column}${data_start}:${param_column}${data_end}",
                'line': {'width': 1.5, 'color': 'black'},
                'marker': {
                    'type': 'circle',
                    'size': 5,
                    'border': {'color': 'black'},
                    'fill': {'color': 'white'}}
            })
            chart.set_x_axis({
                'name': 'Time, h',
                'min': 0,
                'max': next_rounded_value,
                'name_font': {'size': 12, 'italic': False, 'bold': False},
                'num_font': {'size': 10},
                'major_tick_mark': 'cross',
                'minor_tick_mark': 'outside',
                'major_gridlines': {'visible': False},
                'minor_gridlines': {'visible': False},
                # 'major_gridlines': {'visible': True, 'line': {'color': 'gray', 'dash_type': 'dash'}},
            })
        if shaded_error_bar:
            chart_scatter = self.workbook.add_chart({'type': 'line'})
            # Add mean as a scatter to a scatter chart
            chart_scatter.add_series({
                'name': f'{param} mean',
                'categories': categories,
                'values': f"='Aging'!${param_column}${data_start}:${param_column}${data_end}",
                'line': {'width': 1.5, 'color': 'black'},
                'marker': {
                    'type': 'circle',
                    'size': 5,
                    'border': {'color': 'black'},
                    'fill': {'color': 'white'}}
            })

            # Add upper bound
            upper_bound_col = row_to_excel_col(row + 2 + value_type_shift * 3)
            chart.add_series({
                'name': f'{param} upper bound',
                'categories': categories_dates,
                'values': f"='Aging'!${upper_bound_col}${data_start}:${upper_bound_col}${data_end}",
                'line': {'none': True},
                'fill': {'color': '#BDD7EE', 'transparency': 25},
            })

            # Add lower bound
            lower_bound_col = row_to_excel_col(row + 2 + value_type_shift * 2)
            chart.add_series({
                'name': f'{param} lower bound',
                'categories': categories_dates,
                'values': f"='Aging'!${lower_bound_col}${data_start}:${lower_bound_col}${data_end}",
                'line': {'none': True},
                'fill': {'color': 'white'},
            })
            chart.set_x_axis({
                'date_axis': True,
                'name': 'Time, h',
                'min': self.base_date,
                # 'max': date(1907, 5, 31),
                'max': self.base_date + timedelta(days=next_rounded_value),
                'major_unit': major_unit,
                'major_unit_type': 'days',
                'minor_unit': minor_unit,
                'minor_unit_type': 'days',
                'name_font': {'size': 12, 'italic': False, 'bold': False},
                'num_font': {'size': 10},
                # 'num_format': 'dd/mm/yyyy',
                'num_format': 0,
                'major_tick_mark': 'cross',
                'minor_tick_mark': 'outside',
                'major_gridlines': {'visible': False},
                'minor_gridlines': {'visible': False},

            })
            chart.combine(chart_scatter)
        chart.set_title({
            'name': name_suffix,
            'name_font': {'size': 14, 'italic': False, 'bold': False, 'name': 'Calibri (Body)'},
        })
        chart.set_legend({'none': True})
        chart.set_y_axis({
            'name': param,
            'name_font': {'size': 12, 'italic': False, 'bold': False},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': False},
            'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.settings['chart_x_scale'],
                        'y_scale': self.settings['chart_y_scale']})

        return chart
