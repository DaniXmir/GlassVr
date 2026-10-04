#slop2

import copy
import threading
import types

_lock = threading.RLock()
_active_modules = {}
_slot_mapping = {}

def _clone_function(func, globals_dict):
    cloned = types.FunctionType(
        func.__code__, globals_dict, func.__name__, func.__defaults__, func.__closure__
    )
    cloned.__kwdefaults__ = getattr(func, "__kwdefaults__", None)
    cloned.__annotations__ = dict(getattr(func, "__annotations__", {}))
    cloned.__dict__.update(getattr(func, "__dict__", {}))
    cloned.__doc__ = func.__doc__
    cloned.__module__ = globals_dict.get("__name__", func.__module__)
    return cloned

def _create_instance(module, device):
    instance = types.ModuleType(f"{module.__name__}__{device}")
    instance.__dict__.update(module.__dict__)
    instance.__name__ = f"{module.__name__}__{device}"

    for name, value in list(module.__dict__.items()):
        if isinstance(value, (dict, list)):
            try:
                instance.__dict__[name] = copy.deepcopy(value)
            except Exception:
                pass

    for name, value in list(module.__dict__.items()):
        if isinstance(value, types.FunctionType) and value.__globals__ is module.__dict__:
            instance.__dict__[name] = _clone_function(value, instance.__dict__)

    instance.device = device
    return instance

def _make_state(module, device, title, slots):
    instance = _create_instance(module, device)
    stop_event = threading.Event()
    return {
        "instance": instance,
        "thread": None,
        "stop_event": stop_event,
        "slots": set(slots),
        "title": title,
    }

def _start_state(state):
    instance = state["instance"]
    stop_event = state["stop_event"]
    device = instance.device
    title = state["title"]

    def run():
        try:
            instance.device = device
            instance.loop({
                "stop_event": stop_event,
                "device": device,
            })
        except Exception:
            pass

    thread = threading.Thread(
        target=run,
        name=f"GlassVR mode {device}:{title}",
        daemon=True,
    )
    state["thread"] = thread
    thread.start()

def _stop_state(device, title):
    state = _active_modules.pop((device, title), None)
    if state is not None:
        state["stop_event"].set()

def _reconcile_modules_locked(desired):
    normalized = {}
    desired_by_pair = {}

    for (device, mode), module in dict(desired).items():
        if mode not in ("pos", "rot", "input", "skeletal"):
            continue
        if module is None or not hasattr(module, "loop"):
            continue

        title = getattr(module, "title", str(module))
        normalized[(device, mode)] = (title, module)
        desired_by_pair.setdefault((device, title), {"module": module, "slots": set()})
        desired_by_pair[(device, title)]["slots"].add(mode)

    _slot_mapping.clear()
    _slot_mapping.update({key: title for key, (title, _module) in normalized.items()})

    for pair in list(_active_modules):
        if pair not in desired_by_pair:
            _stop_state(*pair)

    for pair, state in list(_active_modules.items()):
        target = desired_by_pair.get(pair)
        if target is not None:
            state["slots"] = set(target["slots"])
            state["instance"].device = pair[0]

    to_start = []
    for (device, title), target in desired_by_pair.items():
        if (device, title) in _active_modules:
            continue

        state = _make_state(
            target["module"],
            device,
            title,
            target["slots"],
        )
        _active_modules[(device, title)] = state
        to_start.append(state)

    return to_start

def reconcile(desired):
    with _lock:
        to_start = _reconcile_modules_locked(desired)

    for state in to_start:
        _start_state(state)

def reconcile_with_modules(desired_slots, modules):
    desired = {}

    for key, title in dict(desired_slots).items():
        device, mode = key
        module = modules.get((device, title))
        if module is not None:
            desired[(device, mode)] = module

    reconcile(desired)

def acquire(module, device, mode):
    if module is None or not hasattr(module, "loop"):
        return

    title = getattr(module, "title", str(module))

    with _lock:
        desired = {}
        for (dev, slot), current_title in _slot_mapping.items():
            if (dev, slot) == (device, mode):
                continue
            state = _active_modules.get((dev, current_title))
            if state is not None:
                desired[(dev, slot)] = state["instance"]
        desired[(device, mode)] = module

    reconcile(desired)

def release(module, device, mode):
    with _lock:
        desired = {}
        for (dev, slot), current_title in _slot_mapping.items():
            if (dev, slot) == (device, mode):
                continue
            state = _active_modules.get((dev, current_title))
            if state is not None:
                desired[(dev, slot)] = state["instance"]

    reconcile(desired)

def get_active_module(device, mode):
    with _lock:
        title = _slot_mapping.get((device, mode))
        if title is None:
            return None

        state = _active_modules.get((device, title))
        return state["instance"] if state is not None else None

def is_running(module, device, mode):
    title = getattr(module, "title", str(module))
    with _lock:
        return _slot_mapping.get((device, mode)) == title

def get_all_active_slots():
    with _lock:
        return dict(_slot_mapping)

def get_active_threads():
    with _lock:
        return {
            key: state["thread"]
            for key, state in _active_modules.items()
            if state["thread"] is not None and state["thread"].is_alive()
        }