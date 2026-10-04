#example page!
#note: "elements" and "widgets" used interchangeably

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton
import math

import steamvr as svr
import elements as el
import settings as se

import controller_handler as sdl

title = "example"
#determines where it will show in the page bar selector
priority = -1

#button example extra
button_click_count = 0
def increment(num, button_widget):
    global button_click_count
    button_click_count += num

    btn = button_widget.findChild(QPushButton)
    if btn:
        btn.setText(f"you have clicked {button_click_count} times!")

#bindable example extra
bind_click_count = 0
bind_label = None

def increment_bind():
    global bind_click_count
    bind_click_count += 1

    if bind_label:
        lbl = bind_label.findChild(QLabel)
        if lbl:
            lbl.setText(f"you have click your binded button {bind_click_count} time!")

#lineedit extra
initial_lineedit_text = se.get_settings().get("example lineedit", "hello world!")

if initial_lineedit_text:
    lineedit_label = el.label({"text": f"you have typed {initial_lineedit_text}"})
else:
    lineedit_label = el.label({"text": "you didnt type anything :("})

def change_lineedit_label_text(text):
    se.update_setting("example lineedit", text)

    lbl = lineedit_label.findChild(QLabel)
    if lbl:
        if text != "":
            lbl.setText(f"you have typed {text}")
        else:
            lbl.setText(f"you didnt type anything :(")

def tab() -> QWidget:
    global bind_label

    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    #simple elements
    #label
    e_label = el.label(
        {"text" : "hellow ;P this is an example page to teach you how to make your own!"#text
        })
    #button
    e_button = el.button({
        "text" : f"you have clicked {button_click_count} times!",#text
        "enabled" : True,#enabled/disabled
        "func" : lambda: increment(1, e_button),#runs when clicked
        "tooltip" : "click to increment by 1"})#every element can have a tooltip!
    #checkbox
    e_checkbox = el.checkbox({
        "text": "checkbox",
        "default": se.get_settings().get("examble checkbox", False),#set the defualt state, this reads it from settings
        "enabled" : True,#enabled/disabled
        "func": lambda value: se.update_setting("examble checkbox", value),#saves its state to settings
        }
    )
    #spinbox
    e_spinbox = el.spinbox({
        "text": "spinbox (int)",
        "min": -10,#lowest
        "max": 10,#highest
        "default": se.get_settings().get("spinbox (int)", 0),
        "steps": 1,#when scrolling with the mouse wheel
        "func": lambda value: se.update_setting("spinbox (int)", value) #ive use something like "e_spinbox.findChildren(QSpinBox)[0].value()" a lot, plz use the new way
    })
    #double spinbox (same but support floats)
    e_doublespinbox = el.doublespinbox({
        "text": "double spinbox (float)",
        "min": -10,
        "max": 10,
        "default": se.get_settings().get("double spinbox (float)", 0.0),
        "steps": 0.1,
        "func": lambda value: se.update_setting("double spinbox (float)", value)
    })

    #line edit
    e_line = el.lineedit({
        "text": "line edit", 
        "default": initial_lineedit_text,
        "placeholder": "type something!",
        "func": lambda value: change_lineedit_label_text(value),
        "tooltip": "type!"
    })

    #image
    e_image = el.image({
        "path" : "assets/fix anim.gif",
        "filtering" : "near",
        "size" : [256,256],
    })

    #add theme using group() for consistency
    example_g = el.group(
        {
        "text": "example",#title
        "box": "v",#/h vertical/horizontal
        "arr": [e_label,
                e_button,
                e_checkbox,
                e_spinbox, e_doublespinbox,
                e_line, lineedit_label,
                e_image],#widgets
        "tooltip" : "your mouse is on me, plz move it!"#tooltip when hovering
        }
    )
    layout_main.addWidget(example_g)

    #multitype, an easier way to creates a row/column of elements
    e_multi = el.multitype(
        {
            "box": "h",
            "arr": [
                {
                    "type": "spinbox",
                    "text": "X",
                    "min": -999999999,
                    "max": 999999999,
                    "default": se.get_settings().get("example x",0),
                    "steps": 1,
                    "func": lambda value: se.update_setting("example x", value),
                    "tooltip" : "X"
                },
                {
                    "type": "spinbox",
                    "text": "Y",
                    "min": -999999999,
                    "max": 999999999,
                    "default": se.get_settings().get("example y",0),
                    "steps": 1,
                    "func": lambda value: se.update_setting("example y", value),
                    "tooltip" : "Y"
                },
                {
                    "type": "spinbox",
                    "text": "Z",
                    "min": -999999999,
                    "max": 999999999,
                    "default": se.get_settings().get("example z",0),
                    "steps": 1,
                    "func": lambda value: se.update_setting("example z", value),
                    "tooltip" : "Z"
                },
            ],
        }
    )

    #this combo box "pre show" populates with every devies's serial steamvr finds when clicked
    #it also saves the selected one in settings
    serial_combobox = el.combobox({
        "text": "serials combox",
        "default": se.get_settings().get(f"serial-combobox serial", ""),
        "items": list(set([se.get_settings().get(f"serial-combobox serial", "")] + list(svr.get_trackers_dict()))),
        "index change": lambda: se.update_setting(f"serial-combobox serial", serial_combobox.findChildren(QComboBox)[0].currentText()),
        "tooltip":"populates with every devies's serial steamvr finds!",
        "pre show": lambda cb: (
            saved := se.get_settings().get(f"serial-combobox serial", ""),
            val := cb.currentText(), 
            cb.clear(), 
            cb.addItems(list({saved, *svr.get_trackers_dict()}) if saved else list(svr.get_trackers_dict())), 
            cb.setCurrentText(val), 
            None
        )[-1]
    })

    #bindable
    #prefix + action should be a unique combo
    #usualy written like this: w = el.bindable({"prefix" : device, "mapping" : "forward"})
    #see wasd module
    device = "example"#replace by hmd/cl-cr/0tracker-1tracker-etc...
    e_bind = el.bindable({
        "prefix" : device, #prefix
        "mapping" : "click", #action
        "func" : lambda: increment_bind() #func is a callback, it runs every time any of the binded buttons are clicked
    })

    bind_label = el.label({"text": f"you have click your binded button {bind_click_count} time!"})

    example_g = el.group(
        {
            "text": "special",
            "box": "v",
            "arr": [e_multi,
                    serial_combobox,
                    e_bind,
                    bind_label],
            "tooltip" : "tooltips are an artform! DONT SPAWM THEM!"
        }
    )
    layout_main.addWidget(example_g)

    l = el.label({"text" : "advance tooltip, hover to see!"})

    #TODO: add filtering for pixel art
    example_advanve_g = el.group(
        {
            "text": "advance tooltip",
            "box": "v",
            "arr": [l],
            "tooltip" : {
                         "box":"h",
                         "images" : [{
                                    "images": [
                                        {
                                        "text": "first drawing of the charecter Fix",
                                        "by": "DaniXmir",
                                        "filtering" : "near",
                                        "path": "assets/proto fix.png",
                                        "size": [256, 256]
                                        },
                                        {
                                        "text": "Fix but more detailed and animated",
                                        "by": "lower text is for crediting a source",
                                        "filtering" : "near",
                                        "path": "assets/fix anim.gif",
                                        "size": [256, 256]
                                        }
                                    ]}]}
        }
    )
    layout_main.addWidget(example_advanve_g)

    return el.scroll({"widget": tab_main})