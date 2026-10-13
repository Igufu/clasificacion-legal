# v2_triples summary

Source: `nlp-tagging/outputs/annotations/standoff_comp.ann` (explicit/literal text). Excel: `PLAN_INSUMO.xlsx`, sheet `DECRETO 31` (E = Attribute, G = Deontic, I = Direct Object).

**Validation: PASSED** (every T: `document.txt[start:end] == text`; consecutive ids; no dangling refs; events/jsonl consistent). No normalized Attributes are included, so the exact text check applies to all entities.

## Entities and relations: before / after filtering

| type | before | after |
|---|---|---|
| Attribute | 234 | 234 |
| Deontic | 261 | 261 |
| DirectObject | 117 | 117 |
| IndirectObject | 34 | 0 |
| DirectObjectProperty | 59 | 0 |
| IndirectObjectProperty | 1 | 0 |
| **T total** | 706 | 612 |
| R PropertyOf | 28 | 0 |
| E (events) | 0 | 261 |

- All 28 PropertyOf relations were dropped (each touches a DirectObjectProperty / IndirectObjectProperty).
- 5 non-brat lines at the end of the source were skipped: `2 arcos por statement`, `sacar implícitos `, `visualización spacy y ver IG parser`, `ver modelo`
- Offsets/text unchanged; ids renumbered consecutively (map: `data/filtered_id_map.csv`).

## Triples

| status | rows |
|---|---|
| complete (Attribute + Deontic + Object) | 102 |
| partial event (Deontic + some args) | 159 |
| no event (no Deontic span) | 62 |
| all three cells empty (skipped) | 42 |
| **Excel rows total** | 365 |

Events written: **261** (one per Deontic span). Partial events lack: object = 122, attribute,object = 25, attribute = 12.
Filtered entities not referenced by any event: Attribute = 10, DirectObject = 3.

## Unmatched rows

Excel cells with a value but no span (existing matching logic only; no new heuristics). Full per-row detail: `reports/join.csv`.

| element | reason | count |
|---|---|---|
| object | no literal match | 156 |
| attribute | statement span not found in document | 50 |
| deontic | statement span not found in document | 50 |
| object | statement span not found in document | 49 |
| attribute | no match (local cascade + cross-reference) | 22 |
| attribute | no match (local cascade) | 17 |
| deontic | no bold surface phrase in Raw Statement cell | 6 |
| deontic | bold surface phrase not found in statement span | 6 |

<details>
<summary>object: no literal match (156)</summary>

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
| 26 | emisión continua de humo visible negro, gris [OR] azul |
| 27 | emisión continuada por el tubo de escape por mas de 5 segundos |
| 30 | Implementacion de Método de control de emisiones del número de partículas en la vía pública de vehiculos diesel |
| 31 | desarrollo de instrumentos [AND] protocolos [AND] límites máximos permitidos |
| 32 | revisión normas de ingreso de vehículos livianos y medianos |
| 34 | etiqueta mencionada (ART 17) |
| 38 | cumplimiento de la medida (ART 18) |
| 54 | exigencia ART. 22 |
| 55 | la no aplicación de la exigencia de biocombustible |
| 56 | dicho combustible |
| 66 | el cumplimiento de la calidad de los combustibles lÍquidos [AND] gaseosos |
| 67 | la calidad de los combustibles lÍquidos [AND] gaseosos |
| 68 | control de calidad |
| 74 | elementos permitan capturar vapores durante operaciones |
| 75 | de equipos de captura y porterior recuperación/ eliminación de vapores |
| 76 | equipos que recurpere / elimine 95% vapores |
| 81 | exigencias DS 160/2008 |
| 82 | de equipos de captura y posterior recuperación de vapor [AND] elementos necesarios para una eficiente operación |
| 84 | informe que de cuenta del cumplimiento de las disposiciones contenidas y medidas que se adoptarán si fuese necesario, |
| 86 | diagnóstico [AND] rediseño del sistema de fiscalización |
| 92 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 93 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 94 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 95 | excepciones temporales |
| 96 | normas de emisión por conceptración del DS 13/2011 |
| 97 | limite de emisión para MP en 30 mg/m³N |
| 99 | condicion (art 37) |
| 100 | listado de aquellas calderas que cumplan con lo establecido en art 37 |
| 102 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 103 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 106 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 107 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 109 | resultados de evaluación del cumplimiento de las metas de emisión de 5 establecimientos |
| 112 | Límite máximo de emisión de CO para fuentes estacionarias. Tabla VI-3 |
| 113 | Límite máximo de emisión de CO para fuentes estacionarias. Tabla VI-3 |
| 116 | modalidad del proceso a ser usado [AND] procedimiento para determinar equivalencia en terminos de emisión por chimenea |
| 122 | certificado de origen del fabricante que |
| 123 | registro de fuentes estacionarias de RMS |
| 126 | cambios de combustible u otra condicion que incida en emisiones |
| 129 | que no supera parámetros |
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
| 161 | listado de grandes establecimeintos nuevos y existentes |
| 163 | planes de reducción de emisiones |
| 164 | aprobación e planes |
| 165 | criterios de evaluación indicados en los Artículos 63 y siguientes. |
| 166 | normas de emisión por concentración Art.58 |
| 169 | situación registrada repecto al cumplimiento de su emisión y compensación |
| 174 | programas de compensación de emisiones |
| 181 | emisiones de las modificaciones o ampliaciones |
| 185 | estimación de sus emisiones de contaminantes [AND] la metodología utilizada, [AND] la cantidad de emisiones a compensar por contaminante [AND] un anexo con la memoria de cálculo |
| 186 | programa preliminar de compensaciones de emisiones |
| 188 | la obligación de compensar emisiones [AND] los montos por los que se deberá realizar |
| 191 | estudio de emisiones COV |
| 196 | certificado de origen |
| 197 | protocolo para el desarrollo de la medición |
| 202 | medidas para reducir emisiones de amoniaco |
| 205 | plan de cumplimiento de exigencia art 70 |
| 206 | plan de cumplimiento exigencia |
| 207 | sistemas de limpieza al interior de los pabellones [OR] alojamiento de los animales |
| 209 | acciones de aseguramiento de buen manejo guano |
| 212 | retiro guano |
| 215 | retiro guano |
| 216 | guano del plantel |
| 218 | retiro guano |
| 221 | calderas de calefacción de uso domiciliario [AND] calefactores [AND] cocinas |
| 223 | medida art 74 |
| 224 | calefactores nuevos que incumplan limite art 83 |
| 225 | medida art 75 |
| 228 | salamandras [AND] braseros [AND] chimeneas de hogar abierto [AND] calefactores hechizos u otros artefactos similares |
| 229 | medida art 77 |
| 232 | medida ART 78 |
| 234 | medida ART 78 |
| 236 | medida ART 79 |
| 239 | catastro de parrillas [AND] hornos de barro [AND] carros ambulantes para uso comercial |
| 240 | retiro, recambio [AND] chatarrizacion de calefactores |
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
| 270 | medida ART 95 y 96 |
| 273 | programa de minimización de quemas agricolas |
| 274 | programa de minimización de quemas agricolas |
| 276 | aprobación recursos del FNDR u otras fuentes de financiamiento |
| 278 | programa para gestión de masas de vegetación |
| 279 | aumento areas verdes |
| 280 | sistema oficial, actualizado y público de áreas verdes urbanas |
| 281 | obtención recursos |
| 282 | realización estudios de factibilidad técnica y economica |
| 284 | documentos MINVU |
| 285 | Plan de desarrollo Intermodal RMS |
| 287 | Municipio de Santiago |
| 289 | cooperación técnica espcecializada en temas de transito y transporte |
| 291 | acciones que peuda desarrollar organismos de la sociedad civil |
| 292 | Implementación programas y acciones |
| 293 | programas [AND] material de apoyo pedagogico de educación ambiental |
| 294 | incorporar temas de prevención y descontaminación atmosférica de la RMS |
| 296 | Plan capacitacion |
| 297 | programa capacitación y concientización |
| 301 | incorporacion de contenidos en páginas web instituciones públicas RMS |
| 303 | Programa Integral Educación Energética |
| 304 | niveles de emisión de equipos de calefacción |
| 309 | Programa de Fiscalización POGEC |
| 311 | información POGEC |
| 314 | Implementación Plan de gestión de tránsito |
| 315 | prohibición de estacionamiento, sentidos y honorarios exclusivos |
| 316 | detalle de medidas consideradas |
| 318 | fechas, horarios, zonas y perimetros especiales y excepciones |
| 319 | fiscalización DS N100/1990 |
| 320 | fiscalización DS18/2001 |
| 321 | artefactos de calección |
| 324 | fechas, horarios, zonas, perímetros, excepciones restricción |
| 326 | medida de prohibición de artefactos de calefacción residencial que usen leña u otros derivados de la madera en la RMS |
| 327 | modificación actividad física |
| 333 | fechas, horarios, zonas, corredores ambientales, perimetros especiales y excepciones |
| 336 | medida de prohibición de artefactos de calefacción residencial que utilicen leña u derivados de la madera |
| 337 | modificación de la actividad fisica en colegios |
| 338 | clases educación física |
| 340 | programa aspirado y lavado de calles |
| 343 | fechas, horarios, zonas, corredores ambientales, perimetros especiales y excepciones |
| 346 | medida de prohibición de artefactos de calefacción residencial que utilicen leña u derivados de la madera |
| 348 | clases educación física |
| 350 | programa aspirado y lavado de calles |
| 352 | pronóstico de calidad del aire [AND] evolución condiciones de ventilación de la cuenca [AND] resultados del sistema de pronósticos de calidad del aire |
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

<details>
<summary>attribute: statement span not found in document (50)</summary>

| stmt_no | excel_value |
|---|---|
| 12 | [Titulares de] Buses |
| 18 | [Titulares de] Vehículos |
| 41 | [Titulares de] maquinaria móvil fuera de ruta |
| 42 | [Titulares de] maquinaria móvil fuera de ruta |
| 43 | Los fabricantes de maquinaria móvil fuera de ruta nueva o sus representantes legales en Chile, distribuidores o importadores |
| 45 | [Distribuidores/expendedores de] petróleo diésel |
| 47 | [Distribuidores/expendedores de] gasolina |
| 57 | [Distribuidores/expendedores de] petróleos combustibles |
| 59 | [Distribuidores/expendedores de] kerosene |
| 61 | [Distribuidores/expendedores de] gas licuado de petróleo |
| 63 | [Distribuidores/expendedores de] gas licuado de petróleo |
| 79 | [Titulares de] tanques que almacenen combustibles líquidos |
| 87 | [Superintendencia de Electricidad y Combustibles] |
| 91 | [Titulares de] fuentes estacionarias |
| 101 | [Titulares de] fuentes estacionarias |
| 108 | Superintendencia del Medio Ambiente |
| 110 | [Titulares de] fuentes estacionarias |
| 114 | [Titulares de] fuentes estacionarias |
| 130 | [Titulares de] fuentes estacionarias |
| 131 | [Titulares de] calderas y procesos con combustión |
| 157 | [Titulares de] grandes establecimientos |
| 158 | [Titulares de] grandes establecimientos |
| 176 | [Titulares de] fuentes |
| 177 | [Titulares de] fuentes |
| 178 | [Titulares de] fuentes |
| 179 | [Titulares de] fuentes |
| 184 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 192 | [Titulares de] grupos electrógenos |
| 193 | [Titulares de] grupos electrógenos |
| 194 | [Titulares de] grupos electrógenos |
| 199 | [Titulares de] grupos electrógenos |
| 203 | [Titulares de] planteles de porcinos |
| 208 | [Titulares de] planteles de porcinos |
| 230 | [Usuarios de] calefactores |
| 241 | [Comercializadores de] calefactores |
| 242 | [Comercializadores de] calefactores |
| 267 | [el Ministerio del Medio Ambiente en conjunto con el Ministerio de Energía] |
| 269 | [Titulares/operadores de] terrenos agrícolas, ganaderos o de aptitud forestal |
| 277 | [Gobierno Regional Metropolitano de Santiago] |
| 283 | Gobierno Regional Metropolitano de Santiagoel Gobierno Regional de la Región Metropolitana de Santiago, en coordinación con el Ministerio de Vivienda y Urbanismo, el Ministerio de Obras Públicas, el Ministerio deTransportes y Telecomunicaciones, y otras instituciones con atribuciones para la construcción de infraestructura pública |
| 306 | La SEREMI del Medio Ambiente con el apoyo de la Intendencia Regional |
| 317 | Ministerio de Transportes y Telecomunicaciones |
| 323 | Ministerio de Transportes y Telecomunicaciones |
| 329 | Organismos competentes |
| 334 | [Titulares de] establecimientos |
| 339 | Organismos competentes |
| 342 | Ministerio de Transportes y Telecomunicaciones |
| 344 | [Titulares de] establecimientos |
| 347 | SEREMI de Educación RM |
| 349 | Organismos competentes |

</details>

<details>
<summary>deontic: statement span not found in document (50)</summary>

| stmt_no | excel_value |
|---|---|
| 12 | solo podrán |
| 18 | deberán |
| 41 | deberá |
| 42 | deberá |
| 43 | deberán |
| 45 | deberá |
| 47 | deberá |
| 57 | deberán |
| 59 | deberá |
| 61 | deberá |
| 63 | deberá |
| 79 | deberán |
| 87 | deberá |
| 91 | deberán |
| 101 | deberán |
| 108 | deberá |
| 110 | deberán |
| 114 | deberán |
| 130 | deberán |
| 131 | deberán |
| 157 | podrán |
| 158 | [deberán] |
| 176 | solo podrán |
| 177 | [no deben] |
| 178 | solo podrán |
| 179 | podrán |
| 184 | deberán |
| 192 | deberán |
| 193 | deberán |
| 194 | deberán |
| 199 | deberán |
| 203 | podrán |
| 208 | deberán |
| 230 | [no deben] |
| 241 | solo [podrán] |
| 242 | deberán |
| 267 | podrá |
| 269 | [no deben] |
| 277 | [deberá] |
| 283 | deberá |
| 306 | [deberán] |
| 317 | [deberá] |
| 323 | [deberá] |
| 329 | [deberán] |
| 334 | deberán |
| 339 | [deberán] |
| 342 | [deberá] |
| 344 | deberán |
| 347 | podrá |
| 349 | [deberán] |

</details>

<details>
<summary>object: statement span not found in document (49)</summary>

| stmt_no | excel_value |
|---|---|
| 18 | Límites [Tabla III-7: Límites de emisión por cilindrada] |
| 41 | Tabla III 8. Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) y en gramos por caballos de fuerza al freno hora (g/bhp-h) |
| 42 | Tabla III-9: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) y en gramos por caballos de fuerza al freno hora (g/bhp-h) [OR] Tabla III-10: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) |
| 43 | certificado de origen sobre tipo o familia de motor de la maquinaria nueva cumple con lo exigido (T 8, 9 o 10) |
| 45 | Requisitos para el combustible diésel tipo grado A1. Tabla IV-1 |
| 47 | Requisitos de propiedades de gasolina para motores de ignición. Tabla IV-2 |
| 57 | Requisitos para petróleos combustibles grado 5 y 6 para uso en calderas y hornos de procesos industriales. Tabla IV-3 |
| 59 | Requisitos para el kerosene doméstico e industrial Tabla IV 4 |
| 61 | Requisitos para el gas licuado de petróleo de uso vehicular. Tabla IV-5 |
| 63 | Requisitos para el gas licuado de petróleo de uso doméstico, industrial y comercial. Tabla IV-6 |
| 79 | sistemas de recuperación de vapor |
| 87 | envio informe anual de cumplimiento de todas las exigencias relacionadas con la recuperación de vapores |
| 91 | Límite máximo de emisión de MP para fuentes estacionarias Tabla VI 1 |
| 101 | Límite máximo de emisión de SO para fuentes estacionarias. Tabla VI-2 |
| 108 | evaluación del cumplimiento de las metas de emisión de 5 establecimientos |
| 110 | Límite máximo de emisión de CO para fuentes estacionarias. Tabla VI-3 |
| 114 | Límite máximo de emisión de NOx para fuentes estacionarias. Tabla VI 4 |
| 130 | mediciones con frecuencia descrita Tabla VI-7: Frecuencia de Medición |
| 131 | emisiones MP NOx So |
| 157 | procesos existentes con concentraciones máximas Tabla VI-11: Emisiones tope por contaminante para grandes establecimientos existentes. |
| 158 | Tabla VI-12: Límites máximos de emisión complementarios para fuentes estacionarias de grandes establecimientos existentes] |
| 176 | emisiones |
| 177 | emisiones cedidas |
| 178 | emisiones por reduccion adicionales |
| 179 | entre diversos tipos de fuentes, actividades [and] sectores economicos |
| 184 | condiciones Tabla VI-14: Emisión máxima proyectos |
| 192 | limites máximos de emision de CO, HC, HCNM, NOx MP |
| 193 | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |
| 194 | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |
| 199 | mantenciones al motor y todos sus componentes |
| 203 | reducciones |
| 208 | cubiertas |
| 230 | calefactores |
| 241 | calefactores nuevos a leña [AND] pellet de madera |
| 242 | calefactores nuevos a leña [AND] pellet de madera |
| 267 | esquemas de incentivos la transferencia tecnológica [AND] esquemas tarifarios especialmente concebidos para la promoción de energías y tecnologías con el menor impacto ambiental. |
| 269 | fuego |
| 277 | programa gestión de áreas verdes |
| 283 | recursos |
| 306 | Plan Operacional de Gestión de Episodios Críticos |
| 317 | restricción vehicular permanente |
| 323 | medida de restricción vehicular |
| 329 | fiscalización |
| 334 | establecimientos |
| 339 | fiscalización |
| 342 | medidas de restriccion vehicular Tabla XII 3: Restricción Vehicular - Emergencia Ambiental |
| 344 | establecimientos |
| 347 | modificación de la actividad fisica en colegios |
| 349 | fiscalización |

</details>

<details>
<summary>attribute: no match (local cascade + cross-reference) (22)</summary>

| stmt_no | excel_value |
|---|---|
| 23 | [Titulares de] vehículos en reparación/en labores de reparto |
| 54 | [Titulares de] combustible de pruebas experimentales |
| 56 | [Titulares de] combustible de pruebas experimentales |
| 68 | [empresas distribuidoras de combustibles] |
| 72 | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |
| 73 | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |
| 74 | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |
| 83 | [Titulares de instalaciones de almacenamiento de combustibles liquidos, nstalaciones de distribución, de equipos de recuperación y/o eliminación de vapores, de camiones tanques, de tanques que almacenen combustibles líquidos] |
| 95 | [Titulares exentos] |
| 96 | [Titulares de] fuentes sujetas al D.S. N°13/2011 del Ministerio del Medio Ambiente |
| 141 | [Titulares de] calderas [AND] [Titulares de] procesos con combustión |
| 181 | [Titulares de] proyectos y actividades que ingresen modificaciones SEIA |
| 185 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 186 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 187 | [Titulares de] proyectos y actividades que ingresen SEIA |
| 201 | [Titulares de] planteles de porcinos |
| 221 | [Usuarios de] artefactos de calefacción residencial |
| 222 | [Usuarios de] artefactos de calefacción residencial |
| 228 | [Usuarios de] artefactos de calefacción residencial |
| 263 | [Ministerio del Medio Ambiente en conjunto con Ministerio de Energía] |
| 264 | [Ministerio del Medio Ambiente en conjunto con Ministerio de Energía] |
| 268 | [Toda persona] |

</details>

<details>
<summary>attribute: no match (local cascade) (17)</summary>

| stmt_no | excel_value |
|---|---|
| 32 | Ministerio del Medio Ambiente |
| 39 | Secretaría Regional Ministerial del Medio Ambiente de la RM |
| 67 | empresas distribuidoras de combustibles |
| 84 | Operadores de las instalaciones de almacenamiento/distribución de combustibles líquidos Clase I |
| 195 | Fabricantes representantes legales de grupos electrógenos, o sus distribuidores o importadores |
| 202 | Empresas productora de cerdos |
| 205 | Titulares de planteles de porcinos |
| 227 | Ministerio del Medio Ambiente |
| 270 | Servicio Agrícola y Ganadero Servicio Agrícola y Ganadero (SAG), y a la Corporación Nacional Forestal (CONAF) |
| 271 | Corporación Nacional Forestal |
| 305 | SEREMI del Medio Ambiente la SEREMI del Medio Ambiente en coordinación con la SEREMI de Energía RM y la SEREMI de Vivienda y Urbanismo RM |
| 319 | Ministerio de Agricultura a través de la CONAF |
| 346 | SEREMI de Salud |
| 350 | Gobierno Regional de la Región Metropolitana de Santiago |
| 354 | Intendente |
| 361 | Superintendencia del Medio Ambiente |
| 364 | Servicios públicos |

</details>

<details>
<summary>deontic: no bold surface phrase in Raw Statement cell (6)</summary>

| stmt_no | excel_value |
|---|---|
| 80 | [deberán] |
| 93 | [no deben] |
| 94 | [no deben] |
| 103 | [no deben] |
| 138 | [no deben] |
| 278 | [deberá] |

</details>

<details>
<summary>deontic: bold surface phrase not found in statement span (6)</summary>

| stmt_no | excel_value |
|---|---|
| 123 | deberá |
| 228 | [no deben] |
| 235 | [no deben] |
| 271 | podrá |
| 355 | [deberá] |
| 358 | [deberá] |

</details>

## Flagged edge cases

All rows also in `reports/edge_cases.csv`.

### Rows with several attributes or objects in one cell (26)

Not split and no cross product: the existing matcher links each cell as a single span (or none). Needs a decision before any split.

| stmt_no | element | excel_value | tid | start | end | span_text | note |
|---|---|---|---|---|---|---|---|
| 26 | object | emisión continua de humo visible negro, gris [OR] azul |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 31 | object | desarrollo de instrumentos [AND] protocolos [AND] límites máximos permitidos |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 42 | object | Tabla III-9: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) y en gramos por caballos de fuerza al freno hora (g/bhp-h) [OR] Tabla III-10: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 66 | object | el cumplimiento de la calidad de los combustibles lÍquidos [AND] gaseosos |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 67 | object | la calidad de los combustibles lÍquidos [AND] gaseosos |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 82 | object | de equipos de captura y posterior recuperación de vapor [AND] elementos necesarios para una eficiente operación |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 86 | object | diagnóstico [AND] rediseño del sistema de fiscalización |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 116 | object | modalidad del proceso a ser usado [AND] procedimiento para determinar equivalencia en terminos de emisión por chimenea |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 141 | attribute | [Titulares de] calderas [AND] [Titulares de] procesos con combustión |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 179 | object | entre diversos tipos de fuentes, actividades [and] sectores economicos |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 185 | object | estimación de sus emisiones de contaminantes [AND] la metodología utilizada, [AND] la cantidad de emisiones a compensar por contaminante [AND] un anexo con la memoria de cálculo |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 188 | object | la obligación de compensar emisiones [AND] los montos por los que se deberá realizar |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 193 | object | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 194 | object | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 207 | object | sistemas de limpieza al interior de los pabellones [OR] alojamiento de los animales |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 221 | object | calderas de calefacción de uso domiciliario [AND] calefactores [AND] cocinas |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 228 | object | salamandras [AND] braseros [AND] chimeneas de hogar abierto [AND] calefactores hechizos u otros artefactos similares |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 239 | object | catastro de parrillas [AND] hornos de barro [AND] carros ambulantes para uso comercial |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 240 | object | retiro, recambio [AND] chatarrizacion de calefactores |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 241 | object | calefactores nuevos a leña [AND] pellet de madera |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 242 | object | calefactores nuevos a leña [AND] pellet de madera |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 267 | object | esquemas de incentivos la transferencia tecnológica [AND] esquemas tarifarios especialmente concebidos para la promoción de energías y tecnologías con el menor impacto ambiental. |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 290 | attribute | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | T184 | 150252 | 150370 | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | ';'/newline-separated; NOT split (no cross product) -- linked as one span by existing matcher |
| 291 | attribute | [el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes] | T185 | 150252 | 150370 | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | ';'/newline-separated; NOT split (no cross product) -- linked as one span by existing matcher |
| 293 | object | programas [AND] material de apoyo pedagogico de educación ambiental |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |
| 352 | object | pronóstico de calidad del aire [AND] evolución condiciones de ventilación de la cuenca [AND] resultados del sistema de pronósticos de calidad del aire |  |  |  |  | [AND]/[OR] marker; NOT split (no cross product) -- no span |

### Empty Deontic / Object (or Attribute) cells (1)

Left empty; no span invented.

| stmt_no | element | excel_value | tid | start | end | span_text | note |
|---|---|---|---|---|---|---|---|
| 12 | object |  |  |  |  |  | Excel column I is empty |

### Bracketed implicit values (375)

Linked to the literal span the offsets point at (the Excel value is kept in `triples.jsonl` as `*_excel` / `deontic`).

| element | note | count |
|---|---|---|
| deontic | implicit: bracketed text not in source; linked to literal span | 143 |
| attribute | implicit: bracketed text not in source; linked to literal span | 80 |
| attribute | bracketed; no span to link | 61 |
| attribute | bracketed; literal span contains the bracket-stripped value | 38 |
| object | bracketed; no span to link | 24 |
| deontic | bracketed; no span to link | 23 |
| object | implicit: bracketed text not in source; linked to literal span | 4 |
| deontic | bracketed; literal span contains the bracket-stripped value | 2 |

<details>
<summary>show rows</summary>

| stmt_no | element | excel_value | tid | start | end | span_text | note |
|---|---|---|---|---|---|---|---|
| 1 | attribute | [Titulares de] Buses | T1 | 59363 | 59368 | buses | implicit: bracketed text not in source; linked to literal span |
| 7 | attribute | [Titulares de] Buses | T2 | 61287 | 61292 | buses | implicit: bracketed text not in source; linked to literal span |
| 8 | attribute | [Titulares de Buses] | T3 | 61287 | 61292 | buses | implicit: bracketed text not in source; linked to literal span |
| 10 | deontic | [deberá] | T239 | 62778 | 62804 | responsabilidad de aplicar | implicit: bracketed text not in source; linked to literal span |
| 11 | deontic | [deberá] | T240 | 63242 | 63250 | generará | implicit: bracketed text not in source; linked to literal span |
| 12 | attribute | [Titulares de] Buses |  |  |  |  | bracketed; no span to link |
| 15 | deontic | [deberá] | T242 | 64482 | 64490 | diseñará | implicit: bracketed text not in source; linked to literal span |
| 16 | attribute | [Ministerio de Transportes y Telecomunicaciones] | T9 | 64435 | 64481 | Ministerio de Transportes y Telecomunicaciones | bracketed; literal span contains the bracket-stripped value |
| 16 | deontic | [deberá] | T243 | 64619 | 64629 | gestionará | implicit: bracketed text not in source; linked to literal span |
| 18 | attribute | [Titulares de] Vehículos |  |  |  |  | bracketed; no span to link |
| 18 | object | Límites [Tabla III-7: Límites de emisión por cilindrada] |  |  |  |  | bracketed; no span to link |
| 19 | deontic | [deberán] | T244 | 65923 | 65933 | promoverán | implicit: bracketed text not in source; linked to literal span |
| 20 | deontic | [deberá] | T245 | 66220 | 66231 | establecerá | implicit: bracketed text not in source; linked to literal span |
| 22 | attribute | [Titulares de] vehículo comercial, transporte de carga y transporte de pasajeros, incluyendo furgones escolares | T13 | 67154 | 67250 | vehículo comercial, transporte de carga y transporte de pasajeros, incluyendo furgones escolares | implicit: bracketed text not in source; linked to literal span |
| 22 | deontic | [no deben] | T247 | 67117 | 67137 | prohíbe la operación | implicit: bracketed text not in source; linked to literal span |
| 23 | attribute | [Titulares de] vehículos en reparación/en labores de reparto |  |  |  |  | bracketed; no span to link |
| 23 | deontic | [pueden] | T248 | 67328 | 67353 | exceptúa esta prohibición | implicit: bracketed text not in source; linked to literal span |
| 24 | deontic | [deberán] | T249 | 67549 | 67565 | será fiscalizada | implicit: bracketed text not in source; linked to literal span |
| 24 | object | medida [prohibición de operación del motor de vehículos detenidos por más de 5 minutos. ART 13] | T502 | 67542 | 67548 | medida | implicit: bracketed text not in source; linked to literal span |
| 25 | attribute | [Carabineros de Chile e inspectores fiscales y municipales] | T15 | 67570 | 67627 | Carabineros de Chile e inspectores fiscales y municipales | bracketed; literal span contains the bracket-stripped value |
| 25 | deontic | [deberán] | T250 | 67663 | 67683 | debiendo denunciarse | implicit: bracketed text not in source; linked to literal span |
| 26 | attribute | [Titulares de] vehículos motorizados de encendido por chispa (ciclo Otto) | T16 | 67925 | 67983 | vehículos motorizados de encendido por chispa (ciclo Otto) | implicit: bracketed text not in source; linked to literal span |
| 26 | deontic | no [podrán] | T251 | 67781 | 67796 | No se permitirá | implicit: bracketed text not in source; linked to literal span |
| 26 | object | emisión continua de humo visible negro, gris [OR] azul |  |  |  |  | bracketed; no span to link |
| 27 | attribute | [Titulares de] vehículos motor diésel | T17 | 68077 | 68099 | vehículos motor diésel | implicit: bracketed text not in source; linked to literal span |
| 27 | deontic | no [podrán] | T252 | 68100 | 68115 | no se permitirá | implicit: bracketed text not in source; linked to literal span |
| 28 | deontic | [deberán] | T253 | 68285 | 68300 | será fiscalizad | implicit: bracketed text not in source; linked to literal span |
| 28 | object | medida [prohibición emisión continua de humo visible negro, gris o azul, excepto vapor de agua (humo blanco), . ART 14] | T504 | 68278 | 68284 | medida | implicit: bracketed text not in source; linked to literal span |
| 29 | attribute | [Carabineros de Chile e inspectores fiscales y municipales] | T19 | 68306 | 68363 | Carabineros de Chile e inspectores fiscales y municipales | bracketed; literal span contains the bracket-stripped value |
| 29 | deontic | [deberán] | T254 | 68365 | 68385 | debiendo denunciarse | implicit: bracketed text not in source; linked to literal span |
| 30 | deontic | [deberán] | T255 | 68674 | 68684 | evaluarán  | implicit: bracketed text not in source; linked to literal span |
| 31 | attribute | [el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones] | T21 | 68575 | 68672 | el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones | bracketed; literal span contains the bracket-stripped value |
| 31 | deontic | [deberán] | T256 | 68984 | 68995 | considerará | implicit: bracketed text not in source; linked to literal span |
| 31 | object | desarrollo de instrumentos [AND] protocolos [AND] límites máximos permitidos |  |  |  |  | bracketed; no span to link |
| 32 | deontic | [deberá] | T257 | 69261 | 69270 |  iniciará | implicit: bracketed text not in source; linked to literal span |
| 34 | attribute | [Titulares de] vehículos motorizados livianos y medianos | T23 | 70017 | 70058 | vehículos motorizados livianos y medianos | implicit: bracketed text not in source; linked to literal span |
| 36 | attribute | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] | T25 | 70365 | 70460 | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | bracketed; literal span contains the bracket-stripped value |
| 38 | attribute | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] | T26 | 70365 | 70460 | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | bracketed; literal span contains the bracket-stripped value |
| 39 | deontic | [deberá] | T263 | 71279 | 71292 | se coordinará | implicit: bracketed text not in source; linked to literal span |
| 40 | attribute | [Titulares de] maquinaria móvil fuera de ruta | T27 | 71599 | 71629 | maquinaria móvil fuera de ruta | implicit: bracketed text not in source; linked to literal span |
| 41 | attribute | [Titulares de] maquinaria móvil fuera de ruta |  |  |  |  | bracketed; no span to link |
| 42 | attribute | [Titulares de] maquinaria móvil fuera de ruta |  |  |  |  | bracketed; no span to link |
| 42 | object | Tabla III-9: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) y en gramos por caballos de fuerza al freno hora (g/bhp-h) [OR] Tabla III-10: Límites máximos de emisión provenientes del sistema de escape en gramos por kilowatt hora (g/kWh) |  |  |  |  | bracketed; no span to link |
| 45 | attribute | [Distribuidores/expendedores de] petróleo diésel |  |  |  |  | bracketed; no span to link |
| 47 | attribute | [Distribuidores/expendedores de] gasolina |  |  |  |  | bracketed; no span to link |
| 48 | attribute | [Distribuidores/expendedores de] gasolina | T29 | 75019 | 75027 | gasolina | implicit: bracketed text not in source; linked to literal span |
| 48 | deontic | [no deben] | T266 | 74978 | 74988 | Se prohíbe | implicit: bracketed text not in source; linked to literal span |
| 50 | attribute | [Distribuidores/expendedores de] gasolina | T30 | 75220 | 75228 | gasolina | implicit: bracketed text not in source; linked to literal span |
| 50 | deontic | no [podrán] | T267 | 75166 | 75192 |  No está permitido agregar | implicit: bracketed text not in source; linked to literal span |
| 54 | attribute | [Titulares de] combustible de pruebas experimentales |  |  |  |  | bracketed; no span to link |
| 54 | deontic | [no deben] | T268 | 75679 | 75693 | no se aplicará | implicit: bracketed text not in source; linked to literal span |
| 56 | attribute | [Titulares de] combustible de pruebas experimentales |  |  |  |  | bracketed; no span to link |
| 57 | attribute | [Distribuidores/expendedores de] petróleos combustibles |  |  |  |  | bracketed; no span to link |
| 59 | attribute | [Distribuidores/expendedores de] kerosene |  |  |  |  | bracketed; no span to link |
| 61 | attribute | [Distribuidores/expendedores de] gas licuado de petróleo |  |  |  |  | bracketed; no span to link |
| 63 | attribute | [Distribuidores/expendedores de] gas licuado de petróleo |  |  |  |  | bracketed; no span to link |
| 66 | deontic | [deberá] | T271 | 78671 | 78682 | fiscalizará | implicit: bracketed text not in source; linked to literal span |
| 66 | object | el cumplimiento de la calidad de los combustibles lÍquidos [AND] gaseosos |  |  |  |  | bracketed; no span to link |
| 67 | deontic | [deberán] | T272 | 79099 | 79119 | será responsabilidad | implicit: bracketed text not in source; linked to literal span |
| 67 | object | la calidad de los combustibles lÍquidos [AND] gaseosos |  |  |  |  | bracketed; no span to link |
| 68 | attribute | [empresas distribuidoras de combustibles] |  |  |  |  | bracketed; no span to link |
| 70 | attribute | [Ministerio de Energía] | T34 | 79394 | 79415 | Ministerio de Energía | bracketed; literal span contains the bracket-stripped value |
| 71 | attribute | [Ministerio de Energía] | T35 | 79394 | 79415 | Ministerio de Energía | bracketed; literal span contains the bracket-stripped value |
| 72 | attribute | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |  |  |  |  | bracketed; no span to link |
| 73 | attribute | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |  |  |  |  | bracketed; no span to link |
| 74 | attribute | [Titulares de] instalaciones de almacenamiento de combustibles liquidos |  |  |  |  | bracketed; no span to link |
| 75 | attribute | [Titulares de] instalaciones de distribución | T36 | 81279 | 81308 | instalaciones de distribución | implicit: bracketed text not in source; linked to literal span |
| 76 | attribute | [Titulares de] equipos de recuperación y/o eliminación de vapores | T37 | 81497 | 81547 | equipos de recuperación y/o eliminación de vapores | implicit: bracketed text not in source; linked to literal span |
| 77 | attribute | [Titulares de] equipos de recuperación y/o eliminación de vapores | T38 | 81497 | 81547 | equipos de recuperación y/o eliminación de vapores | implicit: bracketed text not in source; linked to literal span |
| 79 | attribute | [Titulares de] tanques que almacenen combustibles líquidos |  |  |  |  | bracketed; no span to link |
| 80 | attribute | [Titulares de tanques que almacenen combustibles líquidos] | T40 | 82029 | 82072 | tanques que almacenen combustibles líquidos | implicit: bracketed text not in source; linked to literal span |
| 80 | deontic | [deberán] |  |  |  |  | bracketed; no span to link |
| 81 | attribute | [Titulares de] sistemas de recuperación de vapores | T41 | 82519 | 82554 | sistemas de recuperación de vapores | implicit: bracketed text not in source; linked to literal span |
| 82 | attribute | [Titulares de] camiones tanques | T42 | 82714 | 82730 | camiones tanques | implicit: bracketed text not in source; linked to literal span |
| 82 | object | de equipos de captura y posterior recuperación de vapor [AND] elementos necesarios para una eficiente operación |  |  |  |  | bracketed; no span to link |
| 83 | attribute | [Titulares de instalaciones de almacenamiento de combustibles liquidos, nstalaciones de distribución, de equipos de recuperación y/o eliminación de vapores, de camiones tanques, de tanques que almacenen combustibles líquidos] |  |  |  |  | bracketed; no span to link |
| 85 | deontic | [deberá] | T288 | 83999 | 84011 | desarrollará | implicit: bracketed text not in source; linked to literal span |
| 86 | deontic | [deberá] | T289 | 84416 | 84425 | realizará | implicit: bracketed text not in source; linked to literal span |
| 86 | object | diagnóstico [AND] rediseño del sistema de fiscalización |  |  |  |  | bracketed; no span to link |
| 87 | attribute | [Superintendencia de Electricidad y Combustibles] |  |  |  |  | bracketed; no span to link |
| 88 | attribute | [Superintendencia de Electricidad y Combustibles] | T45 | 84368 | 84415 | Superintendencia de Electricidad y Combustibles | bracketed; literal span contains the bracket-stripped value |
| 89 | deontic | [deberá] | T291 | 85005 | 85018 | implementará  | implicit: bracketed text not in source; linked to literal span |
| 90 | attribute | [Superintendencia de Electricidad y Combustibles] | T47 | 84957 | 85004 | Superintendencia de Electricidad y Combustibles | bracketed; literal span contains the bracket-stripped value |
| 90 | deontic | [deberá] | T292 | 85146 | 85159 |  incorporarán | implicit: bracketed text not in source; linked to literal span |
| 91 | attribute | [Titulares de] fuentes estacionarias |  |  |  |  | bracketed; no span to link |
| 92 | attribute | [Titulares de] hornos panaderos | T48 | 85648 | 85664 | hornos panaderos | implicit: bracketed text not in source; linked to literal span |
| 92 | deontic | [no deben] | T293 | 85592 | 85610 | exentos de cumplir | implicit: bracketed text not in source; linked to literal span |
| 93 | attribute | [Titulares de] calderas | T49 | 85767 | 85775 | calderas | implicit: bracketed text not in source; linked to literal span |
| 93 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 94 | attribute | [Titulares de] calderas | T50 | 85940 | 85948 | calderas | implicit: bracketed text not in source; linked to literal span |
| 94 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 95 | attribute | [Titulares exentos] |  |  |  |  | bracketed; no span to link |
| 95 | deontic | [deberán] | T294 | 86084 | 86098 | se acreditarán | implicit: bracketed text not in source; linked to literal span |
| 96 | attribute | [Titulares de] fuentes sujetas al D.S. N°13/2011 del Ministerio del Medio Ambiente |  |  |  |  | bracketed; no span to link |
| 96 | deontic | [deberán] | T295 | 86267 | 86276 | aplicarán | implicit: bracketed text not in source; linked to literal span |
| 97 | attribute | [Titulares de] calderas | T51 | 86368 | 86376 | calderas | implicit: bracketed text not in source; linked to literal span |
| 98 | attribute | [Titulares de] calderas | T52 | 86368 | 86376 | calderas | implicit: bracketed text not in source; linked to literal span |
| 99 | attribute | Titulares de [calderas] | T53 | 86368 | 86376 | calderas | implicit: bracketed text not in source; linked to literal span |
| 100 | deontic | [deberá] | T299 | 87241 | 87251 | informará  | implicit: bracketed text not in source; linked to literal span |
| 101 | attribute | [Titulares de] fuentes estacionarias |  |  |  |  | bracketed; no span to link |
| 102 | attribute | [Titulares de] calderas | T55 | 87802 | 87810 | calderas | implicit: bracketed text not in source; linked to literal span |
| 102 | deontic | [no deben] | T300 | 87745 | 87764 | exentos de cumplir  | implicit: bracketed text not in source; linked to literal span |
| 103 | attribute | [Titulares de] fuentes estacionarias | T56 | 88061 | 88082 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 103 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 104 | attribute | [Titulares de] fuentes estacionarias | T57 | 88061 | 88082 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 106 | attribute | [Titulares de] fuentes estacionarias | T58 | 88457 | 88478 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 107 | attribute | [Titulares de] fuentes estacionarias | T59 | 88457 | 88478 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 107 | deontic | [no deben] | T303 | 88745 | 88757 | Se exceptúan | implicit: bracketed text not in source; linked to literal span |
| 109 | attribute | [Superintendencia del Medio Ambiente] | T60 | 88928 | 88963 | Superintendencia del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 109 | deontic | [deberá] | T304 | 89448 | 89462 | será entregada | implicit: bracketed text not in source; linked to literal span |
| 110 | attribute | [Titulares de] fuentes estacionarias |  |  |  |  | bracketed; no span to link |
| 112 | attribute | [Titulares de] fuentes estacionarias | T61 | 89944 | 89965 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 113 | attribute | [Titulares de] fuentes estacionarias | T62 | 88457 | 88478 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 113 | deontic | [no deben] | T306 | 88745 | 88758 | Se exceptúan  | implicit: bracketed text not in source; linked to literal span |
| 114 | attribute | [Titulares de] fuentes estacionarias |  |  |  |  | bracketed; no span to link |
| 115 | attribute | [Titulares de] fuentes estacionarias | T63 | 90554 | 90575 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 115 | deontic | [no deben] | T307 | 90839 | 90852 | Se prohíben l | implicit: bracketed text not in source; linked to literal span |
| 116 | attribute | [Superintendencia del Medio Ambiente] | T64 | 90978 | 91013 | Superintendencia del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 116 | object | modalidad del proceso a ser usado [AND] procedimiento para determinar equivalencia en terminos de emisión por chimenea |  |  |  |  | bracketed; no span to link |
| 117 | attribute | [Titulares de] fuentes estacionarias | T65 | 90554 | 90575 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 117 | deontic | [deberá] | T309 | 91215 | 91230 |  se acreditará  | implicit: bracketed text not in source; linked to literal span |
| 118 | attribute | [Titulares de] calderas | T66 | 91589 | 91597 | calderas | implicit: bracketed text not in source; linked to literal span |
| 119 | attribute | [Titulares de] fuentes estacionarias emisoras | T67 | 92378 | 92408 | fuentes estacionarias emisoras | implicit: bracketed text not in source; linked to literal span |
| 120 | attribute | [Titulares de] fuentes estacionarias | T68 | 92378 | 92399 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 121 | attribute | [Titulares de] las calderas | T69 | 92810 | 92822 | las calderas | implicit: bracketed text not in source; linked to literal span |
| 121 | deontic | [podrán] | T313 | 92732 | 92741 | Se eximen | implicit: bracketed text not in source; linked to literal span |
| 122 | attribute | [Titulares de] las calderas | T70 | 92810 | 92822 | las calderas | implicit: bracketed text not in source; linked to literal span |
| 124 | attribute | [Superintendencia del Medio Ambiente] | T72 | 93100 | 93135 | Superintendencia del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 128 | attribute | [Titulares de] fuentes estacionarias | T75 | 93724 | 93745 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 129 | attribute | [Titulares de] fuentes estacionarias | T76 | 93724 | 93745 | fuentes estacionarias | implicit: bracketed text not in source; linked to literal span |
| 130 | attribute | [Titulares de] fuentes estacionarias |  |  |  |  | bracketed; no span to link |
| 131 | attribute | [Titulares de] calderas y procesos con combustión |  |  |  |  | bracketed; no span to link |
| 132 | attribute | [Titulares de] calderas y procesos con combustión | T77 | 95408 | 95442 | calderas y procesos con combustión | implicit: bracketed text not in source; linked to literal span |
| 133 | attribute | [Titulares de] calderas y procesos con combustión | T78 | 95408 | 95442 | calderas y procesos con combustión | implicit: bracketed text not in source; linked to literal span |
| 135 | deontic | [deberá] | T322 | 96190 | 96199 | definirá  | implicit: bracketed text not in source; linked to literal span |
| 136 | attribute | titulares de las fuentes [estacionarias] | T80 | 96363 | 96387 | titulares de las fuentes | implicit: bracketed text not in source; linked to literal span |
| 137 | attribute | [Titulares de] fuentes [estacionarias] | T81 | 96639 | 96646 | fuentes | implicit: bracketed text not in source; linked to literal span |
| 137 | deontic | [no deben] | T324 | 96595 | 96607 | Se exceptúan | implicit: bracketed text not in source; linked to literal span |
| 138 | attribute | [Titulares de] fuentes [estacionarias] | T82 | 96820 | 96827 | fuentes | implicit: bracketed text not in source; linked to literal span |
| 138 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 139 | attribute | [Titulares de] calderas y procesos con combustión | T83 | 96953 | 96987 | calderas y procesos con combustión | implicit: bracketed text not in source; linked to literal span |
| 141 | attribute | [Titulares de] calderas [AND] [Titulares de] procesos con combustión |  |  |  |  | bracketed; no span to link |
| 143 | attribute | [Titulares de] calderas y procesos con combustión | T85 | 96953 | 96987 | calderas y procesos con combustión | implicit: bracketed text not in source; linked to literal span |
| 144 | attribute | [Titulares de] calderas y procesos con combustión | T86 | 96953 | 96987 | calderas y procesos con combustión | implicit: bracketed text not in source; linked to literal span |
| 144 | deontic | [no deben] | T329 | 97926 | 97937 | Se excluyen | implicit: bracketed text not in source; linked to literal span |
| 145 | attribute | [Titulares de] calderas y procesos con combustión | T87 | 96953 | 96987 | calderas y procesos con combustión | implicit: bracketed text not in source; linked to literal span |
| 146 | attribute | Superintendencia [del Medio Ambiente] | T88 | 98345 | 98361 | Superintendencia | implicit: bracketed text not in source; linked to literal span |
| 147 | attribute | [Titulares de] calderas y procesos con combustión | T89 | 96953 | 96987 | calderas y procesos con combustión | implicit: bracketed text not in source; linked to literal span |
| 147 | deontic | [deberán] | T332 | 98617 | 98628 |  implementa | implicit: bracketed text not in source; linked to literal span |
| 147 | object | obligacion [alineación sistema monitoreo e informacion] | T542 | 98635 | 98645 | obligación | implicit: bracketed text not in source; linked to literal span |
| 151 | attribute | [Titulares de] grandes establecimientos | T90 | 99362 | 99386 | grandes establecimientos | implicit: bracketed text not in source; linked to literal span |
| 152 | attribute | [Titulares de] grandes establecimientos | T91 | 99362 | 99386 | grandes establecimientos | implicit: bracketed text not in source; linked to literal span |
| 153 | attribute | [Titulares de] grandes establecimientos | T92 | 99362 | 99386 | grandes establecimientos | implicit: bracketed text not in source; linked to literal span |
| 156 | attribute | [Ministerio del Medio Ambiente] | T94 | 100699 | 100728 | Ministerio del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 156 | deontic | [no podrá] | T337 | 100952 | 100965 | podrá superar | implicit: bracketed text not in source; linked to literal span |
| 157 | attribute | [Titulares de] grandes establecimientos |  |  |  |  | bracketed; no span to link |
| 158 | attribute | [Titulares de] grandes establecimientos |  |  |  |  | bracketed; no span to link |
| 158 | deontic | [deberán] |  |  |  |  | bracketed; no span to link |
| 159 | attribute | [Titulares de] grandes establecimientos | T95 | 102902 | 102926 | grandes establecimientos | implicit: bracketed text not in source; linked to literal span |
| 163 | attribute | [SEREMI del Medio Ambiente] | T99 | 103662 | 103687 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 164 | attribute | [SEREMI del Medio Ambiente] | T100 | 103662 | 103687 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 165 | attribute | [SEREMI del Medio Ambiente] | T101 | 103662 | 103687 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 166 | attribute | [SEREMI del Medio Ambiente] | T102 | 103662 | 103687 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 166 | deontic | [deberá] | T345 | 104283 | 104292 | aplicará  | implicit: bracketed text not in source; linked to literal span |
| 169 | deontic | [deberá] | T346 | 105335 | 105345 | notificará | implicit: bracketed text not in source; linked to literal span |
| 170 | attribute | [Superintendencia del Medio Ambiente] | T104 | 105276 | 105311 | Superintendencia del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 170 | deontic | [deberá] | T347 | 105513 | 105525 | desarrollará | implicit: bracketed text not in source; linked to literal span |
| 173 | deontic | [deberá] | T349 | 106139 | 106148 | aprobados | implicit: bracketed text not in source; linked to literal span |
| 174 | deontic | [deberá] | T350 | 106184 | 106196 | fiscalizados | implicit: bracketed text not in source; linked to literal span |
| 176 | attribute | [Titulares de] fuentes |  |  |  |  | bracketed; no span to link |
| 177 | attribute | [Titulares de] fuentes |  |  |  |  | bracketed; no span to link |
| 177 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 178 | attribute | [Titulares de] fuentes |  |  |  |  | bracketed; no span to link |
| 179 | attribute | [Titulares de] fuentes |  |  |  |  | bracketed; no span to link |
| 179 | object | entre diversos tipos de fuentes, actividades [and] sectores economicos |  |  |  |  | bracketed; no span to link |
| 181 | attribute | [Titulares de] proyectos y actividades que ingresen modificaciones SEIA |  |  |  |  | bracketed; no span to link |
| 182 | attribute | [Titulares de] establecimientos que no pertenecen al listado de grandes establecimientos existentes | T108 | 109941 | 110025 | establecimientos que no pertenecen al listado de grandes establecimientos existentes | implicit: bracketed text not in source; linked to literal span |
| 183 | deontic | [deberá] | T353 | 110250 | 110265 |  se formalizará | implicit: bracketed text not in source; linked to literal span |
| 184 | attribute | [Titulares de] proyectos y actividades que ingresen SEIA |  |  |  |  | bracketed; no span to link |
| 185 | attribute | [Titulares de] proyectos y actividades que ingresen SEIA |  |  |  |  | bracketed; no span to link |
| 185 | object | estimación de sus emisiones de contaminantes [AND] la metodología utilizada, [AND] la cantidad de emisiones a compensar por contaminante [AND] un anexo con la memoria de cálculo |  |  |  |  | bracketed; no span to link |
| 186 | attribute | [Titulares de] proyectos y actividades que ingresen SEIA |  |  |  |  | bracketed; no span to link |
| 187 | attribute | [Titulares de] proyectos y actividades que ingresen SEIA |  |  |  |  | bracketed; no span to link |
| 188 | attribute | [SEREMI del Medio Ambiente] | T110 | 114767 | 114792 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 188 | object | la obligación de compensar emisiones [AND] los montos por los que se deberá realizar |  |  |  |  | bracketed; no span to link |
| 189 | attribute | [Titulares de] grandes establecimientos | T111 | 110165 | 110189 | grandes establecimientos | implicit: bracketed text not in source; linked to literal span |
| 192 | attribute | [Titulares de] grupos electrógenos |  |  |  |  | bracketed; no span to link |
| 193 | attribute | [Titulares de] grupos electrógenos |  |  |  |  | bracketed; no span to link |
| 193 | object | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |  |  |  |  | bracketed; no span to link |
| 194 | attribute | [Titulares de] grupos electrógenos |  |  |  |  | bracketed; no span to link |
| 194 | object | Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h), para desplazamiento volumétrico por cilindro del motor menor a 10 litros. Tabla VI-15 [AND] Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) para desplazamiento volumétrico por cilindro del motor mayor o igual a 10 litros y menor a 30 litros.Tabla VI-16 [AND] Tabla VI-17: Límites máximos de emisión para grupos electrógenos en gramos por kilowatt hora (g/kWh) [AND] y en gramos por caballos de fuerza al freno hora (g/bhp-h) para desplazamiento volumétrico por cilindro del motor mayor o igual a 30 litros |  |  |  |  | bracketed; no span to link |
| 197 | deontic | [deberá] | T363 | 121084 | 121097 | será definido | implicit: bracketed text not in source; linked to literal span |
| 198 | attribute | [Titulares de grupos electrógenos] | T116 | 120614 | 120646 | titulares de grupos electrógenos | bracketed; literal span contains the bracket-stripped value |
| 199 | attribute | [Titulares de] grupos electrógenos |  |  |  |  | bracketed; no span to link |
| 200 | attribute | [Titulares de] grupos electrógenos | T117 | 121390 | 121409 | grupos electrógenos | implicit: bracketed text not in source; linked to literal span |
| 201 | attribute | [Titulares de] planteles de porcinos |  |  |  |  | bracketed; no span to link |
| 203 | attribute | [Titulares de] planteles de porcinos |  |  |  |  | bracketed; no span to link |
| 204 | attribute | [Titulares de] planteles de porcinos | T118 | 123020 | 123041 | planteles de porcinos | implicit: bracketed text not in source; linked to literal span |
| 204 | deontic | [no deben] | T368 | 122979 | 122991 | Se exceptúan | implicit: bracketed text not in source; linked to literal span |
| 204 | object | medida [reducciones amoniaco ART 70] | T562 | 122998 | 123004 | medida | implicit: bracketed text not in source; linked to literal span |
| 206 | deontic | [deberá] | T370 | 123921 | 123932 | fiscalizar  | implicit: bracketed text not in source; linked to literal span |
| 207 | attribute | [Titulares de] planteles de porcinos | T120 | 123020 | 123041 | planteles de porcinos | implicit: bracketed text not in source; linked to literal span |
| 207 | object | sistemas de limpieza al interior de los pabellones [OR] alojamiento de los animales |  |  |  |  | bracketed; no span to link |
| 208 | attribute | [Titulares de] planteles de porcinos |  |  |  |  | bracketed; no span to link |
| 209 | attribute | [Titulares de] planteles de aves de corral | T121 | 124901 | 124928 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 210 | attribute | [Titulares de] planteles de aves de corral | T122 | 125174 | 125201 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 211 | attribute | [Titulares de] planteles de aves de corral | T123 | 125174 | 125201 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 211 | deontic | [podrán] | T374 | 125494 | 125502 | programe | implicit: bracketed text not in source; linked to literal span |
| 212 | attribute | [Titulares de] planteles de aves de corral | T124 | 125174 | 125201 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 212 | deontic | [deberán] | T375 | 125626 | 125636 | completar  | implicit: bracketed text not in source; linked to literal span |
| 213 | attribute | [Titulares de] planteles de aves de corral | T125 | 125747 | 125774 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 214 | attribute | [Titulares de] planteles de aves de corral | T126 | 125747 | 125774 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 214 | deontic | [no deben] | T377 | 126004 | 126015 | se exceptúa | implicit: bracketed text not in source; linked to literal span |
| 215 | attribute | [Titulares de] planteles de aves de corral | T127 | 125747 | 125774 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 215 | deontic | [deberán] | T378 | 126161 | 126171 |  completar | implicit: bracketed text not in source; linked to literal span |
| 216 | attribute | [Titulares de] planteles de aves de corral | T128 | 126283 | 126310 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 217 | attribute | [Titulares de] planteles de aves de corral | T129 | 126283 | 126310 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 217 | deontic | [no deben] | T380 | 126452 | 126463 | se exceptúa | implicit: bracketed text not in source; linked to literal span |
| 218 | attribute | [Titulares de] planteles de aves de corral | T130 | 126283 | 126310 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 218 | deontic | [deberán] | T381 | 126610 | 126619 | completar | implicit: bracketed text not in source; linked to literal span |
| 219 | attribute | [Titulares de] planteles de aves de corral | T131 | 126738 | 126765 | planteles de aves de corral | implicit: bracketed text not in source; linked to literal span |
| 220 | deontic | [deberá] | T383 | 127038 | 127051 | desarrollará  | implicit: bracketed text not in source; linked to literal span |
| 221 | attribute | [Usuarios de] artefactos de calefacción residencial |  |  |  |  | bracketed; no span to link |
| 221 | deontic | [no deben] | T384 | 128663 | 128680 | se prohíbe el uso | implicit: bracketed text not in source; linked to literal span |
| 221 | object | calderas de calefacción de uso domiciliario [AND] calefactores [AND] cocinas |  |  |  |  | bracketed; no span to link |
| 222 | attribute | [Usuarios de] artefactos de calefacción residencial |  |  |  |  | bracketed; no span to link |
| 222 | deontic | solo [podrán] | T385 | 128949 | 128977 | sólo estará permitido el uso | implicit: bracketed text not in source; linked to literal span |
| 223 | deontic | [deberá] | T386 | 129109 | 129151 | fiscalización de esta medida corresponderá | implicit: bracketed text not in source; linked to literal span |
| 224 | attribute | [Usuarios de] calefactores | T134 | 129345 | 129357 | calefactores | implicit: bracketed text not in source; linked to literal span |
| 224 | deontic | [no deben] | T387 | 129324 | 129341 | se prohíbe el uso | implicit: bracketed text not in source; linked to literal span |
| 225 | deontic | [deberá] | T388 | 129465 | 129507 | fiscalización de esta medida corresponderá | implicit: bracketed text not in source; linked to literal span |
| 226 | deontic | [deberá] | T389 | 129764 | 129775 | fortalecerá | implicit: bracketed text not in source; linked to literal span |
| 227 | deontic | [deberá] | T390 | 129829 | 129854 | analizará la pertinencia  | implicit: bracketed text not in source; linked to literal span |
| 228 | attribute | [Usuarios de] artefactos de calefacción residencial |  |  |  |  | bracketed; no span to link |
| 228 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 228 | object | salamandras [AND] braseros [AND] chimeneas de hogar abierto [AND] calefactores hechizos u otros artefactos similares |  |  |  |  | bracketed; no span to link |
| 229 | deontic | [deberá] | T391 | 130404 | 130446 | fiscalización de esta medida corresponderá | implicit: bracketed text not in source; linked to literal span |
| 230 | attribute | [Usuarios de] calefactores |  |  |  |  | bracketed; no span to link |
| 230 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 231 | attribute | [Titulares de] hoteles u otra clase de hospedajes | T138 | 130980 | 131014 | hoteles u otra clase de hospedajes | implicit: bracketed text not in source; linked to literal span |
| 231 | deontic | [no deben] | T392 | 130928 | 130947 | se prohibirá el uso | implicit: bracketed text not in source; linked to literal span |
| 232 | attribute | [Usuarios de] calefactores | T139 | 131064 | 131076 | calefactores | implicit: bracketed text not in source; linked to literal span |
| 232 | deontic | [no deben] | T393 | 131016 | 131036 | Se eximen de cumplir | implicit: bracketed text not in source; linked to literal span |
| 233 | attribute | [Usuarios de] calefactores | T140 | 131254 | 131266 | calefactores | implicit: bracketed text not in source; linked to literal span |
| 234 | deontic | [deberá] | T395 | 131384 | 131426 | fiscalización de esta medida corresponderá | implicit: bracketed text not in source; linked to literal span |
| 235 | attribute | [Usuarios de] calefactores | T142 | 131645 | 131657 | calefactores | implicit: bracketed text not in source; linked to literal span |
| 235 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 236 | deontic | [deberá] | T396 | 131667 | 131709 | fiscalización de esta medida corresponderá | implicit: bracketed text not in source; linked to literal span |
| 237 | deontic | [deberá] | T397 | 131869 | 131878 |  apoyará  | implicit: bracketed text not in source; linked to literal span |
| 239 | deontic | [deberá] | T399 | 132579 | 132588 | levantará | implicit: bracketed text not in source; linked to literal span |
| 239 | object | catastro de parrillas [AND] hornos de barro [AND] carros ambulantes para uso comercial |  |  |  |  | bracketed; no span to link |
| 240 | attribute | [SEREMI del Medio Ambiente] | T147 | 132155 | 132180 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 240 | deontic | [deberá] | T400 | 132980 | 132989 | fomentará | implicit: bracketed text not in source; linked to literal span |
| 240 | object | retiro, recambio [AND] chatarrizacion de calefactores |  |  |  |  | bracketed; no span to link |
| 241 | attribute | [Comercializadores de] calefactores |  |  |  |  | bracketed; no span to link |
| 241 | deontic | solo [podrán] |  |  |  |  | bracketed; no span to link |
| 241 | object | calefactores nuevos a leña [AND] pellet de madera |  |  |  |  | bracketed; no span to link |
| 242 | attribute | [Comercializadores de] calefactores |  |  |  |  | bracketed; no span to link |
| 242 | object | calefactores nuevos a leña [AND] pellet de madera |  |  |  |  | bracketed; no span to link |
| 243 | attribute | [Comercializadores de] calefactores | T148 | 133914 | 133926 | calefactores | implicit: bracketed text not in source; linked to literal span |
| 243 | deontic | [no deben] | T401 | 133852 | 133876 | Se exceptúan de cumplir  | implicit: bracketed text not in source; linked to literal span |
| 244 | deontic | [deberá] | T402 | 134211 | 134284 | control, fiscalización y sanción en caso de incumplimiento, corresponderá | implicit: bracketed text not in source; linked to literal span |
| 245 | deontic | [deberá] | T403 | 134497 | 134507 |  propondrá | implicit: bracketed text not in source; linked to literal span |
| 246 | deontic | [deberá] | T404 | 134873 | 134887 | dará a conocer | implicit: bracketed text not in source; linked to literal span |
| 247 | deontic | [deberá] | T405 | 135221 | 135232 | actualizará | implicit: bracketed text not in source; linked to literal span |
| 248 | attribute | [Comercializadores de] leña | T153 | 135568 | 135572 | leña | implicit: bracketed text not in source; linked to literal span |
| 250 | deontic | [deberá] | T407 | 135922 | 135930 | apoyará  | implicit: bracketed text not in source; linked to literal span |
| 253 | deontic | [deberá] | T410 | 137045 | 137057 | se aplicarán | implicit: bracketed text not in source; linked to literal span |
| 254 | deontic | [deberá] | T411 | 137358 | 137367 | evaluará  | implicit: bracketed text not in source; linked to literal span |
| 255 | attribute | [Ministerio de Vivienda y Urbanismo] | T159 | 137323 | 137357 | Ministerio de Vivienda y Urbanismo | bracketed; literal span contains the bracket-stripped value |
| 255 | deontic | [deberá] | T412 | 137573 | 137582 | aplicarán | implicit: bracketed text not in source; linked to literal span |
| 256 | attribute | [Ministerio de Vivienda y Urbanismo] | T160 | 137323 | 137357 | Ministerio de Vivienda y Urbanismo | bracketed; literal span contains the bracket-stripped value |
| 256 | deontic | [deberá] | T413 | 137664 | 137678 |  se realizará  | implicit: bracketed text not in source; linked to literal span |
| 257 | deontic | [deberá] | T414 | 137959 | 137968 | encargará | implicit: bracketed text not in source; linked to literal span |
| 259 | deontic | [deberá] | T416 | 138581 | 138594 |  desarrollará | implicit: bracketed text not in source; linked to literal span |
| 260 | deontic | [deberá] | T417 | 138904 | 138913 | fomentará | implicit: bracketed text not in source; linked to literal span |
| 262 | deontic | [deberán] | T419 | 139701 | 139711 | elaborarán | implicit: bracketed text not in source; linked to literal span |
| 263 | attribute | [Ministerio del Medio Ambiente en conjunto con Ministerio de Energía] |  |  |  |  | bracketed; no span to link |
| 263 | deontic | [deberán] | T420 | 140068 | 140077 | evaluarán | implicit: bracketed text not in source; linked to literal span |
| 264 | attribute | [Ministerio del Medio Ambiente en conjunto con Ministerio de Energía] |  |  |  |  | bracketed; no span to link |
| 264 | deontic | [deberán] | T421 | 140186 | 140194 | buscarán | implicit: bracketed text not in source; linked to literal span |
| 265 | deontic | [deberán] | T422 | 140556 | 140565 | evaluarán | implicit: bracketed text not in source; linked to literal span |
| 267 | attribute | [el Ministerio del Medio Ambiente en conjunto con el Ministerio de Energía] |  |  |  |  | bracketed; no span to link |
| 267 | object | esquemas de incentivos la transferencia tecnológica [AND] esquemas tarifarios especialmente concebidos para la promoción de energías y tecnologías con el menor impacto ambiental. |  |  |  |  | bracketed; no span to link |
| 268 | attribute | [Toda persona] |  |  |  |  | bracketed; no span to link |
| 268 | deontic | [no debe] | T423 | 141294 | 141314 | se prohíbe la quema  | implicit: bracketed text not in source; linked to literal span |
| 269 | attribute | [Titulares/operadores de] terrenos agrícolas, ganaderos o de aptitud forestal |  |  |  |  | bracketed; no span to link |
| 269 | deontic | [no deben] |  |  |  |  | bracketed; no span to link |
| 270 | deontic | [deberán] | T424 | 141702 | 141748 | La fiscalización de esta medida corresponderá  | implicit: bracketed text not in source; linked to literal span |
| 272 | deontic | [deberán] | T425 | 142274 | 142286 |  elaborarán  | implicit: bracketed text not in source; linked to literal span |
| 273 | deontic | [deberá] | T426 | 142602 | 142611 |  diseñará | implicit: bracketed text not in source; linked to literal span |
| 274 | attribute | [Ministerio de Agricultura] | T170 | 142577 | 142602 | Ministerio de Agricultura | bracketed; literal span contains the bracket-stripped value |
| 274 | deontic | [deberá] | T427 | 142752 | 142769 | deberá orientarse | bracketed; literal span contains the bracket-stripped value |
| 275 | deontic | [deberá] | T428 | 143461 | 143472 |  continuará | implicit: bracketed text not in source; linked to literal span |
| 276 | attribute | [Gobierno Regional Metropolitano de Santiago] | T172 | 143418 | 143461 | Gobierno Regional Metropolitano de Santiago | bracketed; literal span contains the bracket-stripped value |
| 276 | deontic | [deberá] | T429 | 143678 | 143696 | procurando obtener | implicit: bracketed text not in source; linked to literal span |
| 277 | attribute | [Gobierno Regional Metropolitano de Santiago] |  |  |  |  | bracketed; no span to link |
| 277 | deontic | [deberá] |  |  |  |  | bracketed; no span to link |
| 278 | attribute | [Gobierno Regional Metropolitano de Santiago] | T173 | 143418 | 143461 | Gobierno Regional Metropolitano de Santiago | bracketed; literal span contains the bracket-stripped value |
| 278 | deontic | [deberá] |  |  |  |  | bracketed; no span to link |
| 279 | deontic | [deberá] | T430 | 145501 | 145509 |  apoyará | implicit: bracketed text not in source; linked to literal span |
| 280 | deontic | [deberá] | T431 | 145934 | 145943 | elaborará | implicit: bracketed text not in source; linked to literal span |
| 281 | deontic | [deberá] | T432 | 146287 | 146297 | gestionará | implicit: bracketed text not in source; linked to literal span |
| 282 | deontic | [deberá] | T433 | 146539 | 146549 | gestionará | implicit: bracketed text not in source; linked to literal span |
| 285 | deontic | [deberá] | T435 | 148484 | 148493 | propondrá | implicit: bracketed text not in source; linked to literal span |
| 286 | deontic | [deberá] | T436 | 148958 | 148981 | coordinará y gestionará | implicit: bracketed text not in source; linked to literal span |
| 287 | deontic | [deberán] | T437 | 149193 | 149202 | apoyarán  | implicit: bracketed text not in source; linked to literal span |
| 288 | deontic | [deberá] | T438 | 149543 | 149550 | apoyará | implicit: bracketed text not in source; linked to literal span |
| 289 | deontic | [deberá] | T439 | 149932 | 149942 | gestionará | implicit: bracketed text not in source; linked to literal span |
| 290 | deontic | [deberán] | T440 | 150372 | 150382 | elaborarán | implicit: bracketed text not in source; linked to literal span |
| 291 | attribute | [el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes] | T185 | 150252 | 150370 | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | bracketed; literal span contains the bracket-stripped value |
| 291 | deontic | [deberán] | T441 | 150562 | 150572 | propondrán | implicit: bracketed text not in source; linked to literal span |
| 292 | deontic | [deberán] | T442 | 150765 | 150786 | diseñará y coordinará | implicit: bracketed text not in source; linked to literal span |
| 293 | attribute | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] | T187 | 150693 | 150763 | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | bracketed; literal span contains the bracket-stripped value |
| 293 | deontic | [deberán] | T443 | 150851 | 150862 | Fortalecer  | implicit: bracketed text not in source; linked to literal span |
| 293 | object | programas [AND] material de apoyo pedagogico de educación ambiental |  |  |  |  | bracketed; no span to link |
| 294 | attribute | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] | T188 | 150693 | 150763 | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | bracketed; literal span contains the bracket-stripped value |
| 294 | deontic | [deberán] | T444 | 151441 | 151451 | Incentivar | implicit: bracketed text not in source; linked to literal span |
| 295 | deontic | [deberá] | T445 | 151681 | 151691 | coordinará | implicit: bracketed text not in source; linked to literal span |
| 296 | attribute | [SEREMI del Medio Ambiente] | T190 | 151655 | 151680 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 296 | deontic | [deberá] | T446 | 151803 | 151818 | Implementación  | implicit: bracketed text not in source; linked to literal span |
| 297 | attribute | [SEREMI del Medio Ambiente] | T191 | 151655 | 151680 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 297 | deontic | [deberá] | T447 | 152096 | 152110 | Implementación | implicit: bracketed text not in source; linked to literal span |
| 298 | attribute | [SEREMI del Medio Ambiente] | T192 | 151655 | 151680 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 298 | deontic | [deberá] | T448 | 152644 | 152655 | Realización | implicit: bracketed text not in source; linked to literal span |
| 299 | deontic | [deberá] | T449 | 152954 | 152964 | coordinará | implicit: bracketed text not in source; linked to literal span |
| 300 | attribute | [SEREMI del Medio Ambiente] | T194 | 152928 | 152953 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 300 | deontic | [deberá] | T450 | 153104 | 153112 | definirá | implicit: bracketed text not in source; linked to literal span |
| 301 | attribute | [SEREMI del Medio Ambiente] | T195 | 152928 | 152953 | SEREMI del Medio Ambiente | bracketed; literal span contains the bracket-stripped value |
| 301 | deontic | [deberá] | T451 | 153240 | 153248 | Promover | implicit: bracketed text not in source; linked to literal span |
| 302 | deontic | [deberá] | T452 | 153559 | 153571 | se realizará | implicit: bracketed text not in source; linked to literal span |
| 303 | deontic | [deberá] | T453 | 153958 | 153971 |  implementará | implicit: bracketed text not in source; linked to literal span |
| 304 | deontic | [deberá] | T454 | 154341 | 154353 | se informará | implicit: bracketed text not in source; linked to literal span |
| 305 | deontic | [deberán] | T455 | 154800 | 154827 |  diseñarán e implementarán  | implicit: bracketed text not in source; linked to literal span |
| 306 | deontic | [deberán] |  |  |  |  | bracketed; no span to link |
| 309 | deontic | [deberán] | T456 | 156631 | 156641 | coordinado | implicit: bracketed text not in source; linked to literal span |
| 311 | deontic | [deberán] | T457 | 157071 | 157081 |  enviarán  | implicit: bracketed text not in source; linked to literal span |
| 313 | deontic | [deberá] | T458 | 157454 | 157479 |  dispondrá e implementará | implicit: bracketed text not in source; linked to literal span |
| 314 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T202 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | bracketed; literal span contains the bracket-stripped value |
| 314 | deontic | [deberá] | T459 | 157763 | 157777 |  se coordinará | implicit: bracketed text not in source; linked to literal span |
| 315 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T203 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | bracketed; literal span contains the bracket-stripped value |
| 316 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T204 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | bracketed; literal span contains the bracket-stripped value |
| 316 | deontic | [deberá] | T461 | 158384 | 158405 | deberá ser informado  | bracketed; literal span contains the bracket-stripped value |
| 317 | deontic | [deberá] |  |  |  |  | bracketed; no span to link |
| 321 | attribute | [Titulares de] viviendas | T207 | 159958 | 159967 | viviendas | implicit: bracketed text not in source; linked to literal span |
| 321 | deontic | solo [podrán] | T465 | 160058 | 160077 |  sólo se permitirán | implicit: bracketed text not in source; linked to literal span |
| 323 | deontic | [deberá] |  |  |  |  | bracketed; no span to link |
| 325 | attribute | [Titulares de] calefactores de uso residencial | T209 | 161339 | 161370 | calefactores de uso residencial | implicit: bracketed text not in source; linked to literal span |
| 326 | deontic | [deberá] | T468 | 161544 | 161623 | fiscalización de esta medida y sanción en caso de incumplimiento, corresponderá | implicit: bracketed text not in source; linked to literal span |
| 329 | deontic | [deberán] |  |  |  |  | bracketed; no span to link |
| 330 | deontic | [deberá] | T471 | 162424 | 162434 |  reforzará | implicit: bracketed text not in source; linked to literal span |
| 332 | deontic | [deberá] | T472 | 163093 | 163102 | dispondrá | implicit: bracketed text not in source; linked to literal span |
| 334 | attribute | [Titulares de] establecimientos |  |  |  |  | bracketed; no span to link |
| 335 | attribute | [Titulares de] calefactores de uso residencial | T216 | 164360 | 164391 | calefactores de uso residencial | implicit: bracketed text not in source; linked to literal span |
| 336 | deontic | [deberá] | T475 | 164538 | 164620 | La fiscalización de esta medida y sanción en caso de incumplimiento, corresponderá | implicit: bracketed text not in source; linked to literal span |
| 339 | deontic | [deberán] |  |  |  |  | bracketed; no span to link |
| 340 | deontic | [deberá] | T478 | 165422 | 165431 | reforzará | implicit: bracketed text not in source; linked to literal span |
| 342 | deontic | [deberá] |  |  |  |  | bracketed; no span to link |
| 344 | attribute | [Titulares de] establecimientos |  |  |  |  | bracketed; no span to link |
| 345 | attribute | [Titulares de] calefactores de uso residencial | T222 | 167467 | 167498 | calefactores de uso residencial | implicit: bracketed text not in source; linked to literal span |
| 346 | deontic | [deberá] | T481 | 167648 | 167727 | fiscalización de esta medida y sanción en caso de incumplimiento, corresponderá | implicit: bracketed text not in source; linked to literal span |
| 349 | deontic | [deberán] |  |  |  |  | bracketed; no span to link |
| 350 | deontic | [deberá] | T483 | 168526 | 168536 | reforzará  | implicit: bracketed text not in source; linked to literal span |
| 352 | deontic | [deberá] | T484 | 168983 | 168994 |  informará  | implicit: bracketed text not in source; linked to literal span |
| 352 | object | pronóstico de calidad del aire [AND] evolución condiciones de ventilación de la cuenca [AND] resultados del sistema de pronósticos de calidad del aire |  |  |  |  | bracketed; no span to link |
| 353 | deontic | [deberá] | T485 | 169277 | 169286 | declarará | implicit: bracketed text not in source; linked to literal span |
| 354 | deontic | [deberá] | T486 | 169457 | 169470 | hará públicas | implicit: bracketed text not in source; linked to literal span |
| 355 | deontic | [deberá] |  |  |  |  | bracketed; no span to link |
| 357 | deontic | [deberá] | T488 | 170679 | 170687 | informar | implicit: bracketed text not in source; linked to literal span |
| 358 | deontic | [deberá] |  |  |  |  | bracketed; no span to link |
| 359 | deontic | [deberá] | T489 | 171281 | 171314 | tará encargada de la verificación | implicit: bracketed text not in source; linked to literal span |
| 361 | deontic | [deberá] | T491 | 171542 | 171550 | remitirá | implicit: bracketed text not in source; linked to literal span |
| 362 | deontic | [deberá] | T492 | 171746 | 171760 | será publicado | implicit: bracketed text not in source; linked to literal span |
| 364 | deontic | [deberán] | T494 | 172103 | 172113 | solicitar  | implicit: bracketed text not in source; linked to literal span |
| 365 | deontic | [deberán] | T495 | 184137 | 184149 | desarrollará | implicit: bracketed text not in source; linked to literal span |

</details>

### Spans resolved outside their own statement (69)

Existing backward search found the Attribute in an earlier sentence.

<details>
<summary>show rows</summary>

| stmt_no | element | excel_value | tid | start | end | span_text | note |
|---|---|---|---|---|---|---|---|
| 8 | attribute | [Titulares de Buses] | T3 | 61287 | 61292 | buses | span lies outside its statement (62110-62242); resolved from an earlier mention |
| 16 | attribute | [Ministerio de Transportes y Telecomunicaciones] | T9 | 64435 | 64481 | Ministerio de Transportes y Telecomunicaciones | span lies outside its statement (64606-64682); resolved from an earlier mention |
| 25 | attribute | [Carabineros de Chile e inspectores fiscales y municipales] | T15 | 67570 | 67627 | Carabineros de Chile e inspectores fiscales y municipales | span lies outside its statement (67663-67762); resolved from an earlier mention |
| 29 | attribute | [Carabineros de Chile e inspectores fiscales y municipales] | T19 | 68306 | 68363 | Carabineros de Chile e inspectores fiscales y municipales | span lies outside its statement (68365-68464); resolved from an earlier mention |
| 31 | attribute | [el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones] | T21 | 68575 | 68672 | el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones | span lies outside its statement (68963-69118); resolved from an earlier mention |
| 36 | attribute | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] | T25 | 70365 | 70460 | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | span lies outside its statement (70678-70909); resolved from an earlier mention |
| 38 | attribute | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] | T26 | 70365 | 70460 | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | span lies outside its statement (71027-71192); resolved from an earlier mention |
| 70 | attribute | [Ministerio de Energía] | T34 | 79394 | 79415 | Ministerio de Energía | span lies outside its statement (79960-80174); resolved from an earlier mention |
| 71 | attribute | [Ministerio de Energía] | T35 | 79394 | 79415 | Ministerio de Energía | span lies outside its statement (80180-80351); resolved from an earlier mention |
| 77 | attribute | [Titulares de] equipos de recuperación y/o eliminación de vapores | T38 | 81497 | 81547 | equipos de recuperación y/o eliminación de vapores | span lies outside its statement (81652-81894); resolved from an earlier mention |
| 80 | attribute | [Titulares de tanques que almacenen combustibles líquidos] | T40 | 82029 | 82072 | tanques que almacenen combustibles líquidos | span lies outside its statement (82441-82508); resolved from an earlier mention |
| 88 | attribute | [Superintendencia de Electricidad y Combustibles] | T45 | 84368 | 84415 | Superintendencia de Electricidad y Combustibles | span lies outside its statement (84789-84926); resolved from an earlier mention |
| 90 | attribute | [Superintendencia de Electricidad y Combustibles] | T47 | 84957 | 85004 | Superintendencia de Electricidad y Combustibles | span lies outside its statement (85133-85266); resolved from an earlier mention |
| 98 | attribute | [Titulares de] calderas | T52 | 86368 | 86376 | calderas | span lies outside its statement (86744-86933); resolved from an earlier mention |
| 99 | attribute | Titulares de [calderas] | T53 | 86368 | 86376 | calderas | span lies outside its statement (86939-87196); resolved from an earlier mention |
| 104 | attribute | [Titulares de] fuentes estacionarias | T57 | 88061 | 88082 | fuentes estacionarias | span lies outside its statement (88172-88277); resolved from an earlier mention |
| 107 | attribute | [Titulares de] fuentes estacionarias | T59 | 88457 | 88478 | fuentes estacionarias | span lies outside its statement (88744-88832); resolved from an earlier mention |
| 109 | attribute | [Superintendencia del Medio Ambiente] | T60 | 88928 | 88963 | Superintendencia del Medio Ambiente | span lies outside its statement (89343-89600); resolved from an earlier mention |
| 112 | attribute | [Titulares de] fuentes estacionarias | T61 | 89944 | 89965 | fuentes estacionarias | span lies outside its statement (90108-90310); resolved from an earlier mention |
| 113 | attribute | [Titulares de] fuentes estacionarias | T62 | 88457 | 88478 | fuentes estacionarias | span lies outside its statement (88745-88832); resolved from an earlier mention |
| 115 | attribute | [Titulares de] fuentes estacionarias | T63 | 90554 | 90575 | fuentes estacionarias | span lies outside its statement (90826-91014); resolved from an earlier mention |
| 116 | attribute | [Superintendencia del Medio Ambiente] | T64 | 90978 | 91013 | Superintendencia del Medio Ambiente | span lies outside its statement (91015-91164); resolved from an earlier mention |
| 117 | attribute | [Titulares de] fuentes estacionarias | T65 | 90554 | 90575 | fuentes estacionarias | span lies outside its statement (91172-91555); resolved from an earlier mention |
| 120 | attribute | [Titulares de] fuentes estacionarias | T68 | 92378 | 92399 | fuentes estacionarias | span lies outside its statement (92563-92711); resolved from an earlier mention |
| 124 | attribute | [Superintendencia del Medio Ambiente] | T72 | 93100 | 93135 | Superintendencia del Medio Ambiente | span lies outside its statement (93219-93382); resolved from an earlier mention |
| 128 | attribute | [Titulares de] fuentes estacionarias | T75 | 93724 | 93745 | fuentes estacionarias | span lies outside its statement (94332-94448); resolved from an earlier mention |
| 129 | attribute | [Titulares de] fuentes estacionarias | T76 | 93724 | 93745 | fuentes estacionarias | span lies outside its statement (94450-94575); resolved from an earlier mention |
| 133 | attribute | [Titulares de] calderas y procesos con combustión | T78 | 95408 | 95442 | calderas y procesos con combustión | span lies outside its statement (95626-95808); resolved from an earlier mention |
| 143 | attribute | [Titulares de] calderas y procesos con combustión | T85 | 96953 | 96987 | calderas y procesos con combustión | span lies outside its statement (97780-97926); resolved from an earlier mention |
| 144 | attribute | [Titulares de] calderas y procesos con combustión | T86 | 96953 | 96987 | calderas y procesos con combustión | span lies outside its statement (97926-98044); resolved from an earlier mention |
| 145 | attribute | [Titulares de] calderas y procesos con combustión | T87 | 96953 | 96987 | calderas y procesos con combustión | span lies outside its statement (98051-98258); resolved from an earlier mention |
| 147 | attribute | [Titulares de] calderas y procesos con combustión | T89 | 96953 | 96987 | calderas y procesos con combustión | span lies outside its statement (98458-98646); resolved from an earlier mention |
| 151 | attribute | [Titulares de] grandes establecimientos | T90 | 99362 | 99386 | grandes establecimientos | span lies outside its statement (99808-100036); resolved from an earlier mention |
| 152 | attribute | [Titulares de] grandes establecimientos | T91 | 99362 | 99386 | grandes establecimientos | span lies outside its statement (100036-100228); resolved from an earlier mention |
| 153 | attribute | [Titulares de] grandes establecimientos | T92 | 99362 | 99386 | grandes establecimientos | span lies outside its statement (100234-100395); resolved from an earlier mention |
| 156 | attribute | [Ministerio del Medio Ambiente] | T94 | 100699 | 100728 | Ministerio del Medio Ambiente | span lies outside its statement (100928-101092); resolved from an earlier mention |
| 163 | attribute | [SEREMI del Medio Ambiente] | T99 | 103662 | 103687 | SEREMI del Medio Ambiente | span lies outside its statement (103689-103782); resolved from an earlier mention |
| 164 | attribute | [SEREMI del Medio Ambiente] | T100 | 103662 | 103687 | SEREMI del Medio Ambiente | span lies outside its statement (103782-103882); resolved from an earlier mention |
| 165 | attribute | [SEREMI del Medio Ambiente] | T101 | 103662 | 103687 | SEREMI del Medio Ambiente | span lies outside its statement (103882-104155); resolved from an earlier mention |
| 166 | attribute | [SEREMI del Medio Ambiente] | T102 | 103662 | 103687 | SEREMI del Medio Ambiente | span lies outside its statement (104161-104395); resolved from an earlier mention |
| 170 | attribute | [Superintendencia del Medio Ambiente] | T104 | 105276 | 105311 | Superintendencia del Medio Ambiente | span lies outside its statement (105511-105616); resolved from an earlier mention |
| 188 | attribute | [SEREMI del Medio Ambiente] | T110 | 114767 | 114792 | SEREMI del Medio Ambiente | span lies outside its statement (114799-114953); resolved from an earlier mention |
| 189 | attribute | [Titulares de] grandes establecimientos | T111 | 110165 | 110189 | grandes establecimientos | span lies outside its statement (116007-116348); resolved from an earlier mention |
| 198 | attribute | [Titulares de grupos electrógenos] | T116 | 120614 | 120646 | titulares de grupos electrógenos | span lies outside its statement (121228-121366); resolved from an earlier mention |
| 200 | attribute | [Titulares de] grupos electrógenos | T117 | 121390 | 121409 | grupos electrógenos | span lies outside its statement (121716-122182); resolved from an earlier mention |
| 207 | attribute | [Titulares de] planteles de porcinos | T120 | 123020 | 123041 | planteles de porcinos | span lies outside its statement (123968-124284); resolved from an earlier mention |
| 211 | attribute | [Titulares de] planteles de aves de corral | T123 | 125174 | 125201 | planteles de aves de corral | span lies outside its statement (125462-125532); resolved from an earlier mention |
| 212 | attribute | [Titulares de] planteles de aves de corral | T124 | 125174 | 125201 | planteles de aves de corral | span lies outside its statement (125533-125738); resolved from an earlier mention |
| 214 | attribute | [Titulares de] planteles de aves de corral | T126 | 125747 | 125774 | planteles de aves de corral | span lies outside its statement (126003-126069); resolved from an earlier mention |
| 215 | attribute | [Titulares de] planteles de aves de corral | T127 | 125747 | 125774 | planteles de aves de corral | span lies outside its statement (126069-126273); resolved from an earlier mention |
| 217 | attribute | [Titulares de] planteles de aves de corral | T129 | 126283 | 126310 | planteles de aves de corral | span lies outside its statement (126450-126516); resolved from an earlier mention |
| 218 | attribute | [Titulares de] planteles de aves de corral | T130 | 126283 | 126310 | planteles de aves de corral | span lies outside its statement (126516-126722); resolved from an earlier mention |
| 240 | attribute | [SEREMI del Medio Ambiente] | T147 | 132155 | 132180 | SEREMI del Medio Ambiente | span lies outside its statement (132895-133136); resolved from an earlier mention |
| 255 | attribute | [Ministerio de Vivienda y Urbanismo] | T159 | 137323 | 137357 | Ministerio de Vivienda y Urbanismo | span lies outside its statement (137571-137637); resolved from an earlier mention |
| 256 | attribute | [Ministerio de Vivienda y Urbanismo] | T160 | 137323 | 137357 | Ministerio de Vivienda y Urbanismo | span lies outside its statement (137637-137761); resolved from an earlier mention |
| 274 | attribute | [Ministerio de Agricultura] | T170 | 142577 | 142602 | Ministerio de Agricultura | span lies outside its statement (142745-143200); resolved from an earlier mention |
| 276 | attribute | [Gobierno Regional Metropolitano de Santiago] | T172 | 143418 | 143461 | Gobierno Regional Metropolitano de Santiago | span lies outside its statement (143678-143806); resolved from an earlier mention |
| 278 | attribute | [Gobierno Regional Metropolitano de Santiago] | T173 | 143418 | 143461 | Gobierno Regional Metropolitano de Santiago | span lies outside its statement (144453-144874); resolved from an earlier mention |
| 291 | attribute | [el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes] | T185 | 150252 | 150370 | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | span lies outside its statement (150551-150637); resolved from an earlier mention |
| 293 | attribute | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] | T187 | 150693 | 150763 | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | span lies outside its statement (150851-151229); resolved from an earlier mention |
| 294 | attribute | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] | T188 | 150693 | 150763 | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | span lies outside its statement (151441-151593); resolved from an earlier mention |
| 296 | attribute | [SEREMI del Medio Ambiente] | T190 | 151655 | 151680 | SEREMI del Medio Ambiente | span lies outside its statement (151803-152090); resolved from an earlier mention |
| 297 | attribute | [SEREMI del Medio Ambiente] | T191 | 151655 | 151680 | SEREMI del Medio Ambiente | span lies outside its statement (152096-152329); resolved from an earlier mention |
| 298 | attribute | [SEREMI del Medio Ambiente] | T192 | 151655 | 151680 | SEREMI del Medio Ambiente | span lies outside its statement (152644-152867); resolved from an earlier mention |
| 300 | attribute | [SEREMI del Medio Ambiente] | T194 | 152928 | 152953 | SEREMI del Medio Ambiente | span lies outside its statement (153076-153234); resolved from an earlier mention |
| 301 | attribute | [SEREMI del Medio Ambiente] | T195 | 152928 | 152953 | SEREMI del Medio Ambiente | span lies outside its statement (153240-153466); resolved from an earlier mention |
| 314 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T202 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | span lies outside its statement (157746-158025); resolved from an earlier mention |
| 315 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T203 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | span lies outside its statement (158031-158326); resolved from an earlier mention |
| 316 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T204 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | span lies outside its statement (158332-158492); resolved from an earlier mention |

</details>

### Attribute spans shared by several statements (87)

Same offsets appear as separate T lines (one per statement), as in the source.

<details>
<summary>show rows</summary>

| stmt_no | element | excel_value | tid | start | end | span_text | note |
|---|---|---|---|---|---|---|---|
| 7 | attribute | [Titulares de] Buses | T2 | 61287 | 61292 | buses | same offsets as Attribute of stmt [8]; kept as separate T per statement |
| 8 | attribute | [Titulares de Buses] | T3 | 61287 | 61292 | buses | same offsets as Attribute of stmt [7]; kept as separate T per statement |
| 15 | attribute | Ministerio de Transportes y Telecomunicaciones | T8 | 64435 | 64481 | Ministerio de Transportes y Telecomunicaciones | same offsets as Attribute of stmt [16]; kept as separate T per statement |
| 16 | attribute | [Ministerio de Transportes y Telecomunicaciones] | T9 | 64435 | 64481 | Ministerio de Transportes y Telecomunicaciones | same offsets as Attribute of stmt [15]; kept as separate T per statement |
| 28 | attribute | Carabineros de Chile e inspectores fiscales y municipales | T18 | 68306 | 68363 | Carabineros de Chile e inspectores fiscales y municipales | same offsets as Attribute of stmt [29]; kept as separate T per statement |
| 29 | attribute | [Carabineros de Chile e inspectores fiscales y municipales] | T19 | 68306 | 68363 | Carabineros de Chile e inspectores fiscales y municipales | same offsets as Attribute of stmt [28]; kept as separate T per statement |
| 30 | attribute | el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones | T20 | 68575 | 68672 | el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones | same offsets as Attribute of stmt [31]; kept as separate T per statement |
| 31 | attribute | [el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones] | T21 | 68575 | 68672 | el Ministerio de Medio Ambiente en conjunto con el Ministerio de Transportes y Telecomunicaciones | same offsets as Attribute of stmt [30]; kept as separate T per statement |
| 35 | attribute | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | T24 | 70365 | 70460 | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | same offsets as Attribute of stmt [36, 38]; kept as separate T per statement |
| 36 | attribute | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] | T25 | 70365 | 70460 | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | same offsets as Attribute of stmt [35, 38]; kept as separate T per statement |
| 38 | attribute | [el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud] | T26 | 70365 | 70460 | el Ministerio de Obras Públicas, el Ministerio de Vivienda y Urbanismo y el Ministerio de Salud | same offsets as Attribute of stmt [35, 36]; kept as separate T per statement |
| 69 | attribute | Ministerio de Energía | T33 | 79394 | 79415 | Ministerio de Energía | same offsets as Attribute of stmt [70, 71]; kept as separate T per statement |
| 70 | attribute | [Ministerio de Energía] | T34 | 79394 | 79415 | Ministerio de Energía | same offsets as Attribute of stmt [69, 71]; kept as separate T per statement |
| 71 | attribute | [Ministerio de Energía] | T35 | 79394 | 79415 | Ministerio de Energía | same offsets as Attribute of stmt [69, 70]; kept as separate T per statement |
| 76 | attribute | [Titulares de] equipos de recuperación y/o eliminación de vapores | T37 | 81497 | 81547 | equipos de recuperación y/o eliminación de vapores | same offsets as Attribute of stmt [77]; kept as separate T per statement |
| 77 | attribute | [Titulares de] equipos de recuperación y/o eliminación de vapores | T38 | 81497 | 81547 | equipos de recuperación y/o eliminación de vapores | same offsets as Attribute of stmt [76]; kept as separate T per statement |
| 97 | attribute | [Titulares de] calderas | T51 | 86368 | 86376 | calderas | same offsets as Attribute of stmt [98, 99]; kept as separate T per statement |
| 98 | attribute | [Titulares de] calderas | T52 | 86368 | 86376 | calderas | same offsets as Attribute of stmt [97, 99]; kept as separate T per statement |
| 99 | attribute | Titulares de [calderas] | T53 | 86368 | 86376 | calderas | same offsets as Attribute of stmt [97, 98]; kept as separate T per statement |
| 103 | attribute | [Titulares de] fuentes estacionarias | T56 | 88061 | 88082 | fuentes estacionarias | same offsets as Attribute of stmt [104]; kept as separate T per statement |
| 104 | attribute | [Titulares de] fuentes estacionarias | T57 | 88061 | 88082 | fuentes estacionarias | same offsets as Attribute of stmt [103]; kept as separate T per statement |
| 106 | attribute | [Titulares de] fuentes estacionarias | T58 | 88457 | 88478 | fuentes estacionarias | same offsets as Attribute of stmt [107, 113]; kept as separate T per statement |
| 107 | attribute | [Titulares de] fuentes estacionarias | T59 | 88457 | 88478 | fuentes estacionarias | same offsets as Attribute of stmt [106, 113]; kept as separate T per statement |
| 113 | attribute | [Titulares de] fuentes estacionarias | T62 | 88457 | 88478 | fuentes estacionarias | same offsets as Attribute of stmt [106, 107]; kept as separate T per statement |
| 115 | attribute | [Titulares de] fuentes estacionarias | T63 | 90554 | 90575 | fuentes estacionarias | same offsets as Attribute of stmt [117]; kept as separate T per statement |
| 117 | attribute | [Titulares de] fuentes estacionarias | T65 | 90554 | 90575 | fuentes estacionarias | same offsets as Attribute of stmt [115]; kept as separate T per statement |
| 121 | attribute | [Titulares de] las calderas | T69 | 92810 | 92822 | las calderas | same offsets as Attribute of stmt [122]; kept as separate T per statement |
| 122 | attribute | [Titulares de] las calderas | T70 | 92810 | 92822 | las calderas | same offsets as Attribute of stmt [121]; kept as separate T per statement |
| 128 | attribute | [Titulares de] fuentes estacionarias | T75 | 93724 | 93745 | fuentes estacionarias | same offsets as Attribute of stmt [129]; kept as separate T per statement |
| 129 | attribute | [Titulares de] fuentes estacionarias | T76 | 93724 | 93745 | fuentes estacionarias | same offsets as Attribute of stmt [128]; kept as separate T per statement |
| 132 | attribute | [Titulares de] calderas y procesos con combustión | T77 | 95408 | 95442 | calderas y procesos con combustión | same offsets as Attribute of stmt [133]; kept as separate T per statement |
| 133 | attribute | [Titulares de] calderas y procesos con combustión | T78 | 95408 | 95442 | calderas y procesos con combustión | same offsets as Attribute of stmt [132]; kept as separate T per statement |
| 139 | attribute | [Titulares de] calderas y procesos con combustión | T83 | 96953 | 96987 | calderas y procesos con combustión | same offsets as Attribute of stmt [143, 144, 145, 147]; kept as separate T per statement |
| 143 | attribute | [Titulares de] calderas y procesos con combustión | T85 | 96953 | 96987 | calderas y procesos con combustión | same offsets as Attribute of stmt [139, 144, 145, 147]; kept as separate T per statement |
| 144 | attribute | [Titulares de] calderas y procesos con combustión | T86 | 96953 | 96987 | calderas y procesos con combustión | same offsets as Attribute of stmt [139, 143, 145, 147]; kept as separate T per statement |
| 145 | attribute | [Titulares de] calderas y procesos con combustión | T87 | 96953 | 96987 | calderas y procesos con combustión | same offsets as Attribute of stmt [139, 143, 144, 147]; kept as separate T per statement |
| 147 | attribute | [Titulares de] calderas y procesos con combustión | T89 | 96953 | 96987 | calderas y procesos con combustión | same offsets as Attribute of stmt [139, 143, 144, 145]; kept as separate T per statement |
| 151 | attribute | [Titulares de] grandes establecimientos | T90 | 99362 | 99386 | grandes establecimientos | same offsets as Attribute of stmt [152, 153]; kept as separate T per statement |
| 152 | attribute | [Titulares de] grandes establecimientos | T91 | 99362 | 99386 | grandes establecimientos | same offsets as Attribute of stmt [151, 153]; kept as separate T per statement |
| 153 | attribute | [Titulares de] grandes establecimientos | T92 | 99362 | 99386 | grandes establecimientos | same offsets as Attribute of stmt [151, 152]; kept as separate T per statement |
| 155 | attribute | Ministerio del Medio Ambiente | T93 | 100699 | 100728 | Ministerio del Medio Ambiente | same offsets as Attribute of stmt [156]; kept as separate T per statement |
| 156 | attribute | [Ministerio del Medio Ambiente] | T94 | 100699 | 100728 | Ministerio del Medio Ambiente | same offsets as Attribute of stmt [155]; kept as separate T per statement |
| 163 | attribute | [SEREMI del Medio Ambiente] | T99 | 103662 | 103687 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [164, 165, 166]; kept as separate T per statement |
| 164 | attribute | [SEREMI del Medio Ambiente] | T100 | 103662 | 103687 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [163, 165, 166]; kept as separate T per statement |
| 165 | attribute | [SEREMI del Medio Ambiente] | T101 | 103662 | 103687 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [163, 164, 166]; kept as separate T per statement |
| 166 | attribute | [SEREMI del Medio Ambiente] | T102 | 103662 | 103687 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [163, 164, 165]; kept as separate T per statement |
| 169 | attribute | Superintendencia del Medio Ambiente | T103 | 105276 | 105311 | Superintendencia del Medio Ambiente | same offsets as Attribute of stmt [170]; kept as separate T per statement |
| 170 | attribute | [Superintendencia del Medio Ambiente] | T104 | 105276 | 105311 | Superintendencia del Medio Ambiente | same offsets as Attribute of stmt [169]; kept as separate T per statement |
| 196 | attribute | Titulares de grupos electrógenos | T114 | 120614 | 120646 | titulares de grupos electrógenos | same offsets as Attribute of stmt [198]; kept as separate T per statement |
| 198 | attribute | [Titulares de grupos electrógenos] | T116 | 120614 | 120646 | titulares de grupos electrógenos | same offsets as Attribute of stmt [196]; kept as separate T per statement |
| 204 | attribute | [Titulares de] planteles de porcinos | T118 | 123020 | 123041 | planteles de porcinos | same offsets as Attribute of stmt [207]; kept as separate T per statement |
| 207 | attribute | [Titulares de] planteles de porcinos | T120 | 123020 | 123041 | planteles de porcinos | same offsets as Attribute of stmt [204]; kept as separate T per statement |
| 210 | attribute | [Titulares de] planteles de aves de corral | T122 | 125174 | 125201 | planteles de aves de corral | same offsets as Attribute of stmt [211, 212]; kept as separate T per statement |
| 211 | attribute | [Titulares de] planteles de aves de corral | T123 | 125174 | 125201 | planteles de aves de corral | same offsets as Attribute of stmt [210, 212]; kept as separate T per statement |
| 212 | attribute | [Titulares de] planteles de aves de corral | T124 | 125174 | 125201 | planteles de aves de corral | same offsets as Attribute of stmt [210, 211]; kept as separate T per statement |
| 213 | attribute | [Titulares de] planteles de aves de corral | T125 | 125747 | 125774 | planteles de aves de corral | same offsets as Attribute of stmt [214, 215]; kept as separate T per statement |
| 214 | attribute | [Titulares de] planteles de aves de corral | T126 | 125747 | 125774 | planteles de aves de corral | same offsets as Attribute of stmt [213, 215]; kept as separate T per statement |
| 215 | attribute | [Titulares de] planteles de aves de corral | T127 | 125747 | 125774 | planteles de aves de corral | same offsets as Attribute of stmt [213, 214]; kept as separate T per statement |
| 216 | attribute | [Titulares de] planteles de aves de corral | T128 | 126283 | 126310 | planteles de aves de corral | same offsets as Attribute of stmt [217, 218]; kept as separate T per statement |
| 217 | attribute | [Titulares de] planteles de aves de corral | T129 | 126283 | 126310 | planteles de aves de corral | same offsets as Attribute of stmt [216, 218]; kept as separate T per statement |
| 218 | attribute | [Titulares de] planteles de aves de corral | T130 | 126283 | 126310 | planteles de aves de corral | same offsets as Attribute of stmt [216, 217]; kept as separate T per statement |
| 238 | attribute | SEREMI del Medio Ambiente | T145 | 132155 | 132180 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [240]; kept as separate T per statement |
| 240 | attribute | [SEREMI del Medio Ambiente] | T147 | 132155 | 132180 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [238]; kept as separate T per statement |
| 254 | attribute | Ministerio de Vivienda y Urbanismo | T158 | 137323 | 137357 | Ministerio de Vivienda y Urbanismo | same offsets as Attribute of stmt [255, 256]; kept as separate T per statement |
| 255 | attribute | [Ministerio de Vivienda y Urbanismo] | T159 | 137323 | 137357 | Ministerio de Vivienda y Urbanismo | same offsets as Attribute of stmt [254, 256]; kept as separate T per statement |
| 256 | attribute | [Ministerio de Vivienda y Urbanismo] | T160 | 137323 | 137357 | Ministerio de Vivienda y Urbanismo | same offsets as Attribute of stmt [254, 255]; kept as separate T per statement |
| 273 | attribute | Ministerio de Agricultura | T169 | 142577 | 142602 | Ministerio de Agricultura | same offsets as Attribute of stmt [274]; kept as separate T per statement |
| 274 | attribute | [Ministerio de Agricultura] | T170 | 142577 | 142602 | Ministerio de Agricultura | same offsets as Attribute of stmt [273]; kept as separate T per statement |
| 275 | attribute | Gobierno Regional Metropolitano de Santiago | T171 | 143418 | 143461 | Gobierno Regional Metropolitano de Santiago | same offsets as Attribute of stmt [276, 278]; kept as separate T per statement |
| 276 | attribute | [Gobierno Regional Metropolitano de Santiago] | T172 | 143418 | 143461 | Gobierno Regional Metropolitano de Santiago | same offsets as Attribute of stmt [275, 278]; kept as separate T per statement |
| 278 | attribute | [Gobierno Regional Metropolitano de Santiago] | T173 | 143418 | 143461 | Gobierno Regional Metropolitano de Santiago | same offsets as Attribute of stmt [275, 276]; kept as separate T per statement |
| 290 | attribute | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | T184 | 150252 | 150370 | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | same offsets as Attribute of stmt [291]; kept as separate T per statement |
| 291 | attribute | [el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes] | T185 | 150252 | 150370 | el Ministerio del Medio Ambiente, junto con la Intendencia Regional Metropolitana, Ministerios y Servicios competentes | same offsets as Attribute of stmt [290]; kept as separate T per statement |
| 292 | attribute | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | T186 | 150693 | 150763 | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | same offsets as Attribute of stmt [293, 294]; kept as separate T per statement |
| 293 | attribute | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] | T187 | 150693 | 150763 | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | same offsets as Attribute of stmt [292, 294]; kept as separate T per statement |
| 294 | attribute | [la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM] | T188 | 150693 | 150763 | la SEREMI del Medio Ambiente en conjunto con la SEREMI de Educación RM | same offsets as Attribute of stmt [292, 293]; kept as separate T per statement |
| 295 | attribute | SEREMI del Medio Ambiente | T189 | 151655 | 151680 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [296, 297, 298]; kept as separate T per statement |
| 296 | attribute | [SEREMI del Medio Ambiente] | T190 | 151655 | 151680 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [295, 297, 298]; kept as separate T per statement |
| 297 | attribute | [SEREMI del Medio Ambiente] | T191 | 151655 | 151680 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [295, 296, 298]; kept as separate T per statement |
| 298 | attribute | [SEREMI del Medio Ambiente] | T192 | 151655 | 151680 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [295, 296, 297]; kept as separate T per statement |
| 299 | attribute | SEREMI del Medio Ambiente | T193 | 152928 | 152953 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [300, 301]; kept as separate T per statement |
| 300 | attribute | [SEREMI del Medio Ambiente] | T194 | 152928 | 152953 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [299, 301]; kept as separate T per statement |
| 301 | attribute | [SEREMI del Medio Ambiente] | T195 | 152928 | 152953 | SEREMI del Medio Ambiente | same offsets as Attribute of stmt [299, 300]; kept as separate T per statement |
| 313 | attribute | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | T201 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | same offsets as Attribute of stmt [314, 315, 316]; kept as separate T per statement |
| 314 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T202 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | same offsets as Attribute of stmt [313, 315, 316]; kept as separate T per statement |
| 315 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T203 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | same offsets as Attribute of stmt [313, 314, 316]; kept as separate T per statement |
| 316 | attribute | [Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM] | T204 | 157335 | 157443 | Ministerio de Transportes y Telecomunicaciones, a través de la SEREMI de Transportes y Telecomunicaciones RM | same offsets as Attribute of stmt [313, 314, 315]; kept as separate T per statement |

</details>

