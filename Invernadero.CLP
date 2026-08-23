;;; ============================================================================
;;;  +------------------------------------------------------------------------+
;;;  ¦     SISTEMA EXPERTO :: FITOSANIDAD DE CULTIVOS BAJO INVERNADERO        ¦
;;;  ¦     Diagnostico de Plagas y Enfermedades Protegidas | CLIPSide64       ¦
;;;  +------------------------------------------------------------------------+
;;; ============================================================================


;;; ============================================================================
;;;  >>> [1] ESTRUCTURAS Y PLANTILLAS DE DATOS <<<
;;; ============================================================================

(deftemplate fase
   (slot actual (type SYMBOL) (allowed-values inicio preguntas inferencia resultado fin)))

(deftemplate sintoma
   (slot cultivo (type SYMBOL) (allowed-values tomate pimiento pepino lechuga fresa ornamental otro))
   (slot organo (type SYMBOL) (allowed-values hojas fruto flores tallo-cuello raices))
   (slot apariencia (type SYMBOL) (allowed-values moho-gris polvo-blanco manchas-angulares manchas-plateadas melaza-hoja-arrugada cuello-podrido mancha-negra-fruto nodulos-agallas ninguno))
   (slot plaga-visible (type SYMBOL) (allowed-values mosquitas-blancas pulgones bichitos-diminutos ninguno))
   (slot microclima (type SYMBOL) (allowed-values alta-humedad-cerrado templado-seco normal)))

(deftemplate diagnostico
   (slot nombre-patologia (type STRING))
   (slot tipo-agente (type SYMBOL) (allowed-values hongo insecto-plaga nematodo desorden-abiotico desconocido))
   (slot severidad (type SYMBOL) (allowed-values baja media alta critica))
   (slot control-invernadero (type STRING)))


;;; ============================================================================
;;;  >>> [2] HECHOS INICIALES <<<
;;; ============================================================================

(deffacts estado-inicial
   (fase (actual inicio)))


;;; ============================================================================
;;;  >>> [3] FUNCION AUXILIAR DE VALIDACION <<<
;;; ============================================================================

(deffunction preguntar-opcion (?pregunta $?opciones)
   (printout t ?pregunta " ")
   (bind ?resp (read))
   (while (not (member$ ?resp ?opciones)) do
      (printout t "  [!] Entrada no valida. Elija exactamente entre: " ?opciones crlf)
      (printout t ?pregunta " ")
      (bind ?resp (read))
   )
   (return ?resp)
)


;;; ============================================================================
;;;  >>> [4] INTERACCION CON EL OPERADOR DE INVERNADERO <<<
;;; ============================================================================

(defrule bienvenida
   ?f <- (fase (actual inicio))
   =>
   (printout t crlf)
   (printout t "+------------------------------------------------------------------+" crlf)
   (printout t "|   SISTEMA EXPERTO :: DIAGNOSTICO FITOSANITARIO DE INVERNADERO    |" crlf)
   (printout t "|     -- Evaluacion Clinica de Cultivos en Ambiente Protegido --   |" crlf)
   (printout t "+------------------------------------------------------------------+" crlf)
   (printout t "| Ingrese las opciones en minusculas tal como aparecen en la guia. |" crlf)
   (printout t "+------------------------------------------------------------------+" crlf crlf)
   (modify ?f (actual preguntas))
)

(defrule recopilar-datos-invernadero
   ?f <- (fase (actual preguntas))
   =>
   ;; 1. Tipo de cultivo
   (bind ?cul (preguntar-opcion 
      "[?] 1. Cultivo afectado? (tomate / pimiento / pepino / lechuga / fresa / ornamental / otro):" 
      tomate pimiento pepino lechuga fresa ornamental otro))

   ;; 2. Órgano principal
   (bind ?org (preguntar-opcion 
      "[?] 2. Parte de la planta con mayor dano? (hojas / fruto / flores / tallo-cuello / raices):" 
      hojas fruto flores tallo-cuello raices))

   ;; 3. Síntoma o lesión visual
   (bind ?ap (preguntar-opcion 
      "[?] 3. Lesion o aspecto principal? (moho-gris / polvo-blanco / manchas-angulares / manchas-plateadas / melaza-hoja-arrugada / cuello-podrido / mancha-negra-fruto / nodulos-agallas / ninguno):" 
      moho-gris polvo-blanco manchas-angulares manchas-plateadas melaza-hoja-arrugada cuello-podrido mancha-negra-fruto nodulos-agallas ninguno))

   ;; 4. Presencia de insectos vectores
   (bind ?plg (preguntar-opcion 
      "[?] 4. Observa insectos en el enves o vuelo al sacudir? (mosquitas-blancas / pulgones / bichitos-diminutos / ninguno):" 
      mosquitas-blancas pulgones bichitos-diminutos ninguno))

   ;; 5. Ambiente / Ventilación
   (bind ?amb (preguntar-opcion 
      "[?] 5. Condicion ambiental reciente? (alta-humedad-cerrado / templado-seco / normal):" 
      alta-humedad-cerrado templado-seco normal))

   (assert (sintoma 
      (cultivo ?cul) 
      (organo ?org) 
      (apariencia ?ap) 
      (plaga-visible ?plg) 
      (microclima ?amb)))

   (modify ?f (actual inferencia))
)


;;; ============================================================================
;;;  >>> [5] BASE DE CONOCIMIENTO (PATOLOGIAS COMUNES DE INVERNADERO) <<<
;;; ============================================================================

;; 1. BOTRYTIS / MOHO GRIS (El hongo #1 en invernaderos húmedos)
(defrule regla-botrytis
   (fase (actual inferencia))
   (sintoma (organo flores | fruto | hojas | tallo-cuello) (apariencia moho-gris))
   =>
   (assert (diagnostico
      (nombre-patologia "Moho Gris / Podredumbre Gris (Botrytis cinerea)")
      (tipo-agente hongo)
      (severidad critica)
      (control-invernadero "URGENTE: Abrir ventilaciones laterales/cenitales para bajar humedad <75%. Retirar partes con bolsa plastica para evitar esporas. Aplicar fungicidas especificos (Iprodiona, Cyprodinil o Bacillus subtilis).")))
)

;; 2. MOSCA BLANCA (La plaga más destructiva y vector de virus)
(defrule regla-mosca-blanca
   (fase (actual inferencia))
   (sintoma (plaga-visible mosquitas-blancas))
   =>
   (assert (diagnostico
      (nombre-patologia "Infestacion por Mosca Blanca (Bemisia tabaci / Trialeurodes)")
      (tipo-agente insecto-plaga)
      (severidad alta)
      (control-invernadero "Instalar trampas cromaticas adhesivas amarillas. Realizar suelta de parasitoides (Encarsia formosa) o aplicar jabon potasico + extracto de neem al atardecer.")))
)

;; 3. OÍDIO / CENICILLA (Frecuente en cucurbitáceas y solanáceas)
(defrule regla-oidio
   (fase (actual inferencia))
   (sintoma (organo hojas) (apariencia polvo-blanco))
   =>
   (assert (diagnostico
      (nombre-patologia "Oidio / Ceniza blanca (Erysiphe / Leveillula taurica)")
      (tipo-agente hongo)
      (severidad media)
      (control-invernadero "Aumentar separacion de plantas para permitir paso de luz. Aplicar azufre por sublimacion/pulverizacion o bicarbonato potasico. Evitar estres termico.")))
)

;; 4. TRIPS DE LAS FLORES (Plaga que causa plateado y transmite virus TSWV)
(defrule regla-trips
   (fase (actual inferencia))
   (sintoma (apariencia manchas-plateadas) (plaga-visible bichitos-diminutos | ninguno))
   =>
   (assert (diagnostico
      (nombre-patologia "Ataque de Trips (Frankliniella occidentalis)")
      (tipo-agente insecto-plaga)
      (severidad alta)
      (control-invernadero "Colocar placas adhesivas azules a la altura del dosel. Introducir acaros depredadores (Amblyseius swirskii / Orius laevigatus) y monitorear transmision de virus.")))
)

;; 5. MILDIU VELLOSO (Común en lechuga, pepino y espinaca)
(defrule regla-mildiu
   (fase (actual inferencia))
   (sintoma (organo hojas) (apariencia manchas-angulares) (microclima alta-humedad-cerrado))
   =>
   (assert (diagnostico
      (nombre-patologia "Mildiu Velloso (Pseudoperonospora / Bremia lactucae)")
      (tipo-agente hongo)
      (severidad alta)
      (control-invernadero "Evitar condensacion en el techo del plastico. Suspender riego por aspersion; regar solo por goteo matutino. Aplicar fungicidas sistemicos (Metalaxil o Fosetil-Al).")))
)

;; 6. PULGONES / ÁFIDOS
(defrule regla-pulgones
   (fase (actual inferencia))
   (sintoma (apariencia melaza-hoja-arrugada) (plaga-visible pulgones))
   =>
   (assert (diagnostico
      (nombre-patologia "Ataque severo de Pulgon / Afidos (Aphis gossypii / Myzus persicae)")
      (tipo-agente insecto-plaga)
      (severidad media)
      (control-invernadero "Lavado foliar con jabon potasico para retirar melaza y evitar hongo negrilla. Liberar mariquitas (Coccinelidos) o avispillas (Aphidius colemani).")))
)

;; 7. DAMPING-OFF / AHOGAMIENTO DE PLÁNTULAS (Crítico en semilleros/bandejas)
(defrule regla-damping-off
   (fase (actual inferencia))
   (sintoma (organo tallo-cuello) (apariencia cuello-podrido))
   =>
   (assert (diagnostico
      (nombre-patologia "Damping-off o Caida de Plantulas (Pythium / Rhizoctonia)")
      (tipo-agente hongo)
      (severidad critica)
      (control-invernadero "Desinfectar sustratos y bandejas de siembra con vapor o agua oxigenada. Reducir frecuencia de riego en semillero e inocular con Trichoderma harzianum.")))
)

;; 8. PODREDUMBRE APICAL / CULILLO (Desorden fisiológico en tomate/pimiento)
(defrule regla-podredumbre-apical
   (fase (actual inferencia))
   (sintoma (cultivo tomate | pimiento) (organo fruto) (apariencia mancha-negra-fruto))
   =>
   (assert (diagnostico
      (nombre-patologia "Podredumbre Apical / Blossom End Rot (Deficiencia de Calcio / Riego irregular)")
      (tipo-agente desorden-abiotico)
      (severidad media)
      (control-invernadero "No es un patogeno contagioso. Homogeneizar los pulsos de fertirriego (evitar que el sustrato se seque) y aplicar aporte foliar de Nitrato o Quelato de Calcio.")))
)

;; 9. NEMATODOS DE LAS AGALLAS (En suelo o sustrato reutilizado)
(defrule regla-nematodos
   (fase (actual inferencia))
   (sintoma (organo raices) (apariencia nodulos-agallas))
   =>
   (assert (diagnostico
      (nombre-patologia "Nematodos Fitoparasitos Agalladores (Meloidogyne spp.)")
      (tipo-agente nematodo)
      (severidad alta)
      (control-invernadero "Solarizacion del suelo en verano entre ciclos. Incorporar materia organica biofumigante (mostaza/col) y aplicar nematicidas biologicos (Paecilomyces lilacinus).")))
)

;; Regla por defecto
(defrule regla-sin-coincidencia
   (declare (salience -5))
   (fase (actual inferencia))
   (not (diagnostico))
   =>
   (assert (diagnostico
      (nombre-patologia "Patologia o anomalia no catalogada con el patron ingresado")
      (tipo-agente desconocido)
      (severidad baja)
      (control-invernadero "Aislar la planta afectada preventivamente y enviar muestra a laboratorio fitosanitario para analisis bacteriologico/virologico.")))
)

;; Cambio de fase a resultado
(defrule pasar-a-resultado
   (declare (salience -10))
   ?f <- (fase (actual inferencia))
   =>
   (modify ?f (actual resultado))
)


;;; ============================================================================
;;;  >>> [6] REPORTE FITOSANITARIO DE RESULTADOS <<<
;;; ============================================================================

(defrule imprimir-informe-tecnico
   (fase (actual resultado))
   (sintoma (cultivo ?cul))
   (diagnostico (nombre-patologia ?pat) (tipo-agente ?ag) (severidad ?sev) (control-invernadero ?ctrl))
   =>
   (printout t crlf)
   (printout t "+==================================================================+" crlf)
   (printout t "|        DICTAMEN TECNICO FITOSANITARIO DE CULTIVO PROTEGIDO       |" crlf)
   (printout t "+==================================================================+" crlf)
   (printout t "  [+] CULTIVO ANALIZADO   : " ?cul crlf)
   (printout t "  [+] PROBLEMA DIAGNOSTICADO : " ?pat crlf)
   (printout t "  [+] TIPO DE PATOGENO / CAUSA : " ?ag crlf)
   (printout t "  [+] NIVEL DE SEVERIDAD  : " ?sev crlf)
   (printout t "+------------------------------------------------------------------+" crlf)
   (printout t "  [>] PROTOCOLO DE MANEJO INTEGRADO EN INVERNADERO:" crlf)
   (printout t "      " ?ctrl crlf)
   (printout t "+==================================================================+" crlf crlf)
)