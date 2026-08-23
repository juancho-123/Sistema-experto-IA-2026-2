#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import clips # type: ignore
except ImportError:
    sys.exit(
        "Falta instalar la libreria 'clipspy'.\n"
        "Instalala con:  pip install clipspy"
    )

# ==============================================================================
#  [1] CONSTRUCTOS CLIPS
# ==============================================================================
# plantillas y reglas de diagnóstico.

TEMPLATE_FASE = """(deftemplate fase
   (slot actual (type SYMBOL) (allowed-values inicio preguntas inferencia resultado fin)))"""

TEMPLATE_SINTOMA = """(deftemplate sintoma
   (slot cultivo (type SYMBOL) (allowed-values tomate pimiento pepino lechuga fresa ornamental otro))
   (slot organo (type SYMBOL) (allowed-values hojas fruto flores tallo-cuello raices))
   (slot apariencia (type SYMBOL) (allowed-values moho-gris polvo-blanco manchas-angulares manchas-plateadas melaza-hoja-arrugada cuello-podrido mancha-negra-fruto nodulos-agallas ninguno))
   (slot plaga-visible (type SYMBOL) (allowed-values mosquitas-blancas pulgones bichitos-diminutos ninguno))
   (slot microclima (type SYMBOL) (allowed-values alta-humedad-cerrado templado-seco normal)))"""

TEMPLATE_DIAGNOSTICO = """(deftemplate diagnostico
   (slot nombre-patologia (type STRING))
   (slot tipo-agente (type SYMBOL) (allowed-values hongo insecto-plaga nematodo desorden-abiotico desconocido))
   (slot severidad (type SYMBOL) (allowed-values baja media alta critica))
   (slot control-invernadero (type STRING)))"""

REGLA_BOTRYTIS = """(defrule regla-botrytis
   (fase (actual inferencia))
   (sintoma (organo flores | fruto | hojas | tallo-cuello) (apariencia moho-gris))
   =>
   (assert (diagnostico
      (nombre-patologia "Moho Gris / Podredumbre Gris (Botrytis cinerea)")
      (tipo-agente hongo)
      (severidad critica)
      (control-invernadero "URGENTE: Abrir ventilaciones laterales/cenitales para bajar humedad <75%. Retirar partes con bolsa plastica para evitar esporas. Aplicar fungicidas especificos (Iprodiona, Cyprodinil o Bacillus subtilis)."))))"""

REGLA_MOSCA_BLANCA = """(defrule regla-mosca-blanca
   (fase (actual inferencia))
   (sintoma (plaga-visible mosquitas-blancas))
   =>
   (assert (diagnostico
      (nombre-patologia "Infestacion por Mosca Blanca (Bemisia tabaci / Trialeurodes)")
      (tipo-agente insecto-plaga)
      (severidad alta)
      (control-invernadero "Instalar trampas cromaticas adhesivas amarillas. Realizar suelta de parasitoides (Encarsia formosa) o aplicar jabon potasico + extracto de neem al atardecer."))))"""

REGLA_OIDIO = """(defrule regla-oidio
   (fase (actual inferencia))
   (sintoma (organo hojas) (apariencia polvo-blanco))
   =>
   (assert (diagnostico
      (nombre-patologia "Oidio / Ceniza blanca (Erysiphe / Leveillula taurica)")
      (tipo-agente hongo)
      (severidad media)
      (control-invernadero "Aumentar separacion de plantas para permitir paso de luz. Aplicar azufre por sublimacion/pulverizacion o bicarbonato potasico. Evitar estres termico."))))"""

REGLA_TRIPS = """(defrule regla-trips
   (fase (actual inferencia))
   (sintoma (apariencia manchas-plateadas) (plaga-visible bichitos-diminutos | ninguno))
   =>
   (assert (diagnostico
      (nombre-patologia "Ataque de Trips (Frankliniella occidentalis)")
      (tipo-agente insecto-plaga)
      (severidad alta)
      (control-invernadero "Colocar placas adhesivas azules a la altura del dosel. Introducir acaros depredadores (Amblyseius swirskii / Orius laevigatus) y monitorear transmision de virus."))))"""

REGLA_MILDIU = """(defrule regla-mildiu
   (fase (actual inferencia))
   (sintoma (organo hojas) (apariencia manchas-angulares) (microclima alta-humedad-cerrado))
   =>
   (assert (diagnostico
      (nombre-patologia "Mildiu Velloso (Pseudoperonospora / Bremia lactucae)")
      (tipo-agente hongo)
      (severidad alta)
      (control-invernadero "Evitar condensacion en el techo del plastico. Suspender riego por aspersion; regar solo por goteo matutino. Aplicar fungicidas sistemicos (Metalaxil o Fosetil-Al)."))))"""

REGLA_PULGONES = """(defrule regla-pulgones
   (fase (actual inferencia))
   (sintoma (apariencia melaza-hoja-arrugada) (plaga-visible pulgones))
   =>
   (assert (diagnostico
      (nombre-patologia "Ataque severo de Pulgon / Afidos (Aphis gossypii / Myzus persicae)")
      (tipo-agente insecto-plaga)
      (severidad media)
      (control-invernadero "Lavado foliar con jabon potasico para retirar melaza y evitar hongo negrilla. Liberar mariquitas (Coccinelidos) o avispillas (Aphidius colemani)."))))"""

REGLA_DAMPING_OFF = """(defrule regla-damping-off
   (fase (actual inferencia))
   (sintoma (organo tallo-cuello) (apariencia cuello-podrido))
   =>
   (assert (diagnostico
      (nombre-patologia "Damping-off o Caida de Plantulas (Pythium / Rhizoctonia)")
      (tipo-agente hongo)
      (severidad critica)
      (control-invernadero "Desinfectar sustratos y bandejas de siembra con vapor o agua oxigenada. Reducir frecuencia de riego en semillero e inocular con Trichoderma harzianum."))))"""

REGLA_PODREDUMBRE_APICAL = """(defrule regla-podredumbre-apical
   (fase (actual inferencia))
   (sintoma (cultivo tomate | pimiento) (organo fruto) (apariencia mancha-negra-fruto))
   =>
   (assert (diagnostico
      (nombre-patologia "Podredumbre Apical / Blossom End Rot (Deficiencia de Calcio / Riego irregular)")
      (tipo-agente desorden-abiotico)
      (severidad media)
      (control-invernadero "No es un patogeno contagioso. Homogeneizar los pulsos de fertirriego (evitar que el sustrato se seque) y aplicar aporte foliar de Nitrato o Quelato de Calcio."))))"""

REGLA_NEMATODOS = """(defrule regla-nematodos
   (fase (actual inferencia))
   (sintoma (organo raices) (apariencia nodulos-agallas))
   =>
   (assert (diagnostico
      (nombre-patologia "Nematodos Fitoparasitos Agalladores (Meloidogyne spp.)")
      (tipo-agente nematodo)
      (severidad alta)
      (control-invernadero "Solarizacion del suelo en verano entre ciclos. Incorporar materia organica biofumigante (mostaza/col) y aplicar nematicidas biologicos (Paecilomyces lilacinus)."))))"""

REGLA_SIN_COINCIDENCIA = """(defrule regla-sin-coincidencia
   (declare (salience -5))
   (fase (actual inferencia))
   (not (diagnostico))
   =>
   (assert (diagnostico
      (nombre-patologia "Patologia o anomalia no catalogada con el patron ingresado")
      (tipo-agente desconocido)
      (severidad baja)
      (control-invernadero "Aislar la planta afectada preventivamente y enviar muestra a laboratorio fitosanitario para analisis bacteriologico/virologico."))))"""

REGLA_PASAR_A_RESULTADO = """(defrule pasar-a-resultado
   (declare (salience -10))
   ?f <- (fase (actual inferencia))
   =>
   (modify ?f (actual resultado)))"""

CLIPS_LOGIC = [
    TEMPLATE_FASE, TEMPLATE_SINTOMA, TEMPLATE_DIAGNOSTICO,
    REGLA_BOTRYTIS, REGLA_MOSCA_BLANCA, REGLA_OIDIO, REGLA_TRIPS,
    REGLA_MILDIU, REGLA_PULGONES, REGLA_DAMPING_OFF, REGLA_PODREDUMBRE_APICAL,
    REGLA_NEMATODOS, REGLA_SIN_COINCIDENCIA, REGLA_PASAR_A_RESULTADO
]


# ==============================================================================
#  [2] INTERFAZ GRÁFICA (PYTHON + TKINTER)
# ==============================================================================

# Paleta de colores corporativa (tema "invernadero")
COLOR_BG = "#F3F6F3"            # fondo general
COLOR_PANEL = "#FFFFFF"         # fondo de tarjetas/paneles
COLOR_PRIMARY = "#1F6D3D"       # verde principal (marca)
COLOR_PRIMARY_DARK = "#164F2C"  # verde oscuro (hover)
COLOR_ACCENT = "#2E9E5B"        # verde acento
COLOR_TEXT = "#1E2A22"          # texto principal
COLOR_MUTED = "#5B6B60"         # texto secundario
COLOR_BORDER = "#DCE5DD"        # bordes suaves

SEVERIDAD_COLORES = {
    "baja": ("#2E7D32", "#E8F5E9"),
    "media": ("#B8860B", "#FFF8E1"),
    "alta": ("#D2691E", "#FFF1E6"),
    "critica": ("#C62828", "#FDECEA"),
}

FONT_FAMILY = "Segoe UI"


class InvernaderoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Experto · Fitosanidad de Invernaderos")
        self.root.geometry("780x760")
        self.root.minsize(680, 640)
        self.root.configure(bg=COLOR_BG)

        self._configurar_estilos()
        self._construir_layout()

    # --------------------------------------------------------------------
    #  Estilos ttk
    # --------------------------------------------------------------------
    def _configurar_estilos(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background=COLOR_BG)
        style.configure("Header.TFrame", background=COLOR_PRIMARY)
        style.configure("Card.TFrame", background=COLOR_PANEL)

        style.configure(
            "Header.TLabel",
            background=COLOR_PRIMARY,
            foreground="#FFFFFF",
            font=(FONT_FAMILY, 18, "bold"),
        )
        style.configure(
            "SubHeader.TLabel",
            background=COLOR_PRIMARY,
            foreground="#DDEFE2",
            font=(FONT_FAMILY, 10),
        )
        style.configure(
            "SectionTitle.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_PRIMARY_DARK,
            font=(FONT_FAMILY, 12, "bold"),
        )
        style.configure(
            "FieldLabel.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_TEXT,
            font=(FONT_FAMILY, 10, "bold"),
        )
        style.configure(
            "Hint.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_MUTED,
            font=(FONT_FAMILY, 8),
        )
        style.configure(
            "Status.TLabel",
            background=COLOR_BG,
            foreground=COLOR_MUTED,
            font=(FONT_FAMILY, 9),
        )

        style.configure(
            "TCombobox",
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground=COLOR_TEXT,
            arrowcolor=COLOR_PRIMARY_DARK,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#FFFFFF")],
            bordercolor=[("focus", COLOR_ACCENT)],
        )

        style.configure(
            "Accent.TButton",
            background=COLOR_PRIMARY,
            foreground="#FFFFFF",
            font=(FONT_FAMILY, 11, "bold"),
            padding=(18, 10),
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", COLOR_PRIMARY_DARK), ("pressed", COLOR_PRIMARY_DARK)],
        )

    # --------------------------------------------------------------------
    #  Construcción del layout
    # --------------------------------------------------------------------
    def _construir_layout(self):
        # ---------- Encabezado ----------
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(24, 18))
        header.pack(fill="x")

        ttk.Label(header, text="🌱  Diagnóstico Fitosanitario de Invernadero", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Sistema experto basado en CLIPS para el manejo integrado de plagas y enfermedades",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        # ---------- Cuerpo ----------
        body = ttk.Frame(self.root, style="App.TFrame", padding=(24, 18))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        # ----- Tarjeta de entradas -----
        card_inputs = tk.Frame(body, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_inputs.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        inner_inputs = ttk.Frame(card_inputs, style="Card.TFrame", padding=(20, 16))
        inner_inputs.pack(fill="both", expand=True)
        inner_inputs.columnconfigure(1, weight=1)

        ttk.Label(inner_inputs, text="Observaciones del cultivo", style="SectionTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 2)
        )
        ttk.Label(
            inner_inputs,
            text="Seleccione una opción para cada categoría según lo observado en planta.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        # Configuraciones de las opciones (IDÉNTICAS a los allowed-values en CLIPS)
        self.opciones = {
            "🌾  Cultivo": ["tomate", "pimiento", "pepino", "lechuga", "fresa", "ornamental", "otro"],
            "🍃  Órgano principal": ["hojas", "fruto", "flores", "tallo-cuello", "raices"],
            "🔎  Apariencia / lesión": ["moho-gris", "polvo-blanco", "manchas-angulares", "manchas-plateadas", "melaza-hoja-arrugada", "cuello-podrido", "mancha-negra-fruto", "nodulos-agallas", "ninguno"],
            "🐛  Plaga visible": ["mosquitas-blancas", "pulgones", "bichitos-diminutos", "ninguno"],
            "🌡️  Microclima": ["alta-humedad-cerrado", "templado-seco", "normal"],
        }

        self.comboboxes = {}

        fila = 2
        for etiqueta, valores in self.opciones.items():
            ttk.Label(inner_inputs, text=etiqueta, style="FieldLabel.TLabel").grid(
                row=fila, column=0, sticky="w", pady=8, padx=(0, 12)
            )
            cb = ttk.Combobox(inner_inputs, values=valores, state="readonly", font=(FONT_FAMILY, 10))
            cb.grid(row=fila, column=1, sticky="ew", pady=8)
            cb.set("")
            self.comboboxes[etiqueta] = cb
            fila += 1

        # Botón de acción
        btn_bar = ttk.Frame(inner_inputs, style="Card.TFrame")
        btn_bar.grid(row=fila, column=0, columnspan=2, sticky="e", pady=(14, 0))

        self.btn_diagnosticar = ttk.Button(
            btn_bar, text="🔬  Generar diagnóstico", style="Accent.TButton", command=self.ejecutar_diagnostico
        )
        self.btn_diagnosticar.pack(side="right")

        ttk.Button(btn_bar, text="Limpiar", command=self._limpiar_formulario).pack(side="right", padx=(0, 10))

        # ----- Tarjeta de resultados -----
        card_resultado = tk.Frame(body, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_resultado.grid(row=1, column=0, sticky="nsew")

        inner_resultado = ttk.Frame(card_resultado, style="Card.TFrame", padding=(20, 16))
        inner_resultado.pack(fill="both", expand=True)
        inner_resultado.columnconfigure(0, weight=1)
        inner_resultado.rowconfigure(2, weight=1)

        ttk.Label(inner_resultado, text="Dictamen técnico fitosanitario", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        # Insignia de severidad (se actualiza dinámicamente)
        self.badge_severidad = tk.Label(
            inner_resultado,
            text="Sin diagnóstico",
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_MUTED,
            bg="#EEF2EF",
            padx=10,
            pady=3,
        )
        self.badge_severidad.grid(row=1, column=0, sticky="w", pady=(6, 12))

        text_frame = tk.Frame(inner_resultado, bg=COLOR_PANEL)
        text_frame.grid(row=2, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.lbl_resultado_texto = tk.Text(
            text_frame,
            wrap="word",
            font=(FONT_FAMILY, 11),
            bg="#FBFDFB",
            fg=COLOR_TEXT,
            relief="flat",
            padx=14,
            pady=12,
            state="disabled",
            spacing3=6,
        )
        self.lbl_resultado_texto.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.lbl_resultado_texto.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.lbl_resultado_texto.configure(yscrollcommand=scrollbar.set)

        # Estilos de texto (tags) para el informe
        self.lbl_resultado_texto.tag_configure(
            "titulo", font=(FONT_FAMILY, 10, "bold"), foreground=COLOR_PRIMARY_DARK, spacing1=8
        )
        self.lbl_resultado_texto.tag_configure("valor", font=(FONT_FAMILY, 11), foreground=COLOR_TEXT)
        self.lbl_resultado_texto.tag_configure(
            "placeholder", font=(FONT_FAMILY, 10, "italic"), foreground=COLOR_MUTED
        )
        self._mostrar_placeholder()

        # ---------- Barra de estado ----------
        footer = ttk.Frame(self.root, style="App.TFrame", padding=(24, 0, 24, 12))
        footer.pack(fill="x")
        self.lbl_estado = ttk.Label(footer, text="Listo para diagnosticar.", style="Status.TLabel")
        self.lbl_estado.pack(anchor="w")

    # --------------------------------------------------------------------
    #  Utilidades de interfaz
    # --------------------------------------------------------------------
    def _mostrar_placeholder(self):
        self.lbl_resultado_texto.config(state="normal")
        self.lbl_resultado_texto.delete("1.0", tk.END)
        self.lbl_resultado_texto.insert(
            tk.END,
            "Complete el formulario y presione «Generar diagnóstico» para ver aquí el "
            "dictamen técnico y el protocolo de manejo recomendado.",
            "placeholder",
        )
        self.lbl_resultado_texto.config(state="disabled")

    def _limpiar_formulario(self):
        for cb in self.comboboxes.values():
            cb.set("")
        self._mostrar_placeholder()
        self.badge_severidad.config(text="Sin diagnóstico", fg=COLOR_MUTED, bg="#EEF2EF")
        self.lbl_estado.config(text="Formulario limpiado.")

    def _actualizar_badge(self, severidad):
        color_fg, color_bg = SEVERIDAD_COLORES.get(severidad, (COLOR_MUTED, "#EEF2EF"))
        self.badge_severidad.config(
            text=f"Severidad: {severidad.upper()}", fg=color_fg, bg=color_bg
        )

    def _renderizar_informe(self, cultivo, diagnostico):
        self.lbl_resultado_texto.config(state="normal")
        self.lbl_resultado_texto.delete("1.0", tk.END)

        secciones = [
            ("CULTIVO ANALIZADO", cultivo.upper()),
            ("PROBLEMA DIAGNOSTICADO", diagnostico["patologia"]),
            ("TIPO DE PATÓGENO / CAUSA", str(diagnostico["agente"]).upper()),
            ("NIVEL DE SEVERIDAD", str(diagnostico["severidad"]).upper()),
            ("PROTOCOLO DE MANEJO INTEGRADO", diagnostico["control"]),
        ]

        for i, (titulo, valor) in enumerate(secciones):
            self.lbl_resultado_texto.insert(tk.END, f"{titulo}\n", "titulo")
            self.lbl_resultado_texto.insert(tk.END, f"{valor}\n", "valor")
            if i < len(secciones) - 1:
                self.lbl_resultado_texto.insert(tk.END, "\n")

        self.lbl_resultado_texto.config(state="disabled")

    # --------------------------------------------------------------------
    #  Lógica de diagnóstico (sin cambios respecto al motor CLIPS)
    # --------------------------------------------------------------------
    def ejecutar_diagnostico(self):
        # 1. Obtener valores de la interfaz
        valores_seleccionados = [cb.get() for cb in self.comboboxes.values()]

        # Validar que todos tengan algo seleccionado
        if "" in valores_seleccionados:
            messagebox.showwarning("Campos incompletos", "Por favor, selecciona una opción para cada categoría.")
            return

        cultivo, organo, apariencia, plaga, microclima = valores_seleccionados
        self.lbl_estado.config(text="Ejecutando motor de inferencia CLIPS…")
        self.root.update_idletasks()

        # 2. Inicializar Motor CLIPS
        env = clips.Environment()
        for constructo in CLIPS_LOGIC:
            try:
                env.build(constructo)
            except clips.CLIPSError as error:
                messagebox.showerror("Error CLIPS", f"Fallo al compilar lógica:\n{error}")
                self.lbl_estado.config(text="Error al compilar la base de conocimiento.")
                return

        env.reset()

        # 3. Inyectar los hechos directamente al motor (Reemplaza las preguntas por consola)
        hecho_sintoma = f"(sintoma (cultivo {cultivo}) (organo {organo}) (apariencia {apariencia}) (plaga-visible {plaga}) (microclima {microclima}))"
        env.assert_string(hecho_sintoma)
        env.assert_string("(fase (actual inferencia))")

        # 4. Ejecutar el razonamiento
        env.run()

        # 5. Extraer y mostrar resultados
        diagnostico_final = None
        for fact in env.facts():
            if fact.template.name == "diagnostico":
                diagnostico_final = {
                    "patologia": fact["nombre-patologia"],
                    "agente": fact["tipo-agente"],
                    "severidad": fact["severidad"],
                    "control": fact["control-invernadero"]
                }
                break

        if diagnostico_final:
            self._renderizar_informe(cultivo, diagnostico_final)
            self._actualizar_badge(str(diagnostico_final["severidad"]))
            self.lbl_estado.config(text="Diagnóstico generado correctamente.")
        else:
            self.lbl_estado.config(text="El motor no produjo un diagnóstico.")


if __name__ == "__main__":
    app = tk.Tk()
    gui = InvernaderoGUI(app)
    app.mainloop()
