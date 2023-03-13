'''
# PyKBD / os-HID (onscreen HID)

#### pywebview renderers:
 * edgechromium - Windows only
 * gtk - Linux
 * qt - too slow startup to be usable

#### keyboard/mouse backends
  * pynput - Windows (works better), Linux (x11, mouse doesnt work)
  * keyboard, mouse - Linux (x11/Wayland support), Windows (wrong key mapping)
  
#### TESTED SYSTEMS:
 * Windows 10 - [edgechromium, pynput]; mouse pointer is hidden when touch active (required drawing it); transparency doesnt work
 * Linux Mint + Cinnamon - [gtk, keyboard+mouse]; touchpad doesnt work
 * Raspbian + LXDE - [gtk, keyboard+mouse]; touchpad doesnt work
 * Raspbian + Sway - [gtk, keyboard+mouse]; window is auto focused on touch -> keybord doesnt work; touchpad doesnt work

#### USEFUL LINKS:
    <‎‏‎‏‭‮https://kbdlayout.info/kbdusx/virtualkeys>
    <https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes>
    <https://www.compart.com/en/unicode/>

#### CALL ORDER:
    touch button key is pressed -> javascript.ontouchstartend -> api.keyupdown -> KEYS.keyupdown[makes decisions + asks] -> KBD_BACKEND

#### TODOs:
    * [BUG] Windows with CS layout set - 3 keys are swaped
    * custom layout should be exportable (-> *.klc/*.* system layout config file)
    * add dead keys [only for CUSTOM_LAYOUT + defined as "\ˇ"]: pynput - use its functionality; keyboard - on dead key press setup temporary overrides for characters which are compatible
    * remove supress because its not compatible with Linux
    * mouse second=fake pointer
    * mobile mode (setting in *.csv)
    * key remap + key mode for modifiers - char or keycode
    * option to choose modifiers source - internal/keyboard backend
'''


KEY_MAPPING_FILE = ".//keys.csv"
KEYBOARD_UI_FILE = ".//ui.html"

FORCE_PYWEBVIEW_RENDERER = "" # gtk/edgechromium/qt(not recomended)/cocoa(untested, not gonna work)
FORCE_KEYBOARD_BACKEND = "" # mouse/pynput
FORCE_MOUSE_BACKEND = ""  # mouse/pynput

PYWEBVIEW_DEBUG = False
FORCE_DISABLE_CUSTOM_LAYOUT = False
FORCE_DISABLE_VISUALIZATION = False
DRAW_MOUSE_POINTER = ""#"<p style='color: rgba(0,255,0, 0.5);'>🢄</p>" # ""=dont; "<html tag>"=do

CAPTURE_HW_KEYBOARD = False  ## [BROKEN !!!, TODO: replace this with input in html] enables/disables hw keyboard callbacks - useful for bt/usb; can possibly override layout


## SETTINGS LOADER ##

import platform

FORCE_PYWEBVIEW_RENDERER.lower()
FORCE_KEYBOARD_BACKEND.lower()
FORCE_MOUSE_BACKEND.lower()

if not FORCE_PYWEBVIEW_RENDERER in ["edgechromium","gtk","qt", "cef","cocoa"]:
    if   platform.system() == "Windows":
        FORCE_PYWEBVIEW_RENDERER = "edgechromium"
    elif platform.system() == "Linux":
        FORCE_PYWEBVIEW_RENDERER = "gtk"
    else:
        print("UNSUPPORTED SYSTEM - THIS APP MOST LIKELY WOULDNT RUN AS EXPECTED")

if not FORCE_KEYBOARD_BACKEND in ["pynput","keyboard","debug"]:
    if   platform.system() == "Windows":
        FORCE_KEYBOARD_BACKEND = "pynput"
    elif platform.system() == "Linux":
        FORCE_KEYBOARD_BACKEND = "keyboard"
    else:
        print("UNSUPPORTED SYSTEM - THIS APP MOST LIKELY WOULDNT RUN AS EXPECTED")
        
if not FORCE_MOUSE_BACKEND in ["pynput","mouse","debug"]:
    if   platform.system() == "Windows":
        FORCE_MOUSE_BACKEND = "pynput"
    elif platform.system() == "Linux":
        FORCE_MOUSE_BACKEND = "mouse"
    else:
        print("UNSUPPORTED SYSTEM - THIS APP MOST LIKELY WOULDNT RUN AS EXPECTED")

#####################


import webview  # MY FORK (mi4code/pywebview)
import time,threading

   
class _KEYS:

    class key:
        '''
        S = shift
        C = caps lock active
        A = altgr/ctrl+alt
        
        (X = use hw key mode) -> modifier is None
        '''
        def __init__ (self, line_from_csv):
            csv = line_from_csv.split(';')
            for i in range(len(csv)): 
                if "；" in csv[i]: 
                    csv[i] = csv[i].replace("；",";") ## csv semicolon workaround (replaced with "Fullwidth Semicolon" U+FF1B)
            self.id = csv[0+1]
            self.layout = {
                '___':csv[3+1],
                'S__':csv[4+1],
                '_C_':csv[5+1],
                '__A':csv[7+1],
                'SC_':csv[6+1],
                'S_A':csv[8+1],
                '_CA':csv[9+1],
                'SCA':csv[10+1],
                "":""
            }
            #mobile_layout [] # normal, capslock, + onhold options + ?? multiple switchable keyboards
            self.code = {
                'scancode':eval(csv[1+1]),
                'virtualkey':eval(csv[2+1])
            }
            
            self.label = csv[16]
            #self.remap = csv[12]
            
            self.hold = csv[13] != ""
            self.hold_till_any_release = csv[14] != ""
            self.loop = csv[15] != ""
            
            
            self.state = False ## Is button pressed?

        def label_ (self):
            if self.label == "":
                return self.layout[KEYS.ModifiersString()]
            else:
                return self.label
                
        ## key control functions should be runned as thread (so loop with sleep can be used)
        
        def _type(self):
            KEYBOARD_BACKEND.key_type(self.layout[KEYS.ModifiersString()]) 
            API.visualize(self.id)
        def _down(self):
            KEYBOARD_BACKEND.key_down(self)
            self.state = True 
            API.visualize()
        def _up(self):
            KEYBOARD_BACKEND.key_up(self)
            self.state = False
            if self.hold_till_any_release != True:
                for k in KEYS.FindMultiple(lambda f: f.hold_till_any_release and f.state): 
                    k._up()
            API.visualize()
        def _toggle(self):
            if self.state:  self._up()
            else:  self._down()
        def _loop(self,interval=12):
            self.loop_handle = True
            self._down()
            time.sleep(interval*2/1000)
            while self.loop_handle:
                threading.Thread(target=self._toggle,args=()).start() # must be called as thread (otherwise too slow)
                time.sleep(interval/1000)
            self._up()
        
        
        def down(self):
            if self.id == "KEY_A_CAPSLOCK": KEYS.capslock = not KEYS.capslock
            
            if self.layout[KEYS.ModifiersString()] != "":
                self._type()
            elif self.hold or self.hold_till_any_release:
                self._toggle()
            elif self.loop:
                threading.Thread(target=self._loop,args=()).start()
            else:
                self._down()
 
        def up(self):

            if self.layout[KEYS.ModifiersString()] != "":
                pass
            elif self.hold or self.hold_till_any_release:
                pass
            elif self.loop:
                self.loop_handle = False
            else:
                self._up()

    

    def __init__ (self):
        file = open(KEY_MAPPING_FILE,"r",encoding="utf-8")
        self.KEYS_ = []
        while not "ID;SCANCODE;VIRTUALKEY;___;S__;_C_;SC_;__A;S_A;_CA;SCA;" in next(file):
            pass
        for aa in file:
            kk = self.key(aa)
            self.KEYS_.append(kk)
        self.mods = ['_','_','_']
        self.capslock = False
    def __call__ (self, id): # shortcut for find by id
        return self.Find(lambda f: f.id == id)
    
    def Find (self, property):
        for k in self.KEYS_:
            if property(k):
                return k
                
        import inspect
        print("KEY '"+ str(inspect.getsourcelines(property)[0]).strip("['\\n']").split(" = ")[1] +"' NOT FOUND")
        
    def FindMultiple (self, property):
        list = []
        for k in self.KEYS_:
            if property(k):
                list.append(k)
        return list
    
    def ModifiersString(self):
        #return KEYBOARD_BACKEND.modifiers()
    
        list = self.FindMultiple(lambda k: k.state == True)
        mods = ['_','_','_']
        
        list = [k.id for k in list]
        
        if FORCE_DISABLE_CUSTOM_LAYOUT: return "" ## there can be force disabled CUSTOM_LAYOUT
        if ( ("KEY_A_CTRL_L" in list or "KEY_A_CTRL_R" in list) ^ ("KEY_A_ALT_L" in list) ) or "KEY_A_CMD_L" in list or "KEY_A_CMD_R" in list: return ""
        
        
        if "KEY_A_SHIFT_L" in list or "KEY_A_SHIFT_R" in list: mods[0]="S"
        if self.capslock: mods[1]="C"
        if "KEY_A_ALT_R" in list or ( ("KEY_A_CTRL_L" in list or "KEY_A_CTRL_R" in list) and ("KEY_A_ALT_L" in list or "KEY_A_ALT_R" in list) ): mods[2]="A"
        
        return "".join(mods)


class _KEYBOARD_BACKEND__template_name_debug__: # ?is write char (unicode char as key) or press key (emulate key)?
    def __init__ (self):
        pass
        
    def modifiers(self): # CURRENTLY NOT USED
        return "___"
        
    def key_down (self, key): # press [HARDWARE KEY]
        print("[key_down]:", key.label_())
    def key_up (self, key): # release [HARDWARE KEY]
        print("[key_up]:", key.label_())
        
    def key_type (self, key): # press and release [UNICODE CHARACTER] (not used as onclick callback) # should obtain character instead of KEY object
        print("[key_type]:", key.label_())

class _KEYBOARD_BACKEND_pynput: ## OK ##  ... BUGS: blocks hw keyboard when CAPTURE_HW_KEYBOARD=True and CUSTOM_LAYOUT=True and doesnt type the alternative layout/key 
    def __init__ (self):
        global pynput
        import pynput
        #global keynput
        self.keynput = pynput.keyboard.Controller()
        
        self.mods = ["_","_","_"]
        self.cmdkeys = 0
        self.listener_start()

    def listener_start (self):
        if not CAPTURE_HW_KEYBOARD: return
        
        def onpress(k):
            #self.listener_stop()
            
            key = KEYS.Find( lambda f: f.code["virtualkey"] == (k.value.vk if type(k) == pynput.keyboard.Key else k.vk) )
            if key == None: return
            print("kbd::", key.id)
            self.listener.supress = False
            API.key_down( key.id )
            self.listener.supress = True
            #api().key_down( KEYS.Find( 
            #    lambda f: f.code["virtualkey"] == (k.value.vk if type(k) == pynput.keyboard.Key else k.vk)
            #    ).id )
            #api().key_down( KEYS.FindByVK( k.value.vk if type(k) == pynput.keyboard.Key else k.vk ).id )
            #    window.evaluate_js('document.querySelector("#'+KEYS.FindByVK( k.value.vk if type(k) == pynput.keyboard.Key else k.vk ).id+'").onmousedown(); console.log("HWd")')
            #self.listener_start()
        def onrelease (k):
            #self.listener_stop()
            key = KEYS.Find( lambda f: f.code["virtualkey"] == (k.value.vk if type(k) == pynput.keyboard.Key else k.vk) )
            if key == None: return
            self.listener.supress = False
            API.key_up( key.id )
            self.listener.supress = True
            #    window.evaluate_js('document.querySelector("#'+KEYS.FindByVK( k.value.vk if type(k) == pynput.keyboard.Key else k.vk ).id+'").onmouseup(); console.log("HWu")')
            #self.listener_start()

        self.listener = pynput.keyboard.Listener(on_press=onpress, on_release=onrelease, suppress=True)
        #print(dir(self.listener))
            
        self.listener.start()
    def listener_stop (self):
        if not CAPTURE_HW_KEYBOARD: return
        self.listener.stop()
    
    def modifiers(self):
        #return KEYS.ModifiersString()
        print ("HW MODIFIERS DETECTION DEPRECATED")
        return "".join(self.mods)

    def key_down (self, key):
        self.listener_stop()
        
        if True:
            if key.id == "KEY_A_SHIFT_L" or key.id == "KEY_A_SHIFT_R":
                self.mods[0]="S"
            if key.id == "KEY_A_CAPSLOCK":
                if self.mods[1]=="_": self.mods[1]="C"
                else: self.mods[1]="_"
            if key.id == "KEY_A_ALT_R":
                self.mods[2]="A"
                
            if key.id in ["KEY_A_CTRL_L","KEY_A_CTRL_R","KEY_A_CMD_L","KEY_A_CMD_R","KEY_A_ALT_L"]:
                self.cmdkeys+=1

        self.keynput.press( pynput.keyboard.KeyCode().from_vk(key.code["virtualkey"]) )
        
        self.listener_start()
    def key_up (self, key):
        self.listener_stop()
        
        if True:
            if key.id == "KEY_A_SHIFT_L" or key.id == "KEY_A_SHIFT_R":
                self.mods[0]="_"
            #if k == "KEY_A_CAPSLOCK":
            #    if self.modifiers[1]=="_": self.modifiers[1]="C"
            #    else: self.modifiers[1]="_"
            if key.id == "KEY_A_ALT_R":
                self.mods[2]="_"
                
            if key.id in ["KEY_A_CTRL_L","KEY_A_CTRL_R","KEY_A_CMD_L","KEY_A_CMD_R","KEY_A_ALT_L"]:
                self.cmdkeys-=1

        self.keynput.release( pynput.keyboard.KeyCode().from_vk(key.code["virtualkey"]) )
        
        self.listener_start()
    
    def key_type (self, char):
        self.listener_stop()
        self.keynput.type(char)
        #_KEYBOARD_BACKEND_pynput_unicode_only().key_tap(self.to_CHAR(key))
        self.listener_start()

class _KEYBOARD_BACKEND_keyboard: ## OK ##  ... BUGS: modiriers doesnt work for CUSTOM_LAYOUT (I expect that suppress=True prevents the interrnal keyboard module handler from detecting keypresses OR it doesnt detect its own emulated keyboard actions); supress cant work on Linux (use remap instead)
    def __init__ (self):
        global keyboard
        import keyboard
        
        self.caps_state = False ## capslock monitoring should work any time SO MODIFIERS CAN BE DETECTED RIGHT AND KEY LABELS CAN BE SET RIGHT + THIS IS ALSO USED FOR SW KBD ONLY MODE
        keyboard.add_hotkey("caps lock", lambda: exec('self.caps_state = not self.caps_state',{"self":self})) # this doesnt supress the key
        
        if CAPTURE_HW_KEYBOARD: ## TODO: dont type for the second time
            keyboard.on_press(lambda ke: API.key_down(KEYS.Find(lambda f: f.code["scancode"] == ke.scan_code).id), suppress=True)
            keyboard.on_release(lambda ke: API.key_up(KEYS.Find(lambda f: f.code["scancode"] == ke.scan_code).id), suppress=True)
    
    def modifiers(self):
        #return KEYS.ModifiersString()
        print ("HW MODIFIERS DETECTION DEPRECATED")
        
        mods = ["_","_","_"]
        
        if keyboard.is_pressed('ctrl') or keyboard.is_pressed('windows'): return # means use hw key even the layout is diffrent (for compatibily with keyboard shortcuts)
        
        if keyboard.is_pressed('shift'): mods[0]="S"
        if self.caps_state: mods[1]="C"
        if keyboard.is_pressed('alt gr'): mods[2]="A"
        #print("kbd mods::", "".join(mods))
        return "".join(mods) # NEW SINCE v0.0.4

    def key_down (self, key):
        keyboard.press(key.code["scancode"]) ## negative number may be virtualkeycode (see https://github.com/boppreh/keyboard/issues/171)
    def key_up (self, key):
        keyboard.release(key.code["scancode"])
        
    def key_type (self, char):
        #code = key.layout[self.modifiers()]
        keyboard.write(char, exact=True) ## exact=True means type as unicode (this is used automaticaly on Windows; this forces it for Linux - since i dont know how will this perform on Linux THIS MAY BE REMOVED SO IT WILL WORK THE RECOMENDED WAY)


class _MOUSE_BACKEND__template_name_debug__:
    def __init__(self):
        pass
    def button (self,index, click_down_up=None): ## IMPORTANT: index - 1-left/2-right/3-middle/4/5
        if click_down_up == None:
            print("[MOUSE CLICK]",index)
            return
        if click_down_up:
            print("[MOUSE DOWN]",index)
            return
        else:
            print("[MOUSE UP]",index)
            return
    def move(self,x,y,relative_absoulte=True):
        if relative_absoulte:
            print("[MOUSE RELATIVE MOVE]", ("+"+str(x)) if x >= 0 else str(x), ("+"+str(y)) if y>= 0 else str(y) )
            return
        else:
            print("[MOUSE ABSOLUTE MOVE]",x,y)
            return

class _MOUSE_BACKEND_pynput:
    def __init__(self):
        global pynput
        import pynput
        self.mousenput = pynput.mouse.Controller()
    def button (self,index, click_down_up=None):
        if   index == 1: index = pynput.mouse.Button.left
        elif index == 2: index = pynput.mouse.Button.right
        elif index == 3: index = pynput.mouse.Button.middle
        elif index == 4: index = pynput.mouse.Button.x1
        elif index == 5: index = pynput.mouse.Button.x2
    
        if click_down_up == None:
            self.mousenput.click(index)
        elif click_down_up:
            self.mousenput.press(index)
        else:
            self.mousenput.release(index)
    def move(self,x,y,relative_absoulte=True):
        if relative_absoulte:
            self.mousenput.move(x,y)
        else:
            self.mousenput.position = (x,y)
    def scroll(self,y=0,x=0):
        self.mousenput.scroll(x, y)

class _MOUSE_BACKEND_mouse:
    def __init__(self):
        global mouse
        import mouse
    
    def button (self,index, click_down_up=None):
        if   index == 1: index = mouse.LEFT
        elif index == 2: index = mouse.RIGHT
        elif index == 3: index = mouse.MIDDLE
        elif index == 4: index = mouse.X
        elif index == 5: index = mouse.X2
    
        if click_down_up == None:
            mouse.click(index)
        elif click_down_up:
            mouse.press(index)
        else:
            mouse.release(index)
    def move(self,x,y,relative_absoulte=True):
        mouse.move(x, y, absolute=not relative_absoulte)
    def scroll(self,y=0,x=0):
        if x != 0: print("x scroll not implemented")
        mouse.wheel(y)


class webview_api:
    def key_down(self,id):
        KEYS(id).down()
        
    def key_up(self,id):
        KEYS(id).up()
        

    def pointer_click(self,index, click_down_up=None):
        MOUSE_BACKEND.button(index, click_down_up)
      
    def pointer_move(self,x,y):
        MOUSE_BACKEND.move(x,y)
       
    def mouse_scroll(self,y=0,x=0):
        MOUSE_BACKEND.scroll(y,x)
        
    
    def visualize(self, id=None):
        if FORCE_DISABLE_VISUALIZATION: return

        for k in KEYS.FindMultiple(lambda f: True):
            if k.state: window.evaluate_js('document.querySelector("#'+k.id+'").className = "pressed_button";')
            else: window.evaluate_js('document.querySelector("#'+k.id+'").className = "";')
            
            if k.label_() == "" or k.label_() == " ": pass# window.evaluate_js('document.querySelector("#'+k.id+'").innerHTML = "'+"&nbsp;"+'";')
            else: 
                if len(k.label_()) <= 3: window.evaluate_js('document.querySelector("#'+k.id+'").innerHTML = "'+k.label_().replace(" ","&nbsp;")+'";')
                else: window.evaluate_js('document.querySelector("#'+k.id+'").innerHTML = "'+k.label_()+'";')
            
        if id is not None:
            window.evaluate_js('document.querySelector("#'+id+'").className = "div_c"; setTimeout(function(){document.querySelector("#'+id+'").className = "";},200)')
     
    def UI_close(self):
        window.destroy()
    def UI_minimize(self):
        window.minimize()
    def UI_settings(self):
        window.create_confirmation_dialog("Currently there is no GUI settings. If you want to learn how to customize this keyboard see github.com/mi4code/onscreen-hid#configuration","NO SETTINGS YET!")
    


KEYS = _KEYS()  
  
if    FORCE_KEYBOARD_BACKEND == "pynput": KEYBOARD_BACKEND = _KEYBOARD_BACKEND_pynput()
elif FORCE_KEYBOARD_BACKEND == "keyboard": KEYBOARD_BACKEND = _KEYBOARD_BACKEND_keyboard()
elif FORCE_KEYBOARD_BACKEND == "debug": KEYBOARD_BACKEND = _KEYBOARD_BACKEND__template_name_debug__()

if    FORCE_MOUSE_BACKEND == "pynput": MOUSE_BACKEND = _MOUSE_BACKEND_pynput()
elif FORCE_MOUSE_BACKEND == "mouse": MOUSE_BACKEND = _MOUSE_BACKEND_mouse()
elif FORCE_MOUSE_BACKEND == "debug": MOUSE_BACKEND = _MOUSE_BACKEND__template_name_debug__()

if DRAW_MOUSE_POINTER != "":
    def ff (run):
        time.sleep(3)
        while True:
            run()
            time.sleep(0.02)

    if FORCE_MOUSE_BACKEND == "mouse":
        #mouse.hook( lambda ee: window_mouse_pointer.move(mouse.get_position()[0]+1,mouse.get_position()[1]+1) )
        run = lambda: window_mouse_pointer.move(mouse.get_position()[0]+1,mouse.get_position()[1]+1)

    elif FORCE_MOUSE_BACKEND == "pynput":
        #pynput.mouse.Listener(on_move=lambda x,y: window_mouse_pointer.move(x+1, y+1)).start()
        run = lambda: window_mouse_pointer.move(pynput.mouse.Controller().position[0]+1,pynput.mouse.Controller().position[1]+1)
    
    threading.Thread(target=ff,args=(run, )).start()

    window_mouse_pointer = webview.create_window('mouse pointer',
        html="<html><head><style>*{padding 0; margin: 0; background-color: rgba(0,0,0,0);}</style></head><body>"+DRAW_MOUSE_POINTER+"</body></html>",  
        x=0,
        y=0,
        width=10,
        height=10,
        min_size=(1, 1),
        resizable=False,
        easy_drag=False,
        on_top=True,
        frameless=True,
        take_focus=False,
        transparent=True
        )



API = webview_api()


window=webview.create_window('pykbd',
    html=open(KEYBOARD_UI_FILE,"r",encoding="utf-8").read(),  
    js_api=API,

    x=0,
    y=webview.screens[0].height-250 -50,
    width=webview.screens[0].width,#1200 (1:3)
    height=250,
    resizable=True,
    on_top=True,
    frameless=True,
    transparent=platform.system()!="Windows",  # causes problems on windows (window troughtclickable)
    
    take_focus=False,
    )
webview.start(func=lambda: API.visualize(), gui=FORCE_PYWEBVIEW_RENDERER, debug=PYWEBVIEW_DEBUG)
