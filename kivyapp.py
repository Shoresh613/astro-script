from kivy.app import App
from kivy.lang import Builder
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

# Import your custom module if it's being used for house system values or any other function
import astro_script

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen

# This whole commented section was for trying to build the GUI using Material Design Kivy and a separate .kv file,
# but it only showed a black window, so reverted back to something that at least shows something.

# Checking of OpenGL was the problem, as my computer doesn't support hardware acceleration in WSL2.
# import os
# os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# class WindowManager(ScreenManager):
#     pass

# class Home(Screen):
#     pass

# class MyApp(MDApp):
#     def build(self):
#         self.theme_cls.primary_palette = "Blue"
#         sm = WindowManager()
#         sm.add_widget(Home(name='home'))
#         return sm

#     def show_house_system_menu(self):
#         menu_items = [{"text": hs} for hs in astro_script.HOUSE_SYSTEMS.keys()]
#         self.house_system_menu = MDDropdownMenu(
#             caller=self.root.ids.house_system_field,
#             items=menu_items,
#             width_mult=4,
#             callback=self.set_house_system
#         )
#         self.house_system_menu.open()

#     def set_house_system(self, menu_item):
#         self.root.ids.house_system_field.text = menu_item.text
#         self.house_system_menu.dismiss()

# if __name__=="__main__":
#     MyApp().run()


class AstroApp(App):
    def build(self):
        layout = FloatLayout()

        # Background Image
        bg_image = Image(source='AstroScript_background.webp', allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
        layout.add_widget(bg_image)

        # Timezone Spinner
        timezone_label = Label(text='Select Timezone:', size_hint=(None, None), size=(200, 30), pos_hint={'x': 0.1, 'top': 0.9})
        self.spinner_tz = Spinner(
            text='Europe/Stockholm',
            values=('Europe/Stockholm', 'UTC', 'US/Eastern', 'Asia/Tokyo'),
            size_hint=(None, None),
            size=(200, 44),
            pos_hint={'x': 0.1, 'top': 0.85}
        )
        layout.add_widget(timezone_label)
        layout.add_widget(self.spinner_tz)

        # Minor Aspects Checkbox
        minor_aspects_label = Label(text='Include Minor Aspects:', size_hint=(None, None), size=(200, 30), pos_hint={'x': 0.1, 'top': 0.8})
        self.checkbox_minor_aspects = CheckBox(active=False, size_hint=(None, None), size=(50, 30), pos_hint={'x': 0.35, 'top': 0.8})
        layout.add_widget(minor_aspects_label)
        layout.add_widget(self.checkbox_minor_aspects)

        # House System Spinner
        house_system_label = Label(text='Select House System:', size_hint=(None, None), size=(200, 30), pos_hint={'x': 0.1, 'top': 0.75})
        self.spinner_house_system = Spinner(
            text='Placidus',
            values=tuple(astro_script.HOUSE_SYSTEMS.keys()),
            size_hint=(None, None),
            size=(200, 44),
            pos_hint={'x': 0.1, 'top': 0.7}
        )
        layout.add_widget(house_system_label)
        layout.add_widget(self.spinner_house_system)

        # Imprecise Aspects Radio Buttons
        imprecise_aspects_label = Label(text='Imprecise Aspects:', size_hint=(None, None), size=(200, 30), pos_hint={'x': 0.1, 'top': 0.65})
        layout.add_widget(imprecise_aspects_label)
        self.radio_imprecise_aspects_off = CheckBox(group='imprecise_aspects', active=True, size_hint=(None, None), size=(50, 30), pos_hint={'x': 0.35, 'top': 0.65})
        self.radio_imprecise_aspects_warn = CheckBox(group='imprecise_aspects', active=False, size_hint=(None, None), size=(50, 30), pos_hint={'x': 0.45, 'top': 0.65})
        off_label = Label(text='Off', size_hint=(None, None), size=(50, 30), pos_hint={'x': 0.35, 'top': 0.6})
        warn_label = Label(text='Warn', size_hint=(None, None), size=(50, 30), pos_hint={'x': 0.45, 'top': 0.6})
        layout.add_widget(self.radio_imprecise_aspects_off)
        layout.add_widget(self.radio_imprecise_aspects_warn)
        layout.add_widget(off_label)
        layout.add_widget(warn_label)

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
        # Collect inputs from the GUI elements
        name = self.date_input.text  # Assuming this should be the name; adjust as necessary
        date = self.date_input.text
        location = self.location_input.text
        latitude = None  # Assuming you have a method or input to set this
        longitude = None  # Assuming you have a method or input to set this
        timezone = self.spinner_tz.text  # Get the selected item from the spinner
        print(f"###################{timezone}####################")
        place = None  # Assuming you have a method or input to set this
        imprecise_aspects = 'warn' if self.radio_imprecise_aspects_warn.active else 'off'
        minor_aspects = self.checkbox_minor_aspects.active  # This will be True or False, convert if needed
        orb = None  # Assuming you have a method or input to set this
        degree_in_minutes = None  # Assuming you have a method or input to set this
        all_stars = None  # Assuming you have a method or input to set this
        house_system = self.spinner_house_system.text  # Get the selected item from the spinner
        hide_planetary_positions = None  # Assuming you have a method or input to set this
        hide_planetary_aspects = None  # Assuming you have a method or input to set this
        hide_fixed_star_aspects = None  # Assuming you have a method or input to set this

        # Now pass these collected values to your astro_script function
        # Adjust the function call based on actual parameters it needs
        results = astro_script.called_by_gui(name, date, location, latitude, longitude, timezone, place, 
                                            imprecise_aspects, minor_aspects, orb, degree_in_minutes, 
                                            all_stars, house_system, hide_planetary_positions, 
                                            hide_planetary_aspects, hide_fixed_star_aspects)

        # Format and display results
        result = f"Calculations for {date} at {location}\n\n"
        result += f"More details: {results}"
        self.results_input.text = result

if __name__ == '__main__':
    AstroApp().run()
