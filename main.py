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
from kivy.graphics import * # Not needed unless the darker transparent rectangle around the gridlayout starts working

import astro_script
import pytz
import sqlite3


# def read_saved_names(filename='saved_events.json'):
#     """
#     Reads a file containing a dictionary of saved events and returns a list of event names.

#     Args:
#     filename (str): The path to the file containing the saved events.

#     Returns:
#     list: A list of names of saved events.
#     """
#     try:
#         with open(filename, 'r') as file:
#             # Load the dictionary from the file
#             events_dict = json.load(file)
#             # Return the list of keys, which are the names of the events
#             return list(events_dict.keys())
#     except FileNotFoundError:
#         # If the file does not exist, return an empty list
#         print(f"No file found named '{filename}'. Returning an empty list.")
#         return []
#     except json.JSONDecodeError:
#         # Handle cases where the file content is not valid JSON
#         print(f"Error decoding JSON from file '{filename}'. Check file content.")
#         return []
#     except Exception as e:
#         # General exception handling, useful for debugging
#         print(f"An unexpected error occurred: {e}")
#         return []

def read_saved_names(db_filename='events.db'):
    """
    Reads the names of saved events from a SQLite database and returns a list of event names.

    Args:
    db_filename (str): The path to the SQLite database file.

    Returns:
    list: A list of names of saved events.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        
        # Execute a query to retrieve the names of the events
        cursor.execute("SELECT name FROM events")
        rows = cursor.fetchall()
        
        # Extract the names from the query result
        names = [row[0] for row in rows]
        
        # Close the database connection
        conn.close()
        
        return names
    except sqlite3.OperationalError as e:
        # Handle operational errors such as missing tables or database files
        print(f"Database error: {e}")
        return []
    except Exception as e:
        # General exception handling, useful for debugging
        print(f"An unexpected error occurred: {e}")
        return []

class InputScreen(Screen):
    def __init__(self, **kwargs):
        super(InputScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()

        # Background Image
        bg_image = Image(source='AstroScript_background.webp', allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
        self.layout.add_widget(bg_image)

        # Create a background box for the form with a semi-transparent overlay *STILL NOT WORKING*
        background_box = FloatLayout(size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.6})
        with background_box.canvas:
            Color(0, 0, 0, 0.5)  # Black color with 50% opacity
            self.rect = Rectangle(size=background_box.size, pos=background_box.pos)
        
        # Update rectangle position and size on updates *TIED TO THE ABOVE NOT WORKING DARK RECTANGLE
        background_box.bind(pos=self.update_rect, size=self.update_rect)

        # A general layout to contain all elements
        general_layout = GridLayout(cols=1, rows=4, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5}, row_default_height=dp(40), width=self.width)

        # Create a Grid Layout for the form elements
        form_layout = GridLayout(cols=2, rows=9, spacing=10, size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.6}, row_default_height=dp(40), width=self.width)

        # Sub GridLayout for Name Input and Spinner (occupying row 0)
        name_sublayout = GridLayout(cols=4, size_hint=(0.8, None), height=dp(40), pos_hint={'center_x': 0.5, 'y': 0.9})
        general_layout.add_widget(name_sublayout)
        general_layout.add_widget(form_layout)

        # Name input
        name_sublayout.add_widget(Label(text='Name:', halign='right'))
        self.name_input = TextInput(multiline=False, size_hint_x=0.9)
        name_sublayout.add_widget(self.name_input)

        # Name Spinner
        name_sublayout.add_widget(Label(text='Saved Names:', halign='right'))
        self.spinner_name = Spinner(text='', values=read_saved_names(), size_hint_x=0.5)
        name_sublayout.add_widget(self.spinner_name)
                
        # Date and Location Inputs in the same row
        form_layout.add_widget(Label(text='Date:', halign='right'))
        self.date_input = TextInput(multiline=False, hint_text='YYYY-MM-DD hh:mm', size_hint_x=0.5)
        form_layout.add_widget(self.date_input)

        form_layout.add_widget(Label(text='Location:', halign='right'))
        self.location_input = TextInput(multiline=False, hint_text='City, Country', size_hint_x=0.5)
        form_layout.add_widget(self.location_input)

        # Timezone Spinner
        form_layout.add_widget(Label(text='Select Timezone:', halign='right'))
        # self.spinner_tz = Spinner(text='Europe/Stockholm', values=read_time_zones('./timezones.txt'), size_hint_x=0.5)
        self.spinner_tz = Spinner(text='Europe/Stockholm', values=pytz.all_timezones, size_hint_x=0.5)
        form_layout.add_widget(self.spinner_tz)

        # House System Spinner
        form_layout.add_widget(Label(text='Select House System:', halign='right'))
        self.spinner_house_system = Spinner(text='Placidus', values=astro_script.HOUSE_SYSTEMS, size_hint_x=0.5)
        form_layout.add_widget(self.spinner_house_system)

        # Orb size
        form_layout.add_widget(Label(text='Orb size:', halign='right'))
        self.orb_input = TextInput(multiline=False, hint_text='1', size_hint_x=0.5)
        form_layout.add_widget(self.orb_input)

        # Include Minor Aspects Checkbox
        form_layout.add_widget(Label(text='Minor Aspects:', halign='right'))
        self.checkbox_minor_aspects = CheckBox(size_hint_x=None, width=200)
        form_layout.add_widget(self.checkbox_minor_aspects)

        # Imprecise Aspects Checkboxes
        form_layout.add_widget(Label(text='Imprecise Aspects:', halign='right'))
        aspects_layout = GridLayout(cols=2, size_hint_x=None, width=200)
        self.radio_imprecise_aspects_warn = CheckBox(group='imprecise_aspects', active=True)
        aspects_layout.add_widget(self.radio_imprecise_aspects_warn)
        aspects_layout.add_widget(Label(text='Warn'))
        self.radio_imprecise_aspects_off = CheckBox(group='imprecise_aspects', active=False)
        aspects_layout.add_widget(self.radio_imprecise_aspects_off)
        aspects_layout.add_widget(Label(text='Off'))
        form_layout.add_widget(aspects_layout)

        # Add the form layout to the main layout
        # self.layout.add_widget(form_layout)

        # Calculate Button
        general_layout.calc_button = Button(text='Calculate', size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5, 'y': 0.1})
        general_layout.calc_button.bind(on_press=self.on_button_press)
        general_layout.add_widget(general_layout.calc_button)
        
        # Set next properties after creating the TextInput instances
        self.date_input.next = self.location_input
        self.location_input.next = self.spinner_tz

        # Add the complete layout to the screen
        self.layout.add_widget(general_layout)
        self.add_widget(self.layout)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_button_press(self, instance):
        # Code to collect data, call processing functions, and manage screen transition
        self.manager.current = 'results_screen'

        # Collect inputs from the GUI elements
        if self.name_input.text:
            name = self.name_input.text 
        if self.spinner_name.text:  # Sets the name to the one in the spinner if selected
            name = self.spinner_name.text 
        date = self.date_input.text
        location = self.location_input.text
        latitude = None  # Assuming you have a method or input to set this
        longitude = None  # Assuming you have a method or input to set this
        timezone = self.spinner_tz.text  # Get the selected item from the spinner
        place = None  # Assuming you have a method or input to set this
        imprecise_aspects = 'warn' if self.radio_imprecise_aspects_warn.active else 'off'
        minor_aspects = "true" if self.checkbox_minor_aspects.active else "false"
        orb = self.orb_input.text if self.orb_input.text else 1 # Default to 1
        degree_in_minutes = None  # Assuming you have a method or input to set this
        all_stars = None  # Assuming you have a method or input to set this
        house_system = self.spinner_house_system.text  # Get the selected item from the spinner
        house_cusps = None  # Not yet implemented in GUI
        hide_planetary_positions = None  # Assuming you have a method or input to set this
        hide_planetary_aspects = None  # Assuming you have a method or input to set this
        hide_fixed_star_aspects = None  # Assuming you have a method or input to set this
        hide_asteroid_aspects = None  # Assuming you have a method or input to set this

        # Now pass these collected values to your astro_script function
        # Adjust the function call based on actual parameters it needs
        results = astro_script.called_by_gui(name, date, location, latitude, longitude, timezone, None, place, # change 'False' to value of davison when implemented 
                                            imprecise_aspects, minor_aspects, False, False, orb, degree_in_minutes, 'true', # change'true' to value of moon node selection when implemented
                                            all_stars, house_system, house_cusps, hide_planetary_positions, 
                                            hide_planetary_aspects, hide_fixed_star_aspects, hide_asteroid_aspects, None, False, None, False, "return_text", None) # change 'False' to value of transits or synastry when implemented, second None is guid

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
            font_name='fonts/RobotoMono-Regular.ttf',
            font_size='10sp', 
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0, 0, 0.5, 1),  # Dark blue background color
            foreground_color=(1, 1, 1, 1),  # White text color
            multiline=True,
      )
        scroll_view = ScrollView(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        scroll_view.add_widget(self.results_input)
        self.layout.add_widget(scroll_view)

        back_button = Button(
            text='Back',
            size_hint=(0.1, 0.1), 
            pos_hint={'center_x': 0.9, 'y': 0.02}
        )
        back_button.bind(on_release=self.go_back)
        self.layout.add_widget(back_button)

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
