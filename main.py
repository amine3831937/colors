import json
import os
import requests
import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex

# Fetch dye data from GitHub live
def load_substances():
    try:
        url = f"https://amine3831937.github.io/numbers/substances.json?v={int(time.time())}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to load substances from server: {e}")
        return {}

substances = load_substances()

# Width options per fabric type
width_options = {
    'Doppio Raso': ('3mm', '6mm', '8mm', '10mm', '16mm', '25mm', '40mm', '55mm'),
    'Gros Grain': ('3mm', '8mm', '16mm', '25mm', '55mm'),
    'Cotone': ('3mm', '7mm', '15mm', '25mm', '40mm'),
    'Taffeta': ('6mm', '10mm', '16mm', '25mm', '40mm'),
    'Cristal': ('4mm', '8mm', '16mm', '25mm', '40mm', '60mm'),
    'Spigato': ('3mm', '8mm', '16mm', '30mm', '60mm'),
    'Coda': ()
}

class GreenOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = get_color_from_hex("#222831")
        self.color = (1, 1, 1, 1)

class DyeCalculator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.history = []

        self.color_input = TextInput(
            hint_text='Colore',
            size_hint=(1, 0.9),
            input_filter='int',
            halign='center',
            font_size=85,
            padding=(10, 70),
            multiline=False,
            background_normal='',
            background_color=get_color_from_hex("#222831"),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(1, 1, 1, 1)
        )

        self.tissue_spinner = Spinner(
            text='Nastro',
            values=tuple(width_options.keys()),
            option_cls=GreenOption,
            background_normal='',
            font_size=85,
            background_color=get_color_from_hex("#393E46"),
            color=(1, 1, 1, 1)
        )
        self.tissue_spinner.bind(text=self.update_widths)

        self.width_input = Spinner(
            text='Misura',
            values=(),
            background_normal='',
            font_size=85,
            background_color=get_color_from_hex("#00ADB5"),
            color=get_color_from_hex("#000000")
        )

        self.liters_input = TextInput(
            hint_text='Litri',
            input_filter='int',
            size_hint=(1, 0.9),
            halign='center',
            font_size=85,
            padding=(10, 70),
            multiline=False,
            background_normal='',
            background_color=get_color_from_hex("#000000"),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=get_color_from_hex("#00ADB5")
        )

        self.percent_input = TextInput(
            hint_text='Aggiungere %',
            size_hint=(1, 0.5),
            input_filter='int',
            halign='center',
            font_size=45,
            padding=(10, 40),
            multiline=False,
            background_normal='',
            background_color=get_color_from_hex("#222831"),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(1, 1, 1, 1)
        )

        self.result_label = Label(
            text='Risultato',
            size_hint=(1, 2.3),
            font_size=75
        )

        # Buttons
        calc_reset_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.5))
        calc_btn = Button(
            text='Calcolare',
            size_hint=(0.5, 1),
            on_press=self.calculate
        )
        reset_btn = Button(
            text='Reset',
            size_hint=(0.5, 1),
            on_press=self.reset_fields
        )
        calc_reset_layout.add_widget(calc_btn)
        calc_reset_layout.add_widget(reset_btn)

        history_clear_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.5))
        history_btn = Button(
            text='Cronologia',
            size_hint=(0.5, 1),
            on_press=self.show_history
        )
        clear_history_btn = Button(
            text='Cancella Cronologia',
            size_hint=(0.5, 1),
            on_press=self.clear_history
        )
        history_clear_layout.add_widget(history_btn)
        history_clear_layout.add_widget(clear_history_btn)

        # Add widgets
        self.add_widget(self.color_input)
        self.add_widget(self.tissue_spinner)
        self.add_widget(self.width_input)
        self.add_widget(self.liters_input)
        self.add_widget(self.percent_input)
        self.add_widget(self.result_label)
        self.add_widget(calc_reset_layout)
        self.add_widget(history_clear_layout)

    def update_widths(self, spinner, text):
        self.width_input.values = width_options.get(text, ())
        self.width_input.text = 'Misura'

    def reset_fields(self, instance):
        self.color_input.text = ''
        self.liters_input.text = ''
        self.percent_input.text = ''
        self.tissue_spinner.text = 'Nastro'
        self.width_input.text = 'Misura'
        self.result_label.text = 'Risultato'

    def format_result(self, results):
        lines = [f"{k:<8}:   {v:.2f}" for k, v in results.items()]
        return "\n".join(lines)

    def calculate(self, instance):
        try:
            color_id = self.color_input.text.strip()
            tissue = self.tissue_spinner.text
            width = self.width_input.text
            liters = int(self.liters_input.text.strip())
            percent = self.percent_input.text.strip()
            add_percent = int(percent) if percent else 0

            if not all([color_id, tissue, width]):
                self.result_label.text = "Completa tutti i campi."
                return

            color_data = substances.get(color_id, {})
            tissue_data = color_data.get(tissue, {})
            recipe = tissue_data.get(width)

            if not recipe:
                self.result_label.text = "Dati non trovati."
                return

            results = {}
            for sub, amount in recipe.items():
                base_total = amount * liters
                final_total = base_total * (1 + add_percent / 100)
                results[sub] = final_total

            result_text = self.format_result(results)
            self.result_label.text = result_text

            # Add operation info to history
            history_entry = f" Col {color_id} , {tissue} {width} , {liters} L , {percent}% :\n"
            for sub, value in results.items():
                history_entry += f"   {sub}: {value:.2f} \n"

            self.history.append(history_entry)

        except Exception as e:
            self.result_label.text = f"Errore: {e}"

    def show_history(self, instance):
        history_content = "\n".join(self.history) if self.history else "Nessuna operazione salvata."
        history_label = Label(text=history_content, size_hint_y=None)
        history_label.bind(texture_size=history_label.setter('size'))

        scrollview = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scrollview.add_widget(history_label)

        popup = Popup(title='Cronologia Operazioni',
                      content=scrollview,
                      size_hint=(0.8, 0.8))
        popup.open()

    def clear_history(self, instance):
        self.history = []

class DyeApp(App):
    def build(self):
        return DyeCalculator()

if __name__ == '__main__':
    DyeApp().run()
