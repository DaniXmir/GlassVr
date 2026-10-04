#creates a page for sdl controllers
from PyQt6.QtWidgets import QWidget
import sdl_display

title = "sdl"
priority = 100

def tab() -> QWidget:
    return sdl_display.SDLDisplay()