from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform


# Import your custom module if it's being used for house system values or any other function
import astro_script

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.screenmanager import ScreenManager, Screen

# This whole commented section was for trying to build the GUI using Material Design Kivy and a separate .kv file,
# but it only showed a black window, so reverted back to something that at least shows something.

class WindowManager(ScreenManager):
    pass

class Home(Screen):
    pass

class MyApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        sm = WindowManager()
        sm.add_widget(Home(name='home'))
        return sm

    def show_house_system_menu(self):
        menu_items = [{"text": hs} for hs in astro_script.HOUSE_SYSTEMS.keys()]
        self.house_system_menu = MDDropdownMenu(
            caller=self.root.ids.house_system_field,
            items=menu_items,
            width_mult=4,
            callback=self.set_house_system
        )
        self.house_system_menu.open()

    def set_house_system(self, menu_item):
        self.root.ids.house_system_field.text = menu_item.text
        self.house_system_menu.dismiss()

if __name__=="__main__":
    MyApp().run()

