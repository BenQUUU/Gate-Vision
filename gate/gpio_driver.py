import time

class DummyRelay:
    def __init__(self, active_high=False):
        self.active_high = active_high
        self.state = False

    def on(self):
        self.state = True
        print("[RELAY] ON")

    def off(self):
        self.state = False
        print("[RELAY] OFF")

def build_relay(pin, active_high=False):
    try:
        from gpiozero import OutputDevice
        dev = OutputDevice(pin, active_high=active_high, initial_value=False)
        class RelayWrap:
            def on(self): dev.on()
            def off(self): dev.off()
        print(f"[GPIO] Using gpiozero on pin {pin}, active_high={active_high}")
        return RelayWrap()
    except Exception as e:
        print(f"[GPIO] gpiozero unavailable, using DummyRelay: {e}")
        return DummyRelay(active_high=active_high)

def read_limit_switch(pin):
    try:
        from gpiozero import Button
        btn = Button(pin, pull_up=True)
        return btn.is_pressed
    except Exception as e:
        print(f"[GPIO] limit switch dummy for pin {pin}: {e}")
        return lambda: False
