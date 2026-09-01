#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
 Sistema de Lógica Difusa con scikit-fuzzy (skfuzzy) + interfaz Tkinter
 Tema: Invernadero inteligente — Control automático de tiempo de riego
==============================================================================
"""

import sys
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    sys.exit("Falta matplotlib. Instálalo con:  pip install matplotlib")

try:
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl
except ImportError:
    sys.exit(
        "Falta scikit-fuzzy (o alguna de sus dependencias).\n"
        "Instálalo con:  pip install scipy numpy matplotlib networkx scikit-fuzzy"
    )


# ==============================================================================
# [1] PARÁMETROS DE LAS ETIQUETAS (a,b,c,d) - LÓGICA MEJORADA
# ==============================================================================
# Se ajustan para tener sentido agronómico en un invernadero
TEMP_PARAMS = {
    "Fria": (0, 0, 15, 20),
    "Optima": (15, 20, 25, 30),
    "Calor": (25, 30, 40, 40),
}
HUM_PARAMS = {
    "Seca": (0, 0, 20, 40),
    "Ideal": (30, 50, 60, 75),
    "Exceso": (65, 80, 100, 100),
}
RIEGO_PARAMS = {
    "Nada": (0, 0, 0, 5),          # Riego de 0 a 5 min (tendencia a 0)
    "Moderado": (3, 10, 15, 22),   # Riego medio
    "Abundante": (18, 25, 30, 30), # Riego largo para combatir sequía severa
}

# Descripciones para la interfaz visual
DESCRIPCION_REGLAS = [
    "R1: SI humedad es Exceso  ➔  riego Nada (evita ahogamiento).",
    "R2: SI humedad es Ideal   ➔  riego Moderado (mantenimiento).",
    "R3: SI humedad es Seca Y temperatura Calor  ➔  riego Abundante.",
    "R4: SI humedad es Seca Y temperatura (Fría o Óptima)  ➔  riego Moderado.",
]


# ==============================================================================
# [2] NÚCLEO DIFUSO (skfuzzy)
# ==============================================================================
def construir_sistema():
    temperatura = ctrl.Antecedent(np.arange(0, 40.01, 0.1), "temperatura")
    humedad = ctrl.Antecedent(np.arange(0, 100.01, 0.1), "humedad_suelo")
    riego = ctrl.Consequent(np.arange(0, 30.01, 0.1), "tiempo_riego")

    # Inyección de las funciones de pertenencia trapezoidales
    for nombre, params in TEMP_PARAMS.items():
        temperatura[nombre.lower()] = fuzz.trapmf(temperatura.universe, list(params))
    for nombre, params in HUM_PARAMS.items():
        humedad[nombre.lower()] = fuzz.trapmf(humedad.universe, list(params))
    for nombre, params in RIEGO_PARAMS.items():
        riego[nombre.lower()] = fuzz.trapmf(riego.universe, list(params))

    # Creación de las reglas matemáticas
    regla1 = ctrl.Rule(humedad["exceso"], riego["nada"])
    regla2 = ctrl.Rule(humedad["ideal"], riego["moderado"])
    regla3 = ctrl.Rule(humedad["seca"] & temperatura["calor"], riego["abundante"])
    # skfuzzy permite usar el operador OR (|) internamente para agrupar antecedentes
    regla4 = ctrl.Rule(humedad["seca"] & (temperatura["fria"] | temperatura["optima"]), riego["moderado"])

    sistema_ctrl = ctrl.ControlSystem([regla1, regla2, regla3, regla4])
    simulacion = ctrl.ControlSystemSimulation(sistema_ctrl)
    return temperatura, humedad, riego, simulacion


def describir_rango(a, b, c, d):
    if a == b == c == d:
        return f"Solo en {a}"
    if a == b and c == d:
        return f"100% segura entre {a} y {d} (escalón)"
    if a == b:
        return f"100% segura hasta {c}; luego baja gradualmente hasta {d}"
    if c == d:
        return f"Sube gradualmente desde {a}; 100% segura desde {b}"
    return f"Sube de {a} a {b}; 100% segura de {b} a {c}; baja de {c} a {d}"


# ==============================================================================
# [3] PALETA / ESTILO (Diseño UI)
# ==============================================================================
COLOR_BG = "#F3F6F3"
COLOR_PANEL = "#FFFFFF"
COLOR_PRIMARY = "#1F6D3D"
COLOR_PRIMARY_DARK = "#164F2C"
COLOR_TEXT = "#1E2A22"
COLOR_MUTED = "#5B6B60"
COLOR_BORDER = "#DCE5DD"
FONT_FAMILY = "Segoe UI"


# ==============================================================================
# [4] APLICACIÓN TKINTER
# ==============================================================================
class InvernaderoSkfuzzyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invernadero difuso · scikit-fuzzy")
        self.root.geometry("1000x1040")
        self.root.minsize(880, 800)
        self.root.configure(bg=COLOR_BG)

        self.temperatura, self.humedad, self.riego, self.sim = construir_sistema()
        self.carpeta_script = Path(__file__).resolve().parent

        self._configurar_estilos()
        self._construir_layout()

    def _configurar_estilos(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background=COLOR_BG)
        style.configure("Header.TFrame", background=COLOR_PRIMARY)
        style.configure("Card.TFrame", background=COLOR_PANEL)
        style.configure("Header.TLabel", background=COLOR_PRIMARY, foreground="#FFFFFF",
                         font=(FONT_FAMILY, 16, "bold"))
        style.configure("SubHeader.TLabel", background=COLOR_PRIMARY, foreground="#DDEFE2",
                         font=(FONT_FAMILY, 10))
        style.configure("SectionTitle.TLabel", background=COLOR_PANEL, foreground=COLOR_PRIMARY_DARK,
                         font=(FONT_FAMILY, 12, "bold"))
        style.configure("FieldLabel.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT,
                         font=(FONT_FAMILY, 10))
        style.configure("Hint.TLabel", background=COLOR_PANEL, foreground=COLOR_MUTED,
                         font=(FONT_FAMILY, 8, "italic"))
        style.configure("Resultado.TLabel", background=COLOR_PANEL, foreground=COLOR_PRIMARY_DARK,
                         font=(FONT_FAMILY, 14, "bold"))
        style.configure("Status.TLabel", background=COLOR_BG, foreground=COLOR_MUTED,
                         font=(FONT_FAMILY, 9))
        style.configure("Accent.TButton", background=COLOR_PRIMARY, foreground="#FFFFFF",
                         font=(FONT_FAMILY, 11, "bold"), padding=(16, 9))
        style.map("Accent.TButton", background=[("active", COLOR_PRIMARY_DARK)])
        style.configure("Secondary.TButton", padding=(10, 6))
        style.configure("Treeview", rowheight=24, font=(FONT_FAMILY, 9))
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 9, "bold"))

    def _construir_layout(self):
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(24, 16))
        header.pack(fill="x")
        ttk.Label(header, text="🌱 Sistema Experto de Invernadero — Lógica Difusa Mamdani",
                  style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Temperatura + Humedad del suelo  →  Tiempo de riego",
                  style="SubHeader.TLabel").pack(anchor="w", pady=(4, 0))

        footer = ttk.Frame(self.root, style="App.TFrame", padding=(16, 4, 16, 10))
        footer.pack(side="bottom", fill="x")
        self.lbl_estado = ttk.Label(footer, text="Ingresa temperatura y humedad, y presiona calcular.",
                                     style="Status.TLabel")
        self.lbl_estado.pack(anchor="w")

        # ---- Lógica de adaptabilidad del Scroll solucionada ----
        canvas = tk.Canvas(self.root, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas, style="App.TFrame")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        frame_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(frame_id, width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _rueda(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _rueda)

        body = ttk.Frame(scroll_frame, style="App.TFrame", padding=(16, 14, 16, 4))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)

        self._construir_tarjeta_rangos(body)

        card_reglas = tk.Frame(body, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_reglas.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        inner_r = ttk.Frame(card_reglas, style="Card.TFrame", padding=(16, 10))
        inner_r.pack(fill="x")
        ttk.Label(inner_r, text="Reglas del sistema", style="SectionTitle.TLabel").pack(anchor="w")
        for r in DESCRIPCION_REGLAS:
            ttk.Label(inner_r, text=r, style="FieldLabel.TLabel").pack(anchor="w", pady=(2, 0))

        card_in = tk.Frame(body, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_in.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        inner_in = ttk.Frame(card_in, style="Card.TFrame", padding=(16, 12))
        inner_in.pack(fill="x")

        ttk.Label(inner_in, text="Valores nítidos a evaluar", style="SectionTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )

        ttk.Label(inner_in, text="Temperatura (0-40 °C)", style="FieldLabel.TLabel").grid(row=1, column=0, sticky="w")
        self.var_temp = tk.StringVar(value="32")
        ttk.Entry(inner_in, textvariable=self.var_temp, width=10).grid(row=1, column=1, sticky="w", padx=(6, 30))

        ttk.Label(inner_in, text="Humedad suelo (0-100 %)", style="FieldLabel.TLabel").grid(row=1, column=2, sticky="w")
        self.var_hum = tk.StringVar(value="25")
        ttk.Entry(inner_in, textvariable=self.var_hum, width=10).grid(row=1, column=3, sticky="w", padx=(6, 0))

        botones = ttk.Frame(inner_in, style="Card.TFrame")
        botones.grid(row=2, column=0, columnspan=4, sticky="w", pady=(12, 0))
        ttk.Button(botones, text="🔬 Calcular Inferencia", style="Accent.TButton",
                   command=self.calcular).pack(side="left")
        ttk.Button(botones, text="💾 Guardar gráficas (PNG)", style="Secondary.TButton",
                   command=self.guardar_graficas).pack(side="left", padx=(10, 0))

        self.lbl_resultado = ttk.Label(inner_in, text="Tiempo de riego: —", style="Resultado.TLabel")
        self.lbl_resultado.grid(row=3, column=0, columnspan=4, sticky="w", pady=(12, 0))

        card_graf = tk.Frame(body, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_graf.grid(row=3, column=0, sticky="nsew")
        inner_g = ttk.Frame(card_graf, style="Card.TFrame", padding=(10, 10))
        inner_g.pack(fill="both", expand=True)
        inner_g.columnconfigure(0, weight=1)

        self.frame_temp = tk.Frame(inner_g, bg=COLOR_PANEL, height=260)
        self.frame_temp.grid(row=0, column=0, sticky="nsew", pady=2)
        self.frame_hum = tk.Frame(inner_g, bg=COLOR_PANEL, height=260)
        self.frame_hum.grid(row=1, column=0, sticky="nsew", pady=2)
        self.frame_riego = tk.Frame(inner_g, bg=COLOR_PANEL, height=260)
        self.frame_riego.grid(row=2, column=0, sticky="nsew", pady=2)

        for frame, texto in (
            (self.frame_temp, "Presiona «Calcular» para ver la gráfica de Temperatura"),
            (self.frame_hum, "Presiona «Calcular» para ver la gráfica de Humedad"),
            (self.frame_riego, "Presiona «Calcular» para ver la gráfica de Riego"),
        ):
            frame.pack_propagate(False)
            tk.Label(frame, text=texto, bg=COLOR_PANEL, fg=COLOR_MUTED,
                     font=(FONT_FAMILY, 9, "italic")).pack(expand=True)

    def _construir_tarjeta_rangos(self, parent):
        card = tk.Frame(parent, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        inner = ttk.Frame(card, style="Card.TFrame", padding=(16, 12))
        inner.pack(fill="both", expand=True)
        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)

        ttk.Label(inner, text="ℹ️  Rangos de cada etiqueta (funciones de pertenencia)",
                  style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            inner,
            text="Fuera del \"rango completo\" la etiqueta vale 0%. Entre el rango completo y el "
                 "\"100% segura\" el valor sube o baja poco a poco (transición).",
            style="Hint.TLabel", wraplength=900, justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 10))

        col_temp = ttk.Frame(inner, style="Card.TFrame")
        col_temp.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(col_temp, text="🌡️ Temperatura (°C)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 4))
        self._crear_tabla_rangos(col_temp, TEMP_PARAMS)

        col_hum = ttk.Frame(inner, style="Card.TFrame")
        col_hum.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(col_hum, text="💧 Humedad del suelo (%)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 4))
        self._crear_tabla_rangos(col_hum, HUM_PARAMS)

    def _crear_tabla_rangos(self, parent, params_dict):
        columnas = ("etiqueta", "completo", "seguro")
        tree = ttk.Treeview(parent, columns=columnas, show="headings", height=len(params_dict))
        tree.heading("etiqueta", text="Etiqueta")
        tree.heading("completo", text="Rango completo (a–d)")
        tree.heading("seguro", text="100% segura (b–c)")
        tree.column("etiqueta", width=90, anchor="center")
        tree.column("completo", width=140, anchor="center")
        tree.column("seguro", width=140, anchor="center")

        for nombre, (a, b, c, d) in params_dict.items():
            rango_completo = f"{a} – {d}"
            rango_seguro = f"{b} – {c}" if b != c else f"{b}"
            tree.insert("", "end", values=(nombre, rango_completo, rango_seguro))

        tree.pack(fill="x")

        for nombre, (a, b, c, d) in params_dict.items():
            texto = f"• {nombre}: {describir_rango(a, b, c, d)}"
            tk.Label(parent, text=texto, bg=COLOR_PANEL, fg=COLOR_MUTED,
                     font=(FONT_FAMILY, 8), wraplength=380, justify="left").pack(anchor="w", pady=(2, 0))

    def _embeber_grafica(self, frame, variable):
        for widget in frame.winfo_children():
            widget.destroy()

        variable.view(sim=self.sim)
        fig = plt.gcf()
        fig.set_size_inches(7.6, 2.3)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        plt.close(fig)
        return canvas

    def calcular(self):
        try:
            t = float(self.var_temp.get())
            h = float(self.var_hum.get())
        except ValueError:
            messagebox.showerror("Valor inválido", "Temperatura y humedad deben ser números.")
            return

        if not (0 <= t <= 40):
            messagebox.showwarning("Fuera de rango", "La temperatura debería estar entre 0 y 40 °C.")
        if not (0 <= h <= 100):
            messagebox.showwarning("Fuera de rango", "La humedad debería estar entre 0 y 100 %.")

        self.lbl_estado.config(text="Calculando inferencia difusa con skfuzzy…")
        self.root.update_idletasks()

        self.sim.input["temperatura"] = t
        self.sim.input["humedad_suelo"] = h

        try:
            self.sim.compute()
        except Exception as err:
            self.lbl_resultado.config(text="Tiempo de riego: sin activación")
            self.lbl_estado.config(text="Ninguna regla se activó con estos valores.")
            messagebox.showwarning(
                "Sin activación",
                f"El motor difuso no encontró reglas aplicables para T={t} y H={h}.\n\nError técnico: {err}",
            )
            return

        resultado = self.sim.output["tiempo_riego"]
        self.lbl_resultado.config(text=f"Tiempo estimado de riego: {resultado:.2f} minutos")

        self._embeber_grafica(self.frame_temp, self.temperatura)
        self._embeber_grafica(self.frame_hum, self.humedad)
        self._embeber_grafica(self.frame_riego, self.riego)

        self.lbl_estado.config(text="Cálculo completado exitosamente.")

    def guardar_graficas(self):
        try:
            t = float(self.var_temp.get())
            h = float(self.var_hum.get())
        except ValueError:
            messagebox.showerror("Valor inválido", "Calcula primero con valores válidos.")
            return

        self.sim.input["temperatura"] = t
        self.sim.input["humedad_suelo"] = h
        try:
            self.sim.compute()
        except Exception as err:
            messagebox.showwarning("Sin activación", f"No se puede graficar: {err}")
            return

        nombres = {
            self.temperatura: "invernadero_temperatura.png",
            self.humedad: "invernadero_humedad.png",
            self.riego: "invernadero_riego.png",
        }
        rutas_guardadas = []
        for variable, nombre_archivo in nombres.items():
            variable.view(sim=self.sim)
            fig = plt.gcf()
            ruta = self.carpeta_script / nombre_archivo
            fig.savefig(ruta, dpi=150, bbox_inches="tight")
            plt.close(fig)
            rutas_guardadas.append(str(ruta))

        messagebox.showinfo(
            "Gráficas guardadas",
            "Se generaron las gráficas como PNG en la misma carpeta del script:\n\n" + "\n".join(rutas_guardadas),
        )
        self.lbl_estado.config(text="Gráficas guardadas correctamente.")


if __name__ == "__main__":
    root = tk.Tk()
    app = InvernaderoSkfuzzyApp(root)
    root.mainloop()