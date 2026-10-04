#hmd page!
#TODO: FIX calculate_vr_fov!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
)
import math
import webbrowser
import elements as el
import settings as se
import mirroring

title = "Headset"
priority = 0

misc3 = el.multitype(
    {
        "box": "h",
        "arr": [
            {
                "type": "doublespinbox",
                "text": "FOV",
                "min": -999999999,
                "max": 999999999,
                "default": se.get_settings()["fov"],
                "steps": 0.01,
                "func": lambda: calculate_vr_fov(),
            },
        ],
    }
)

def tab() -> QWidget:
    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    enable_checkbox = el.checkbox(
        {
            "text": "enable hmd",
            "default": se.get_settings()["enable hmd"],
            "func": lambda: se.update_setting(
                "enable hmd", enable_checkbox.findChild(QCheckBox).isChecked()
            ),
        }
    )

    enable_g = el.group(
        {
            "text": "enable",
            "box": "h",
            "arr": [enable_checkbox],
            "tooltip": "enables headset simulation via extended mode!",
        }
    )
    layout_main.addWidget(enable_g)

    modes = el.modes("hmd")
    modes_g = el.group(
        {
            "text": "modes",
            "box": "h",
            "arr": [modes],
            "tooltip": "position and rotation modes of the simulated hmd",
        }
    )
    layout_main.addWidget(modes_g)

    res = el.multitype(
        {
            "box": "h",
            "arr": [
                {
                    "type": "spinbox",
                    "text": "X",
                    "min": 0,
                    "max": 999999999,
                    "default": se.get_settings()["resolution x"],
                    "steps": 1,
                    "func": lambda: se.update_setting(
                        "resolution x", res.findChildren(QSpinBox)[0].value()
                    ),
                },
                {
                    "type": "spinbox",
                    "text": "Y",
                    "min": 0,
                    "max": 999999999,
                    "default": se.get_settings()["resolution y"],
                    "steps": 1,
                    "func": lambda: se.update_setting(
                        "resolution y", res.findChildren(QSpinBox)[1].value()
                    ),
                },
                {
                    "type": "spinbox",
                    "text": "Refresh Rate",
                    "min": 0,
                    "max": 999999999,
                    "default": se.get_settings()["refresh rate"],
                    "steps": 1,
                    "func": lambda: se.update_setting(
                        "refresh rate", res.findChildren(QSpinBox)[2].value()
                    ),
                },
            ],
        }
    )
    res_g = el.group(
        {
            "text": "resolution",
            "box": "h",
            "arr": [res],
            "tooltip": "the resolution and refresh rate of your simulated headset!",
        }
    )
    layout_main.addWidget(res_g)

    misc1 = el.multitype(
        {
            "box": "h",
            "arr": [
                {
                    "type": "checkbox",
                    "text": "Stereoscopic(SBS)",
                    "default": se.get_settings()["stereoscopic"],
                    "func": lambda: se.update_setting(
                        "stereoscopic", misc1.findChildren(QCheckBox)[0].isChecked()
                    ),
                },
                {
                    "type": "checkbox",
                    "text": "Fullscreen",
                    "default": se.get_settings()["fullscreen"],
                    "func": lambda: se.update_setting(
                        "fullscreen", misc1.findChildren(QCheckBox)[1].isChecked()
                    ),
                },
            ],
        }
    )

    misc2 = el.multitype(
        {
            "box": "h",
            "arr": [
                {
                    "type": "doublespinbox",
                    "text": "IPD",
                    "min": -999999999,
                    "max": 999999999,
                    "default": se.get_settings()["ipd"] * 1000,
                    "steps": 1.0,
                    "func": lambda: se.update_setting(
                        "ipd", misc2.findChildren(QDoubleSpinBox)[0].value() * 0.001
                    ),
                },
                {
                    "type": "doublespinbox",
                    "text": "Distance from tracker to eyes",
                    "min": -999999999,
                    "max": 999999999,
                    "default": se.get_settings()["head to eye dist"],
                    "steps": 0.1,
                    "func": lambda: se.update_setting(
                        "head to eye dist",
                        misc2.findChildren(QDoubleSpinBox)[1].value(),
                    ),
                },
            ],
        }
    )

    lenses_m = el.multitype({
        "group": "main",
        "arr": [
            {
                "type": "doublespinbox",
                "text": "tilt angle",
                "min": -999999999,
                "max": 999999999,
                "default": se.get_settings().get("hmd tilt", 0.0),
                "steps": 0.1,
                "func": lambda: se.update_setting("hmd tilt", lenses_m.findChildren(QDoubleSpinBox)[0].value())
            },
            {
                "type": "doublespinbox",
                "text": "canted angle",
                "min": -999999999,
                "max": 999999999,
                "default": se.get_settings().get("canting", 0.0),
                "steps": 0.1,
                "func": lambda: (
                    se.update_setting("canting", lenses_m.findChildren(QDoubleSpinBox)[1].value()),
                    calculate_vr_fov()
                )
            }
        ]
    })

    rgb_red = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "doublespinbox",
                "text": "Red K1",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Red_K1", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Red_K1", rgb_red.findChildren(QDoubleSpinBox)[0].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "Red K2",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Red_K2", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Red_K2", rgb_red.findChildren(QDoubleSpinBox)[1].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "Red K3",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Red_K3", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Red_K3", rgb_red.findChildren(QDoubleSpinBox)[2].value()
                ),
            },
        ],
    })

    rgb_green = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "doublespinbox",
                "text": "Green K1",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Green_K1", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Green_K1", rgb_green.findChildren(QDoubleSpinBox)[0].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "Green K2",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Green_K2", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Green_K2", rgb_green.findChildren(QDoubleSpinBox)[1].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "Green K3",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Green_K3", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Green_K3", rgb_green.findChildren(QDoubleSpinBox)[2].value()
                ),
            },
        ],
    })

    rgb_blue = el.multitype({
        "box": "h",
        "arr": [
            {
                "type": "doublespinbox",
                "text": "Blue K1",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Blue_K1", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Blue_K1", rgb_blue.findChildren(QDoubleSpinBox)[0].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "Blue K2",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Blue_K2", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Blue_K2", rgb_blue.findChildren(QDoubleSpinBox)[1].value()
                ),
            },
            {
                "type": "doublespinbox",
                "text": "Blue K3",
                "min": -999.0,
                "max": 999.0,
                "default": se.get_settings().get("Blue_K3", 0.0),
                "steps": 0.01,
                "func": lambda: se.update_setting(
                    "Blue_K3", rgb_blue.findChildren(QDoubleSpinBox)[2].value()
                ),
            },
        ],
    })

    misc_g = el.group(
        {"text": "misc",
        "box": "v",
        "arr": [misc1, misc2, misc3],
        "tooltip": "misc"}
    )
    layout_main.addWidget(misc_g)

    lenses_g = el.group(
        {
            "text": "lenses",
            "box": "v",
            "arr": [lenses_m],
            "tooltip" : {
                         "box":"h",
                         "images" : [{
                                    "images": [
                                        {
                                        "text": "headset display assembly with tilted displays",
                                        "by": "Mañolo(posted on hadesvr discord)",
                                        "path": "plugins/builtin pages/hmd/Mañolo 20angle.jpg",
                                        "size": [256, 256]
                                        },
                                        {
                                        "text": "valve index canted displays",
                                        "by": "valve(index deep dive - fov)",
                                        "path": "plugins/builtin pages/hmd/IndexBinocular.gif",
                                        "size": [256, 256]
                                        }
                                    ]}]}
        }
    )
    layout_main.addWidget(lenses_g)

    distortion_g = el.group(
        {
            "text": "distortion",
            "box": "v",
            "arr": [rgb_red, rgb_green, rgb_blue],
            "tooltip" : "adjust if youre using traditional lenses like fresnel, not birdbaths"
        }
    )
    layout_main.addWidget(distortion_g)

    layout_main.addWidget(create_streaming())
    layout_main.addWidget(el.offsets("hmd"))

    return el.scroll({"widget": tab_main})

#fov is calculated here
#the driver only reads outer/inner/top/bottom so change them if you want more control
#supports canted displays! (need testing)
def calculate_vr_fov():
    try:
        fov_spinboxes = misc3.findChildren(QDoubleSpinBox)
        if fov_spinboxes:
            se.update_setting("fov", fov_spinboxes[0].value())
    except Exception as e:
        print(f"UI Error: {e}")
        return

    settings = se.get_settings()

    diagonal_fov_deg = min(179.9, float(settings.get("fov", 90.0))) 
    canting_deg = float(settings.get("canting", 0.0))

    width = float(settings.get("resolution x", 1920))
    height = float(settings.get("resolution y", 1080))

    if height <= 0 or width <= 0 or diagonal_fov_deg <= 0:
        return

    aspect = width / height

    diag_rad = math.radians(diagonal_fov_deg)
    tan_half_diag = math.tan(diag_rad / 2.0)

    tan_half_v = tan_half_diag / math.sqrt(aspect ** 2 + 1.0)
    tan_half_h = aspect * tan_half_v

    h_half_fov = math.degrees(math.atan(tan_half_h))
    v_half_fov = math.degrees(math.atan(tan_half_v))

    outer_fov_deg = h_half_fov + canting_deg
    inner_fov_deg = h_half_fov - canting_deg
    
    outer_fov_deg = max(0.1, outer_fov_deg)
    inner_fov_deg = max(0.0, inner_fov_deg) 
    
    top_fov_deg = max(0.1, v_half_fov)
    bottom_fov_deg = max(0.1, v_half_fov)

    se.update_setting("outer", outer_fov_deg)
    se.update_setting("inner", inner_fov_deg)
    se.update_setting("top", top_fov_deg)
    se.update_setting("bottom", bottom_fov_deg)

def create_streaming():
    mirroring.start_mirror_window()
    mirroring.start_mirror_web()

    settings = se.get_settings()

    cb_mirror_win = el.checkbox(
        {
            "text": "mirror to window",
            "default": settings.get("mirror window", False),
            "func": lambda: se.update_setting(
                "mirror window", cb_mirror_win.findChild(QCheckBox).isChecked()
            ),
        }
    )

    cb_win_fullscreen = el.checkbox(
        {
            "text": "start fullscreen",
            "default": settings.get("start mirror window fullscreen", False),
            "func": lambda: se.update_setting(
                "start mirror window fullscreen",
                cb_win_fullscreen.findChild(QCheckBox).isChecked(),
            ),
        }
    )

    sb_monitor_index = el.spinbox(
        {
            "text": "start monitor index",
            "min": 0,
            "max": 999999999,
            "default": settings.get("start mirror window monitor index", 1),
            "steps": 1,
            "func": lambda: se.update_setting(
                "start mirror window monitor index",
                sb_monitor_index.findChild(QSpinBox).value(),
            ),
        }
    )

    window_row = QWidget()
    win_layout = QHBoxLayout(window_row)
    win_layout.setContentsMargins(0, 0, 0, 0)
    win_layout.addWidget(cb_mirror_win)
    win_layout.addWidget(cb_win_fullscreen)
    win_layout.addWidget(sb_monitor_index)

    cb_mirror_web = el.checkbox(
        {
            "text": "mirror to web",
            "default": settings.get("mirror web", False),
            "func": lambda: se.update_setting(
                "mirror web", cb_mirror_web.findChild(QCheckBox).isChecked()
            ),
        }
    )

    sb_web_port = el.spinbox(
        {
            "text": "port",
            "min": 0,
            "max": 999999999,
            "default": settings.get("mirror web port", 9999),
            "steps": 1,
            "func": lambda: se.update_setting(
                "mirror web port", sb_web_port.findChild(QSpinBox).value()
            ),
        }
    )

    sb_web_bitrate = el.spinbox(
        {
            "text": "bitrate",
            "min": 1,
            "max": 100,
            "default": settings.get("mirror web bitrate", 100),
            "steps": 1,
            "func": lambda: se.update_setting(
                "mirror web bitrate", sb_web_bitrate.findChild(QSpinBox).value()
            ),
        }
    )

    dsb_web_scale = el.doublespinbox(
        {
            "text": "res scale",
            "min": 0.1,
            "max": 1.0,
            "default": settings.get("mirror web scale", 1.0),
            "steps": 0.1,
            "func": lambda: se.update_setting(
                "mirror web scale", dsb_web_scale.findChild(QDoubleSpinBox).value()
            ),
        }
    )

    btn_open_stream = el.button(
        {
            "text": "open stream",
            "func": lambda: webbrowser.open(
                f"http://127.0.0.1:{se.get_settings().get('mirror web port', 9999)}"
            ),
        }
    )

    web_row = QWidget()
    web_layout = QHBoxLayout(web_row)
    web_layout.setContentsMargins(0, 0, 0, 0)
    web_layout.addWidget(cb_mirror_web)
    web_layout.addWidget(sb_web_port)
    web_layout.addWidget(sb_web_bitrate)
    web_layout.addWidget(dsb_web_scale)
    web_layout.addWidget(btn_open_stream)

    mirroring_g = el.group(
        {
            "text": "Mirroring",
            "box": "v",
            "arr": [window_row, web_row],
            "tooltip": (
                "(experimental: slow please avoid!!!) mirror to window: pops out the 'headset window' "
                "(alt+enter to fullscreen) mirror to url: streams the 'headset window' to a web page"
                "(lower bitrate/res = faster streaming), you can also use Sunshine + moonlight-web-stream for faster performance"
            ),
        }
    )

    return mirroring_g