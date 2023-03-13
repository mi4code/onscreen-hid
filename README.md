# Onscreen HID
Fully customizable onscreen keyboard and touchpad app written in python and HTML.


### Features
 * customizable UI written in HTML
 * full hardware-like keyboard
 * touchpad with basic gestures (tap, double tap, scolling, right click)
 * option to override system keyboard layout
 
### Installation
 * install [pywebview from my fork](https://github.com/mi4code/pywebview) `pip install https://github.com/mi4code/pywebview/archive/window-take_focus.zip`
 * install [pynput](https://github.com/moses-palmer/pynput) or [keyboard](https://github.com/boppreh/keyboard) and [mouse](https://github.com/boppreh/mouse) modules
 * then clone this repo and run the `oshid.py` file
 
### Configuration
 there are 3 places where you can edit something
 * `oshid.py` - [variables on the begining](https://github.com/mi4code/onscreen-hid/blob/master/oshid.py#37)
 * `ui.html` = UI file 
    There are [some CSS variables](https://github.com/mi4code/onscreen-hid/blob/master/ui.html#5) to make basic customization easier.
    If you want custom UI you can build your own (just use same `ids` and callbacks - `window.pywebview.api.key_down(<id>);` `window.pywebview.api.key_up(<id>);`).
 * `keys.csv` = layout/key mapping file
   

### Known bugs and limitations
 * touchpad doesnt work on all systems (some treat touch as mouse so the mouse pointer gets placed to the touch location)
 * dead keys arent currently supported in custom layout mode (as workaround use [Unicode combining diacritical marks](https://www.unicodemap.org/range/7/Combining_Diacritical_Marks/) (U+0301 - U+036F)) 
 * touchpad doesnt support zooming since its not mouse feature


### TODOs
 * settings GUI
 * monitoring caps/num/scroll lock
 * dead keys
 * handwriting/speech to text
 * act as bluetooth/USB HID device (Linux)
 * apply layout to hardware keyboard (Windows -> export to *.klc; Linux -> export to ???)
