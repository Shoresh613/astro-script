from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image

import astro_script

class AstroApp(App):
    def build(self):
        layout = FloatLayout()

        # Background Image
        bg_image = Image(source='AstroScript_background.webp', allow_stretch=True, keep_ratio=False)
        layout.add_widget(bg_image)

        # Date Input
        self.date_input = TextInput(size_hint=(0.8, 0.06), pos_hint={'x': 0.1, 'top': 0.9}, multiline=False, hint_text='YYYY-MM-DD')
        layout.add_widget(self.date_input)

        # Location Input
        self.location_input = TextInput(size_hint=(0.8, 0.06), pos_hint={'x': 0.1, 'top': 0.82}, multiline=False, hint_text='City, Country')
        layout.add_widget(self.location_input)

        # Calculate Button
        self.calc_button = Button(text='Calculate', size_hint=(0.8, 0.08), pos_hint={'x': 0.1, 'top': 0.75})
        self.calc_button.bind(on_press=self.on_button_press)
        layout.add_widget(self.calc_button)

        # Scrollable Results Container
        self.results_input = TextInput(readonly=True, background_color=(1, 1, 1, 0.3), foreground_color=(0, 0, 0, 1), size_hint=(0.8, 0.4), pos_hint={'x': 0.1, 'top': 0.65})
        scroll_view = ScrollView(size_hint=(1, None), size=(200, 200))
        scroll_view.add_widget(self.results_input)
        layout.add_widget(scroll_view)

        return layout

    def on_button_press(self, instance):
        date = self.date_input.text
        location = self.location_input.text
        astro_script.main(f"--date {date}", f"--location {location}")
        result = f"Calculations for {date} at {location}\n\n"
        result += "More details about the astrological calculations can be displayed here..."
        self.results_input.text = result

if __name__ == '__main__':
    AstroApp().run()
