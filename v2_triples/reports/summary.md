# v2_triples summary

Each Excel row is mapped to the statement it describes; its Attribute, Deontic and Direct Object cells are looked up in the statement's own text, allowing whitespace / case / Spanish accent differences (so Excel `amoniaco` matches `amoníaco`). Bracketed cells (`[Titulares de] Buses`, `[deberá]`, …) are implicit by convention and skipped. Any cell that still can't be found is dropped and counted in the non-literal ratio below. There is no event trigger: every pair of literal spans in the same row becomes one brat binary relation (AttrDeontic, AttrObject, DeonticObject).

**Validation: PASSED**

## Row outcomes

| status | rows |
|---|---|
| complete (A + D + O literal, 3 relations) | 18 |
| pair (2 literal roles, 1 relation) | 84 |
| single (1 literal role, 0 relations) | 113 |
| no literal span (row kept text, no spans) | 108 |
| all three cells empty (skipped) | 42 |
| **Excel rows total** | 365 |

## Literal vs. non-literal per role

A cell is **non-literal** when it is bracketed (implicit value) or when it is non-bracketed but doesn't appear in the statement's text even after whitespace / case / accent folding. Empty cells are excluded from the ratio.

| role | with value | literal | non-literal | non-literal ratio | empty cells |
|---|---|---|---|---|---|
| Attribute | 323 | 116 | 207 | 64.1% | 42 |
| Deontic | 323 | 106 | 217 | 67.2% | 42 |
| DirectObject | 322 | 113 | 209 | 64.9% | 43 |

## Spans and relations written

| kind | count |
|---|---|
| Attribute | 116 |
| Deontic | 106 |
| DirectObject | 113 |
| **T total** | 335 |
| R AttrDeontic | 38 |
| R AttrObject | 46 |
| R DeonticObject | 54 |
| **R total** | 138 |

## Non-literal rows

Non-bracketed Excel cells that still don't appear literally in the statement text, grouped by role. Full per-row detail: `reports/join.csv`, `reports/edge_cases.csv`.

<details>
<summary>attribute (28)</summary>

| stmt_no | excel_value |
|---|---|
| 32 | Ministerio del Medio Ambiente |
| 39 | Secretaría Regional Ministerial del Medio Ambiente de la RM |
| 43 | Los fabricantes de maquinaria móvil fuera de ruta nueva o sus representantes legales en Chile, distribuidores o importadores |
| 67 | empresas distribuidoras de combustibles |
| 84 | Operadores de las instalaciones de almacenamiento/distribución de combustibles líquidos Clase I |
| 108 | Superintendencia del Medio Ambiente |
| 195 | Fabricantes representantes legales de grupos electrógenos, o sus distribuidores o importadores |
| 202 | Empresas productora de cerdos |
| 205 | Titulares de planteles de porcinos |
| 227 | Ministerio del Medio Ambiente |
| 270 | Servicio Agrícola y Ganadero Servicio Agrícola y Ganadero (SAG), y a la Corporación Nacional Forestal (CONAF) |
| 271 | Corporación Nacional Forestal |
| 283 | Gobierno Regional Metropolitano de Santiagoel Gobierno Regional de la Región Metropolitana de Santiago, en coordinación con el Ministerio de Vivienda y Urbanismo, el Ministerio de Obras Públicas, el Ministerio deTransportes y Telecomunicaciones, y otras instituciones con atribuciones para la construcción de infraestructura pública |
| 305 | SEREMI del Medio Ambiente la SEREMI del Medio Ambiente en coordinación con la SEREMI de Energía RM y la SEREMI de Vivienda y Urbanismo RM |
| 306 | La SEREMI del Medio Ambiente con el apoyo de la Intendencia Regional |
| 317 | Ministerio de Transportes y Telecomunicaciones |
| 319 | Ministerio de Agricultura a través de la CONAF |
| 323 | Ministerio de Transportes y Telecomunicaciones |
| 329 | Organismos competentes |
| 339 | Organismos competentes |
| 342 | Ministerio de Transportes y Telecomunicaciones |
| 346 | SEREMI de Salud |
| 347 | SEREMI de Educación RM |
| 349 | Organismos competentes |
| 350 | Gobierno Regional de la Región Metropolitana de Santiago |
| 354 | Intendente |
| 361 | Superintendencia del Medio Ambiente |
| 364 | Servicios públicos |

</details>

<details>
<summary>deontic (49)</summary>

| stmt_no | excel_value |
|---|---|
| 12 | solo podrán |
| 18 | deberán |
| 41 | deberá |
| 42 | deberá |
| 43 | deberán |
| 45 | deberá |
| 47 | deberá |
| 55 | podrá |
| 57 | deberán |
| 59 | deberá |
| 61 | deberá |
| 63 | deberá |
| 79 | deberán |
| 87 | deberá |
| 91 | deberán |
| 99 | deberán |
| 101 | deberán |
| 104 | deberán |
| 108 | deberá |
| 110 | deberán |
| 114 | deberán |
| 129 | debe |
| 130 | deberán |
| 131 | deberán |
| 133 | deberán |
| 136 | deberán |
| 140 | deberá |
| 152 | podrán |
| 157 | podrán |
| 176 | solo podrán |
| 178 | solo podrán |
| 179 | podrán |
| 184 | deberán |
| 187 | deberán |
| 189 | deberán |
| 192 | deberán |
| 193 | deberán |
| 194 | deberán |
| 199 | deberán |
| 202 | deberán |
| 203 | podrán |
| 208 | deberán |
| 242 | deberán |
| 248 | deberán |
| 267 | podrá |
| 283 | deberá |
| 334 | deberán |
| 344 | deberán |
| 347 | podrá |

</details>

<details>
<summary>object (181)</summary>

| stmt_no | excel_value |
|---|---|
| 8 | mismos procesos de análisis técnicos para homologación estandares vigentes |
| 10 | Programa de incentivos de Reducción de Emisiones y de Eficiencia Energetica |
| 13 | Programa de implementación de una zona de baja emisión en la RMS |
| 19 | establecimiento de marco normativo estandares eficiencia energética |
| 20 | estrategia de incentivos |
| 21 | cupo exclusivo de al menos 5% de las nuevas inscripciones |
| 22 | su motor |
| 23 | su motor |
| 27 | emisión continuada por el tubo de escape por mas de 5 segundos |
| 30 | Implementacion de Método de control de emisiones del número de partículas en la vía pública de vehiculos diesel |
| 32 | revisión normas de ingreso de vehículos livianos y medianos |
| 34 | etiqueta mencionada (ART 17) |
| 38 | cumplimiento de la medida (ART 18) |
| 41 | Tabla III 8. Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) y en gramos por caballos de fuerza al freno hora (g/bhp-h) |
| 43 | certificado de origen sobre tipo o familia de motor de la maquinaria nueva cumple con lo exigido (T 8, 9 o 10) |
| 45 | Requisitos para el combustible diésel tipo grado A1. Tabla IV-1 |
| 47 | Requisitos de propiedades de gasolina para motores de ignición. Tabla IV-2 |
| 54 | exigencia ART. 22 |
| 55 | la no aplicación de la exigencia de biocombustible |
| 56 | dicho combustible |
| 57 | Requisitos para petróleos combustibles grado 5 y 6 para uso en calderas y hornos de procesos industriales. Tabla IV-3 |
| 59 | Requisitos para el kerosene doméstico e industrial Tabla IV 4 |
| 61 | Requisitos para el gas licuado de petróleo de uso vehicular. Tabla IV-5 |
| 63 | Requisitos para el gas licuado de petróleo de uso doméstico, industrial y comercial. Tabla IV-6 |
| 68 | control de calidad |
| 74 | elementos permitan capturar vapores durante operaciones |
| 75 | de equipos de captura y porterior recuperación/ eliminación de vapores |
| 76 | equipos que recurpere / elimine 95% vapores |
| 79 | sistemas de recuperación de vapor |
| 81 | exigencias DS 160/2008 |
| 84 | informe que de cuenta del cumplimiento de las disposiciones contenidas y medidas que se adoptarán si fuese necesario, |
| 87 | envio informe anual de cumplimiento de todas las exigencias relacionadas con la recuperación de vapores |
| 91 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 92 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 93 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 94 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 95 | excepciones temporales |
| 96 | normas de emisión por conceptración del DS 13/2011 |
| 97 | limite de emisión para MP en 30 mg/m³N |
| 99 | condicion (art 37) |
| 100 | listado de aquellas calderas que cumplan con lo establecido en art 37 |
| 101 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 102 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 103 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 106 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 107 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 108 | evaluación del cumplimiento de las metas de emisión de 5 establecimientos |
| 109 | resultados de evaluación del cumplimiento de las metas de emisión de 5 establecimientos |
| 110 | Límite máximo de emisión de CO para fuentes estacionarias. Tabla VI-3 |
| 112 | Límite máximo de emisión de CO para fuentes estacionarias. Tabla VI-3 |
| 113 | Límite máximo de emisión de CO para fuentes estacionarias. Tabla VI-3 |
| 114 | Límite máximo de emisión de NOx para fuentes estacionarias. Tabla VI 4 |
| 122 | certificado de origen del fabricante que |
| 123 | registro de fuentes estacionarias de RMS |
| 126 | cambios de combustible u otra condicion que incida en emisiones |
| 129 | que no supera parámetros |
| 130 | mediciones con frecuencia descrita Tabla VI-7: Frecuencia de Medición |
| 131 | emisiones MP NOx So |
| 133 | instrumentación industrial |
| 135 | medidas en los gases de combustion que permitan estimar nivel de actividad de la fuente y sus emisiones |
| 137 | instrumentación |
| 138 | instrumentación |
| 140 | sistema de monitoreo continuo |
| 141 | acreditacion de emisiones con metodos de Art 46 |
| 144 | valores |
| 145 | datos del monitoreo continuo |
| 146 | protocolos cumplimiento art (54) |
| 156 | emisión másica superior a la autorizada vigente |
| 157 | procesos existentes con concentraciones máximas Tabla VI-11: Emisiones tope por contaminante para grandes establecimientos existentes. |
| 158 | Tabla VI-12: Límites máximos de emisión complementarios para fuentes estacionarias de grandes establecimientos existentes] |
| 161 | listado de grandes establecimeintos nuevos y existentes |
| 163 | planes de reducción de emisiones |
| 164 | aprobación e planes |
| 165 | criterios de evaluación indicados en los Artículos 63 y siguientes. |
| 166 | normas de emisión por concentración Art.58 |
| 169 | situación registrada repecto al cumplimiento de su emisión y compensación |
| 174 | programas de compensación de emisiones |
| 176 | emisiones |
| 177 | emisiones cedidas |
| 178 | emisiones por reduccion adicionales |
| 181 | emisiones de las modificaciones o ampliaciones |
| 184 | condiciones Tabla VI-14: Emisión máxima proyectos |
| 186 | programa preliminar de compensaciones de emisiones |
| 191 | estudio de emisiones COV |
| 192 | limites máximos de emision de CO, HC, HCNM, NOx MP |
| 196 | certificado de origen |
| 197 | protocolo para el desarrollo de la medición |
| 199 | mantenciones al motor y todos sus componentes |
| 202 | medidas para reducir emisiones de amoniaco |
| 203 | reducciones |
| 205 | plan de cumplimiento de exigencia art 70 |
| 206 | plan de cumplimiento exigencia |
| 208 | cubiertas |
| 209 | acciones de aseguramiento de buen manejo guano |
| 212 | retiro guano |
| 215 | retiro guano |
| 216 | guano del plantel |
| 218 | retiro guano |
| 223 | medida art 74 |
| 224 | calefactores nuevos que incumplan limite art 83 |
| 225 | medida art 75 |
| 229 | medida art 77 |
| 230 | calefactores |
| 232 | medida ART 78 |
| 234 | medida ART 78 |
| 236 | medida ART 79 |
| 243 | límites de emisión ART 83 |
| 244 | incumplimiento art 83 |
| 246 | listado de calefactores a leña y pellet de madera que cumplan con la norma de emision art 83 |
| 247 | informacion para consumidores acerca de las restricciones de uso de calefactores que los afectan |
| 255 | estandares técnicos para el acondicionamiento |
| 257 | estudio para diseño de viviendas de baja demanda térmica |
| 259 | estudio que evalúe las mejores alternativas disponibles para la generacion de proyectos de vivienda y calefaccion sustentable |
| 261 | resultados del estudio |
| 262 | informe de pre-factibilidad sobre creación de un sistema de certificación de emisiones y/o etiquetado de emisiones y eficiencia energética |
| 264 | canales que permitan ir mejorando especificaciones técnicas de los artefactos que se vendan en el mercado |
| 268 | hojas secas y todo tipo de residuos |
| 269 | fuego |
| 270 | medida ART 95 y 96 |
| 273 | programa de minimización de quemas agricolas |
| 274 | programa de minimización de quemas agricolas |
| 276 | aprobación recursos del FNDR u otras fuentes de financiamiento |
| 277 | programa gestión de áreas verdes |
| 278 | programa para gestión de masas de vegetación |
| 279 | aumento areas verdes |
| 280 | sistema oficial, actualizado y público de áreas verdes urbanas |
| 281 | obtención recursos |
| 282 | realización estudios de factibilidad técnica y economica |
| 283 | recursos |
| 284 | documentos MINVU |
| 285 | Plan de desarrollo Intermodal RMS |
| 287 | Municipio de Santiago |
| 289 | cooperación técnica espcecializada en temas de transito y transporte |
| 291 | acciones que peuda desarrollar organismos de la sociedad civil |
| 292 | Implementación programas y acciones |
| 294 | incorporar temas de prevención y descontaminación atmosférica de la RMS |
| 296 | Plan capacitacion |
| 297 | programa capacitación y concientización |
| 301 | incorporacion de contenidos en páginas web instituciones públicas RMS |
| 303 | Programa Integral Educación Energética |
| 304 | niveles de emisión de equipos de calefacción |
| 306 | Plan Operacional de Gestión de Episodios Críticos |
| 309 | Programa de Fiscalización POGEC |
| 311 | información POGEC |
| 314 | Implementación Plan de gestión de tránsito |
| 315 | prohibición de estacionamiento, sentidos y honorarios exclusivos |
| 316 | detalle de medidas consideradas |
| 317 | restricción vehicular permanente |
| 318 | fechas, horarios, zonas y perimetros especiales y excepciones |
| 319 | fiscalización DS N100/1990 |
| 320 | fiscalización DS18/2001 |
| 321 | artefactos de calección |
| 323 | medida de restricción vehicular |
| 324 | fechas, horarios, zonas, perímetros, excepciones restricción |
| 326 | medida de prohibición de artefactos de calefacción residencial que usen leña u otros derivados de la madera en la RMS |
| 327 | modificación actividad física |
| 329 | fiscalización |
| 333 | fechas, horarios, zonas, corredores ambientales, perimetros especiales y excepciones |
| 334 | establecimientos |
| 336 | medida de prohibición de artefactos de calefacción residencial que utilicen leña u derivados de la madera |
| 337 | modificación de la actividad fisica en colegios |
| 338 | clases educación física |
| 339 | fiscalización |
| 340 | programa aspirado y lavado de calles |
| 342 | medidas de restriccion vehicular Tabla XII 3: Restricción Vehicular - Emergencia Ambiental |
| 343 | fechas, horarios, zonas, corredores ambientales, perimetros especiales y excepciones |
| 344 | establecimientos |
| 346 | medida de prohibición de artefactos de calefacción residencial que utilicen leña u derivados de la madera |
| 347 | modificación de la actividad fisica en colegios |
| 348 | clases educación física |
| 349 | fiscalización |
| 350 | programa aspirado y lavado de calles |
| 354 | medidas de prevención/mitigación |
| 355 | situación preemergencia y emergencia para MP10 y MP2,5 |
| 356 | declaración episodio critico o adoptar medidas correspondientes a niveles menos estricto |
| 357 | situación de episodios e alterta, preemergencia y emergencia fuera POGEC |
| 358 | medidas del PDDA |
| 359 | estado de avance de las medidas PDDA |
| 360 | estado de avance de las medidas PDDA |
| 361 | informe de avance medidas del plan y fiscalización |
| 362 | informe de avance medidas del plan y fiscalización |

</details>

## Bracketed (implicit) rows

Bracketed Excel values are implicit by convention and never considered literal; counted here for reference.

<details>
<summary>attribute (179)</summary>

| stmt_no | excel_value |
|---|---|
| 1 | [Titulares de] Buses |
| 7 | [Titulares de] Buses |
| 8 | [Titulares de Buses] |
| 12 | [Titulares de] Buses |
| 16 | [Ministerio de Transportes y Telecomunicaciones] |
| 18 | [Titulares de] Vehículos |
| 22 | [Titulares de] vehículo comercial, transporte de carga y transporte de pasajeros, incluyendo furgones escolares |
| 23 | [Titulares de] vehículos en reparación/en labores de reparto |
| 25 | [Carabineros de Chile e inspectores fiscales y municipales] |
| 26 | [Titulares de] vehículos motorizados de encendido por chispa (ciclo Otto) |
| 27 | [Titulares de] vehículos motor diésel |
| 29 | [Carabineros de Chile e inspectores fiscales y municipales] |
| 31 | [el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones] |
| 34 | [Titulares de] vehículos motorizados livianos y medianos |
| 36 | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] |
| 38 | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] |
| 40 | [Titulares de] maquinaria móvil fuera de ruta |
| 41 | [Titulares de] maquinaria móvil fuera de ruta |
| 42 | [Titulares de] maquinaria móvil fuera de ruta |
| 45 | [Distribuidores/expendedores de] petróleo diésel |
| 47 | [Distribuidores/expendedores de] gasolina |
| 48 | [Distribuidores/expendedores de] gasolina |
| 50 | [Distribuidores/expendedores de] gasolina |
| 54 | [Titulares de] combustible de pruebas experimentales |
| 56 | [Titulares de] combustible de pruebas experimentales |
| 57 | [Distribuidores/expendedores de] petróleos combustibles |
| 59 | [Distribuidores/expendedores de] kerosene |
| 61 | [Distribuidores/expendedores de] gas licuado de petróleo |
| 63 | [Distribuidores/expendedores de] gas licuado de petróleo |
| 68 | [empresas distribuidoras de combustibles] |
| 70 | [Ministerio de Energía] |
| 71 | [Ministerio de Energía] |
| 72 | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |
| 73 | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |
| 74 | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |
| 75 | [Titulares de] instalaciones de distribución |
| 76 | [Titulares de] equipos de recuperación y/o eliminación de vapores |
| 77 | [Titulares de] equipos de recuperación y/o eliminación de vapores |
| 79 | [Titulares de] tanques que almacenen combustibles líquidos |
| 80 | [Titulares de tanques que almacenen combustibles líquidos] |
| 81 | [Titulares de] sistemas de recuperación de vapores |
| 82 | [Titulares de] camiones tanques |
| 83 | [Titulares de instalaciones de almacenamiento de combustibles liquidos, nstalaciones de distribución, de equipos de recuperación y/o eliminación de vapores, de camiones tanques, de tanques que almacenen combustibles líquidos] |
| 87 | [Superintendencia de Electricidad y Combustibles] |
| 88 | [Superintendencia de Electricidad y Combustibles] |
| 90 | [Superintendencia de Electricidad y Combustibles] |
| 91 | [Titulares de] fuentes estacionarias |
| 92 | [Titulares de] hornos panaderos |
| 93 | [Titulares de] calderas |
| 94 | [Titulares de] calderas |
| 95 | [Titulares exentos] |
| 96 | [Titulares de] fuentes sujetas al D.S. N°13/2011 del Ministerio del Medio Ambiente |
| 97 | [Titulares de] calderas |
| 98 | [Titulares de] calderas |
| 99 | Titulares de [calderas] |
| 101 | [Titulares de] fuentes estacionarias |
| 102 | [Titulares de] calderas |
| 103 | [Titulares de] fuentes estacionarias |
| 104 | [Titulares de] fuentes estacionarias |
| 106 | [Titulares de] fuentes estacionarias |
| 107 | [Titulares de] fuentes estacionarias |
| 109 | [Superintendencia del Medio Ambiente] |
| 110 | [Titulares de] fuentes estacionarias |
| 112 | [Titulares de] fuentes estacionarias |
| 113 | [Titulares de] fuentes estacionarias |
| 114 | [Titulares de] fuentes estacionarias |
| 115 | [Titulares de] fuentes estacionarias |
| 116 | [Superintendencia del Medio Ambiente] |
| 117 | [Titulares de] fuentes estacionarias |
| 118 | [Titulares de] calderas |
| 119 | [Titulares de] fuentes estacionarias emisoras |
| 120 | [Titulares de] fuentes estacionarias |
| 121 | [Titulares de] las calderas |
| 122 | [Titulares de] las calderas |
| 124 | [Superintendencia del Medio Ambiente] |
| 128 | [Titulares de] fuentes estacionarias |
| 129 | [Titulares de] fuentes estacionarias |
| 130 | [Titulares de] fuentes estacionarias |
| 131 | [Titulares de] calderas y procesos con combustión |
| 132 | [Titulares de] calderas y procesos con combustión |
| 133 | [Titulares de] calderas y procesos con combustión |
| 136 | titulares de las fuentes [estacionarias] |
| 137 | [Titulares de] fuentes [estacionarias] |
| 138 | [Titulares de] fuentes [estacionarias] |
| 139 | [Titulares de] calderas y procesos con combustión |
| 141 | [Titulares de] calderas [AND] [Titulares de] procesos con combustión |
| 143 | [Titulares de] calderas y procesos con combustión |
| 144 | [Titulares de] calderas y procesos con combustión |
| 145 | [Titulares de] calderas y procesos con combustión |
| 146 | Superintendencia [del Medio Ambiente] |
| 147 | [Titulares de] calderas y procesos con combustión |
| 151 | [Titulares de] grandes establecimientos |
| 152 | [Titulares de] grandes establecimientos |
| 153 | [Titulares de] grandes establecimientos |
| 156 | [Ministerio del Medio Ambiente] |
| 157 | [Titulares de] grandes establecimientos |
| 158 | [Titulares de] grandes establecimientos |
| 159 | [Titulares de] grandes establecimientos |
| 163 | [SEREMI del Medio Ambiente] |
| 164 | [SEREMI del Medio Ambiente] |
| 165 | [SEREMI del Medio Ambiente] |
| 166 | [SEREMI del Medio Ambiente] |
| 170 | [Superintendencia del Medio Ambiente] |
| 176 | [Titulares de] fuentes |
| 177 | [Titulares de] fuentes |
| 178 | [Titulares de] fuentes |
| 179 | [Titulares de] fuentes |
| 181 | [Titulares de] proyectos y actividades que ingresen modificaciones SEIA |
| 182 | [Titulares de] establecimientos que no pertenecen al listado de grandes establecimientos existentes |
| 184 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 185 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 186 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 187 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 188 | [SEREMI del Medio Ambiente] |
| 189 | [Titulares de] grandes establecimientos |
| 192 | [Titulares de] grupos electrógenos |
| 193 | [Titulares de] grupos electrógenos |
| 194 | [Titulares de] grupos electrógenos |
| 198 | [Titulares de grupos electrógenos] |
| 199 | [Titulares de] grupos electrógenos |
| 200 | [Titulares de] grupos electrógenos |
| 201 | [Titulares de] planteles de porcinos |
| 203 | [Titulares de] planteles de porcinos |
| 204 | [Titulares de] planteles de porcinos |
| 207 | [Titulares de] planteles de porcinos |
| 208 | [Titulares de] planteles de porcinos |
| 209 | [Titulares de] planteles de aves de corral |
| 210 | [Titulares de] planteles de aves de corral |
| 211 | [Titulares de] planteles de aves de corral |
| 212 | [Titulares de] planteles de aves de corral |
| 213 | [Titulares de] planteles de aves de corral |
| 214 | [Titulares de] planteles de aves de corral |
| 215 | [Titulares de] planteles de aves de corral |
| 216 | [Titulares de] planteles de aves de corral |
| 217 | [Titulares de] planteles de aves de corral |
| 218 | [Titulares de] planteles de aves de corral |
| 219 | [Titulares de] planteles de aves de corral |
| 221 | [Usuarios de] artefactos de calefacción residencial |
| 222 | [Usuarios de] artefactos de calefacción residencial |
| 224 | [Usuarios de] calefactores |
| 228 | [Usuarios de] artefactos de calefacción residencial |
| 230 | [Usuarios de] calefactores |
| 231 | [Titulares de] hoteles u otra clase de hospedajes |
| 232 | [Usuarios de] calefactores |
| 233 | [Usuarios de] calefactores |
| 235 | [Usuarios de] calefactores |
| 240 | [SEREMI del Medio Ambiente] |
| 241 | [Comercializadores de] calefactores |
| 242 | [Comercializadores de] calefactores |
| 243 | [Comercializadores de] calefactores |
| 248 | [Comercializadores de] leña |
| 255 | [Ministerio de Vivienda y Urbanismo] |
| 256 | [Ministerio de Vivienda y Urbanismo] |
| 263 | [Ministerio del Medio Ambiente en conjunto con Ministerio de Energía] |
| 264 | [Ministerio del Medio Ambiente en conjunto con Ministerio de Energía] |
| 267 | [el Ministerio del Medio Ambiente en conjunto con el Ministerio de Energía] |
| 268 | [Toda persona] |
| 269 | [Titulares/operadores de] terrenos agrícolas, ganaderos o de aptitud forestal |
| 274 | [Ministerio de Agricultura] |
| 276 | [Gobierno Regional Metropolitano de Santiago] |
| 277 | [Gobierno Regional Metropolitano de Santiago] |
| 278 | [Gobierno Regional Metropolitano de Santiago] |
| 291 | [el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes] |
| 293 | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] |
| 294 | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] |
| 296 | [SEREMI del Medio Ambiente] |
| 297 | [SEREMI del Medio Ambiente] |
| 298 | [SEREMI del Medio Ambiente] |
| 300 | [SEREMI del Medio Ambiente] |
| 301 | [SEREMI del Medio Ambiente] |
| 314 | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] |
| 315 | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] |
| 316 | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] |
| 321 | [Titulares de] viviendas |
| 325 | [Titulares de] calefactores de uso residencial |
| 334 | [Titulares de] establecimientos |
| 335 | [Titulares de] calefactores de uso residencial |
| 344 | [Titulares de] establecimientos |
| 345 | [Titulares de] calefactores de uso residencial |

</details>

<details>
<summary>deontic (168)</summary>

| stmt_no | excel_value |
|---|---|
| 10 | [deberá] |
| 11 | [deberá] |
| 15 | [deberá] |
| 16 | [deberá] |
| 19 | [deberán] |
| 20 | [deberá] |
| 22 | [no deben] |
| 23 | [pueden] |
| 24 | [deberán] |
| 25 | [deberán] |
| 26 | no [podrán] |
| 27 | no [podrán] |
| 28 | [deberán] |
| 29 | [deberán] |
| 30 | [deberán] |
| 31 | [deberán] |
| 32 | [deberá] |
| 39 | [deberá] |
| 48 | [no deben] |
| 50 | no [podrán] |
| 54 | [no deben] |
| 66 | [deberá] |
| 67 | [deberán] |
| 80 | [deberán] |
| 85 | [deberá] |
| 86 | [deberá] |
| 89 | [deberá] |
| 90 | [deberá] |
| 92 | [no deben] |
| 93 | [no deben] |
| 94 | [no deben] |
| 95 | [deberán] |
| 96 | [deberán] |
| 100 | [deberá] |
| 102 | [no deben] |
| 103 | [no deben] |
| 107 | [no deben] |
| 109 | [deberá] |
| 113 | [no deben] |
| 115 | [no deben] |
| 117 | [deberá] |
| 121 | [podrán] |
| 135 | [deberá] |
| 137 | [no deben] |
| 138 | [no deben] |
| 144 | [no deben] |
| 147 | [deberán] |
| 156 | [no podrá] |
| 158 | [deberán] |
| 166 | [deberá] |
| 169 | [deberá] |
| 170 | [deberá] |
| 173 | [deberá] |
| 174 | [deberá] |
| 177 | [no deben] |
| 183 | [deberá] |
| 197 | [deberá] |
| 204 | [no deben] |
| 206 | [deberá] |
| 211 | [podrán] |
| 212 | [deberán] |
| 214 | [no deben] |
| 215 | [deberán] |
| 217 | [no deben] |
| 218 | [deberán] |
| 220 | [deberá] |
| 221 | [no deben] |
| 222 | solo [podrán] |
| 223 | [deberá] |
| 224 | [no deben] |
| 225 | [deberá] |
| 226 | [deberá] |
| 227 | [deberá] |
| 228 | [no deben] |
| 229 | [deberá] |
| 230 | [no deben] |
| 231 | [no deben] |
| 232 | [no deben] |
| 234 | [deberá] |
| 235 | [no deben] |
| 236 | [deberá] |
| 237 | [deberá] |
| 239 | [deberá] |
| 240 | [deberá] |
| 241 | solo [podrán] |
| 243 | [no deben] |
| 244 | [deberá] |
| 245 | [deberá] |
| 246 | [deberá] |
| 247 | [deberá] |
| 250 | [deberá] |
| 253 | [deberá] |
| 254 | [deberá] |
| 255 | [deberá] |
| 256 | [deberá] |
| 257 | [deberá] |
| 259 | [deberá] |
| 260 | [deberá] |
| 262 | [deberán] |
| 263 | [deberán] |
| 264 | [deberán] |
| 265 | [deberán] |
| 268 | [no debe] |
| 269 | [no deben] |
| 270 | [deberán] |
| 272 | [deberán] |
| 273 | [deberá] |
| 274 | [deberá] |
| 275 | [deberá] |
| 276 | [deberá] |
| 277 | [deberá] |
| 278 | [deberá] |
| 279 | [deberá] |
| 280 | [deberá] |
| 281 | [deberá] |
| 282 | [deberá] |
| 285 | [deberá] |
| 286 | [deberá] |
| 287 | [deberán] |
| 288 | [deberá] |
| 289 | [deberá] |
| 290 | [deberán] |
| 291 | [deberán] |
| 292 | [deberán] |
| 293 | [deberán] |
| 294 | [deberán] |
| 295 | [deberá] |
| 296 | [deberá] |
| 297 | [deberá] |
| 298 | [deberá] |
| 299 | [deberá] |
| 300 | [deberá] |
| 301 | [deberá] |
| 302 | [deberá] |
| 303 | [deberá] |
| 304 | [deberá] |
| 305 | [deberán] |
| 306 | [deberán] |
| 309 | [deberán] |
| 311 | [deberán] |
| 313 | [deberá] |
| 314 | [deberá] |
| 316 | [deberá] |
| 317 | [deberá] |
| 321 | solo [podrán] |
| 323 | [deberá] |
| 326 | [deberá] |
| 329 | [deberán] |
| 330 | [deberá] |
| 332 | [deberá] |
| 336 | [deberá] |
| 339 | [deberán] |
| 340 | [deberá] |
| 342 | [deberá] |
| 346 | [deberá] |
| 349 | [deberán] |
| 350 | [deberá] |
| 352 | [deberá] |
| 353 | [deberá] |
| 354 | [deberá] |
| 355 | [deberá] |
| 357 | [deberá] |
| 358 | [deberá] |
| 359 | [deberá] |
| 361 | [deberá] |
| 362 | [deberá] |
| 364 | [deberán] |
| 365 | [deberán] |

</details>

<details>
<summary>object (28)</summary>

| stmt_no | excel_value |
|---|---|
| 18 | Límites [Tabla III-7: Límites de emisión por cilindrada] |
| 24 | medida [prohibición de operación del motor de vehículos detenidos por más de 5 minutos. ART 13] |
| 26 | emisión continua de humo visible negro, gris [OR] azul |
| 28 | medida [prohibición emisión continua de humo visible negro, gris o azul, excepto vapor de agua (humo blanco), . ART 14] |
| 31 | desarrollo de instrumentos [AND] protocolos [AND] límites máximos permitidos |
| 42 | Tabla III-9: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) y en gramos por caballos de fuerza al freno hora (g/bhp-h) [OR] Tabla III-10: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) |
| 66 | el cumplimiento de la calidad de los combustibles lÍquidos [AND] gaseosos |
| 67 | la calidad de los combustibles lÍquidos [AND] gaseosos |
| 82 | de equipos de captura y posterior recuperación de vapor [AND] elementos necesarios para una eficiente operación |
| 86 | diagnóstico [AND] rediseño del sistema de fiscalización |
| 116 | modalidad del proceso a ser usado [AND] procedimiento para determinar equivalencia en terminos de emisión por chimenea |
| 147 | obligacion [alineación sistema monitoreo e informacion] |
| 179 | entre diversos tipos de fuentes, actividades [and] sectores economicos |
| 185 | estimación de sus emisiones de contaminantes [AND] la metodología utilizada, [AND] la cantidad de emisiones a compensar por contaminante [AND] un anexo con la memoria de cálculo |
| 188 | la obligación de compensar emisiones [AND] los montos por los que se deberá realizar |
| 193 | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |
| 194 | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |
| 204 | medida [reducciones amoniaco ART 70] |
| 207 | sistemas de limpieza al interior de los pabellones [OR] alojamiento de los animales |
| 221 | calderas de calefacción de uso domiciliario [AND] calefactores [AND] cocinas |
| 228 | salamandras [AND] braseros [AND] chimeneas de hogar abierto [AND] calefactores hechizos u otros artefactos similares |
| 239 | catastro de parrillas [AND] hornos de barro [AND] carros ambulantes para uso comercial |
| 240 | retiro, recambio [AND] chatarrizacion de calefactores |
| 241 | calefactores nuevos a leña [AND] pellet de madera |
| 242 | calefactores nuevos a leña [AND] pellet de madera |
| 267 | esquemas de incentivos la transferencia tecnológica [AND] esquemas tarifarios especialmente concebidos para la promoción de energías y tecnologías con el menor impacto ambiental. |
| 293 | programas [AND] material de apoyo pedagogico de educación ambiental |
| 352 | pronóstico de calidad del aire [AND] evolución condiciones de ventilación de la cuenca [AND] resultados del sistema de pronósticos de calidad del aire |

</details>

## Multi-value cells

Rows whose Excel cell holds several items separated by `;` / newline / `[AND]` / `[OR]`. Not split (no cross product): the row contributes at most one T per role.

<details>
<summary>multi-value rows (26)</summary>

| stmt_no | element | excel_value | note |
|---|---|---|---|
| 26 | object | emisión continua de humo visible negro, gris [OR] azul | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 31 | object | desarrollo de instrumentos [AND] protocolos [AND] límites máximos permitidos | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 42 | object | Tabla III-9: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) y en gramos por caballos de fuerza al freno hora (g/bhp-h) [OR] Tabla III-10: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 66 | object | el cumplimiento de la calidad de los combustibles lÍquidos [AND] gaseosos | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 67 | object | la calidad de los combustibles lÍquidos [AND] gaseosos | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 82 | object | de equipos de captura y posterior recuperación de vapor [AND] elementos necesarios para una eficiente operación | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 86 | object | diagnóstico [AND] rediseño del sistema de fiscalización | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 116 | object | modalidad del proceso a ser usado [AND] procedimiento para determinar equivalencia en terminos de emisión por chimenea | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 141 | attribute | [Titulares de] calderas [AND] [Titulares de] procesos con combustión | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 179 | object | entre diversos tipos de fuentes, actividades [and] sectores economicos | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 185 | object | estimación de sus emisiones de contaminantes [AND] la metodología utilizada, [AND] la cantidad de emisiones a compensar por contaminante [AND] un anexo con la memoria de cálculo | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 188 | object | la obligación de compensar emisiones [AND] los montos por los que se deberá realizar | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 193 | object | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 194 | object | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 207 | object | sistemas de limpieza al interior de los pabellones [OR] alojamiento de los animales | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 221 | object | calderas de calefacción de uso domiciliario [AND] calefactores [AND] cocinas | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 228 | object | salamandras [AND] braseros [AND] chimeneas de hogar abierto [AND] calefactores hechizos u otros artefactos similares | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 239 | object | catastro de parrillas [AND] hornos de barro [AND] carros ambulantes para uso comercial | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 240 | object | retiro, recambio [AND] chatarrizacion de calefactores | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 241 | object | calefactores nuevos a leña [AND] pellet de madera | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 242 | object | calefactores nuevos a leña [AND] pellet de madera | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 267 | object | esquemas de incentivos la transferencia tecnológica [AND] esquemas tarifarios especialmente concebidos para la promoción de energías y tecnologías con el menor impacto ambiental. | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 290 | attribute | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | ';'/newline or [AND]/[OR]; NOT split -- linked as one span |
| 291 | attribute | [el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes] | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 293 | object | programas [AND] material de apoyo pedagogico de educación ambiental | ';'/newline or [AND]/[OR]; NOT split and no literal span |
| 352 | object | pronóstico de calidad del aire [AND] evolución condiciones de ventilación de la cuenca [AND] resultados del sistema de pronósticos de calidad del aire | ';'/newline or [AND]/[OR]; NOT split and no literal span |

</details>

