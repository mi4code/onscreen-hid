# Onscreen HID
Fully customizable onscreen keyboard and touchpad app written in python and HTML.


### Features
 * customizable UI written in HTML (see [building custom UI]())
 * full hardware-like keyboard
 * touchpad with basic gestures (tap, double tap, scolling, right click)
 * option to override system keyboard layout
 

### Limitations and known bugs
 * touchpad doesnt work on all systems (some treat touch as mouse so the mouse pointer gets placed to the touch location)
 * dead keys arent currently supported in custom layout mode (as workaround use [Unicode combining diacritical marks](https://www.unicodemap.org/range/7/Combining_Diacritical_Marks/) (U+0301 - U+036F)) 
 * touchpad doesnt support zooming since its not mouse feature
 
## Installation
 * install [pywebview from my fork](https://github.com/mi4code/pywebview) `pip install https://github.com/mi4code/pywebview/archive/window-take_focus.zip`
 * install [pynput](https://github.com/moses-palmer/pynput) or [keyboard](https://github.com/boppreh/keyboard) and [mouse](https://github.com/boppreh/mouse) modules
 * then download this repo and run the *.py file
 
## Configuration
 see variables on the begining of the *.py file
