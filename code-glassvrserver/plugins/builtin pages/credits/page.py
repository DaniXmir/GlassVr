#so lonely here :(

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

import ctypes

import elements as el

title = "Credits"
priority = 999999999

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)
    layout_main.setSpacing(2)

    t = el.label({"text" : "made by DaniXmir!"})
    t.setFixedSize(200, 100)

    b = el.button({
        "icon" : "assets/fix anim.gif",
        "icon_size" : [128,128],
        "filtering" : "nearest",
        "group" : "invis",
        "func" : lambda : func()}
        )
    b.setFixedSize(128, 128)

    fix_g = el.group({
    "text": "fix!",
    "box": "v",
    "alignment" : Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
    "arr": [
        t,
        b
    ],
    "tooltip" : ";P"
    })
    layout_main.addWidget(fix_g,stretch=1)

    g = 'https://github.com/DaniXmir/GlassVr'
    github_l = el.label({
    "text": f"open the project on <a href={g} style='color: #4da6ff;'>github!</a>",
    "tooltip": g
    })

    d = 'https://discord.gg/jyvWdKBpPj'
    discord_l = el.label({
    "text": f"join the <a href={d} style='color: #4da6ff;'>discord!</a>",
    "tooltip": d
    })

    y = 'https://www.youtube.com/@danixmir106'
    youtube_l = el.label({
    "text": f"subscribe on <a href={y} style='color: #4da6ff;'>youtube!</a>",
    "tooltip": y
    })

    links_g = el.group({
    "text": "links!",
    "box": "h",
    "arr": [
        github_l,
        discord_l,
        youtube_l
    ],
    "tooltip" : "plz sub!"
    })
    layout_main.addWidget(links_g)

    return el.scroll({"widget": tab_main, "color group": "g1"})

def func():
    ctypes.windll.user32.MessageBoxW(0, "OUCH!!!!!!!!!!!", ";P", 0)