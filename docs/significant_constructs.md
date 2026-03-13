# Significant DR Bridge Constructs

# TODO add frequency tables for the construct aggregate values actually used in the bridge - what the de actual numbers 'travelling' along the bridge actually look like? 

# TODO in addition to marginals of the aggregate (or otherwise) variable that travels along the bridge, add bivariate tables of it for each SES variable -- the aim is to figure out which variable is doing the work, and if this has an influence of the behavior of the bridge, the expectation being that a robust bridge should have matching ses drivers. 

# TODO what is the relationship, expected and observed, between alpha and gamma?? do more robust aggregates lead to more robust bridges? is the strength of the singal realted to the robustness of the connection? 

## Overview

This document lists all 56 survey constructs that have at least one statistically significant Doubly Robust (DR) bridge edge in the v4 construct-level sweep. A significant edge means the 95% bootstrap CI for Goodman-Kruskal gamma excludes zero (ci_low > 0 OR ci_high < 0), indicating that shared SES factors (sex, age, education, locality size) produce a detectable monotonic co-variation between the two constructs across Mexican survey respondents.

Constructs are drawn from 26 nationally representative surveys conducted in Mexico (2014-2015), covering 24 thematic domains. Variables use Spanish-language question text as recorded in the original survey instruments. The sweep covered 4,979 cross-domain construct pairs with 7.2% (360 pairs) reaching significance.

Entries are ordered by Cronbach's alpha descending. Formative indices and constructs with undefined or negative alpha appear at the bottom.

---

## Construct Quality Tiers

Each construct is assigned to one of five quality tiers based on internal consistency:

**good** (alpha >= 0.70)
> Strong internal consistency. Items reliably measure the same underlying construct. These are the most trustworthy aggregate scores for hypothesis testing and policy inference.

**questionable** (alpha 0.50–0.69)
> Moderate consistency. The construct is interpretable but items share less variance. Results are useful for exploratory and descriptive analysis; use with caution in confirmatory settings.

**tier3_caveat** (alpha 0.01–0.49)
> Weak consistency. Items may be multidimensional or only loosely related to a single latent factor. Treat results as exploratory signals only. Conceptual coherence may still justify the aggregate, but statistical reliability is limited.

**single_item_tier2** (no Cronbach's alpha)
> Alpha is undefined for a single item. The reported value is the item-total correlation between the selected item and the domain's best available multi-item scale. The single best item was chosen for constructs where multi-item measurement was not feasible given the survey instrument design.

**formative_index** (alpha is meaningless by design)
> Items are not assumed to be correlated — they are independent indicators that each contribute uniquely to the construct (e.g., a count of deprivations, a sum of asset ownership flags). A negative or near-zero alpha is expected and correct for formative measures. Do not interpret alpha as a quality indicator for these constructs.

---

## Constructs

## [01] FED|legal_uniformity_preference  (alpha = 0.9482, good, N valid = 1,200)

**Domain:** Federalismo | **Survey:** FEDERALISMO

_Measures citizens' preference for a single national law versus state-specific laws across multiple policy domains (crime, corruption, information access, security, environment, taxation), capturing the normative dimension of legal centralization._

**Variables:**
- `p53_1` — 53 ¿Usted preferiría que para combatir los delitos existiera una sola ley para todo el país o que cada estado tenga leyes...
- `p53_2` — 53 ¿Usted preferiría que para combatir la corrupción existiera una sola ley para todo el país o que cada estado tenga l...
- `p53_3` — 53 ¿Usted preferiría que para acceder a la información del gobierno existiera una sola ley para todo el país o que cada ...
- `p53_4` — 53 ¿Usted preferiría que para seguridad pública existiera una sola ley para todo el país o que cada estado tenga leyes ...
- `p53_5` — 53 ¿Usted preferiría que para cuidar el medio ambiente existiera una sola ley para todo el país o que cada estado tenga...
- `p53_6` — 53 ¿Usted preferiría que para cobrar impuestos existiera una sola ley para todo el país o que cada estado tenga leyes d...

## [02] FED|perceived_representativeness  (alpha = 0.9157, good, N valid = 1,200)

**Domain:** Federalismo | **Survey:** FEDERALISMO

_Measures the degree to which citizens feel that various levels and types of elected officials (municipal, state, federal) represent the interests of people like themselves. Captures a multi-level assessment of political representation._

**Variables:**
- `p12_1` — 12 ¿Qué tanto considera que los partidos políticos representa(n) los intereses de gente como usted?
- `p12_2` — 12 ¿Qué tanto considera que los diputados locales representa(n) los intereses de gente como usted?
- `p12_3` — 12 ¿Qué tanto considera que los diputados federales representa(n) los intereses de gente como usted?
- `p12_4` — 12 ¿Qué tanto considera que el gobernador representa(n) los intereses de gente como usted?
- `p12_5` — 12 ¿Qué tanto considera que el presidente del país representa(n) los intereses de gente como usted?
- `p12_6` — 12 ¿Qué tanto considera que el presidente municipal representa(n) los intereses de gente como usted?

## [03] REL|supernatural_beliefs  (alpha = 0.9003, good, N valid = 1,023)

**Domain:** Religion, Secularizacion y Laicidad | **Survey:** RELIGION_SECULARIZACION_Y_LAICIDAD

_Measures the breadth and depth of an individual's belief in supernatural, religious, and metaphysical entities or forces, ranging from orthodox Christian beliefs (God, hell, resurrection) to folk and syncretic beliefs (witchcraft, karma, limpias, reincarnation). Captures the overall cosmological worldview._

**Variables:**
- `p17_1` — 17. ¿Cree usted en la existencia de Dios?
- `p17_2` — 17. ¿Cree usted en la existencia de vida después de la muerte?
- `p17_4` — 17. ¿Cree usted en la existencia del infierno?
- `p17_5` — 17. ¿Cree usted en la existencia del paraíso?
- `p17_6` — 17. ¿Cree usted en la existencia del pecado
- `p17_7` — 17. ¿Cree usted en la existencia del alma
- `p17_8` — 17. ¿Cree usted en la existencia de la resurrección de los muertos?
- `p17_9` — 17. ¿Cree usted en la existencia del diablo?
- `p17_10` — 17. ¿Cree usted en la existencia de la reencarnación?
- `p17_11` — 17. ¿Cree usted en la existencia de la brujería?
- `p17_12` — 17. ¿Cree usted en la existencia del karma?
- `p17_13` — 17. ¿Cree usted en la existencia de las limpias?
- `p17_14` — 17. ¿Cree usted en la existencia del destino?
- `p17_15` — 17. ¿Cree usted en la existencia del poder de la mente?

## [04] MED|pro_environmental_civic_engagement  (alpha = 0.7960, good, N valid = 1,200)

**Domain:** Medio Ambiente | **Survey:** MEDIO_AMBIENTE

_Measures the extent to which respondents have taken active collective or civic actions in defense of the environment, including petitions, protests, donations, reporting, and attending talks._

**Variables:**
- `p34_1` — 34 ¿En los últimos cinco años usted ha firmado alguna petición colectiva sobre alguna cuestión ambiental?
- `p34_2` — 34 ¿En los últimos cinco años usted ha hecho algún donativo a algún grupo ambientalista?
- `p34_3` — 34 ¿En los últimos cinco años usted ha participado en algún acto de protesta o manifestación sobre alguna cuestión ambiental?
- `p34_4` — 34 ¿En los últimos cinco años usted ha denunciado ante las autoridades algún daño o contaminación al medio ambiente?
- `p34_5` — 34 ¿En los últimos cinco años usted ha asistido alguna plática o conferencia sobre medio ambiente?

## [05] SOC|digital_technology_access_and_ownership  (alpha = 0.7857, good, N valid = 255)

**Domain:** Sociedad de la Informacion | **Survey:** SOCIEDAD_DE_LA_INFORMACION

_Measures the actual stock of digital and communication devices in the household, capturing material access to the information society. Together these items form a composite index of household technological endowment._

**Variables:**
- `p5a_7` — 5 ¿Cuántos? Computadora de escritorio
- `p5a_10` — 5 ¿Cuántos? Conexión a internet

## [06] EDU|digital_and_cultural_capital  (alpha = 0.7450, good, N valid = 1,199)

**Domain:** Educacion | **Survey:** EDUCACION

_Respondent's access to and use of information and communication technologies, reading habits, and cultural participation, reflecting the stock of resources available for informal learning and social engagement._

# TODO note that these are actually TWO dimensions that seem foled into one. are they? 

**Variables:**
- `p47_3` — 47 ¿Tiene usted computadora o tableta?
- `p47_4` — 47 ¿Tiene usted Internet?
- `p47_6` — 47 ¿Tiene usted teléfono celular?
- `p48_1` — 48 ¿Usted utiliza la computadora para obtener información?
- `p48_3` — 48 ¿Usted utiliza la computadora para apoyar la educación/capacitación?
- `p45_1` — 45 ¿Con qué frecuencia lee usted el periódico?
- `p45_2` — 45 ¿Con qué frecuencia lee usted libros?
- `p44_5` — 44 ¿Con qué frecuencia asiste usted a exposiciones y museos?

## [07] REL|personal_religiosity  (alpha = 0.7318, good, N valid = 961)

**Domain:** Religion, Secularizacion y Laicidad | **Survey:** RELIGION_SECULARIZACION_Y_LAICIDAD

_Measures the degree to which religion is personally meaningful and actively practiced in daily life, including prayer outside formal worship, finding comfort in religion, using religious values to guide family behavior, reliance on clergy for life decisions, and the importance of God in one's life._

**Variables:**
- `p10` — 10. ¿Acostumbra orar o hacer peticiones a un poder superior fuera del templo o de las celebraciones religiosas?
- `p12` — 12. ¿Usted encuentra o no encuentra confort y fuerza en la religión?
- `p13_1` — 13. ¿Por lo general, usted toma o no toma en cuenta los valores de la religión para manejar su comportamiento en la familia?
- `p14` — 14. Para tomar decisiones importantes en su vida, ¿qué tanto se guía por las recomendaciones de los sacerdotes (o ministros)?
- `p25` — 25. ¿Usted dedica algunos momentos a rezar, meditar, a la contemplación o algo similar?
- `p11` — 11. ¿Usted le pediría algún favor a la Virgen de Guadalupe o a algún santo?

## [08] HAB|household_asset_endowment  (alpha = 0.7254, good, N valid = 1,200)

**Domain:** Habitabilidad de Vivienda | **Survey:** LA_CONDICION_DE_HABITABILIDAD_DE_VIVIENDA_EN_MEXICO

_Measures the stock of durable goods and domestic appliances present in the dwelling — from basic items like refrigerators and washing machines to modern assets like computers and solar panels — as a proxy for household socioeconomic status and living standards._

# TODO see if these items would work to compute AMAI scores

**Variables:**
- `p36_1` — 36 ¿Esta vivienda cuenta con Radio o radio grabadora
- `p36_2` — 36 ¿Esta vivienda cuenta con Televisión
- `p36_4` — 36 ¿Esta vivienda cuenta con Licuadora
- `p36_5` — 36 ¿Esta vivienda cuenta con Lavadora
- `p36_6` — 36 ¿Esta vivienda cuenta con Refrigerador
- `p36_8` — 36 ¿Esta vivienda cuenta con Teléfono móvil (celular)
- `p36_9` — 36 ¿Esta vivienda cuenta con Automóvil o camioneta propios
- `p36_10` — 36 ¿Esta vivienda cuenta con Computadora
- `p36_18` — 36 ¿Esta vivienda cuenta con Calentador o boiler de gas
- `p36_21` — 36 ¿Esta vivienda cuenta con Calefacción
- `p36_22` — 36 ¿Esta vivienda cuenta con Paneles solares para energía
- `p36_29` — 36 ¿Esta vivienda cuenta con Aire acondicionado

## [09] IND|national_economic_outlook  (alpha = 0.7166, good, N valid = 1,111)

**Domain:** Indigenas | **Survey:** INDIGENAS

_Measures respondents' retrospective and prospective evaluations of Mexico's overall economic situation, capturing both sociotropic economic assessments and economic expectations._

# TODO these questions are available in more than one questionnarie, no? If they are, let's comparetheir marginals across versions - perhaps they shift singificantly by domian if previously asked questions bias the outlook. Is this true? 

**Variables:**
- `p1` — 1. Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación actual del país?
- `p2` — 2. En general, ¿cree usted que el próximo año la situación económica del país va a mejorar o empeorar?

## [10] CIE|science_technology_self_efficacy  (alpha = 0.6992, questionable, N valid = 1,104)

**Domain:** Ciencia y Tecnologia | **Survey:** CIENCIA_Y_TECNOLOGIA

_Measures respondents' perceived ability to understand and engage with science and technology, including self-assessed knowledge levels and agreement that science is too specialized to comprehend. Captures the subjective sense of competence in scientific and technological domains._

# TODO how are scales of first two and third reconciled? I can expect a good correlation between them-- this is why I want to see the marginals of the aggregate variable for the construct, because if these variables have different scales, their addition might not be trivial. So, explain aggregation in detail. 

**Variables:**
- `p16` — 16 En una escala de calificación del cero al 10, como en la escuela, en donde cero es nada y 10 es mucho, ¿qué tantos conocimientos tiene usted sobre ciencia?
- `p17` — 17 ¿Y sobre tecnología?
- `p45_1` — 45 Ahora dígame por favor, ¿qué tan de acuerdo o desacuerdo está usted con los siguientes enunciados? La ciencia es demasiado especializada para entenderla...

## [11] GLO|economic_globalization_attitudes  (alpha = 0.6936, questionable, N valid = 1,200)

**Domain:** Globalizacion | **Survey:** GLOBALIZACION

_Measures respondents' evaluations of economic integration with the world, including opinions on free trade agreements, foreign investment, and the US-Mexico trade relationship._

# TODO this one might have changed in time, a good reason to explore the time dimension of the y-surface in WVS. Which other constructs could be good candidates for time-wise analysis in WVS? 

**Variables:**
- `p46_1` — 46 En general, ¿cree usted que los Tratados de Libre Comercio, son positivos o negativos para la economía mexicana?
- `p47` — 47 Dígame, ¿cuál de los siguientes enunciados refleja mejor su perspectiva respecto al comercio exterior?
- `p48` — 48 De manera general ¿usted está de acuerdo o en desacuerdo con los Tratados de Libre Comercio celebrados entre México y otros países?
- `p49_1` — 49 En su opinión, ¿el gobierno mexicano debe permitir o no debe permitir que los extranjeros inviertan en telefonía?
- `p31_1` — 31 ¿Qué piensa usted de la relación comercial entre México y Estados Unidos? ¿Cree que es positiva o negativa para nuestra economía?

## [12] ECO|human_capital_and_employment_preparation  (alpha = 0.6581, questionable, N valid = 657)

**Domain:** Economia y Empleo | **Survey:** ECONOMIA_Y_EMPLEO

_Measures the relationship between education, training, and labor market readiness, including highest education attained, perceived educational adequacy for one's job, participation in professional development, and perceived utility of that training. Captures the latent construct of human capital investment._

**Variables:**
- `p64` — 64 ¿Cuál era su nivel de estudios al empezar a trabajar?
- `p65` — 65 Qué nivel de estudios cree usted que es el más adecuado para realizar el trabajo que desempeña en la actualidad o el último que tuvo?
- `p67` — 67 ¿Cuál es el nivel más alto de estudios terminados que usted ha alcanzado?
- `p71` — 71. ¿Usted ha realizado o realiza actualmente, algún tipo de formación para mejorar su calificación profesional o de actualización en su área de trabajo?

## [13] CIE|institutional_trust_in_science  (alpha = 0.6367, questionable, N valid = 1,200)

**Domain:** Ciencia y Tecnologia | **Survey:** CIENCIA_Y_TECNOLOGIA

_Measures respondents' trust in and perceived integrity of scientific institutions and actors, including skepticism about scientists' motivations, confidence in research disciplines, and perceived commitment of Mexican scientists to society._

**Variables:**
- `p32_1` — 32 Y dígame, ¿qué tan de acuerdo o en desacuerdo está con las siguientes frases? Los científicos desarrollan investigaciones en beneficio de la sociedad...
- `p33` — 33 En su opinión ¿qué tan comprometidos están los científicos mexicanos con la sociedad?
- `p40_1` — 40 Indique qué tan de acuerdo o en desacuerdo está con los siguientes enunciados: Los científicos siguen intereses políticos y no científicos...
- `p50_1` — 50 Indíqueme por favor qué tanta confianza le tiene a la investigación que se realiza en las siguientes disciplinas: Medicina
- `p49_1` — 49 Dígame por favor, ¿qué tan de acuerdo o en desacuerdo esta con las siguientes afirmaciones? Las universidades deben buscar la verdad aunque el resultado sea incómodo...

## [14] FED|political_interest_and_engagement  (alpha = 0.6342, questionable, N valid = 1,200)

**Domain:** Federalismo | **Survey:** FEDERALISMO

_Measures the extent to which citizens are attentive to and engaged with politics, including frequency of news consumption, self-reported interest in politics, perceived relevance of politics to daily life, and the tendency to disengage when personal circumstances are satisfactory._

**Variables:**
- `p5` — 5 ¿Con qué frecuencia acostumbra leer, ver o escuchar noticias o programas sobre política o asuntos públicos?
- `p6` — 6 ¿Qué tanto se interesa usted en la política?
- `p7` — 7 ¿Qué tanto piensa usted que la política tiene que ver con su vida diaria?

## [15] DER|social_rights_service_quality  (alpha = 0.6284, questionable, N valid = 1,200)

**Domain:** Derechos Humanos, Discriminacion y Grupos Vulnerables | **Survey:** DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES

_Measures citizens' evaluations of the state's fulfillment of social and economic rights — including public health services, public education quality, and dignified housing — reflecting perceived adequacy of social rights provision by the government._

**Variables:**
- `p30` — 30 ¿Qué tan eficientes o ineficientes considera usted que son los servicios públicos de salud?
- `p31` — 31 ¿Usted considera que habita una vivienda digna?
- `p32` — 32 ¿Cómo considera la calidad de la educación pública?

## [16] SEG|crime_victimization_exposure  (alpha = 0.6092, formative_index, N valid = 1,200)

**Domain:** Seguridad Publica | **Survey:** SEGURIDAD_PUBLICA

_Measures the extent and type of direct criminal victimization experienced by the respondent or household members in the past 12 months, including frequency across specific crime types and whether the most recent incident was reported to authorities._

**Variables:**
- `p56` — 56 En los últimos doce meses, ¿alguna persona que vivía o vive en este hogar fue víctima de algún delito?  [GATEWAY]
- `p56_1` — 56.1 ¿Cuántas personas fueron víctimas?
- `p57` — 57 Y dígame, en los últimos doce meses, ¿usted fue víctima de algún delito?  [GATEWAY]
- `p57_1` — 57.1 ¿Cuántas veces?
- `p58_1` — 58 En los últimos doce meses, ¿usted fue víctima de robo a transeúnte?
- `p58a_1` — 58 ¿Cuántas veces? Robo a transeúnte
- `p58a_2` — 58 ¿Cuántas veces? Robo a casa habitación
- `p58a_3` — 58 ¿Cuántas veces? Robo de automóvil, camión o taxi
- `p58a_5` — 58 ¿Cuántas veces? Robo en transporte público
- `p58a_7` — 58 ¿Cuántas veces? Extorsión
- `p58a_8` — 58 ¿Cuántas veces? Secuestro exprés
- `p58a_9` — 58 ¿Cuántas veces? Secuestro
- `p60` — 60 Con relación a este último delito del que fue víctima, ¿Usted presentó la denuncia ante el Ministerio Público?

## [17] EDU|educational_returns_belief  (alpha = 0.6073, questionable, N valid = 1,199)

**Domain:** Educacion | **Survey:** EDUCACION

_Respondent's beliefs about the instrumental and social value of education, including whether studying improves employment prospects, income, and societal well-being, and whether it is generally worthwhile._

**Variables:**
- `p37` — 37 ¿Usted considera que vale o no vale la pena estudiar?
- `p55_3` — 55 ¿Cree usted que la escuela prepara para tener mejores empleos?
- `p55_4` — 55 ¿Cree usted que estudiar mejora el ingreso de las personas?
- `p55_5` — 55 ¿Cree usted que por estudiar tenemos una mejor sociedad?

## [18] FED|fiscal_and_service_federalism_preferences  (alpha = 0.6026, questionable, N valid = 1,200)

**Domain:** Federalismo | **Survey:** FEDERALISMO

_Measures citizens' preferences regarding the distribution of fiscal resources, administrative responsibilities, and service delivery across government levels, reflecting attitudes toward decentralization versus centralization of governance functions._

# TODO this list is too broad, it most surely contains more than one dimention and, if not properly aggregated, is quite multimodal. Review variables, values, and suggest a redesign. 

**Variables:**
- `p31_1` — 31 En su opinión, ¿quién es el principal responsable de los problemas en materia de agua potable: el gobierno municipal, estatal o federal?
- `p32_1` — 32 Y en su experiencia, ¿quién debería de estar a cargo del agua potable?
- `p33` — 33 En general, ¿quién debería de resolver los problemas de su localidad/colonia?
- `p34_1` — 34 En su opinión ¿quién debe hacerse cargo de los servicios educativos en su estado: el gobierno federal, el gobierno estatal o el gobierno municipal?
- `p36` — 36 ¿Cómo deberían repartirse el dinero de los impuestos?
- `p37_1` — 37 De acuerdo a su experiencia, ¿los servicios que proporciona el gobierno municipal corresponden o no corresponden a los impuestos que paga?
- `p38` — 38 ¿Con cuál de las siguientes frases está usted más de acuerdo?
- `p60` — 60 Por lo que usted piensa, para gobernar el país ¿qué es mejor, que el gobierno federal concentre las decisiones importantes o que las decisiones se tomen en los estados?

## [19] MIG|transnational_social_ties  (alpha = 0.6010, questionable, N valid = 360)

**Domain:** Migracion | **Survey:** MIGRACION

_Measures the extent and nature of the respondent's social network connections to Mexicans living abroad, including family, friends, remittance flows, and frequency of contact, capturing embeddedness in transnational social fields._

# TODO why is n so low?

**Variables:**
- `p21` — 21 ¿Tiene familiares que ahora viven fuera de México?
- `p21_2` — 21.2 ¿Usted o su familia reciben dinero de familiares que trabajan fuera del país?
- `p22` — 22 ¿Algún amigo de usted vive en el extranjero?
- `p23` — 23 ¿Con qué frecuencia está en contacto con los mexicanos que conoce y viven en el extranjero?
- `p24` — 24 ¿Si usted decidiera migrar a otro país donde vive la gente que conoce, qué tanto considera que lo apoyarían?

## [20] CUL|political_efficacy_and_engagement  (alpha = 0.5935, questionable, N valid = 1,200)

**Domain:** Cultura Politica | **Survey:** CULTURA_POLITICA

_Measures citizens' sense that politics is relevant to their lives, that they can influence government decisions, and their subjective interest in and comprehension of political affairs._

# TODO again, too many variables with too many topics and scales. It's ok if the topics are varied, but the question format, answer codes, etc. may not aggregate well. Consider for recode  or removal to improve fit. 

**Variables:**
- `p10` — 10 ¿Qué tanto se interesa usted en la política?
- `p11` — 11 ¿Qué tanto piensa usted que la política tiene que ver con su vida diaria?
- `p20` — 20 En general ¿qué tan complicada es para usted la política?
- `p21` — 21 En su opinión, ¿la política contribuye o no contribuye a mejorar el nivel de vida de todos los mexicanos?
- `p25` — 25 En su opinión, ¿vale o no vale la pena participar en política?
- `p46` — 46 ¿Qué tanto cree usted que los ciudadanos pueden influir en las decisiones del gobierno?
- `p51` — 51 En general, ¿Está Ud. satisfecho con las posibilidades que tiene actualmente de participar en las cuestiones políticas del país?
- `p52` — 52 ¿Y qué tan satisfecho está usted con la manera en que sus opiniones son tomadas en cuenta?

## [21] DER|perceived_discrimination_social_exclusion  (alpha = 0.5814, questionable, N valid = 1,200)

**Domain:** Derechos Humanos, Discriminacion y Grupos Vulnerables | **Survey:** DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES

_Measures respondents' perceptions of and attitudes toward discriminatory treatment based on physical appearance, skin color, religion, disability, and sexual orientation, including both personal experiences of rights violations and observed societal discrimination against vulnerable groups._

# TODO see that p35_1 is about experience and the rest are about attitudes - they may not be correlated at all. Drop it. And again, reveiw answer codes and make sure aggregation is propperly done and recode is optimal. 

**Variables:**
- `p35_1` — 35 ¿Alguna vez ha sentido que sus derechos no han sido respetados por su apariencia física?
- `p36_1` — 36 ¿Usted le dejaría de rentar o no una habitación en su casa a una persona exclusivamente por su religión?
- `p39` — 39 ¿Cómo cree que las personas de piel obscura son tratadas en México?
- `p40_1` — 40 ¿Toleraría o no toleraría que un(a) hijo(a) suyo(a) manifestara su homosexualidad?
- `p41` — 41 ¿Estaría de acuerdo o en desacuerdo en que se penalizara a quienes den muestra en público de su homosexualidad?
- `p44` — 44 ¿Considera correcto o incorrecto que se prohíba la entrada a un lugar público a cualquier persona sólo por su aspecto físico?

## [22] REL|religious_socialization  (alpha = 0.5548, questionable, N valid = 847)

**Domain:** Religion, Secularizacion y Laicidad | **Survey:** RELIGION_SECULARIZACION_Y_LAICIDAD

_Measures the extent to which an individual's religious identity and practice were shaped by family and institutional upbringing, including whether they share the religion of their parents, whether family members are religiously homogeneous, and whether they received formal religious education._

# TODO why n so low?

**Variables:**
- `p2` — 2. ¿En el pasado fue miembro de una iglesia o denominación religiosa?
- `p3` — 3. ¿Tiene usted la misma religión de su papá?
- `p4` — 4. ¿Tiene usted la misma religión de su mamá?
- `p5` — 5. En su familia, ¿todos tienen la misma religión?
- `p6` — 6. ¿Recibió alguna educación religiosa?
- `p33_1` — 33. ¿Sus padres y usted piensan (pensaban) de la misma manera sobre los siguientes aspectos? La religión

## [23] DER|rights_awareness_personal_experience  (alpha = 0.5536, questionable, N valid = 1,200)

**Domain:** Derechos Humanos, Discriminacion y Grupos Vulnerables | **Survey:** DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES

_Measures respondents' direct personal experience with human rights violations and labor rights abuses, as well as their sense of protection against authority abuse, capturing the lived dimension of rights rather than abstract attitudes._

# TODO are these the only options for experiences of hr violations? review questionnair if test if more options are available. 

**Variables:**
- `p45` — 45 ¿Considera usted que alguna vez han sido violados sus derechos humanos?
- `p53` — 53 ¿Alguna vez ha sido víctima de acoso escolar (bullying)?
- `p54` — 54 ¿Alguna vez ha sido víctima de acoso laboral (mobbing)?

## [24] NIN|perceived_situation_of_children_and_youth  (alpha = 0.5463, questionable, N valid = 1,200)

**Domain:** Ninos, Adolescentes y Jovenes | **Survey:** NINOS_ADOLESCENTES_Y_JOVENES

_Measures respondents' perception of whether the general situation (social, economic) of children, adolescents, and young people in Mexico has improved or deteriorated over time, capturing a broad evaluative orientation toward generational well-being._

**Variables:**
- `p5` — 5 En su opinión, desde el año 2010 hasta la hoy, ¿la situación general de los niños en México ha mejorado o ha empeorado?
- `p31` — 31 En su opinión, desde el año 2010 hasta hoy, ¿la situación general de los adolescentes en México ha mejorado o ha empeorado?
- `p61` — 61 Y desde el año 2010 a la fecha, ¿la situación económica de los jóvenes en México ha mejorado o ha empeorado?

## [25] NIN|youth_participation_and_voice  (alpha = 0.5462, questionable, N valid = 1,181)

**Domain:** Ninos, Adolescentes y Jovenes | **Survey:** NINOS_ADOLESCENTES_Y_JOVENES

_Measures normative attitudes toward the extent to which children and adolescents should have a say in decisions affecting them — in family, school, and public life — capturing beliefs about youth agency, civic inclusion, and rights._

# TODO review options, recodes, etc. p47 may not me properly recoded to match the rest.

**Variables:**
- `p12` — 12 En general, ¿qué tanto piensa Ud. que deberían tomarse en cuenta las opiniones de los niños en las decisiones familiares?
- `p13` — 13 Y en general, ¿qué tanto piensa Ud. que deberían tomarse en cuenta las opiniones de los niños en lo que afecta a su escuela?
- `p38` — 38 En general, ¿qué tanto piensa usted que deberían tomarse en cuenta las opiniones de los adolescentes en las decisiones familiares?
- `p39` — 39 Y en general, ¿qué tanto piensa usted que deberían tomarse en cuenta las opiniones de los adolescentes en las decisiones que les afectan en su escuela?
- `p41` — 41 ¿En qué ocasiones consideras que deben participar los adolescentes en marchas o movilizaciones públicas?
- `p47` — 47 Usted cree que los adolescentes deben tener...

## [26] GLO|international_institutional_engagement  (alpha = 0.5448, questionable, N valid = 1,200)

**Domain:** Globalizacion | **Survey:** GLOBALIZACION

_Measures the degree to which respondents support Mexico's participation in and deference to international institutions and multilateral governance, including the UN, NGOs, and international human rights bodies._

# TODO review coding, many of these may not be properly recoded 

**Variables:**
- `p52_1` — 52 ¿Usted considera que México debe involucrarse con la comunidad internacional para tratar temas como calentamiento global?
- `p54_1` — 54 Le voy a mencionar algunos problemas. Para cada uno, dígame si cree que las políticas en esas áreas deberían decidirlas los gobiernos nacionales o los organismos internacionales...
- `p57` — 57 ¿Cree usted que la ONU DEBE o NO DEBE promover activamente los derechos humanos en los Estados miembros?
- `p58` — 58 ¿Usted acudiría a un organismo internacional (como por ejemplo la Comisión Interamericana de Derechos Humanos) para defender sus derechos?
- `p60_1` — 60 ¿Cree usted que las Naciones Unidas deberían o no deberían tener el derecho de hacer uso de la fuerza militar para defender los derechos humanos?
- `p63_1` — 63 ¿Considera que México debe trabajar en colaboración con otros países para resolver el problema de migración?

## [27] POB|intergenerational_mobility_perception  (alpha = 0.5370, questionable, N valid = 1,075)

**Domain:** Pobreza | **Survey:** POBREZA

_Perceived economic mobility across generations, capturing whether respondents believe their own situation has improved relative to their parents and whether they expect their children/grandchildren to fare better or worse, as well as their assessment of structural opportunities for youth upward mobility._

# recode? 

**Variables:**
- `p22` — 22. ¿Considera usted que su situación económica es mejor o peor que la que tenían sus padres cuando usted tenía 18 años?
- `p23` — 23. Independientemente de lo que a usted le gustaría, ¿piensa que en un futuro la situación económica de sus hijos (nietos) será mejor o peor que la suya actual?
- `p24` — 24. Pensando en los cambios económicos del país en los últimos años, ¿usted considera que las posibilidades de los jóvenes de hoy para salir adelante son mejores o peores que las de sus padres?
- `p36` — 36. ¿Qué tan de acuerdo o en desacuerdo está usted con la siguiente afirmación? 'Aunque tener estudios siga siendo necesario, ya no garantiza tener un buen trabajo'

## [28] ENV|assessment_of_older_adult_wellbeing_and_social_conditions  (alpha = 0.5319, questionable, N valid = 1,200)

**Domain:** Envejecimiento | **Survey:** ENVEJECIMIENTO

_Reflects respondents' evaluations of the current and future quality of life, dignity, and social situation of older adults in Mexico, including perceived trends over time and the societal salience of their problems._

# recode? 

**Variables:**
- `p9` — 9 Por lo que usted ha visto, desde el año 2010 hasta hoy, ¿la situación general de los adultos mayores en México ha mejorado o ha empeorado?
- `p10` — 10 En su opinión, en 10 años, ¿la situación general de los adultos mayores en México será mejor o peor?
- `p38` — 38 ¿Qué tanto cree usted que la gente tenga en consideración los problemas de los adultos mayores, hoy en día?

## [29] HAB|basic_services_access  (alpha = 0.5301, questionable, N valid = 1,126)

**Domain:** Habitabilidad de Vivienda | **Survey:** LA_CONDICION_DE_HABITABILIDAD_DE_VIVIENDA_EN_MEXICO

_Captures the availability and adequacy of essential infrastructure services within the dwelling, including water supply frequency and delivery method, drainage, and electricity, reflecting the degree to which households are connected to public utility networks._

**Variables:**
- `p7` — 7 ¿Cuántos días a la semana les llega el agua?
- `p7_1` — 7.1 El agua les llega...
- `p8` — 8 Esta vivienda tiene...
- `p10` — 10 Esta vivienda tiene drenaje o desagüe de aguas sucias...
- `p11` — 11 ¿Hay luz eléctrica en esta vivienda?
- `p36_30` — 36 ¿Esta vivienda cuenta con Drenaje

## [30] COR|civic_enforcement_norms  (alpha = 0.5246, questionable, N valid = 1,139)

**Domain:** Corrupcion y Cultura de la Legalidad | **Survey:** CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD

_Measures respondents' beliefs about how rule violations should be sanctioned and their personal behavioral responses when witnessing misconduct, reflecting internalized norms around accountability and social enforcement._

# recode? 


**Variables:**
- `p20` — 20 En una escuela, ¿qué debe hacer un maestro que sorprende a un alumno (a) robando el alimento de un compañero?
- `p21` — 21 En el centro de trabajo, ¿cómo se debe sancionar el robo de material de papelería?
- `p22` — 22 Si en un supermercado sorprenden a alguien robando mercancía, ¿qué debe hacer el gerente?
- `p23` — 23 Si usted sabe que compañeros de la escuela o trabajo compraron un examen, ¿qué hace?
- `p24` — 24 Si estando en el supermercado usted ve que una persona mete un producto a su bolso para no pagarlo, ¿qué hace?

## [31] DEP|attitudes_toward_cultural_openness_and_foreign_influence  (alpha = 0.5163, questionable, N valid = 1,174)

**Domain:** Cultura, Lectura y Deporte | **Survey:** CULTURA_LECTURA_Y_DEPORTE

_Measures respondents' orientations toward cultural diversity and external cultural influence, including perceptions of foreign cultural impact, preferences for cultural homogeneity versus pluralism, and openness to multicultural education._

# TODO there are several questions formats and topics, perhaps too disimilar. Review p29_1 if it is open-ended, and consider options to recode. 

**Variables:**
- `p25` — 25. En su opinión, ¿es preferible hablar de una cultura mexicana o hablar de las culturas mexicanas?
- `p26` — 26. ¿Cree usted que actualmente recibimos menos, igual, o más influencia cultural del extranjero que antes?
- `p27` — 27. ¿Cree usted que recibir influencia cultural del extranjero...?
- `p28` — 28. En su opinión, ¿qué es preferible para el país?
- `p29_1` — 29. En su opinión, ¿qué de lo siguiente sería más importante conservar? 1a mención
- `p31_1` — 31. ¿Qué tan importante considera usted que los maestros de primaria tengan la posibilidad de conocer la cultura de otros países?
- `p32` — 32. En su opinión, ¿la enseñanza de algunas lenguas indígenas debería incluirse en las escuelas primarias del país?

## [32] HAB|structural_housing_quality  (alpha = 0.5109, questionable, N valid = 1,197)

**Domain:** Habitabilidad de Vivienda | **Survey:** LA_CONDICION_DE_HABITABILIDAD_DE_VIVIENDA_EN_MEXICO

_Measures the physical quality of the dwelling's basic construction materials — walls, roof, and floor — as indicators of structural adequacy and habitability. Together these items form a composite index of material precariousness._

**Variables:**
- `p1` — 1 ¿De qué material es la mayor parte de las paredes o muros de esta vivienda?
- `p2` — 2 ¿De qué material es la mayor parte de los techos de esta vivienda?
- `p3` — 3 ¿De qué material es la mayor parte del piso de esta vivienda?

## [33] IND|social_distance_toward_indigenous_people  (alpha = 0.5097, questionable, N valid = 1,102)

**Domain:** Indigenas | **Survey:** INDIGENAS

_Measures the willingness of non-indigenous respondents to engage in close personal, domestic, or professional relationships with indigenous people, reflecting affective prejudice and behavioral exclusion tendencies._

**Variables:**
- `p37_1` — 37. ¿Usted contrataría a una persona indígena para cuidar a sus hijos?
- `p39_1` — 39. Ahora dígame ¿usted tiene o ha tenido algún amigo indígena?
- `p40_1` — 40. ¿Estaría dispuesto o no a permitir que en su casa vivieran personas indígenas?

## [34] CIE|perceived_societal_value_of_science_technology  (alpha = 0.5085, questionable, N valid = 1,110)

**Domain:** Ciencia y Tecnologia | **Survey:** CIENCIA_Y_TECNOLOGIA

_Measures beliefs about the practical contribution and importance of science and technology to solving Mexico's social problems, including perceived usefulness of scientific knowledge, quality of science education, and expectations for future contributions._

# recode to assure consistent values with the construct aggregate

**Variables:**
- `p34` — 34 Para usted, ¿qué tanto ha contribuido la ciencia mexicana a solucionar los problemas del país?
- `p36` — 36 ¿Qué tan importante es para usted el conocimiento científico?
- `p44_1` — 44 ¿Para usted qué tan importante es la tecnología para aprender?
- `p57` — 57 ¿Qué tan eficiente considera usted que es la utilización de la tecnología en México?
- `p58` — 58 ¿Qué tanto apoyo considera usted que se da al desarrollo de la tecnología en el país?
- `p42_1` — 42 Y utilizando esa misma escala, ¿qué tan buena o mala diría usted que es la calidad de la enseñanza de las ciencias en las escuelas?
- `p39_1` — 39 Ahora le voy a pedir por favor que me diga, qué tan de acuerdo o en desacuerdo está usted con los siguientes enunciados: La ciencia ayuda a hacer la vida mejor...
- `p51_1` — 51 Por favor indíqueme qué tan de acuerdo o desacuerdo está con los siguientes enunciados: México debe importar tecnología de otros países...

## [35] FAM|conjugal_union_attitudes  (alpha = 0.5042, questionable, N valid = 1,200)

**Domain:** Familia | **Survey:** FAMILIA

_Measures attitudes and behaviors related to forming, maintaining, and dissolving conjugal unions, including motivations for partnering, tolerance of infidelity, and perceived causes of divorce — reflecting normative orientations toward marriage and partnership stability._

# TODO recode!!

**Variables:**
- `p21` — 21 En su opinión, ¿qué características deben buscarse en una persona para elegirla como pareja conyugal y formar una familia?
- `p22` — 22 ¿En su familia que importancia tienen las opiniones de sus miembros cuando alguien elige una pareja conyugal?
- `p23` — 23 En su caso, ¿cuál fue la razón por la que usted decidió iniciar su (primera) unión conyugal?
- `p32` — 32 Es cada vez más frecuente, que entre las parejas conyugales estables, alguno de sus miembros tenga relaciones extraconyugales...
- `p33` — 33 ¿Usted ha tenido alguna una vez relaciones extraconyugales?
- `p35` — 35 ¿En qué condiciones aceptaría la infidelidad de su pareja conyugal, en caso de enterarse?
- `p38` — 38 Cada vez es más frecuente que las parejas conyugales se separen o se divorcien; en su opinión, ¿a qué se debe esto?

## [36] CUL|authoritarian_predisposition  (alpha = 0.4947, tier3_caveat, N valid = 1,200)

**Domain:** Cultura Politica | **Survey:** CULTURA_POLITICA

_Taps into citizens' preference for strong executive leadership over legal constraints, tolerance for bypassing rules to achieve just ends, and willingness to subordinate individual freedoms to security or order._

# TODO recode!!

**Variables:**
- `p17` — 17 La libertad y la seguridad son valores que a veces pueden chocar, si tuviera que escoger uno, ¿con cuál se quedaría?
- `p61` — 61 En su opinión, es verdadera o falsa la siguiente frase: 'un líder fuerte puede hacer más por el país que todas las leyes'
- `p64` — 64 En su afán por buscar la justicia, cómo deberían actuar las autoridades
- `p65` — 65 Qué tan de acuerdo o en desacuerdo está usted con la siguiente frase: 'En ocasiones, para obrar correctamente hay que saltarse las normas'
- `p60` — 60 ¿Si una decisión fue tomada por la mayoría de las personas:...
- `p23` — 23 Si una buena medida para resolver un problema puede crear conflictos, ¿qué debería hacerse: aplicarla aunque se creen conflictos?

## [37] CUL|institutional_trust_and_electoral_confidence  (alpha = 0.4858, tier3_caveat, N valid = 1,200)

**Domain:** Cultura Politica | **Survey:** CULTURA_POLITICA

_Captures citizens' trust in key political and social institutions (police, neighbors, INE) and their confidence in the integrity of electoral processes, reflecting broader faith in the formal rules of the political game._
# TODO recode!!

**Variables:**
- `p41` — 41 En general, ¿diría que las elecciones en nuestro país son...?
- `p42` — 42 Por lo que usted ha visto, ¿el INE (antes IFE) garantiza o no garantiza la limpieza de los procesos electorales?
- `p43` — 43 Ahora que el INE (antes IFE) se hace cargo de las elecciones de los estados, ¿cree usted que las elecciones serán más o menos limpias?
- `p71` — 71 Por lo que usted ha visto, ¿los partidos políticos compran o no el voto de la gente?
- `p72` — 72 ¿Alguna vez a usted o alguien de su familia le ofrecieron algo a cambio de su voto?

## [38] SOC|internet_engagement_and_digital_literacy  (alpha = 0.4825, tier3_caveat, N valid = 364)

**Domain:** Sociedad de la Informacion | **Survey:** SOCIEDAD_DE_LA_INFORMACION

_Captures both the self-assessed proficiency with which respondents navigate the internet and the range of purposeful online activities they undertake, reflecting functional digital competence beyond mere access._

**Variables:**
- `p33_7` — 33 ¿Para qué utiliza la computadora? Navegar en internet
- `p45_2` — 45 ¿Y alguna vez usted ha usado internet para denunciar algún delito?
- `p39_7` — 39 ¿En qué lugares suele usar internet? En cualquier lugar con datos móviles

## [39] DEP|cultural_socialization_in_childhood  (alpha = 0.4802, tier3_caveat, N valid = 1,188)

**Domain:** Cultura, Lectura y Deporte | **Survey:** CULTURA_LECTURA_Y_DEPORTE

_Measures the degree to which respondents were exposed to cultural practices and resources during childhood through parental behavior, capturing early cultural capital transmission within the family._

**Variables:**
- `p8` — 8. Cuando usted era niño(a), ¿qué tanto le hablaban sus papás de cosas referentes a la cultura?
- `p11` — 11. Después de que usted aprendió a leer, ¿sus padres u otros familiares acostumbraban regalarle libros?
- `p12_1` — 12. Cuando usted era niño(a), ¿con qué frecuencia leía solo?

## [40] EDU|perceived_education_quality  (alpha = 0.4697, tier3_caveat, N valid = 1,199)

**Domain:** Educacion | **Survey:** EDUCACION

_Respondent's overall evaluation of the quality of education in Mexico, including perceived trends over time, a numeric rating, and belief about whether school content is relevant to real life and work._

# TODO recode? but note that items are too dissimilar - this is not useful, review to see if other items might be useful to improve it

**Variables:**
- `p49` — 49 En general, cree usted que en los diez últimos años la calidad de la educación en México...
- `p51` — 51 ¿Cree usted que lo que se enseña en la escuela está relacionado con lo que se debe aprender para la vida?

## [41] FAM|family_value_transmission  (alpha = 0.4569, tier3_caveat, N valid = 1,200)

**Domain:** Familia | **Survey:** FAMILIA

_Captures the values respondents consider most important within the family, what they learned from their family of origin and practice daily, and what fundamental values parents should pass on to children — reflecting the perceived role of the family as a moral socialization institution._
# TODO recode!!

**Variables:**
- `p54` — 54 ¿Cuál es el valor más importante que aprendió en su familia y que practica en su vida cotidiana?
- `p55` — 55 En su opinión, ¿cuáles son los valores fundamentales que deben transmitir los padres a los hijos?
- `p57` — 57 ¿Qué influencia tiene la religión en la vida familiar en México?

## [42] FAM|ideal_family_normativity  (alpha = 0.4506, tier3_caveat, N valid = 972)

**Domain:** Familia | **Survey:** FAMILIA

_Captures respondents' normative beliefs about what constitutes an ideal family structure, what prevents its achievement in Mexico, and what actions could bring it about — reflecting underlying traditionalism versus pluralism in family ideology._


# TODO recode!! items and recode?

**Variables:**
- `p13` — 13 ¿Qué tipo de familia considera usted ideal y de la cual una persona deba aspirar a formar parte?
- `p14` — 14 Como ya mencionó, existe un tipo ideal de familia. En México, ¿qué situaciones evitan que este tipo de familia ideal se logre?
- `p15` — 15 ¿Qué se puede hacer para que el ideal de familia pueda lograrse?
- `p16` — 16 Nos hemos acostumbrado a referirnos a una familia como un grupo de personas en el que se identifica una pareja formada por un hombre y una mujer...
- `p67` — 67 Si compara la familia de una generación anterior a la suya, por ejemplo si es el caso, la de sus padres con su familia actual, ¿cuáles cree que son las diferencias más importantes?
- `p68` — 68 En el futuro, digamos en los próximos 20 años, ¿cuáles considera usted que serán los principales cambios de la familia?

## [43] JUS|legal_self_efficacy_and_access  (alpha = 0.4386, tier3_caveat, N valid = 635)

**Domain:** Justicia | **Survey:** JUSTICIA

_Respondent's perceived capacity to navigate the legal system, including knowledge of rights, willingness to use courts, access to legal representation, and beliefs about the utility of formal legal recourse._
# TODO recode!!

**Variables:**
- `p35` — 35 En su opinión ¿qué tanto sirve el amparo para defender los derechos de las personas?
- `p36` — 36 ¿Usted cree que en México se puede o no demandar al gobierno, si le causa algún daño?
- `p37` — 37 ¿Qué posibilidades cree usted que tendría una persona de ganar una demanda al gobierno?
- `p39` — 39 Por lo que usted ha visto, ¿vale o no vale la pena acudir a un tribunal para poner una demanda?
- `p54` — 54 Si usted tuviera un problema legal, ¿qué preferiría, gastar dinero con un abogado o arreglar las cosas por su cuenta?

## [44] GEN|intimate_partner_power_dynamics  (alpha = 0.4071, tier3_caveat, N valid = 637)

**Domain:** Genero | **Survey:** GENERO

_Measures the balance of power and autonomy within romantic partnerships, capturing control over finances, decision-making, information sharing, and freedom of movement between partners._
# TODO recode and options, review questionnaire to find other items that may be useful - p23 is a much longer list of items. 

**Variables:**
- `p19` — 19. ¿Alguna vez su pareja le ha dejado sin dinero para realizar actividades o no?
- `p23_1` — 23. Regularmente, ¿usted pide permiso a su pareja para salir sola(o) de día?
- `p23_5` — 23. Regularmente, ¿usted pide permiso a su pareja para visitar familiares?

## [45] NIN|youth_educational_opportunity_and_labor_prospects  (alpha = 0.3997, single_item_tier2, N valid = 1,200)

**Domain:** Ninos, Adolescentes y Jovenes | **Survey:** NINOS_ADOLESCENTES_Y_JOVENES

_Measures perceptions of whether today's children and young people have better or worse access to education and quality employment compared to previous generations, capturing intergenerational mobility beliefs._

# TODO recode!!


**Variables:**
- `p28_1` — 28 ¿Usted cree que los niños mexicanos tienen más o menos oportunidades de la que tuvieron los que son adultos actualmente?
- `p81_2` — 81 ¿Usted cree que los jóvenes mexicanos tienen más o menos oportunidades de la que tuvieron los que son adultos actualmente para estudiar?
- `p83_1` — 83 ¿Usted cree que los jóvenes de hoy con respecto a los de hace 30 años, tienen trabajos de mejor o peor calidad?

## [46] REL|religious_tolerance  (alpha = 0.3931, single_item_tier2, N valid = 1,077)

**Domain:** Religion, Secularizacion y Laicidad | **Survey:** RELIGION_SECULARIZACION_Y_LAICIDAD

_Measures the degree to which individuals accept religious diversity in their social environment, including willingness to cohabit with people of other religions, family tolerance toward non-Catholics, justification for expelling religious minorities from communities, and opinions on how authorities should handle religious conflicts._
# TODO recode!!

**Variables:**
- `p44_1` — 44. En su opinión, ¿qué tan tolerante o intolerante es su familia con los no católicos?
- `p47` — 47. Para usted, ¿Qué tanto se JUSTIFICA expulsar de una comunidad a alguien que no es de la religión que tiene la mayoría?
- `p48` — 48. Si en una comunidad la mayoría de la gente es católica y decide que los protestantes no deben vivir allí, ¿qué debe hacer el gobierno?

## [47] NIN|children_rights_recognition_and_respect  (alpha = 0.3759, single_item_tier2, N valid = 1,200)

**Domain:** Ninos, Adolescentes y Jovenes | **Survey:** NINOS_ADOLESCENTES_Y_JOVENES

_Measures the degree to which respondents believe children's rights are known, respected, and upheld in Mexico, including awareness of specific rights and perceptions of how well institutions honor them._
# TODO recode!!

**Variables:**
- `p17_1` — 17 ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes afirmaciones? En la colonia, localidad o municipio donde vivo se respetan los derechos de los niños
- `p19` — 19 Por lo que usted cree, los niños deben tener...
- `p20` — 20 En su opinión los niños deben ser considerados como
- `p21_2` — 21 ¿Usted cree que los niños tienen derecho a ir a la escuela?
- `p22` — 22 ¿Qué tanto cree usted que en México se respetan los derechos de los niños?
- `p73_3` — 73 ¿Usted cree que los jóvenes tienen derecho a participar en un juicio?

## [48] DEP|reading_engagement_and_literacy  (alpha = 0.3654, single_item_tier2, N valid = 483)

**Domain:** Cultura, Lectura y Deporte | **Survey:** CULTURA_LECTURA_Y_DEPORTE

_Measures respondents' current relationship with reading, including access to books, perceived reading ability, self-reported reading habits across publication types, and perceived barriers to reading._

# TODO why is n so low? consider this construct for removal

**Variables:**
- `p15a_1` — 15. ¿Acostumbra leer algunas de las siguientes publicaciones? Periódicos o revistas locales (del barrio)
- `p15c_2` — 15. Versión: Periódicos o revistas regionales (del estado)
- `p15c_3` — 15. Versión: Periódicos o revistas nacionales (del país)

## [49] JUS|police_trust_and_legitimacy  (alpha = 0.3536, single_item_tier2, N valid = 1,200)

**Domain:** Justicia | **Survey:** JUSTICIA

_Respondent's trust in and respect for police, and perception of whether police act fairly and professionally. Combines affective trust ratings with evaluative judgments about police conduct._

# TODO recode!! and check other items


**Variables:**
- `p24_1` — 24 Dígame, ¿qué tanto respeto le tiene usted a la policía federal?
- `p25a_1` — 25 Con su conocimiento de la situación del país, ¿considera que la policía resuelve los problemas de manera justa?
- `p59` — 59 Cuando la policía investiga los delitos es probable que cometa abusos. ¿De qué manera piensa usted que se pueden evitar estos abusos?
- `p40_2_1` — 40.2 Si tiene un problema y recurre a la Policía usted esperaría que sean respetuosos en el trato

## [50] GEN|sexual_and_reproductive_attitudes  (alpha = 0.3530, single_item_tier2, N valid = 1,200)

**Domain:** Genero | **Survey:** GENERO

_Measures attitudes toward sexual behavior, contraception, abortion, and reproductive decision-making, reflecting normative beliefs about sexuality and reproductive rights in Mexico._
# TODO recode!! 

**Variables:**
- `p45` — 45. ¿Cree usted que está bien o mal que las personas tengan relaciones sexuales antes de casarse?
- `p46_1` — 46. Ahora le voy a mencionar algunos métodos anticonceptivos, por favor dígame si lo conoce o no lo conoce; y si lo conoce, si lo usaría...
- `p47` — 47. ¿Qué opina sobre una mujer joven, menor de 18 años, que trabaja como prostituta o trabajadora sexual?
- `p50` — 50. Ante un embarazo adolescente no planeado, ¿cuál cree que es la opción más adecuada?
- `p51` — 51. ¿Quién debe decidir si continúa o no el embarazo?

## [51] GEN|tolerance_of_gender_based_violence  (alpha = 0.3359, single_item_tier2, N valid = 1,200)

**Domain:** Genero | **Survey:** GENERO

_Measures the degree to which respondents accept, justify, or normalize physical and verbal violence against women in domestic and family contexts._
# TODO recode!! remove p65, to dissimilar

**Variables:**
- `p31` — 31. Si un matrimonio de amigos suyos discute y el hombre comienza a gritar a su mujer, usted que siente...
- `p32` — 32. ¿Consideras que dentro de las familias mexicanas hay o no hay violencia?
- `p33` — 33. ¿En su familia ha habido violencia?
- `p65` — 65. ¿Usted ha escuchado a hablar de la Ley para prevenir la violencia contra las mujeres?

## [52] GLO|transnational_exposure  (alpha = 0.3336, single_item_tier2, N valid = 1,200)

**Domain:** Globalizacion | **Survey:** GLOBALIZACION

_Measures the extent of respondents' direct personal experience with the world beyond Mexico, including international travel, residence abroad, language skills, and close ties to people living in other countries._
# TODO recode!! p8_2, who is ellos? review questionnair for other options

**Variables:**
- `p2` — 2 ¿Podría indicarme cuántos idiomas habla además del español?
- `p3` — 3 ¿Ha vivido usted en otro país?
- `p8_2` — 8.2 ¿Y qué tanto se comunica con ellos?
- `p7` — 7 ¿Tiene relación con extranjeros que vivan en el país?

## [53] COR|reporting_behavior_and_barriers  (alpha = 0.0518, formative_index, N valid = 1,200)

**Domain:** Corrupcion y Cultura de la Legalidad | **Survey:** CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD

_Measures actual behavior and motivations related to reporting corruption and authority abuse, including whether incidents were reported, reasons for non-reporting, and outcomes when reports were made._

# TODO recode!! and review, drop p29, p32-- if it doesn't improve, drop this construct. 


**Variables:**
- `p27` — 27 ¿Durante el último año usted se vio afectado por un acto de corrupción?  [GATEWAY]
- `p28` — 28 ¿Denunció el acto de corrupción?
- `p29` — 29 ¿Podría decirme dónde?
- `p30` — 30 ¿Podría decirme por qué no lo denunció?
- `p31` — 31 Por lo general, ¿cuál es su reacción ante los actos de abuso de autoridad que se le presentan en su vida?  [GATEWAY]
- `p32` — 32 Podría indicarme, ¿por qué siempre se queda callado?
- `p33` — 33 Cuando ha denunciado abusos de autoridad, ¿qué sucede?

## [54] HAB|housing_tenure_security  (alpha = -0.1360, formative_index, N valid = 1,200)

**Domain:** Habitabilidad de Vivienda | **Survey:** LA_CONDICION_DE_HABITABILIDAD_DE_VIVIENDA_EN_MEXICO

_Measures the legal and practical security of the household's occupancy arrangement, including ownership status, who holds title, how the dwelling was acquired, and whether it was obtained through a formal financing institution._

# TODO recode and remove p15 and 16, drop construt if it doesnt improve. 


**Variables:**
- `p13` — 13 ¿Esta vivienda es propiedad de alguna persona que vive aquí?  [GATEWAY]
- `p14` — 14 ¿A quién pertenece esta vivienda?  [GATEWAY]
- `p15` — 15 La vivienda en la cual usted habita, es:  [GATEWAY]
- `p15_1` — 15.1 ¿Quién se la presta o para quién la cuida?
- `p16` — 16 ¿Su vivienda la compró construida o la construyó?  [GATEWAY]
- `p17` — 17 ¿Quién la compró?
- `p18` — 18 En caso de haber adquirido su vivienda a través de una institución, ¿en cuál fue?

## [55] ECO|job_search_and_employment_precarity  (alpha = N/A, formative_index, N valid = 709)

**Domain:** Economia y Empleo | **Survey:** ECONOMIA_Y_EMPLEO

_Measures the experience of unemployment and job insecurity, including active job-seeking behavior, perceived probability of finding or losing work, duration of unemployment, and willingness to accept unfavorable job conditions. Reflects labor market vulnerability and precariousness._

# drop construct

**Variables:**
- `p48` — 48 Para usted, ¿qué tan probable es que en los próximos doce meses pierda su trabajo actual?
- `p49` — 49 En este momento, ¿le gustaría cambiar de trabajo?
- `p50` — 50 Y en este momento, ¿usted está buscando otro empleo?
- `p56` — 56 ¿Ha buscado usted empleo en los últimos tres meses?  [GATEWAY]
- `p57` — 57. ¿Cuánto tiempo (en meses) calcula usted que llevará buscando empleo?
- `p58` — 58. Y en su opinión, ¿cree muy probable, algo probable, poco probable o nada probable que en los próximos doce meses encuentre empleo?
- `p59_1` — 59. ¿Aceptaría un trabajo si implicara un cambio de residencia?
- `p59_3` — 59. ¿Aceptaría un trabajo si implicara ingresos inferiores a los que considera adecuados a su formación?
- `p59_4` — 59. ¿Aceptaría un trabajo si implicara una categoría inferior a la que usted considera que tiene?

## [56] EDU|school_environment_quality  (alpha = N/A, formative_index, N valid = 997)

**Domain:** Educacion | **Survey:** EDUCACION

_Respondent's assessment of the physical and social conditions of their current school, including facility condition, safety perception, adequacy of laboratories, and teacher engagement with students._

# drop construct

**Variables:**
- `p12` — 12 ¿En qué estado se encuentran las instalaciones de su escuela?
- `p13` — 13 ¿Considera usted que su escuela es segura o insegura?
- `p14_4` — 14 ¿Considera adecuados o inadecuados los siguientes espacios y personas que tienen que ver con su formación en la escuela?
- `p30_1` — 30 Señale usted con qué frecuencia sus profesores captaban la atención del grupo y generan interés en la clase  [GATEWAY]
- `p18` — 18 En el último año, ¿cuál ha sido la atención que dan los profesores de su escuela a problemas que se presentan entre los estudiantes?
- `p16_6` — 16 En una escala del 0 al 10, ¿Cómo calificaría a su escuela en cuanto a impulsar programas de salud?

---

**Generation details:** Data sources used — `construct_dr_sweep.json` (4,979 pairs, 360 significant), `construct_variable_manifest.json` (102 constructs), `semantic_variable_selection_v4.json` (v4 SVS with construct clusters), `encuestas/los_mex_dict.json` (variable question text via `column_names_to_labels` per survey). Survey variable codes are matched to their respective domain survey. All 56 constructs had 100% variable text retrieval from the survey dictionary.

---

**Process summary:** All 56 constructs were confirmed with exact `ci_low > 0 OR ci_high < 0` filtering from `construct_dr_sweep.json`. Variable question texts were retrieved from `encuestas/los_mex_dict.json` (located at `/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict.json`) using `column_names_to_labels` per survey, matched via a domain-code-to-survey-name mapping. Every variable code for all 56 constructs resolved to question text — no `[text not found]` entries. Question texts are truncated at 120 characters where needed. The single_item_tier2 constructs show their full variable cluster (not just the selected single item), as the full cluster is what is stored in SVS v4.