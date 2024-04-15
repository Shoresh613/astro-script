import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
import kivy
kivy.require('1.11.1')  # Replace '1.11.1' with your Kivy version
from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text='Hello, Kivy on WSL!')

if __name__ == '__main__':
    TestApp().run()
