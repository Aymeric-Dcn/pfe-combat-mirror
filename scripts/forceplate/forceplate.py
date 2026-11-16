"""PC side of the force plate prototype (NUCLEO-F072RB firmware nucleo_acq).

Commands:
  monitor   print the 4 channels a few times per second (trimming, checks)
  live      live plot of the forces and of the centre of pressure
  record    save the stream to CSV
  tare      store the no-load output of each channel
  step      average one calibration step (known load on one sensor)
  fit       fit force = gain * (V - V0) for each sensor from the steps
  point     average one plate calibration point (known mass at x, y)
  fitplate  correct the 4 gains from the plate points (least squares)

Use --sim instead of --port to try any command without the board.
Requires: pyserial, numpy, matplotlib.
"""

import argparse
import csv
import json
import math
import os
import struct
import sys
import threading
import time
from collections import deque

import numpy as np

SAMPLE_RATE = 2000
BAUD_RATE = 921600
FRAME = struct.Struct("<2sH6HB")
SYNC = b"\xa5\x5a"
N_SENSORS = 4
COP_MIN_FORCE = 20.0           # N, below this the centre of pressure is not computed

MODES = [(1.03, "sensitive"), (0.505, "standard"), (0.103, "high force")]

DEFAULT_CALIB = {
    "positions_mm": [[105, 105], [-105, 105], [105, -105], [-105, -105]],
    "offset_v": None,
    "tare_vref_v": None,
    "gain_n_per_v": None,
    "fit_vref_v": None,
    "plate_correction": [1.0, 1.0, 1.0, 1.0],
}


def mode_name(vref):
    ref, name = min(MODES, key=lambda m: abs(m[0] - vref))
    return name if abs(ref - vref) < 0.15 else "unknown: board not connected?"


# ---------------------------------------------------------------- input


class SimulatedPort:
    """Produces frames like the board: after 2.5 s at rest, one 600 N punch per second."""

    def __init__(self):
        self.t0 = time.perf_counter()
        self.sent = 0
        self.rng = np.random.default_rng(0)

    def read(self, size):
        time.sleep(0.005)
        due = int((time.perf_counter() - self.t0) * SAMPLE_RATE)
        out = bytearray()
        while self.sent < due and len(out) < size:
            out += self._frame(self.sent)
            self.sent += 1
        return bytes(out)

    def _frame(self, n):
        t = n / SAMPLE_RATE
        phase = t % 1.0
        punch = 600 * math.sin(math.pi * (phase - 0.2) / 0.015) if t > 2.5 and 0.2 <= phase < 0.215 else 0.0
        share = [0.55, 0.2, 0.17, 0.08]
        vref = 0.505
        mv = []
        for k in range(N_SENSORS):
            f = 15 + punch * share[k]                     # 15 N preload per corner
            v = vref + f * (2.495 / 445) + self.rng.normal(0, 0.002)
            mv.append(int(round(min(v, 3.29) * 1000)))
        payload = struct.pack("<H6H", n & 0xFFFF, *mv, int(vref * 1000), 3300)
        return SYNC + payload + bytes([sum(payload) & 0xFF])

    def close(self):
        pass


class Stream:
    """Reads and checks the frames in a background thread."""

    def __init__(self, port=None, sim=False):
        if sim:
            self.port = SimulatedPort()
        else:
            import serial
            self.port = serial.Serial(port, BAUD_RATE, timeout=0.05)
            self.port.reset_input_buffer()
        self.buf = bytearray()
        self.lock = threading.Lock()
        self.pending = []
        self.listeners = []
        self.frames = 0
        self.gaps = 0
        self.bad = 0
        self.last_cnt = None
        self.index = 0
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            data = self.port.read(4096)
            if data:
                self._parse(data)

    def _parse(self, data):
        self.buf += data
        rows = []
        while True:
            i = self.buf.find(SYNC)
            if i < 0:
                del self.buf[:-1]
                break
            if len(self.buf) - i < FRAME.size:
                del self.buf[:i]
                break
            raw = bytes(self.buf[i:i + FRAME.size])
            _, cnt, *vals, chk = FRAME.unpack(raw)
            if sum(raw[2:-1]) & 0xFF != chk:
                self.bad += 1
                del self.buf[:i + 1]
                continue
            del self.buf[:i + FRAME.size]
            if self.last_cnt is not None:
                step = (cnt - self.last_cnt) & 0xFFFF
                if step != 1:
                    self.gaps += 1
                self.index += step
            self.last_cnt = cnt
            self.frames += 1
            # sample index, 4 channels, vref, vdda (volts)
            rows.append((self.index, *(v / 1000 for v in vals)))
        if rows:
            with self.lock:
                for q in self.listeners:
                    q.extend(rows)

    def listen(self, maxlen=None):
        q = deque(maxlen=maxlen)
        with self.lock:
            self.listeners.append(q)
        return q

    def collect(self, seconds):
        q = self.listen()
        end = time.time() + seconds
        while time.time() < end:
            time.sleep(0.05)
        with self.lock:
            self.listeners.remove(q)
            rows = list(q)
        if not rows:
            sys.exit("No data received: check the port and that the board is running.")
        return np.array(rows)

    def close(self):
        self.running = False
        self.thread.join(timeout=1)
        self.port.close()


# ---------------------------------------------------------------- calibration file


def load_calib(path):
    calib = dict(DEFAULT_CALIB)
    if os.path.exists(path):
        with open(path) as f:
            calib.update(json.load(f))
    return calib


def save_calib(path, calib):
    with open(path, "w") as f:
        json.dump(calib, f, indent=2)
    print(f"Saved {path}")


def forces(volts, calib):
    """volts: (n, 4) array. Returns (n, 4) forces in N, or None without gains."""
    if not calib["gain_n_per_v"] or not calib["offset_v"]:
        return None
    gain = np.array(calib["gain_n_per_v"]) * np.array(calib["plate_correction"])
    return (volts - np.array(calib["offset_v"])) * gain


def centre_of_pressure(f, calib):
    pos = np.array(calib["positions_mm"], dtype=float)
    total = f.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        x = (f * pos[:, 0]).sum(axis=1) / total
        y = (f * pos[:, 1]).sum(axis=1) / total
    low = total < COP_MIN_FORCE
    x[low] = np.nan
    y[low] = np.nan
    return total, x, y


def check_mode(calib, vref, key):
    ref = calib.get(key)
    if ref and abs(ref - vref) > 0.05:
        print(f"Warning: V_REF is {vref:.3f} V ({mode_name(vref)} mode) but "
              f"{key} was done at {ref:.3f} V ({mode_name(ref)} mode).")


# ---------------------------------------------------------------- commands


def cmd_monitor(stream, args, calib):
    rf = parse_rf(args.rf)
    print("Ctrl+C to stop.")
    try:
        while True:
            d = stream.collect(0.25)
            v = d[:, 1:5].mean(axis=0)
            vref, vdda = d[:, 5].mean(), d[:, 6].mean()
            line = " ".join(f"V{k + 1}={v[k]:.3f}" for k in range(N_SENSORS))
            line += f" | VREF={vref:.3f} ({mode_name(vref)}) VDDA={vdda:.2f}"
            f = forces(v[None, :], calib)
            if f is not None:
                line += " | F=" + " ".join(f"{x:6.1f}" for x in f[0]) + f" sum={f.sum():6.1f} N"
            if rf:
                r = [rf[k] / (v[k] / vref - 1) if v[k] > vref * 1.002 else float("inf")
                     for k in range(N_SENSORS)]
                line += " | R=" + " ".join(f"{x / 1e3:.1f}k" for x in r)
            line += f" | gaps={stream.gaps} bad={stream.bad}"
            print(line, flush=True)
    except KeyboardInterrupt:
        pass


def parse_rf(text):
    if not text:
        return None
    vals = [float(x) * 1e3 for x in text.split(",")]
    return vals * N_SENSORS if len(vals) == 1 else vals


def cmd_record(stream, args, calib):
    print(f"Recording {args.duration} s to {args.output}...")
    start = time.time()
    d = stream.collect(args.duration)
    v = d[:, 1:5]
    f = forces(v, calib)
    with open(args.output, "w", newline="") as fh:
        w = csv.writer(fh)
        head = ["t_s", "sample"] + [f"v{k + 1}" for k in range(N_SENSORS)] + ["vref", "vdda"]
        if f is not None:
            head += [f"f{k + 1}" for k in range(N_SENSORS)] + ["f_total", "x_mm", "y_mm"]
            total, x, y = centre_of_pressure(f, calib)
        w.writerow(head)
        first = d[0, 0]
        for i, row in enumerate(d):
            out = [f"{(row[0] - first) / SAMPLE_RATE:.4f}", int(row[0] - first)]
            out += [f"{x:.3f}" for x in row[1:]]
            if f is not None:
                out += [f"{x:.1f}" for x in f[i]] + [f"{total[i]:.1f}"]
                out += ["" if math.isnan(x[i]) else f"{x[i]:.1f}",
                        "" if math.isnan(y[i]) else f"{y[i]:.1f}"]
            w.writerow(out)
    print(f"{len(d)} frames (started {time.strftime('%H:%M:%S', time.localtime(start))}), "
          f"gaps={stream.gaps}, bad={stream.bad}")


def cmd_tare(stream, args, calib):
    print(f"Tare: keep the plate unloaded for {args.duration} s...")
    d = stream.collect(args.duration)
    calib["offset_v"] = [round(x, 4) for x in d[:, 1:5].mean(axis=0)]
    calib["tare_vref_v"] = round(float(d[:, 5].mean()), 4)
    noise = d[:, 1:5].std(axis=0)
    print("Offsets (V): " + " ".join(f"{x:.4f}" for x in calib["offset_v"]))
    print("Noise (mV rms): " + " ".join(f"{x * 1e3:.1f}" for x in noise))
    if noise.max() > 0.01:
        print("Warning: the outputs moved during the tare. Keep the plate still and run it again.")
    save_calib(args.calib, calib)


def cmd_step(stream, args, calib):
    k = args.sensor - 1
    print(f"Sensor {args.sensor}, {args.load} N ({args.dir}): averaging {args.duration} s...")
    d = stream.collect(args.duration)
    v = d[:, 1 + k]
    row = [time.strftime("%Y-%m-%d %H:%M:%S"), args.sensor, args.load, args.dir,
           f"{v.mean():.4f}", f"{v.std() * 1e3:.2f}", f"{d[:, 5].mean():.4f}", len(d)]
    new = not os.path.exists(args.steps)
    with open(args.steps, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["time", "sensor", "load_n", "dir", "v_mean", "v_std_mv", "vref", "frames"])
        w.writerow(row)
    print(f"V = {v.mean():.4f} V (std {v.std() * 1e3:.2f} mV) -> {args.steps}")
    if v.max() > 3.25:
        print("Warning: output saturated, lower RV or change mode.")


def cmd_fit(args, calib):
    with open(args.steps) as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("No steps recorded.")
    gains = list(calib["gain_n_per_v"] or [None] * N_SENSORS)
    for s in range(1, N_SENSORS + 1):
        rs = [r for r in rows if int(r["sensor"]) == s]
        if len(rs) < 3:
            continue
        load = np.array([float(r["load_n"]) for r in rs])
        v = np.array([float(r["v_mean"]) for r in rs])
        up = np.array([r["dir"] == "up" for r in rs])
        zero = v[load == 0]
        v0 = zero.mean() if len(zero) else calib["offset_v"][s - 1]
        x = v - v0
        # least squares through the origin: load = gain * (V - V0)
        gain = float((x * load).sum() / (x * x).sum())
        res = load - gain * x
        fs = load.max()
        r2 = 1 - (res ** 2).sum() / ((load - load.mean()) ** 2).sum()
        print(f"\nSensor {s}: gain = {gain:.1f} N/V, V0 = {v0:.4f} V, R2 = {r2:.4f}")
        print(f"  max deviation from the line: {abs(res).max():.1f} N "
              f"({100 * abs(res).max() / fs:.1f} % of {fs:.0f} N)")
        hyst = []
        for L in np.unique(load[(load > 0) & (load < fs)]):
            vu, vd = v[(load == L) & up], v[(load == L) & ~up]
            if len(vu) and len(vd):
                hyst.append(gain * abs(vd.mean() - vu.mean()))
        if hyst:
            print(f"  hysteresis: {max(hyst):.1f} N ({100 * max(hyst) / fs:.1f} % FS)")
        rep = [gain * v[(load == L) & (up == u)].std(ddof=1)
               for L in np.unique(load) for u in (True, False)
               if ((load == L) & (up == u)).sum() > 1]
        if rep:
            print(f"  repeatability (std of repeated steps): {max(rep):.1f} N "
                  f"({100 * max(rep) / fs:.1f} % FS)")
        gains[s - 1] = round(gain, 2)
    calib["gain_n_per_v"] = gains
    calib["fit_vref_v"] = float(np.mean([float(r["vref"]) for r in rows]))
    if calib["offset_v"] is None:
        print("\nNo tare yet: run 'tare' before measuring forces.")
    save_calib(args.calib, calib)


def cmd_point(stream, args, calib):
    print(f"Mass {args.mass} kg at ({args.x}, {args.y}) mm: averaging {args.duration} s...")
    d = stream.collect(args.duration)
    v = d[:, 1:5].mean(axis=0)
    new = not os.path.exists(args.points)
    with open(args.points, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["time", "x_mm", "y_mm", "mass_kg"] + [f"v{k + 1}" for k in range(N_SENSORS)])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), args.x, args.y, args.mass]
                   + [f"{x:.4f}" for x in v])
    f = forces(v[None, :], calib)
    if f is not None:
        total, x, y = centre_of_pressure(f, calib)
        where = "" if math.isnan(x[0]) else f", centre at ({x[0]:.0f}, {y[0]:.0f}) mm"
        print(f"Measured: {total[0]:.1f} N (expected {args.mass * 9.81:.1f} N){where}")


def cmd_fitplate(args, calib):
    with open(args.points) as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < 3:
        sys.exit("At least 3 points are needed (5 or more recommended).")
    calib["plate_correction"] = [1.0] * N_SENSORS
    v = np.array([[float(r[f"v{k + 1}"]) for k in range(N_SENSORS)] for r in rows])
    w = np.array([float(r["mass_kg"]) * 9.81 for r in rows])
    xy = np.array([[float(r["x_mm"]), float(r["y_mm"])] for r in rows])
    f = forces(v, calib)
    if f is None:
        sys.exit("Run 'tare' and 'fit' first.")
    pos = np.array(calib["positions_mm"], dtype=float)

    def report(f, label):
        total, x, y = centre_of_pressure(f, calib)
        err_f = 100 * np.abs(total - w) / w
        err_p = np.hypot(x - xy[:, 0], y - xy[:, 1])
        print(f"{label}: force error max {err_f.max():.1f} %, mean {err_f.mean():.1f} % | "
              f"position error max {np.nanmax(err_p):.1f} mm, mean {np.nanmean(err_p):.1f} mm")

    report(f, "Before")
    # sum c_k F_k = W, sum c_k F_k x_k = W x, sum c_k F_k y_k = W y
    a = np.vstack([f, f * pos[:, 0], f * pos[:, 1]])
    b = np.concatenate([w, w * xy[:, 0], w * xy[:, 1]])
    scale = np.concatenate([np.ones(len(w)), np.full(2 * len(w), 1 / 100)])   # weigh N and N.m alike
    c, *_ = np.linalg.lstsq(a * scale[:, None], b * scale, rcond=None)
    report(f * c, "After ")
    calib["plate_correction"] = [round(float(x), 4) for x in c]
    print("Corrections: " + " ".join(f"{x:.3f}" for x in c))
    save_calib(args.calib, calib)


def cmd_live(stream, args, calib):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    window = 2 * SAMPLE_RATE
    q = stream.listen(maxlen=window)
    has_f = forces(np.zeros((1, 4)), calib) is not None
    unit = "N" if has_f else "V"
    pos = np.array(calib["positions_mm"], dtype=float)
    half = max(np.abs(pos).max() * 1.3, 50)

    fig, (ax, axp) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [2, 1]})
    t = np.arange(-window, 0) / SAMPLE_RATE
    lines = [ax.plot(t, np.zeros(window), label=f"sensor {k + 1}")[0] for k in range(N_SENSORS)]
    if has_f:
        lines.append(ax.plot(t, np.zeros(window), "k", lw=2, label="total")[0])
    ax.set_xlabel("time (s)")
    ax.set_ylabel(unit)
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    axp.set_xlim(-half, half)
    axp.set_ylim(-half, half)
    axp.set_aspect("equal")
    axp.plot(pos[:, 0], pos[:, 1], "s", color="gray")
    for k, (x, y) in enumerate(pos):
        axp.annotate(str(k + 1), (x, y), textcoords="offset points", xytext=(6, 6))
    axp.set_title("centre of pressure (mm)")
    cop, = axp.plot([], [], "o", color="crimson")
    trail, = axp.plot([], [], "-", color="crimson", alpha=0.3)
    info = ax.text(0.99, 0.97, "", transform=ax.transAxes, ha="right", va="top")
    peak = [0.0]

    def update(_):
        with stream.lock:
            d = np.array(q)
        if len(d) < 2:
            return lines
        v = d[:, 1:5]
        y = forces(v, calib) if has_f else v
        n = len(d)
        for k in range(N_SENSORS):
            lines[k].set_data(t[-n:], y[:, k])
        top, low = y.max(), y.min()
        if has_f:
            total, x, yy = centre_of_pressure(y, calib)
            lines[-1].set_data(t[-n:], total)
            top, low = max(top, total.max()), min(low, total.min())
            peak[0] = max(peak[0], top)
            recent = slice(-SAMPLE_RATE // 5, None)
            trail.set_data(x[recent], yy[recent])
            i = int(np.argmax(total))           # last strong impact in the window
            cop.set_data(x[i:i + 1], yy[i:i + 1])
            info.set_text(f"total {total[-1]:.0f} N, peak {peak[0]:.0f} N")
        span = max(top - min(low, 0), 1 if has_f else 0.1)
        ax.set_ylim(min(low, 0) - 0.05 * span, top + 0.1 * span)
        return lines

    if args.duration:
        time.sleep(args.duration)
        update(0)
        fig.savefig(args.save or "live.png")
        return
    anim = FuncAnimation(fig, update, interval=50, cache_frame_data=False)
    plt.show()
    del anim


# ---------------------------------------------------------------- main


def main():
    p = argparse.ArgumentParser(description="Force plate prototype: acquisition and calibration.")
    p.add_argument("--port", "-p", help="serial port of the Nucleo (e.g. COM5, /dev/ttyACM0)")
    p.add_argument("--sim", action="store_true", help="use simulated data instead of the board")
    p.add_argument("--calib", default="calibration.json", help="calibration file")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("monitor")
    s.add_argument("--rf", help="feedback resistance in kOhm (one value or 4 comma-separated) "
                               "to show the sensor resistance")
    s = sub.add_parser("live")
    s.add_argument("--duration", type=float, help="close after this many seconds and save a PNG")
    s.add_argument("--save", help="PNG file name with --duration")
    s = sub.add_parser("record")
    s.add_argument("--duration", "-d", type=float, default=10)
    s.add_argument("--output", "-o", default=time.strftime("record_%Y%m%d_%H%M%S.csv"))
    s = sub.add_parser("tare")
    s.add_argument("--duration", "-d", type=float, default=2)
    s = sub.add_parser("step")
    s.add_argument("--sensor", type=int, required=True, choices=range(1, N_SENSORS + 1))
    s.add_argument("--load", type=float, required=True, help="applied load in N")
    s.add_argument("--dir", choices=["up", "down"], default="up", help="loading or unloading")
    s.add_argument("--duration", "-d", type=float, default=3)
    s.add_argument("--steps", default="steps.csv")
    s = sub.add_parser("fit")
    s.add_argument("--steps", default="steps.csv")
    s = sub.add_parser("point")
    s.add_argument("--x", type=float, required=True, help="mm, from the plate centre")
    s.add_argument("--y", type=float, required=True)
    s.add_argument("--mass", type=float, required=True, help="kg")
    s.add_argument("--duration", "-d", type=float, default=3)
    s.add_argument("--points", default="points.csv")
    s = sub.add_parser("fitplate")
    s.add_argument("--points", default="points.csv")
    args = p.parse_args()

    calib = load_calib(args.calib)
    if args.cmd == "fit":
        return cmd_fit(args, calib)
    if args.cmd == "fitplate":
        return cmd_fitplate(args, calib)

    if not args.port and not args.sim:
        p.error("--port or --sim is required for this command")
    stream = Stream(args.port, sim=args.sim)
    try:
        time.sleep(0.2)
        d = stream.collect(0.1)
        vref = float(d[:, 5].mean())
        print(f"Connected: V_REF = {vref:.3f} V ({mode_name(vref)} mode), VDDA = {d[:, 6].mean():.2f} V")
        if args.cmd != "tare":
            check_mode(calib, vref, "tare_vref_v")
        check_mode(calib, vref, "fit_vref_v")
        {"monitor": cmd_monitor, "live": cmd_live, "record": cmd_record, "tare": cmd_tare,
         "step": cmd_step, "point": cmd_point}[args.cmd](stream, args, calib)
    finally:
        stream.close()


if __name__ == "__main__":
    main()
