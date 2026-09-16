import math
import random
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt


# ============================================================
# MODELO DEL SIMULADOR DE ATERRIZAJE
# ============================================================

RANGES = [
    (-0.3, 0.3),
    (-2.5, 2.5),
    (0.3, 5),
    (-4, 4),
    (5, 50),
    (0.08, 0.7),
    (0, 16)
]

INITIAL_RANGES = [
    (-0.03, 0.03),
    (-0.25, 0.25),
    (2, 5),
    (-0.4, 0.4),
    (20, 50),
    (0.08, 0.7),
    (0, 3)
]


def clamp(x, a, b):
    return max(a, min(b, x))


class Lander:
    @staticmethod
    def simulate(genes, cfg, trace=False):
        x = cfg["x"]
        y = cfg["height"]
        vx = 0.0
        vy = -12.0
        fuel = cfg["fuel"]
        t = 0.0
        angle = 0.0
        throttle = 0.0

        path = []

        if trace:
            path.append({
                "x": x, "y": y, "vx": vx, "vy": vy,
                "fuel": fuel, "t": t, "angle": angle,
                "throttle": throttle
            })

        dt = 0.1

        for _ in range(1200):
            if y <= 0:
                break

            desired = -min(
                genes[4],
                genes[2] * math.sqrt(max(0, y))
            )

            ax = clamp(
                -genes[0] * x - genes[1] * vx,
                -8,
                8
            )

            ay = clamp(
                genes[6] + genes[3] * (desired - vy),
                0,
                22
            )

            angle = clamp(
                math.atan2(ax, max(ay, 0.01)),
                -genes[5],
                genes[5]
            )

            thrust = clamp(
                math.hypot(ax, ay),
                0,
                24
            )

            thrust = min(thrust, fuel * 24 / dt)
            throttle = thrust / 24

            old = {
                "x": x,
                "y": y,
                "vx": vx,
                "vy": vy,
                "fuel": fuel,
                "t": t,
                "angle": angle,
                "throttle": throttle
            }

            vx += (
                math.sin(angle) * thrust +
                cfg["wind"]
            ) * dt

            vy += (
                math.cos(angle) * thrust -
                9.81
            ) * dt

            x += vx * dt
            y += vy * dt

            fuel = max(
                0,
                fuel - throttle * dt
            )

            t += dt

            if y <= 0:
                f = old["y"] / (old["y"] - y)

                x = old["x"] + f * (x - old["x"])
                vx = old["vx"] + f * (vx - old["vx"])
                vy = old["vy"] + f * (vy - old["vy"])
                fuel = old["fuel"] + f * (fuel - old["fuel"])
                t = old["t"] + f * (t - old["t"])
                y = 0

            if trace:
                path.append({
                    "x": x,
                    "y": y,
                    "vx": vx,
                    "vy": vy,
                    "fuel": fuel,
                    "t": t,
                    "angle": angle,
                    "throttle": throttle
                })

        landed = (
            y == 0
            and abs(x) <= 20
            and abs(vx) <= 2
            and abs(vy) <= 3
            and abs(angle) <= math.pi / 18
        )

        cost = (
            2 * abs(x)
            + 12 * abs(vx)
            + 18 * abs(vy)
            + 30 * abs(angle)
            + (2000 + y if y > 0 else 0)
        )

        fitness = (
            (10000 if landed else 0)
            + 2000 / (1 + cost)
            + (fuel if landed else 0)
        )

        return {
            "genes": genes[:],
            "fitness": fitness,
            "landed": landed,
            "end": {
                "x": x,
                "y": y,
                "vx": vx,
                "vy": vy,
                "fuel": fuel,
                "t": t,
                "angle": angle,
                "throttle": throttle
            },
            "path": path
        }


class GeneticAlgorithm:
    def __init__(self, cfg):
        self.cfg = cfg
        self.rng = random.Random(cfg["seed"])

        self.population = [
            [
                a + self.rng.random() * (b - a)
                for a, b in INITIAL_RANGES
            ]
            for _ in range(cfg["population"])
        ]

        self.generation = 0
        self.best = None
        self.history = []

    def select(self, ranked):
        best = ranked[
            self.rng.randrange(len(ranked))
        ]

        for _ in range(2):
            candidate = ranked[
                self.rng.randrange(len(ranked))
            ]

            if candidate["fitness"] > best["fitness"]:
                best = candidate

        return best["genes"]

    def step(self):
        evaluated = [
            Lander.simulate(
                genes,
                self.cfg
            )
            for genes in self.population
        ]

        ranked = sorted(
            evaluated,
            key=lambda item: item["fitness"],
            reverse=True
        )

        if (
            self.best is None
            or ranked[0]["fitness"] > self.best["fitness"]
        ):
            self.best = ranked[0]

        success = sum(
            1 for item in ranked
            if item["landed"]
        )

        self.history.append({
            "gen": self.generation + 1,
            "best": self.best["fitness"],
            "success": success
        })

        # Conserva los dos mejores pilotos.
        next_population = [
            ranked[0]["genes"][:],
            ranked[1]["genes"][:]
        ]

        while len(next_population) < self.cfg["population"]:
            a = self.select(ranked)
            b = self.select(ranked)

            cut = 1 + self.rng.randrange(
                len(RANGES) - 1
            )

            cross = (
                self.rng.random()
                < self.cfg["crossover"]
            )

            child = []

            for j, value in enumerate(a):
                x = (
                    b[j]
                    if cross and j >= cut
                    else value
                )

                lo, hi = RANGES[j]

                if (
                    self.rng.random()
                    < self.cfg["mutation"]
                ):
                    x += (
                        self.rng.random()
                        + self.rng.random()
                        + self.rng.random()
                        - 1.5
                    ) * (hi - lo) * 0.2

                x = clamp(x, lo, hi)
                child.append(x)

            next_population.append(child)

        self.population = next_population
        self.generation += 1

        return {
            "generation": self.generation,
            "best": self.best,
            "history": self.history,
            "ranked": ranked,
            "evaluated": evaluated
        }


# ============================================================
# SIMULADOR GRÁFICO
# ============================================================

class Simulador:
    def __init__(self, root):
        self.root = root
        self.root.title("Aprendiendo a aterrizar")
        self.root.geometry("1050x800")
        self.root.configure(bg="#0b1220")

        self.running = False
        self.paused = False
        self.ga = None
        self.history = []

        self.cfg = {
            "height": 500,
            "x": 180,
            "wind": 0,
            "fuel": 40,
            "population": 80,
            "generations": 20,
            "crossover": 0.86,
            "mutation": 0.15,
            "seed": 42
        }

        self.create_interface()

    def create_interface(self):
        title = tk.Label(
            self.root,
            text="Aprendiendo a aterrizar",
            bg="#0b1220",
            fg="#eaf0f7",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=(15, 3))

        subtitle = tk.Label(
            self.root,
            text="Observa cómo mejora una población de pilotos.",
            bg="#0b1220",
            fg="#b2c1d3",
            font=("Arial", 12)
        )
        subtitle.pack()

        config = tk.Frame(
            self.root,
            bg="#0b1220"
        )
        config.pack(pady=12)

        self.entries = {}

        values = [
            ("Pilotos", "population", 80),
            ("Generaciones", "generations", 20),
            ("Semilla", "seed", 42),
            ("Cruce", "crossover", 0.86),
            ("Mutación por gen", "mutation", 0.15)
        ]

        for i, (text, key, value) in enumerate(values):
            tk.Label(
                config,
                text=text,
                bg="#0b1220",
                fg="#b2c1d3"
            ).grid(row=0, column=i * 2)

            entry = tk.Entry(
                config,
                width=8,
                bg="#111d2c",
                fg="#eaf0f7",
                insertbackground="white"
            )
            entry.insert(0, str(value))
            entry.grid(
                row=0,
                column=i * 2 + 1,
                padx=(4, 10)
            )

            self.entries[key] = entry

        buttons = tk.Frame(
            self.root,
            bg="#0b1220"
        )
        buttons.pack(pady=5)

        self.start_button = tk.Button(
            buttons,
            text="Iniciar",
            command=self.start,
            bg="#85e4cb",
            fg="#08241e",
            font=("Arial", 11, "bold"),
            padx=20
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = tk.Button(
            buttons,
            text="Pausar",
            command=self.pause,
            state="disabled",
            padx=20
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.reset_button = tk.Button(
            buttons,
            text="Reiniciar",
            command=self.reset,
            state="disabled",
            padx=20
        )
        self.reset_button.grid(row=0, column=2, padx=5)

        stats = tk.Frame(
            self.root,
            bg="#0b1220"
        )
        stats.pack(pady=8)

        self.gen_label = self.make_stat(
            stats, "Generación", "— / 20", 0
        )
        self.active_label = self.make_stat(
            stats, "En vuelo", "0", 1
        )
        self.safe_label = self.make_stat(
            stats, "Aterrizajes seguros", "0", 2
        )
        self.failed_label = self.make_stat(
            stats, "Fallidos", "0", 3
        )

        self.canvas = tk.Canvas(
            self.root,
            height=410,
            bg="#142b42",
            highlightthickness=0
        )
        self.canvas.pack(
            fill="both",
            expand=False,
            padx=20,
            pady=10
        )

        self.status = tk.Label(
            self.root,
            text="Pulsa Iniciar para ver la primera generación.",
            bg="#0b1220",
            fg="#eaf0f7",
            font=("Arial", 13)
        )
        self.status.pack(pady=8)

        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=800,
            mode="determinate"
        )
        self.progress.pack(pady=5)

    def make_stat(self, parent, title, value, column):
        frame = tk.Frame(
            parent,
            bg="#0b1220"
        )
        frame.grid(row=0, column=column, padx=25)

        tk.Label(
            frame,
            text=title,
            bg="#0b1220",
            fg="#b2c1d3"
        ).pack()

        label = tk.Label(
            frame,
            text=value,
            bg="#0b1220",
            fg="white",
            font=("Arial", 12, "bold")
        )
        label.pack()

        return label

    def read_config(self):
        self.cfg["population"] = int(
            self.entries["population"].get()
        )
        self.cfg["generations"] = int(
            self.entries["generations"].get()
        )
        self.cfg["seed"] = int(
            self.entries["seed"].get()
        )
        self.cfg["crossover"] = float(
            self.entries["crossover"].get()
        )
        self.cfg["mutation"] = float(
            self.entries["mutation"].get()
        )

    def start(self):
        try:
            self.read_config()
        except ValueError:
            self.status.config(
                text="Revisa los valores introducidos."
            )
            return

        self.ga = GeneticAlgorithm(self.cfg)
        self.history = []
        self.running = True
        self.paused = False

        self.start_button.config(
            state="disabled"
        )
        self.pause_button.config(
            state="normal"
        )
        self.reset_button.config(
            state="normal"
        )

        self.run_generation()

    def run_generation(self):
        if not self.running or self.paused:
            return

        if (
            self.ga.generation
            >= self.cfg["generations"]
        ):
            self.finish()
            return

        result = self.ga.step()

        self.history.append(
            result["history"][-1]
        )

        generation = result["generation"]

        safe = result["history"][-1]["success"]

        self.gen_label.config(
            text=f"{generation} / {self.cfg['generations']}"
        )

        self.safe_label.config(
            text=str(safe)
        )

        self.failed_label.config(
            text=str(
                self.cfg["population"] - safe
            )
        )

        self.active_label.config(
            text=str(self.cfg["population"])
        )

        self.status.config(
            text=(
                f"Generación {generation}: "
                f"{safe} de {self.cfg['population']} "
                f"aterrizajes seguros."
            )
        )

        self.draw_generation(
            result["evaluated"]
        )

        self.progress["value"] = (
            generation /
            self.cfg["generations"]
        ) * 100

        self.root.after(
            1000,
            self.run_generation
        )

    def draw_generation(self, pilots):
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        if width <= 1:
            width = 1000

        height = 410

        # Cielo
        self.canvas.create_rectangle(
            0, 0, width, height,
            fill="#142b42",
            outline=""
        )

        # Plataforma
        ground = height - 45

        self.canvas.create_rectangle(
            0,
            ground,
            width,
            height,
            fill="#233e35",
            outline=""
        )

        platform_left = width / 2 - 45
        platform_right = width / 2 + 45

        self.canvas.create_rectangle(
            platform_left,
            ground - 4,
            platform_right,
            ground,
            fill="#85e4cb",
            outline=""
        )

        self.canvas.create_text(
            width / 2,
            ground + 20,
            text="Plataforma",
            fill="#85e4cb"
        )

        for pilot in pilots:
            end = pilot["end"]

            x = width / 2 + end["x"] * 0.45
            y = ground - end["y"] * 0.55

            x = max(8, min(width - 8, x))
            y = max(12, min(ground - 8, y))

            if pilot["landed"]:
                self.canvas.create_text(
                    x,
                    y,
                    text="✓",
                    fill="#85e4cb",
                    font=("Arial", 13, "bold")
                )
            else:
                self.canvas.create_text(
                    x,
                    y,
                    text="×",
                    fill="#ffa19a",
                    font=("Arial", 13, "bold")
                )

    def pause(self):
        if not self.running:
            return

        self.paused = not self.paused

        if self.paused:
            self.pause_button.config(
                text="Continuar"
            )
        else:
            self.pause_button.config(
                text="Pausar"
            )
            self.run_generation()

    def reset(self):
        self.running = False
        self.paused = False
        self.ga = None
        self.history = []

        self.start_button.config(
            state="normal",
            text="Iniciar"
        )
        self.pause_button.config(
            state="disabled",
            text="Pausar"
        )
        self.reset_button.config(
            state="disabled"
        )

        self.gen_label.config(
            text=f"— / {self.entries['generations'].get()}"
        )
        self.active_label.config(text="0")
        self.safe_label.config(text="0")
        self.failed_label.config(text="0")

        self.status.config(
            text="Pulsa Iniciar para ver la primera generación."
        )

        self.progress["value"] = 0

        self.canvas.delete("all")

    def finish(self):
        self.running = False

        self.start_button.config(
            state="normal",
            text="Volver a iniciar"
        )
        self.pause_button.config(
            state="disabled"
        )

        self.status.config(
            text="Experimento terminado."
        )

        self.show_chart()

    def show_chart(self):
        if not self.history:
            return

        generations = [
            h["gen"] for h in self.history
        ]

        successes = [
            h["success"] for h in self.history
        ]

        plt.figure(
            "Aterrizajes seguros por generación",
            figsize=(9, 5)
        )

        plt.bar(
            generations,
            successes
        )

        plt.xlabel("Generación")
        plt.ylabel("Aterrizajes seguros")
        plt.title(
            "Aterrizajes seguros por generación"
        )

        plt.ylim(
            0,
            self.cfg["population"]
        )

        plt.grid(
            axis="y",
            alpha=0.25
        )

        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = Simulador(root)
    root.mainloop()
