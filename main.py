from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen

import astro_script

def read_time_zones(filename):
    """
    Reads a text file with one time zone per line and returns a list of time zones.

    Args:
    filename (str): The path to the file containing the time zones.

    Returns:
    list: A list of time zones read from the file.
    """
    time_zones = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                # Strip any leading/trailing whitespace characters, including newline
                time_zone = line.strip()
                if time_zone:  # This checks if the line is not empty
                    time_zones.append(time_zone)
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return time_zones


class InputScreen(Screen):
    def __init__(self, **kwargs):
        super(InputScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()

        # Background Image
        bg_image = Image(source='AstroScript_background.webp', allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
        self.layout.add_widget(bg_image)

        # Create a Grid Layout for the form elements
        form_layout = GridLayout(cols=2, rows=7, spacing=10, size_hint=(0.8, None), pos_hint={'center_x': 0.5, 'center_y': 0.6}, row_default_height=dp(40), width=self.width)

        # Date and Location Inputs in the same row
        form_layout.add_widget(Label(text='Date:', halign='right'))
        self.date_input = TextInput(multiline=False, hint_text='YYYY-MM-DD hh:mm', size_hint_x=0.5)
        form_layout.add_widget(self.date_input)

        form_layout.add_widget(Label(text='Location:', halign='right'))
        self.location_input = TextInput(multiline=False, hint_text='City, Country', size_hint_x=0.5)
        form_layout.add_widget(self.location_input)

        # Timezone Spinner
        form_layout.add_widget(Label(text='Select Timezone:', halign='right'))
        self.spinner_tz = Spinner(text='Europe/Stockholm', values=read_time_zones('./timezones.txt'), size_hint_x=0.5)
        form_layout.add_widget(self.spinner_tz)

        # Include Minor Aspects Checkbox
        form_layout.add_widget(Label(text='Include Minor Aspects:', halign='right'))
        self.checkbox_minor_aspects = CheckBox(size_hint_x=None, width=200)
        form_layout.add_widget(self.checkbox_minor_aspects)

        # House System Spinner
        form_layout.add_widget(Label(text='Select House System:', halign='right'))
        self.spinner_house_system = Spinner(text='Placidus', values=astro_script.HOUSE_SYSTEMS, size_hint_x=0.5)
        form_layout.add_widget(self.spinner_house_system)

        # Imprecise Aspects Checkboxes
        form_layout.add_widget(Label(text='Imprecise Aspects:', halign='right'))
        aspects_layout = GridLayout(cols=2, size_hint_x=None, width=200)
        self.radio_imprecise_aspects_off = CheckBox(group='imprecise_aspects', active=True)
        aspects_layout.add_widget(self.radio_imprecise_aspects_off)
        aspects_layout.add_widget(Label(text='Off'))
        self.radio_imprecise_aspects_warn = CheckBox(group='imprecise_aspects', active=False)
        aspects_layout.add_widget(self.radio_imprecise_aspects_warn)
        aspects_layout.add_widget(Label(text='Warn'))
        form_layout.add_widget(aspects_layout)

        # Add the form layout to the main layout
        self.layout.add_widget(form_layout)

        # Calculate Button
        self.calc_button = Button(text='Calculate', size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5, 'y': 0.1})
        self.calc_button.bind(on_press=self.on_button_press)
        self.layout.add_widget(self.calc_button)
        
        # Set next properties after creating the TextInput instances
        self.date_input.next = self.location_input
        self.location_input.next = self.spinner_tz

        # Add the complete layout to the screen
        self.add_widget(self.layout)


    def on_button_press(self, instance):
        # Code to collect data, call processing functions, and manage screen transition
        self.manager.current = 'results_screen'

                # Collect inputs from the GUI elements
        name = self.date_input.text  # Assuming this should be the name; adjust as necessary
        date = self.date_input.text
        location = self.location_input.text
        latitude = None  # Assuming you have a method or input to set this
        longitude = None  # Assuming you have a method or input to set this
        timezone = self.spinner_tz.text  # Get the selected item from the spinner
        place = None  # Assuming you have a method or input to set this
        imprecise_aspects = 'warn' if self.radio_imprecise_aspects_warn.active else 'off'
        minor_aspects = "true" if self.checkbox_minor_aspects.active else "false"
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

        # Switch to the ResultsScreen
        self.manager.current = 'results_screen'
        
        # Access the ResultsScreen instance from the ScreenManager and update its results_input
        results_screen = self.manager.get_screen('results_screen')
        results_screen.display_results(results)

class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super(ResultsScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        # Scrollable container for results
        self.results_input = TextInput(
            readonly=True,
            font_name='fonts/RobotoMono-Regular.ttf',  # Replace with the correct path to the font file
            font_size='11sp',  # Adjust the size as needed
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0, 0, 0.5, 1),  # Dark blue background color
            foreground_color=(1, 1, 1, 1),  # White text color
            multiline=True,
      )
        scroll_view = ScrollView(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        scroll_view.add_widget(self.results_input)
        self.layout.add_widget(scroll_view)

        # Back Button
        back_button = Button(
            text='Back',
            size_hint=(0.1, 0.1),  # You can adjust the size as needed
            pos_hint={'center_x': 0.8, 'y': 0.02}  # You can adjust the position as needed
        )
        back_button.bind(on_release=self.go_back)
        self.layout.add_widget(back_button)

        # Adding the layout to the screen
        # self.add_widget(self.layout)

    def display_results(self, results):
        self.results_input.text = results
    
    def go_back(self, instance):
        # This method changes the current screen to the input screen
        self.manager.current = 'input_screen'

class AstroApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(InputScreen(name='input_screen'))
        sm.add_widget(ResultsScreen(name='results_screen'))
        return sm

    def on_start(self):
        if platform == 'android':
            from jnius import autoclass
            # References to the Android classes
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            View = autoclass('android.view.View')
            # Hook the Android onBackPressed event
            PythonActivity.mActivity.onBackPressedListener = self.on_back_pressed

    def on_back_pressed(self):
        # Here you can define what happens when the back button is pressed.
        # Let's say you want to go back to the input screen:
        sm = self.root
        if sm.current_screen.name != 'input_screen':
            sm.current = 'input_screen'
            return True  # To prevent closing the app
        return False  # To allow the app to close
    
if __name__ == '__main__':
    AstroApp().run()
