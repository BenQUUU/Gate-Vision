import asyncio, time
from .gpio_driver import build_relay, read_limit_switch

class GateController:
    def __init__(self, cfg, logger):
        self.cfg = cfg
        self.log = logger
        g = cfg["gate"]
        self.pulse = g.get("pulse_sec", 0.7)
        self.cooldown_after_close = g.get("cooldown_after_close", 8)
        self.opening_timeout = g.get("opening_timeout", 5)
        self.open_auto_close = g.get("open_auto_close", 15)
        self.closing_timeout = g.get("closing_timeout", 10)
        self.grace_sec = g.get("grace_sec", 60)

        self.relay = build_relay(g["relay_pin"], g.get("relay_active_high", False))

        # limit switches optional
        self.use_limit = g.get("use_limit_switch", False)
        self.is_closed = None
        self.is_open = None
        if self.use_limit:
            cpin = g.get("limit_switch_pin_closed")
            opin = g.get("limit_switch_pin_open")
            self.is_closed = read_limit_switch(cpin) if cpin is not None else (lambda: False)
            self.is_open   = read_limit_switch(opin) if opin is not None else (lambda: False)

        self.state = "CLOSED"
        self.gate_inhibit = False
        self.grace_until = {"in": 0.0, "out": 0.0}

    def _now(self): return time.monotonic()

    def cam_muted(self, cam):
        return self._now() < self.grace_until[cam]

    def set_grace(self, cam):
        self.grace_until[cam] = self._now() + self.grace_sec

    async def _pulse(self):
        self.relay.on()
        await asyncio.sleep(self.pulse)
        self.relay.off()

    async def request_open(self, cam, reason, attach=None):
        if self.gate_inhibit or self.cam_muted(cam):
            return False
        self.log.log("request_open", cam=cam, reason=reason, state=self.state)
        self.gate_inhibit = True
        self.set_grace(cam)
        await self._pulse()
        asyncio.create_task(self._track_cycle())
        return True

    async def _track_cycle(self):
        # OPENING
        self.state = "OPENING"
        t0 = self._now()
        if self.use_limit and self.is_open:
            # wait until open limit is hit or timeout
            while (self._now() - t0) < self.opening_timeout and not self.is_open():
                await asyncio.sleep(0.05)
        else:
            await asyncio.sleep(self.opening_timeout)
        self.state = "OPEN"
        self.log.log("gate_state", state=self.state)

        # wait for auto close
        await asyncio.sleep(self.open_auto_close)

        # CLOSING
        self.state = "CLOSING"
        self.log.log("gate_state", state=self.state)
        t1 = self._now()
        if self.use_limit and self.is_closed:
            while (self._now() - t1) < self.closing_timeout and not self.is_closed():
                await asyncio.sleep(0.05)
        else:
            await asyncio.sleep(self.closing_timeout)

        self.state = "CLOSED"
        self.log.log("gate_state", state=self.state)
        await asyncio.sleep(self.cooldown_after_close)
        self.gate_inhibit = False
        self.log.log("gate_inhibit_off")
