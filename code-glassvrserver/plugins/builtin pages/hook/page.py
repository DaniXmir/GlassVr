#hooks page!
#made this cuz for some reason if you connect 4 controllers to steamvr you cant change there roles

#TODO: add hook level offsets

from PyQt6.QtWidgets import QWidget, QVBoxLayout

import elements as el
import settings as se

title = "hooks"
priority = 80

_hooks = None

_row_widgets = {}
_hook_group_widget = None
_add_button_widget = None

def _make_default_entry():
    return {
        "serial": "",
        "disable": False,
        "model visible": True,
        "override tracking serial": "",
        "override role": "pass",
    }

def _save():
    se.update_setting("hook overrides", _hooks)

def _make_delete(entry):
    def delete():
        _hooks.remove(entry)
        _save()
        _sync_rows()
    return delete

def _sync_rows():
    current_ids = set()
    order = []

    for entry in _hooks:
        eid = id(entry)
        current_ids.add(eid)

        row = _row_widgets.get(eid)
        if row is None:
            row = el.hook({
                "entry": entry,
                "on_change": _save,
                "on_delete": _make_delete(entry),
            })
            _row_widgets[eid] = row

        order.append(row)

    stale_ids = [eid for eid in _row_widgets if eid not in current_ids]
    for eid in stale_ids:
        widget = _row_widgets.pop(eid)
        widget.setParent(None)
        widget.deleteLater()

    el.reorder_group({
        "widget": _hook_group_widget,
        "order": order,
        "last": _add_button_widget,
    })


def _add_hook():
    _hooks.append(_make_default_entry())
    _save()
    _sync_rows()


def tab() -> QWidget:
    global _hooks, _hook_group_widget, _add_button_widget

    _hooks = se.get_settings().get("hook overrides", [])

    tab_main = QWidget()
    layout_main = QVBoxLayout(tab_main)

    l = el.label({"text" : "this page is for modifying the behavior of other drivers"})
    
    label_g = el.group({
        "text": "warning",
        "box": "v",
        "arr": [l],
        "tooltip": "kinda advance!!!"
    })
    layout_main.addWidget(label_g,stretch=1)

    _hook_group_widget = el.group({
        "text": "hooks",
        "box": "v",
        "arr": [],
        "tooltip": "hooks"
    })
    layout_main.addWidget(_hook_group_widget,stretch=10)

    _add_button_widget = el.button({
        "text": "add hook",
        "func": _add_hook,
    })

    _sync_rows()

    return el.scroll({"widget": tab_main})