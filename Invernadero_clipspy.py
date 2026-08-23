#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import clips
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

class InvernaderoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Experto :: Fitosanidad de Invernaderos")
        self.root.geometry("650x700")
        self.root.configure(padx=20, pady=20)

        # Título principal
        lbl_titulo = ttk.Label(root, text="Diagnóstico Fitosanitario de Cultivos", font=("Helvetica", 16, "bold"))
        lbl_titulo.pack()

        # Frame de Entradas
        frame_inputs = ttk.LabelFrame(root, text=" Ingrese los datos observados ", padding=(15, 15))
        frame_inputs.pack(fill="x", pady=10)

        # Configuraciones de las opciones (IDÉNTICAS a los allowed-values en CLIPS)
        self.opciones = {
            "Cultivo:": ["tomate", "pimiento", "pepino", "lechuga", "fresa", "ornamental", "otro"],
            "Órgano Principal:": ["hojas", "fruto", "flores", "tallo-cuello", "raices"],
            "Apariencia / Lesión:": ["moho-gris", "polvo-blanco", "manchas-angulares", "manchas-plateadas", "melaza-hoja-arrugada", "cuello-podrido", "mancha-negra-fruto", "nodulos-agallas", "ninguno"],
            "Plaga Visible:": ["mosquitas-blancas", "pulgones", "bichitos-diminutos", "ninguno"],
            "Microclima:": ["alta-humedad-cerrado", "templado-seco", "normal"]
        }

        self.comboboxes = {}

        # Crear los labels y comboboxes
        row = 0
        for label_text, valores in self.opciones.items():
            ttk.Label(frame_inputs, text=label_text, font=("Helvetica", 10, "bold")).grid(row=row, column=0, sticky="w", pady=8, padx=5)
            # Combobox con estado "readonly" para que solo se pueda seleccionar y no escribir.
            cb = ttk.Combobox(frame_inputs, values=valores, state="readonly", width=30)
            cb.grid(row=row, column=1, sticky="w", pady=8, padx=5)
            self.comboboxes[label_text] = cb
            row += 1

        # Botón de acción
        btn_diagnosticar = ttk.Button(root, text="Generar Diagnóstico", command=self.ejecutar_diagnostico)
        btn_diagnosticar.pack(pady=20)

        # Frame de Resultados
        self.frame_resultados = ttk.LabelFrame(root, text=" Dictamen Técnico Fitosanitario ", padding=(15, 15))
        self.frame_resultados.pack(fill="both", expand=True)

        self.lbl_resultado_texto = tk.Text(self.frame_resultados, wrap="word", font=("Helvetica", 11), height=10, bg="#f4f4f4", state="disabled")
        self.lbl_resultado_texto.pack(fill="both", expand=True)

    def ejecutar_diagnostico(self):
        # 1. Obtener valores de la interfaz
        valores_seleccionados = [cb.get() for cb in self.comboboxes.values()]

        # Validar que todos tengan algo seleccionado
        if "" in valores_seleccionados:
            messagebox.showwarning("Campos incompletos", "Por favor, selecciona una opción para cada categoría.")
            return

        cultivo, organo, apariencia, plaga, microclima = valores_seleccionados

        # 2. Inicializar Motor CLIPS
        env = clips.Environment()
        for constructo in CLIPS_LOGIC:
            try:
                env.build(constructo)
            except clips.CLIPSError as error:
                messagebox.showerror("Error CLIPS", f"Fallo al compilar lógica:\n{error}")
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
            texto_informe = (
                f"CULTIVO ANALIZADO:\n{cultivo.upper()}\n\n"
                f"PROBLEMA DIAGNOSTICADO:\n{diagnostico_final['patologia']}\n\n"
                f"TIPO DE PATÓGENO / CAUSA:\n{str(diagnostico_final['agente']).upper()}\n\n"
                f"NIVEL DE SEVERIDAD:\n{str(diagnostico_final['severidad']).upper()}\n\n"
                f"PROTOCOLO DE MANEJO INTEGRADO:\n{diagnostico_final['control']}"
            )

            # Actualizar el panel de texto
            self.lbl_resultado_texto.config(state="normal")
            self.lbl_resultado_texto.delete(1.0, tk.END)
            self.lbl_resultado_texto.insert(tk.END, texto_informe)
            self.lbl_resultado_texto.config(state="disabled")

if __name__ == "__main__":
    app = tk.Tk()

    # Intento de mejora visual (tema nativo de sistema)
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")

    gui = InvernaderoGUI(app)
    app.mainloop()
