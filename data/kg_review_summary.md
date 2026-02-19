# KG Ontology Review Checklist
Generated: 2026-02-18 17:40  
Edit `data/kg_ontology.json` directly to make corrections, then reload the KG.

## PRIORITY 1 — Cross-Domain Relationships  
**Review ALL 7 items.** Mark each as ✅ keep | ❌ delete | ✏️ edit.

| From | Type | To | Evidence | Strength |
|------|------|----|----------|----------|
| `CIE__interest_in_science_and_technology` | predicts | `SOC__media_consumption` | Research indicates that higher interest in science correlates with increased consumption of science-related media (e.g., media about science). | strong |
| `CON__political_partisanship` | correlates_with | `CUL__political_interest` | Partisan orientations influence political engagement and interest, as shown in studies on political psychology. | strong |
| `COR__perceptions_of_corruption` | negatively_affects | `ECO__trust_in_government` | Perceived corruption diminishes trust in government institutions (e.g., transparency and accountability literature). | strong |
| `DEP__cultural_knowledge` | enables | `IDE__cultural_identity` | Cultural exposure and knowledge reinforce cultural identity and patriotism. | moderate |
| `FAM__family_support` | predicts | `EDU__educational_motivation` | Family support is linked to higher motivation and positive attitudes towards education. | moderate |
| `REL__religious_beliefs` | correlates_with | `DER__perceptions_of_human_rights` | Religious beliefs often influence perceptions of human rights and social justice issues. | moderate |
| `GLO__linguistic_diversity` | enables | `IND__cultural_practices_and_language` | Linguistic diversity supports the preservation of cultural practices and language among indigenous groups. | moderate |

## PRIORITY 2 — Construct Definitions by Topic  
Skim each block (~3 min per topic). Check: do the construct labels make sense given the sample questions?

### CIE — ciencia y tecnologia

**`CIE__science_concept_associations`** — Associations with Science and Technology (4 questions)
  - `p1_1|CIE`: ¿Podría decirme, por favor, tres palabras que asocie con la palabra CIENCIA? 1° MENCIÓN
  - `p1_1a_1|CIE`: ¿Podría decirme, por favor, tres palabras que asocie con la palabra CIENCIA? 1° MENCIÓN
  - `p2_1|CIE`: Ahora le voy a pedir que me diga, por favor, tres palabras que asocie con la palabra TECNOLOGÍA.  1° MENCIÓN
  - _(+1 more)_

**`CIE__home_literature`** — Home Library Content (20 questions)
  - `p3_1|CIE`: ¿En su casa hay libros de superación personal?
  - `p3_2|CIE`: ¿En su casa hay libros científicos?
  - `p3_3|CIE`: ¿En su casa hay libros técnicos?
  - _(+17 more)_

**`CIE__internet_access_and_use`** — Internet Access and Usage (9 questions)
  - `p4|CIE`: ¿Tiene usted una computadora en su casa?
  - `p5|CIE`: ¿Tiene usted acceso a internet?
  - `p6|CIE`: ¿Con qué frecuencia utiliza internet?
  - _(+6 more)_

**`CIE__media_consumption_science`** — Media Consumption about Science (10 questions)
  - `p9_1|CIE`: ¿Por cuál medio de comunicación lee, observa o escucha noticias de ciencia? 1° MENCIÓN
  - `p10t1|CIE`: Otro1
  - `p10t2|CIE`: Otro2
  - _(+7 more)_

**`CIE__interest_in_science_and_technology`** — Interest in Science and Technology (12 questions)
  - `p11|CIE`: ¿Qué tanto se interesa en la ciencia o en asuntos que tienen que ver con la ciencia?
  - `p12|CIE`: ¿Qué tan seguido acostumbra leer, ver, o escuchar noticias o programas sobre ciencia o asuntos científicos?
  - `p14_1|CIE`: Además de la ESCUELA, ¿En qué lugares escucha más hablar sobre ciencia?  1° MENCIÓN
  - _(+9 more)_

**`CIE__trust_and_opinion_scientists`** — Trust and Opinions about Scientists (25 questions)
  - `p18|CIE`: ¿Qué tan útil es (ha sido) para usted el conocimiento científico que adquirió (adquiere) en la escuela?
  - `p19|CIE`: ¿Ha adquirido alguna información científica fuera de la escuela?
  - `p20_1|CIE`: Y me puede decir principalmente, ¿dónde adquirió esa información? 1° MENCIÓN
  - _(+22 more)_

### CON — cultura constitucional

**`CON__political_partisanship`** — Political Partisanship (1 questions)
  - `partido_pol|CON`: Partido Político

### COR — corrupcion y cultura de la legalidad

**`COR__perceptions_of_corruption`** — Perceptions of corruption (12 questions)
  - `p2|COR`: En comparación con su infancia, actualmente la corrupción es:
  - `p3|COR`: Dentro de 5 años, cree usted que la corrupción será:
  - `p5|COR`: En su opinión, ¿dónde se realizan los primeros actos de corrupción?
  - _(+9 more)_

**`COR__trust_in_persons`** — Trust in persons (17 questions)
  - `p6_1|COR`: En una escala donde 0 es 'nada honesto' y 10 es 'muy honesto', ¿cómo calificaría a los siguientes personajes? Sacerdote
  - `p6_2|COR`: En una escala donde 0 es 'nada honesto' y 10 es 'muy honesto', ¿cómo calificaría a los siguientes personajes? Funcionari
  - `p6_3|COR`: En una escala donde 0 es 'nada honesto' y 10 es 'muy honesto', ¿cómo calificaría a los siguientes personajes? Maestro
  - _(+14 more)_

**`COR__behavior_and_attitudes`** — Behavior and attitudes towards corruption (26 questions)
  - `p4_1|COR`: En el último año a usted, ¿le han solicitado dinero extra para realizar algunos de los siguientes  trámites? para recone
  - `p4_2|COR`: En el último año a usted, ¿le han solicitado dinero extra para realizar algunos de los siguientes  trámites? para renova
  - `p4_3|COR`: En el último año a usted, ¿le han solicitado dinero extra para realizar algunos de los siguientes  trámites? para incapa
  - _(+23 more)_

**`COR__sources_and_reporting`** — Sources and reporting of corruption (8 questions)
  - `p11|COR`: Si usted ve que a una persona se le cae su cartera, ¿qué hace?
  - `p12|COR`: Cuando se trata de agilizar un trámite ¿qué es más común, qué usted ofrezca dinero o le pidan dinero?
  - `p23|COR`: Si usted sabe que compañeros de la escuela o trabajo compraron un examen, ¿qué hace?
  - _(+5 more)_

**`COR__perceptions_of_institutions`** — Perceptions of institutions' role in combating corruption (17 questions)
  - `p16|COR`: Según su percepción, ¿dónde hay más corrupción?
  - `p17|COR`: Dentro del gobierno, ¿dónde considera usted que hay mayor corrupción?
  - `p18|COR`: Según su percepción, ¿dónde son más estrictos con la sanción en faltas como:  la mentira, el engaño o el robo?
  - _(+14 more)_

### CUL — cultura politica

**`CUL__economic_perception`** — Perception of the economic situation (3 questions)
  - `p1|CUL`: Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación económica actu
  - `p2|CUL`: ¿Y cree usted que en el próximo año…?
  - `p4|CUL`: ¿Y cree usted que en el próximo año…?

**`CUL__political_satisfaction`** — Satisfaction with the political system (0 questions)

**`CUL__national_pride`** — National pride and identity (1 questions)
  - `p5|CUL`: ¿Qué tan orgulloso se siente de ser mexicano?

**`CUL__public_sentiment`** — Public sentiment and emotional climate (4 questions)
  - `p3|CUL`: De las siguientes palabras, ¿con cuál está usted más de acuerdo para describir la situación política del país?
  - `p6_1|CUL`: ¿Cuál cree que es el sentimiento que más predomina entre la gente en estos días? 1° MENCIÓN
  - `p6_1a_1|CUL`: ¿Cuál cree que es el sentimiento que más predomina entre la gente en estos días? 1° MENCIÓN
  - _(+1 more)_

**`CUL__political_interest`** — Interest and engagement in politics (5 questions)
  - `p8|CUL`: ¿Con qué frecuencia acostumbra leer, ver o escuchar noticias o programas sobre política o asuntos públicos?
  - `p9_1|CUL`: ¿Cómo se informa principalmente de lo que sucede en el país? 1° MENCIÓN
  - `p10|CUL`: ¿Qué tanto se interesa usted en la política?
  - _(+2 more)_

**`CUL__democratic_attitudes`** — Attitudes towards democracy and democratic processes (4 questions)
  - `p21|CUL`: En su opinión, ¿la política contribuye o no contribuye a mejorar el nivel de vida de todos los mexicanos?
  - `p23|CUL`: Si una buena medida para resolver un problema puede crear conflictos, ¿qué debería hacerse: aplicarla aunque se creen co
  - `p24|CUL`: ¿Qué tan de acuerdo o en desacuerdo está usted con la siguiente frase: 'mientras en mi casa las cosas estén bien, no me 
  - _(+1 more)_

**`CUL__political_institutions`** — Political Institutions (8 questions)
  - `p13_1|CUL`: ¿Quién o quiénes realizan las siguientes funciones? Juzgar a los delincuentes
  - `p13_2|CUL`: ¿Quién o quiénes realizan las siguientes funciones? Organizar las elecciones
  - `p13_3|CUL`: ¿Quién o quiénes realizan las siguientes funciones? Aprobar los gastos del gobierno
  - _(+5 more)_

**`CUL__political_orientation`** — Political Orientation (8 questions)
  - `p14_1|CUL`: En política generalmente se habla de 'izquierda' y 'derecha'. En una escala de 1 a 5 siendo que uno es la posición más a
  - `p14_2|CUL`: En política generalmente se habla de 'izquierda' y 'derecha'. En una escala de 1 a 5 siendo que uno es la posición más a
  - `p14_3|CUL`: En política generalmente se habla de 'izquierda' y 'derecha'. En una escala de 1 a 5 siendo que uno es la posición más a
  - _(+5 more)_

**`CUL__party_perception`** — Party Perception (10 questions)
  - `p15_1|CUL`: Y los partidos que le voy a mencionar a  continuación ¿en qué posición de esta misma escala considera que están en estos
  - `p15_2|CUL`: Y los partidos que le voy a mencionar a  continuación ¿en qué posición de esta misma escala considera que están en estos
  - `p15_3|CUL`: Y los partidos que le voy a mencionar a  continuación ¿en qué posición de esta misma escala considera que están en estos
  - _(+7 more)_

**`CUL__self_position`** — Self Position (1 questions)
  - `p16|CUL`: Y utilizando esa misma escala ¿usted en lo personal en qué posición se colocaría?

**`CUL__values_conflict`** — Values Conflict (12 questions)
  - `p17|CUL`: La libertad y la seguridad son valores que a veces pueden chocar, si tuviera que escoger uno, ¿con cuál se quedaría?
  - `p19_1|CUL`: Ahora le voy a leer algunos pares de frases. Dígame por favor para usted cuál de las dos frases es preferible A
  - `p19_2|CUL`: Ahora le voy a leer algunos pares de frases. Dígame por favor para usted cuál de las dos frases es preferible B
  - _(+9 more)_

**`CUL__security_anxiety`** — Security Anxiety (1 questions)
  - `p18|CUL`: Con respecto a la seguridad pública que se vive en su estado, ¿qué situación le provoca a usted más ansiedad o temor?: d

**`CUL__political_complexity`** — Political Complexity (1 questions)
  - `p20|CUL`: En general ¿qué tan complicada es para usted la política?

**`CUL__trust_in_institutions`** — Trust In Institutions (4 questions)
  - `p22|CUL`: Qué tan de acuerdo o en desacuerdo está usted con la siguiente frase: 'Un funcionario público puede sacar provecho de su
  - `p26|CUL`: ¿Cree usted que los asuntos que se discuten en la Cámara de Diputados son importantes para los ciudadanos o sólo son de 
  - `p42|CUL`: Por lo que usted ha visto, ¿el INE (antes IFE) garantiza o no garantiza la limpieza de los procesos electorales?
  - _(+1 more)_

**`CUL__participation_attitudes`** — Participation Attitudes (2 questions)
  - `p25|CUL`: En su opinión, ¿vale o no vale la pena participar en política?
  - `p27|CUL`: ¿Qué tan de acuerdo o en desacuerdo estaría usted con que una parte de la Cámara de Diputados se eligiera mediante un so

**`CUL__self_representation`** — Self Representation (1 questions)
  - `p28|CUL`: ¿Cuál de estas personas cree usted que representa más sus intereses?

**`CUL__democratic_knowledge`** — Democratic Knowledge (2 questions)
  - `p29|CUL`: ¿Para qué sirve la democracia?
  - `p29a|CUL`: ¿Para qué sirve la democracia?

**`CUL__democratic_importance`** — Democratic Importance (2 questions)
  - `p30|CUL`: Para que una sociedad sea considerada como una democracia, ¿cuál de los siguientes aspectos considera usted qué es el má
  - `p33|CUL`: En una escala donde 0 es 'nada importante' y 10 es 'absolutamente importante', ¿Qué tan importante es para usted que Méx

**`CUL__governance_preference`** — Governance Preference (1 questions)
  - `p31|CUL`: ¿Para gobernar al país que es preferible?

**`CUL__democratic_quality`** — Democratic Quality (1 questions)
  - `p34|CUL`: Y, usando una escala de 0 a 10 donde 0 es 'nada democrático' y 10 es  completamente democrático', ¿cómo calificaría la f

**`CUL__democratic_satisfaction`** — Democratic Satisfaction (1 questions)
  - `p35|CUL`: ¿Qué tan satisfecho está usted con la democracia que tenemos hoy en México?

**`CUL__democratic_improvement`** — Democratic Improvement (3 questions)
  - `p37_1|CUL`: ¿Qué medidas le parece que podrían tomarse para mejorar el funcionamiento de la democracia en México?  ¿Algo más? 1 menc
  - `p37_4|CUL`: ¿Qué medidas le parece que podrían tomarse para mejorar el funcionamiento de la democracia en México?  ¿Algo más? 4 menc
  - `p37_5|CUL`: ¿Qué medidas le parece que podrían tomarse para mejorar el funcionamiento de la democracia en México?  ¿Algo más? 5 menc

**`CUL__democratic_legacy`** — Democratic Legacy (1 questions)
  - `p38|CUL`: ¿Usted cree que el gobierno se debe apoyar en las ideas de la Revolución Mexicana o debe cambiar de ideas?

**`CUL__constitutional_change`** — Constitutional Change (1 questions)
  - `p39|CUL`: En su opinión, ¿qué sería preferible: hacer una constitución nueva, cambiarla sólo en parte o dejarla como está?

**`CUL__constitutional_trust`** — Constitutional Trust (1 questions)
  - `p40|CUL`: ¿Qué tanto cree que se cumple la constitución en México?

**`CUL__electoral_process`** — Electoral Process (1 questions)
  - `p41|CUL`: En general, ¿diría que las elecciones en nuestro país son…?

**`CUL__regulatory_environment`** — Regulatory Environment (1 questions)
  - `p44_1|CUL`: Por lo que usted ha visto, ¿en qué medida se puede poner el negocio que se quiera?

### DEP — cultura lectura y deporte

**`DEP__cultural_attitudes`** — Cultural Attitudes and Perceptions (10 questions)
  - `p1_1|DEP`: Por favor, dígame tres palabras o frases en las que piensa cuando oye la palabra CULTURA. 1° MENCIÓN
  - `p1_1a_1|DEP`: Por favor, dígame tres palabras o frases en las que piensa cuando oye la palabra CULTURA. 1° MENCIÓN
  - `p2|DEP`: En general, ¿qué tanto interés tiene por la cultura?
  - _(+7 more)_

**`DEP__media_consumption`** — Media Consumption and Preferences (39 questions)
  - `p3_1|DEP`: En una escala del 0 al 10, donde 0 es 'nada importante' y 10 es 'muy importante', ¿qué tan importante es para su vida ve
  - `p3_2|DEP`: En una escala del 0 al 10, donde 0 es 'nada importante' y 10 es 'muy importante', ¿qué tan importante es para su vida oí
  - `p3_3|DEP`: En una escala del 0 al 10, donde 0 es 'nada importante' y 10 es 'muy importante', ¿qué tan importante es para su vida te
  - _(+36 more)_

**`DEP__literacy_and_access`** — Literacy and Access to Cultural and Sports Resources (3 questions)
  - `p16|DEP`: ¿Qué tan fácil o difícil es para usted leer?
  - `p17|DEP`: ¿Cuál es su principal dificultad/limitación para leer?
  - `p18_1|DEP`: En su opinión, ¿para qué sirve la lectura?  1° MENCIÓN

**`DEP__sport_participation`** — Sports Participation and Engagement (10 questions)
  - `p19|DEP`: ¿Actualmente practica usted algún deporte?
  - `p19_1a_1|DEP`: Sí ¿Cuál(es)?
  - `p19_2a_1|DEP`: A veces ¿Cuál(es)?
  - _(+7 more)_

**`DEP__cultural_knowledge`** — Cultural Knowledge and Childhood Cultural Exposure (14 questions)
  - `p8|DEP`: Cuando usted era niño(a), ¿qué tanto le hablaban sus papás de cosas referentes a la cultura?
  - `p9_1|DEP`: Cuando usted era niño(a), ¿sus padres lo llevaban a visitar museos ?
  - `p9_2|DEP`: Cuando usted era niño(a), ¿sus padres lo llevaban a algún evento de tipo cultural?
  - _(+11 more)_

**`DEP__influence_of_foreign_culture`** — Influence of Foreign Culture (3 questions)
  - `p26|DEP`: ¿Cree usted que actualmente recibimos menos, igual, o más influencia cultural del extranjero que antes?
  - `p27|DEP`: ¿Cree usted que recibir influencia cultural del extranjero…?
  - `p28|DEP`: En su opinión, ¿qué es preferible para el país?

**`DEP__leisure_activities`** — Leisure Activities (1 questions)
  - `p4_1|DEP`: En su tiempo libre, dígame tres actividades que prefiere hacer. 1° MENCIÓN

### DER — derechos humanos discriminacion y grupos vulnerables

**`DER__perceptions_of_human_rights`** — Perceptions of Human Rights (5 questions)
  - `p2|DER`: ¿Qué tan de acuerdo o en desacuerdo está usted con el siguiente enunciado? Es importante que los derechos humanos de los
  - `p3|DER`: En su opinión ¿se respetan los derechos humanos en el país?
  - `p31|DER`: ¿Usted considera que habita una vivienda digna?
  - _(+2 more)_

**`DER__trust_in_justice_system`** — Trust in Justice System (11 questions)
  - `p4|DER`: De las siguientes autoridades, ¿cuál cree usted que viola con más frecuencia los derechos humanos?
  - `p4a|DER`: De las siguientes autoridades, ¿cuál cree usted que viola con más frecuencia los derechos humanos?
  - `p5|DER`: ¿Usted qué tanto se siente protegido contra los abusos de autoridad?
  - _(+8 more)_

**`DER__discrimination_experiences`** — Experiences and Attitudes Toward Discrimination (34 questions)
  - `p11_1|DER`: Si una persona es víctima de un delito, ¿considera que esa persona tiene derecho a la reparación del daño?
  - `p11_2|DER`: Si una persona es víctima de un delito, ¿considera que esa persona tiene derecho a participar con el Ministerio Público 
  - `p11_3|DER`: Si una persona es víctima de un delito, ¿considera que esa persona tiene derecho a hacer justicia por su propia mano?
  - _(+31 more)_

**`DER__attitudes_toward_rights_protections`** — Attitudes Toward Rights Protections and Limits (28 questions)
  - `p6|DER`: En su opinión, ¿qué tanto sirve el 'amparo' para defender los derechos de las personas?
  - `p7|DER`: ¿Con qué frase está usted más de acuerdo?
  - `p8|DER`: ¿Cree usted que los ciudadanos…?
  - _(+25 more)_

**`DER__vulnerable_groups`** — Perceptions and Attitudes Toward Vulnerable Groups (0 questions)

### ECO — economia y empleo

**`ECO__economic_satisfaction`** — Economic Satisfaction (7 questions)
  - `p1|ECO`: ¿Qué tan satisfecho está con la situación económica actual que vive el país?
  - `p2|ECO`: ¿Qué tan satisfecho está usted con su situación económica actual?
  - `p16_1|ECO`: El salario mínimo diario en México es de alrededor de 65 pesos al día, dígame por favor ¿alcanza a cubrir o no alcanza a
  - _(+4 more)_

**`ECO__perceived_economic_comparison`** — Perceived Economic Comparison with Parents and Future Generations (8 questions)
  - `p3|ECO`: Desde su punto de vista de la  situación económica actual ¿usted vive _________ que sus padres cuando tenían su edad?
  - `p4|ECO`: Dada la situación económica actual, ¿usted cree que sus hijos podrán vivir__________ que usted?
  - `p7_1|ECO`: Más de 10 millones de mexicanos nacidos en territorio nacional viven ahora en Estados Unidos, usted cree que se fueron..
  - _(+5 more)_

**`ECO__causes_of_economic_problems`** — Perceived Causes of Economic Problems (10 questions)
  - `p6_1|ECO`: Podría decirme por favor, ¿qué tanto cree que afecta al avance de la economía del país la inseguridad?
  - `p6_2|ECO`: Podría decirme por favor, ¿qué tanto cree que afecta al avance de la economía del país la corrupción?
  - `p6_3|ECO`: Podría decirme por favor, ¿qué tanto cree que afecta al avance de la economía del país la falta de capacitación de los t
  - _(+7 more)_

**`ECO__trust_in_government`** — Trust in Government and Institutions (20 questions)
  - `p5|ECO`: En su opinión, ¿quién es más responsable de la situación económica del país?
  - `p9_1|ECO`: ¿Qué debería hacer el gobierno por la economía del país? Enumere de uno a cinco en orden de importancia. Que no aumenten
  - `p9_2|ECO`: ¿Qué debería hacer el gobierno por la economía del país? Enumere de uno a cinco en orden de importancia. Que no haya end
  - _(+17 more)_

**`ECO__employment_conditions`** — Employment Conditions and Labor Market (18 questions)
  - `p25|ECO`: ¿En cuál de las siguientes situaciones se encuentra usted actualmente?
  - `p26|ECO`: ¿Cuánto tiempo (en años) lleva en este trabajo?
  - `p27|ECO`: ¿Podría decirme cuántos meses?
  - _(+15 more)_

**`ECO__worker_satisfaction`** — Worker Satisfaction and Conditions (17 questions)
  - `p18_1|ECO`: A la hora de valorar un empleo, ¿Qué tan importante es para usted cada uno de los siguientes aspectos? Que sea estable y
  - `p18_2|ECO`: A la hora de valorar un empleo, ¿Qué tan importante es para usted cada uno de los siguientes aspectos? Que proporcione i
  - `p18_3|ECO`: A la hora de valorar un empleo, ¿Qué tan importante es para usted cada uno de los siguientes aspectos? Que tenga prestig
  - _(+14 more)_

### EDU — educacion

**`EDU__educational_attainment`** — Educational Attainment (4 questions)
  - `p1_1|EDU`: ¿Cuál es su máximo nivel de escolaridad?
  - `p1_2|EDU`: ¿Cuál es el máximo nivel de escolaridad de su padre?
  - `p1_3|EDU`: ¿Cuál es el máximo nivel de escolaridad de su madre?
  - _(+1 more)_

**`EDU__school_quality_perception`** — Perception of School Quality (27 questions)
  - `p8|EDU`: La escuela en la que usted estudia es:
  - `p9_1|EDU`: ¿Qué causas influyeron para que usted estudiara en la escuela en la que actualmente está inscrita(o)?  1° MENCIÓN
  - `p9_1a|EDU`: ¿Qué causas influyeron para que usted estudiara en la escuela en la que actualmente está inscrita(o)?  1° MENCIÓN
  - _(+24 more)_

**`EDU__teacher_quality`** — Teacher Quality and Behavior (14 questions)
  - `p15_1|EDU`: Señale usted con qué frecuencia sus profesores captan la atención del grupo y generan interés en la clase
  - `p15_2|EDU`: Señale usted con qué frecuencia sus profesores propician que usted aprenda por sí mismo
  - `p15_3|EDU`: Señale usted con qué frecuencia sus profesores son respetuosos
  - _(+11 more)_

**`EDU__peer_behavior`** — Peer Behavior and Social Environment (18 questions)
  - `p17_1|EDU`: ¿En el último año ha visto que sus compañeros respetan y aceptan las diferentes formas de ser de los demás?
  - `p17_2|EDU`: ¿En el último año ha visto que sus compañeros esconden, rompen o roban cosas de otras personas?
  - `p17_3|EDU`: ¿En el último año ha visto que sus compañeros respetan la escuela porque es un espacio de todos?
  - _(+15 more)_

**`EDU__educational_motivation`** — Motivations and Reasons for Studying (17 questions)
  - `p2|EDU`: ¿Usted estudia actualmente?
  - `p3|EDU`: ¿Cuenta con una beca u otro apoyo económico para realizar sus estudios?
  - `p4|EDU`: ¿Quién le otorga este apoyo?
  - _(+14 more)_

### ENV — envejecimiento

**`ENV__age_perceptions`** — Perceptions of Age and Aging (8 questions)
  - `p1_1|ENV`: Dígame por favor, tres palabras que asocie con la palabra ADULTO MAYOR.  1° MENCIÓN
  - `p1_1a_1|ENV`: Dígame por favor, tres palabras que asocie con la palabra ADULTO MAYOR.  1° MENCIÓN
  - `p2|ENV`: ¿Cuántas personas de 60 años y más viven en este hogar?
  - _(+5 more)_

**`ENV__attitudes_towards_older_people`** — Attitudes Towards Older People (30 questions)
  - `p3|ENV`: ¿Esta/s persona/s es/son familiar/es suyo/s?
  - `p6_1|ENV`: Según su opinión, ¿una persona se puede considerar vieja cuando necesita de ayuda para la mayoría de sus actividades cot
  - `p6_2|ENV`: Según su opinión, ¿una persona se puede considerar vieja cuando su movilidad se ve reducida o desaparece?
  - _(+27 more)_

**`ENV__discrimination`** — Discrimination Against Older Adults (32 questions)
  - `p16_1|ENV`: Podría decirme, por favor, ¿qué tipo de maltrato cree usted que se da en contra de los adultos mayores? Negligencia (no 
  - `p16_2|ENV`: Podría decirme, por favor, ¿qué tipo de maltrato cree usted que se da en contra de los adultos mayores? Auto-negligencia
  - `p16_3|ENV`: Podría decirme, por favor, ¿qué tipo de maltrato cree usted que se da en contra de los adultos mayores? Maltrato físico 
  - _(+29 more)_

**`ENV__maltrato_y_abuso`** — Maltrato y Abuso hacia Adultos Mayores (5 questions)
  - `p19_1|ENV`: Por lo que usted sabe, ¿en su familia, algún adulto mayor ha sufrido alguna de las siguientes situaciones? Lo han golpea
  - `p19_2|ENV`: Por lo que usted sabe, ¿en su familia, algún adulto mayor ha sufrido alguna de las siguientes situaciones? Lo han empuja
  - `p19_3|ENV`: Por lo que usted sabe, ¿en su familia, algún adulto mayor ha sufrido alguna de las siguientes situaciones? Le han jalado
  - _(+2 more)_

**`ENV__social_responsibility`** — Perceived Responsibility for Elder Care (5 questions)
  - `p7_1|ENV`: ¿Cuál considera usted que es el principal problema que enfrentan los adultos mayores en México?
  - `p7_2|ENV`: ¿Y el segundo más importante?
  - `p7_1a_1|ENV`: ¿Cuál considera usted que es el principal problema que enfrentan los adultos mayores en México?
  - _(+2 more)_

### FAM — familia

**`FAM__family_structure`** — Family Structure and Composition (9 questions)
  - `p1|FAM`: El lugar en donde usted vivió durante su infancia, digamos, hasta los 14 años de edad era...
  - `p2|FAM`: ¿Vivió su infancia siendo parte de una familia?
  - `p3|FAM`: Entonces, ¿en dónde vivió su infancia?
  - _(+6 more)_

**`FAM__family_relationships`** — Family Relationships and Dynamics (30 questions)
  - `p8|FAM`: ¿Cómo describiría su infancia hasta los 14 años, muy feliz, feliz, medianamente feliz o infeliz?
  - `p9|FAM`: ¿Por qué?
  - `p16|FAM`: Nos hemos acostumbrado a referirnos a una familia como un grupo de personas en el que se identifica una pareja formada p
  - _(+27 more)_

**`FAM__family_values`** — Family Values and Norms (13 questions)
  - `p11_1|FAM`: Por favor, dígame tres ventajas de vivir en familia. 1° MENCIÓN
  - `p12_1|FAM`: Y cuáles serían tres desventajas? 1° MENCIÓN
  - `p13|FAM`: ¿Qué tipo de familia considera usted ideal y de la cual una persona deba aspirar a formar parte? Le voy a mencionar algu
  - _(+10 more)_

**`FAM__family_problems`** — Problems and Challenges in Family (4 questions)
  - `p17|FAM`: En la actualidad, ¿cuál considera que es el principal problema que enfrenta la familia en México?
  - `p32|FAM`: Es cada vez más frecuente, que entre las parejas conyugales estables, alguno de sus miembros tenga relaciones extraconyu
  - `p38|FAM`: Cada vez es más frecuente que las parejas conyugales se separen o se divorcien; en su opinión, ¿a qué se debe esto?
  - _(+1 more)_

**`FAM__family_support`** — Family Support and Resources (18 questions)
  - `p10|FAM`: ¿Para lograr lo que se ha propuesto en la vida, su familia l@ ha apoyado o ha sido un obstáculo?
  - `p18_1|FAM`: ¿Qué organizaciones existen en México para resolver los problemas que enfrentan las familias? 1° MENCIÓN
  - `p19|FAM`: En su opinión, ¿qué es lo que busca una persona cuando decide formar una familia?
  - _(+15 more)_

**`FAM__family_influence`** — Influence of External Factors on Family (5 questions)
  - `p40|FAM`: ¿Cómo afectan las nuevas tecnologías de comunicación (como internet, facebook, twitter, whatsapp, etc.) a las relaciones
  - `p43|FAM`: ¿Cada vez es más frecuente que la mujer, madre de familia,  trabaje fuera de su hogar. En su opinión, ¿cómo repercute es
  - `p56|FAM`: En su opinión, ¿cuál es la institución que mayor influencia tiene en la vida familiar en México?
  - _(+2 more)_

### FED — federalismo

**`FED__economic_perception`** — Perception of Economic Situation (2 questions)
  - `p1|FED`: Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación económica actu
  - `p3|FED`: En general, usted cree que en el próximo año la situación económica del país...

**`FED__political_attitudes`** — Attitudes Toward Political Situation (4 questions)
  - `p2|FED`: De las siguientes palabras, ¿con cuál está usted más de acuerdo para describir la situación política del país?
  - `p4|FED`: Y cree usted que en el próximo año la situación política del país…
  - `p7|FED`: ¿Qué tanto piensa usted que la política tiene que ver con su vida diaria?
  - _(+1 more)_

**`FED__trust_in_institutions`** — Trust in Government and Public Institutions (36 questions)
  - `p9_1|FED`: ¿Cuáles son las tres instituciones de gobierno que más influyen en su vida diaria? 1° MENCIÓN
  - `p10|FED`: Por lo que usted ha visto, ¿qué tan buena o mala considera que es la relación entre el gobierno municipal y el gobierno 
  - `p11|FED`: Y por lo que usted ha visto, ¿qué tan buena o mala diría que es la relación entre el gobierno del estado y el gobierno f
  - _(+33 more)_

**`FED__government_relationships`** — Perceived Relationships Among Government Levels (6 questions)
  - `p14_1|FED`: ¿Qué tanto caso le hacen al ciudadano autoridades como las siguientes?  Los presidentes municipales (delegados en el DF)
  - `p14_2|FED`: ¿Qué tanto caso le hacen al ciudadano autoridades como las siguientes?  Los gobernadores de los estados   (el Jefe de Go
  - `p14_3|FED`: ¿Qué tanto caso le hacen al ciudadano autoridades como las siguientes?  Presidente de la República
  - _(+3 more)_

**`FED__political_participation`** — Political Engagement and Participation (5 questions)
  - `p5|FED`: ¿Con qué frecuencia acostumbra leer, ver o escuchar noticias o programas sobre política o asuntos públicos?
  - `p6|FED`: ¿Qué tanto se interesa usted en la política?
  - `p15_1|FED`: ¿Qué tanto aprueba o desaprueba la labor que realiza el presidente municipal o Delegado?
  - _(+2 more)_

**`FED__corruption_perception`** — Perception of Corruption in Government (6 questions)
  - `p18_1|FED`: ¿Qué tanta corrupción considera usted que hay en  el gobierno del estado?
  - `p18_2|FED`: ¿Qué tanta corrupción considera usted que hay en  la policía federal?
  - `p18_3|FED`: ¿Qué tanta corrupción considera usted que hay en  la policía municipal
  - _(+3 more)_

**`FED__national_identity`** — National Identity (3 questions)
  - `p19_1|FED`: ¿Qué tan orgulloso se siente usted de ser de este municipio?
  - `p19_2|FED`: ¿Qué tan orgulloso se siente usted de ser de este estado?
  - `p19_3|FED`: ¿Qué tan orgulloso se siente usted de ser mexicano?

**`FED__values_and_norms`** — Values And Norms (2 questions)
  - `p20_1|FED`: ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases?  Yo tengo los mismos valores que la mayoría de
  - `p20_2|FED`: ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases?  En nuestra sociedad existe un gran acuerdo so

**`FED__government_intervention`** — Government Intervention (7 questions)
  - `p21_1|FED`: Por lo que usted piensa, ¿El gobierno federal debería o no debería intervenir en las decisiones con respecto a lo que se
  - `p21_2|FED`: Por lo que usted piensa, ¿El gobierno federal debería o no debería intervenir en las decisiones con respecto a la decisi
  - `p21_3|FED`: Por lo que usted piensa, ¿El gobierno federal debería o no debería intervenir en las decisiones con respecto a la venta 
  - _(+4 more)_

**`FED__decision_making`** — Decision Making (4 questions)
  - `p22|FED`: Según su opinión, cuando hay que tomar decisiones importantes en una comunidad, como por ejemplo, dónde poner un nuevo p
  - `p23|FED`: Si una decisión fue tomada por la mayoría de las personas...
  - `p24|FED`: En su opinión, ¿cómo deberían tomarse las decisiones importantes para EL PAÍS?
  - _(+1 more)_

**`FED__electoral_process`** — Electoral Process (5 questions)
  - `p26_1|FED`: Por lo que usted sabe, ¿quién organiza las elecciones para Presidente Municipal?
  - `p26_2|FED`: Por lo que usted sabe, ¿quién organiza las elecciones para el gobernador de su estado?
  - `p26_3|FED`: Por lo que usted sabe, ¿quién organiza las elecciones para el presidente del país?
  - _(+2 more)_

### GEN — genero

**`GEN__economic_perceptions`** — Perceptions of the country's economic situation (2 questions)
  - `p1|GEN`: Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación actual del paí
  - `p2|GEN`: En general, ¿cree usted que el próximo año la situación económica del país va a mejorar o empeorar?

**`GEN__gender_associations`** — Associations and stereotypes related to gender (4 questions)
  - `p3_1|GEN`: ¿Dígame dos palabras que asocie con la palabra  mujer? 1° MENCIÓN
  - `p3_1a_1|GEN`: ¿Dígame dos palabras que asocie con la palabra  mujer? 1° MENCIÓN
  - `p4_1|GEN`: ¿Dígame dos palabras que asocie con la palabra hombre? 1° MENCIÓN
  - _(+1 more)_

**`GEN__gender_advantages_disadvantages`** — Perceived advantages and disadvantages of being woman or man (9 questions)
  - `p5|GEN`: ¿Cuál cree qué es la mayor ventaja de ser mujer?
  - `p5a_1|GEN`: ¿Cuál cree qué es la mayor ventaja de ser mujer?
  - `p6|GEN`: ¿Y la mayor desventaja de ser mujer?
  - _(+6 more)_

**`GEN__gender_roles`** — Roles and responsibilities related to gender (18 questions)
  - `p24|GEN`: En general, ¿usted considera que en cuanto a las tareas del hogar…?
  - `p25_1|GEN`: Dígame con qué frecuencia usted realiza las siguientes actividades, siempre, muchas veces, pocas veces o nunca: Tender c
  - `p25_2|GEN`: Dígame con qué frecuencia usted realiza las siguientes actividades, siempre, muchas veces, pocas veces o nunca: Sacudir 
  - _(+15 more)_

**`GEN__relationship_dynamics`** — Relationship and household decision-making dynamics (22 questions)
  - `p11_1|GEN`: Le voy  leer otras frases ahora relacionadas con aspectos de trabajo, por favor indíqueme si usted está de acuerdo o en 
  - `p11_2|GEN`: Le voy  leer otras frases ahora relacionadas con aspectos de trabajo, por favor indíqueme si usted está de acuerdo o en 
  - `p11_3|GEN`: Le voy  leer otras frases ahora relacionadas con aspectos de trabajo, por favor indíqueme si usted está de acuerdo o en 
  - _(+19 more)_

**`GEN__work_and_finance`** — Work, income, and financial control within relationships (9 questions)
  - `p21|GEN`: Ahora dígame, ¿Sabe usted o no cuánto gana su pareja?
  - `p22|GEN`: Y ¿Usted le dice a su pareja cuánto dinero gana?
  - `p23_1|GEN`: Regularmente, ¿usted pide permiso a su pareja para salir sola(o) de día?
  - _(+6 more)_

**`GEN__gender_attitudes`** — Attitudes towards gender roles and equality (16 questions)
  - `p10_1|GEN`: Le voy  leer algunas frases, por favor indíqueme si usted está de acuerdo o en desacuerdo con cada una de ellas. Se debe
  - `p10_2|GEN`: Le voy  leer algunas frases, por favor indíqueme si usted está de acuerdo o en desacuerdo con cada una de ellas. La educ
  - `p10_3|GEN`: Le voy  leer algunas frases, por favor indíqueme si usted está de acuerdo o en desacuerdo con cada una de ellas. Entre m
  - _(+13 more)_

### GLO — globalizacion

**`GLO__linguistic_diversity`** — Linguistic Diversity (3 questions)
  - `p1_1|GLO`: Con la palabra maíz yo asocio comida, mercado, animales. ¿Podría decirme tres palabras que asocie con la palabra GLOBALI
  - `p2|GLO`: ¿Podría indicarme cuántos idiomas habla además del español?
  - `p2_1_1a_1|GLO`:   2.1. ¿Cuál/es? 1° MENCIÓN

**`GLO__migration_experience`** — Migration Experience (8 questions)
  - `p3|GLO`: ¿Ha vivido usted en otro país?
  - `p3_1_1a_1|GLO`:   3.1 ¿En qué país/es? 1° MENCIÓN
  - `p3_2|GLO`:   3.2 ¿Cuál fue la principal razón?
  - _(+5 more)_

**`GLO__international_travel`** — International Travel (6 questions)
  - `p4|GLO`: Dígame por favor, ¿aproximadamente cuántas veces en su vida ha viajado fuera de México?
  - `p4_1_1a_1|GLO`: 1 ¿A qué países?  1° MENCIÓN
  - `p4_2|GLO`:   4.2 ¿Por qué motivos han sido sus viajes? Indique inicialmente la más frecuente.
  - _(+3 more)_

**`GLO__attitudes_towards_foreigners`** — Attitudes Towards Foreigners (24 questions)
  - `p7|GLO`: ¿Tiene relación con extranjeros que vivan en el país?
  - `p7_1_1|GLO`: 7.1¿En qué ámbito de su vida suele convivir con ellos?
  - `p7_1_1a|GLO`: 7.1¿En qué ámbito de su vida suele convivir con ellos?
  - _(+21 more)_

**`GLO__religious_attitudes`** — Religious Attitudes (18 questions)
  - `p12_1|GLO`: En una escala donde 1 es "muy desfavorable" y 5 "muy favorable" ¿Podría indicarme cuál es su opinión respecto a la relig
  - `p12_2|GLO`: En una escala donde 1 es "muy desfavorable" y 5 "muy favorable" ¿Podría indicarme cuál es su opinión respecto a la relig
  - `p12_3|GLO`: En una escala donde 1 es "muy desfavorable" y 5 "muy favorable" ¿Podría indicarme cuál es su opinión respecto a la relig
  - _(+15 more)_

**`GLO__national_pride`** — National Pride (20 questions)
  - `p14|GLO`: Y ahora dígame, ¿está usted de acuerdo o en desacuerdo con la siguiente afirmación: 'Las personas deberían tener los mis
  - `p15|GLO`: ¿Qué tan orgulloso está de ser mexicano?
  - `p16_1|GLO`: ¿Qué tan orgulloso está usted de México en cada uno de los siguientes ámbitos? El funcionamiento de la democracia
  - _(+17 more)_

### HAB — la condicion de habitabilidad de vivienda en mexico

**`HAB__material_construction`** — Material and Construction Quality (3 questions)
  - `p1|HAB`: ¿De qué material es la mayor parte de las paredes o muros de esta vivienda?
  - `p2|HAB`: ¿De qué material es la mayor parte de los techos de esta vivienda?
  - `p3|HAB`: ¿De qué material es la mayor parte del piso de esta vivienda?

**`HAB__utilities_services`** — Utilities and Services Availability (12 questions)
  - `p5|HAB`: ¿Esta vivienda tiene un cuarto para cocinar?
  - `p5a|HAB`: ¿Qué aparato usa para cocinar?
  - `p5_1|HAB`:  5.1 En el cuarto donde cocinan, ¿también duermen?
  - _(+9 more)_

**`HAB__ownership_and_property`** — Ownership and Property Characteristics (16 questions)
  - `p13|HAB`: ¿Esta vivienda es propiedad de alguna  persona que vive aquí?
  - `p14|HAB`: ¿A quién pertenece esta vivienda?
  - `p15|HAB`: La vivienda en la cual usted habita, es:
  - _(+13 more)_

**`HAB__location_and_access`** — Location and Accessibility (29 questions)
  - `p22|HAB`: ¿En qué zona o zonas se encuentran?
  - `p23|HAB`: ¿Sobre qué tipo de terreno está su casa?
  - `p24|HAB`: Su vivienda se encuentra en…
  - _(+26 more)_

**`HAB__housing_conditions`** — Housing Conditions and Maintenance (19 questions)
  - `p4|HAB`: ¿Cuántos cuartos se usan para dormir sin contar pasillos?
  - `p4_1|HAB`:  4.1 Sin contar pasillos ni baños, ¿cuántos cuartos tiene en total esta vivienda?
  - `p28|HAB`: ¿Qué clase de vivienda tiene usted?
  - _(+16 more)_

### IDE — identidad y valores

**`IDE__patriotismo`** — Patriotism (7 questions)
  - `p3_1|IDE`: De los siguientes lugares que le voy a mencionar, dígame qué tan unido se siente a su barrio o colonia
  - `p3_2|IDE`: De los siguientes lugares que le voy a mencionar, dígame qué tan unido se siente a su localidad o pueblo
  - `p3_3|IDE`: De los siguientes lugares que le voy a mencionar, dígame qué tan unido se siente a su estado
  - _(+4 more)_

**`IDE__identidad_cultural`** — Cultural Identity (4 questions)
  - `p1_1|IDE`: Con la palabra maíz, yo asocio comida, mercado, animales. Dígame por favor, tres palabras que asocies con la palabra MÉX
  - `p1_1a_1|IDE`: Con la palabra maíz, yo asocio comida, mercado, animales. Dígame por favor, tres palabras que asocies con la palabra MÉX
  - `p2_1|IDE`: Y ahora, voy a pedir que me diga, por favor, tres palabras que asocie con la palabra MEXICANO. 1° MENCIÓN
  - _(+1 more)_

**`IDE__percepciones_sociales`** — Social Perceptions (21 questions)
  - `p9|IDE`: En su opinión, ¿qué habría que hacer con los grupos étnicos o culturales que viven en nuestro país?
  - `p10_1|IDE`: ¿Alguna vez ha sentido usted que lo han hecho menos por causa de sus costumbres y cultura  en el trabajo?
  - `p10_2|IDE`: ¿Alguna vez ha sentido usted que lo han hecho menos por causa de sus costumbres y cultura  en la escuela?
  - _(+18 more)_

**`IDE__bienestar_y_satisfacción`** — Well-being and Satisfaction (17 questions)
  - `p11|IDE`: Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación económica actu
  - `p12|IDE`: En general, cree usted que en el próximo año la situación económica del país:…
  - `p18|IDE`: ¿Considera usted que su situación económica es mejor o es peor que la de sus padres?
  - _(+14 more)_

**`IDE__valores_y_normas`** — Values and Norms (7 questions)
  - `p4|IDE`: ¿Con cuál de estas dos frases está usted más de acuerdo?
  - `p8|IDE`: .¿Qué tan importante es para usted conservar las tradiciones de su lugar de origen?
  - `p26_1|IDE`: ¿Para usted qué significa tener éxito en su vida?  1° MENCIÓN
  - _(+4 more)_

**`IDE__emociones_y_percepciones`** — Emociones Y Percepciones (3 questions)
  - `p5_1|IDE`: ¿Cuál de las siguientes emociones refleja mejor lo que siente sobre México?  1° MENCIÓN
  - `p5_1a|IDE`: ¿Cuál de las siguientes emociones refleja mejor lo que siente sobre México?  1° MENCIÓN
  - `p7|IDE`: Usted se siente…

**`IDE__problemas_nacionales`** — Problemas Nacionales (2 questions)
  - `p15_1|IDE`: ¿Cuál cree que son los tres principales problemas del país? 1° MENCIÓN
  - `p15_1a|IDE`: ¿Cuál cree que son los tres principales problemas del país? 1° MENCIÓN

**`IDE__problemas_familiares`** — Problemas Familiares (1 questions)
  - `p16_1|IDE`: Y ahora dígame por favor, ¿cuáles son los tres problemas MAS graves en su familia? 1° MENCIÓN

**`IDE__problemas_comunitarios`** — Problemas Comunitarios (1 questions)
  - `p17_1|IDE`: Y ¿cuáles diría usted que son los tres problemas MAS graves en el lugar donde usted vive? 1° MENCIÓN

**`IDE__aspiraciones`** — Aspiraciones (1 questions)
  - `p21|IDE`: Imagine que en las próximas semanas usted tuviera la oportunidad de realizar alguno de sus sueños, ¿cuál sueño realizarí

**`IDE__autonomía`** — Autonomía (5 questions)
  - `p30_1|IDE`: Dígame, ¿qué tanto control siente que tiene sobre los siguientes aspectos de su vida? Su situación económica
  - `p30_2|IDE`: Dígame, ¿qué tanto control siente que tiene sobre los siguientes aspectos de su vida? Su trabajo
  - `p30_3|IDE`: Dígame, ¿qué tanto control siente que tiene sobre los siguientes aspectos de su vida? Sus condiciones de vivienda
  - _(+2 more)_

**`IDE__divisiones_sociales`** — Divisiones Sociales (10 questions)
  - `p34_1|IDE`: Siempre hay diferencias entre la gente que vive en un mismo lugar, ¿qué tanto cree usted que la educación provoque divis
  - `p34_2|IDE`: Siempre hay diferencias entre la gente que vive en un mismo lugar, ¿qué tanto cree usted que la riqueza provoque divisio
  - `p34_3|IDE`: Siempre hay diferencias entre la gente que vive en un mismo lugar, ¿qué tanto cree usted que la riqueza provoque divisio
  - _(+7 more)_

**`IDE__normas_morales`** — Normas Morales (1 questions)
  - `p35_1|IDE`: ¿Quién o quiénes deben poner los límites a la conducta de las personas? 1° MENCIÓN

### IND — indigenas

**`IND__indigenous_identity`** — Indigenous Identity and Roots (25 questions)
  - `p3|IND`: ¿De qué estado es originario usted?
  - `p4|IND`: ¿Y de qué municipio?
  - `p5|IND`: ¿Qué tan seguido va a su lugar de origen?
  - _(+22 more)_

**`IND__perceptions_and_stereotypes`** — Perceptions and Stereotypes about Indigenous People (10 questions)
  - `p11_1|IND`: Con la palabra maíz, yo asocio comida, mercado, animales. Dígame por favor, tres palabras que asocie con la palabra INDÍ
  - `p11_1a_1|IND`: Con la palabra maíz, yo asocio comida, mercado, animales. Dígame por favor, tres palabras que asocie con la palabra INDÍ
  - `p26_1|IND`: ¿Qué tan positiva o negativa es la imagen de los indígenas en su familia?
  - _(+7 more)_

**`IND__discrimination_and_racism`** — Discrimination and Racism (10 questions)
  - `p21|IND`: ¿Usted considera que hay o no hay racismo en México?
  - `p25_1|IND`: ¿Usted considera que los siguientes actos son discriminatorios o no contra los indígenas? No darles trabajo
  - `p25_2|IND`: ¿Usted considera que los siguientes actos son discriminatorios o no contra los indígenas? Que no haya diputados indígena
  - _(+7 more)_

**`IND__socioeconomic_conditions`** — Socioeconomic Conditions and Opportunities (12 questions)
  - `p1|IND`: Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación actual del paí
  - `p2|IND`: En general, ¿cree usted que el próximo año la situación económica del país va a mejorar o empeorar?
  - `p16|IND`: ¿Usted sabe aproximadamente, cuántos grupos indígenas hay en México?
  - _(+9 more)_

**`IND__cultural_practices_and_language`** — Cultural Practices and Language (2 questions)
  - `p18_1|IND`: Podría mencionarme tres grupos indígenas que recuerde: 1° MENCIÓN
  - `p18_1a_1|IND`: Podría mencionarme tres grupos indígenas que recuerde: 1° MENCIÓN

**`IND__attitudes_towards_indigenous`** — Attitudes towards Indigenous People (16 questions)
  - `p20|IND`: Por lo que usted piensa, ¿el color de piel, influye o no influye en el trato que reciben las personas?
  - `p22|IND`: ¿Cree usted que las costumbres de los indígenas son un obstáculo o no para el progreso de las regiones donde habitan?
  - `p23|IND`: ¿Cuál cree usted que debe ser la acción más adecuada del gobierno para los pueblos indígenas?
  - _(+13 more)_

**`IND__advantages_disadvantages`** — Advantages Disadvantages (5 questions)
  - `p13|IND`: ¿Cuál cree que es la mayor ventaja de ser indígena en México?
  - `p13a_1|IND`: ¿Cuál cree que es la mayor ventaja de ser indígena en México?
  - `p14|IND`: ¿Y cuál cree que es la mayor desventaja de ser indígena en México?
  - _(+2 more)_

### JUS — justicia

**`JUS__perceptions_of_justice`** — Perceptions of Justice (6 questions)
  - `p6_1|JUS`: En su opinión, ¿quién o quiénes deben poner los límites a la conducta de las personas? 1° MENCIÓN
  - `p11_1|JUS`: Por lo que usted ha visto, ¿quién viola más las leyes?  1° MENCIÓN
  - `p17|JUS`: Por lo que usted piensa, si un hombre mata a alguien y las autoridades no hacen nada, ¿los miembros de la comunidad tien
  - _(+3 more)_

**`JUS__trust_in_institutions`** — Trust in Institutions (39 questions)
  - `p8|JUS`: En una escala de 0 a 10, donde 0 es no 'respeta nada' y 10 es 'respeta mucho' ¿qué tanto cree usted que los gobernantes 
  - `p9|JUS`: Usando la misma escala, ¿qué tanto cree usted que los ciudadanos respetan las leyes en México?
  - `p10|JUS`: Usando la misma escala, ¿qué tanto respeta usted la ley?
  - _(+36 more)_

**`JUS__legal_knowledge`** — Legal Knowledge (6 questions)
  - `p12|JUS`: Todos tenemos derechos y obligaciones ¿qué tanto considera usted que conoce sus derechos?
  - `p13|JUS`: Todos tenemos derechos y obligaciones ¿qué tanto considera usted que conoce sus obligaciones?
  - `p28|JUS`: Si tuviera que defenderse legalmente y no contara con dinero para pagar a un abogado, usted…
  - _(+3 more)_

**`JUS__attitudes_towards_law`** — Attitudes Towards Law (13 questions)
  - `p4|JUS`: ¿Qué tan de acuerdo o en desacuerdo está usted con que, para conseguir información, se torture a una persona detenida po
  - `p5_1|JUS`: Cuando usted piensa que tiene la razón, ¿está o no está dispuesto a ir en contra de lo que piensan sus padres?
  - `p5_2|JUS`: Cuando usted piensa que tiene la razón, ¿está o no está dispuesto a ir en contra de su cónyuge o pareja?
  - _(+10 more)_

**`JUS__opinions_on_justice_system`** — Opinions on Justice System (16 questions)
  - `p1|JUS`: Comparada con la situación que tenía el país hace un año, ¿cómo diría usted que es la situación económica actual del paí
  - `p2|JUS`: De las siguientes palabras, ¿con cuál está usted más de acuerdo para describir la situación política del país?
  - `p3_1|JUS`: En su opinión, ¿cuáles son los TRES problemas más graves de nuestro país?  1° MENCIÓN
  - _(+13 more)_

### MED — medio ambiente

**`MED__environmental_attitudes`** — Environmental Attitudes and Perceptions (14 questions)
  - `p3_1|MED`: ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases? Aquí donde vive, la mayoría de la gente es hon
  - `p3_2|MED`: ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases? Aquí donde vive, la gente se interesa sólo en 
  - `p3_3|MED`: ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases? Aquí donde vive, si uno tiene un problema siem
  - _(+11 more)_

**`MED__environmental_knowledge`** — Environmental Knowledge and Awareness (4 questions)
  - `p8|MED`: En una escala de 0 al 10  en donde 0 es   sabe 'nada' y 10 es 'sabe mucho' ¿cuánto cree usted que sabe sobre las CAUSAS 
  - `p9|MED`: ¿Y cuánto cree usted que sabe sobre las SOLUCIONES para estos problemas ambientales? En una escala de 0 al 10  en donde 
  - `p27_1|MED`: En su opinión, ¿en qué medida es verdad cada una de las siguientes afirmaciones? El cambio climático es causado por un h
  - _(+1 more)_

**`MED__environmental_behaviors`** — Environmental Behaviors and Practices (17 questions)
  - `p15_1|MED`: ¿Qué tan de acuerdo o en desacuerdo está usted con cada una de las siguientes frases? Me gustaría unirme y participar ac
  - `p15_2|MED`: ¿Qué tan de acuerdo o en desacuerdo está usted con cada una de las siguientes frases? No me involucraría en una organiza
  - `p15_3|MED`: ¿Qué tan de acuerdo o en desacuerdo está usted con cada una de las siguientes frases? Me gustaría apoyar una organizació
  - _(+14 more)_

**`MED__environmental_values`** — Environmental Values and Ethical Perspectives (21 questions)
  - `p10_1|MED`: ¿Qué tan perjudicial considera que es para el medio ambiente la contaminación causada por los coches?
  - `p10_2|MED`: ¿Qué tan perjudicial considera que es para el medio ambiente la contaminación causada por la industria?
  - `p10_3|MED`: ¿Qué tan perjudicial considera que es para el medio ambiente la contaminación  causada por químicos y pesticidas usados 
  - _(+18 more)_

**`MED__policy_opinions`** — Opinions on Environmental Policies and Laws (14 questions)
  - `p12_1|MED`: Respecto a las siguientes frases, ¿qué tan de acuerdo o en desacuerdo está usted con...? Los gobiernos deberían controla
  - `p12_2|MED`: Respecto a las siguientes frases, ¿qué tan de acuerdo o en desacuerdo está usted con...? Las industrias deberían protege
  - `p12_3|MED`: Respecto a las siguientes frases, ¿qué tan de acuerdo o en desacuerdo está usted con...? No importa que la industria no 
  - _(+11 more)_

**`MED__environmental_concerns`** — Concerns about Environmental Issues (10 questions)
  - `p1_1|MED`: De los siguientes temas, ¿cuáles cree usted que son los TRES más importantes para México? 1ª MENCIÒN
  - `p1_2|MED`: De los siguientes temas, ¿cuáles cree usted que son los TRES más importantes para México? 2ª MENCIÒN
  - `p1_3|MED`: De los siguientes temas, ¿cuáles cree usted que son los TRES más importantes para México? 3ª MENCIÒN
  - _(+7 more)_

### MIG — migracion

**`MIG__life_satisfaction`** — Life Satisfaction (1 questions)
  - `p1|MIG`: En términos generales, usted diría que está con su vida…

**`MIG__perceptions_society`** — Perceptions of Society (12 questions)
  - `p2|MIG`: ¿Cuál considera que es su principal problema en la actualidad?
  - `p5_1|MIG`: Por lo que usted piensa, ¿Qué tan positivo o negativo es para la sociedad que esté compuesta por personas de  distintas 
  - `p5_2|MIG`: Por lo que usted piensa, ¿Qué tan positivo o negativo es para la sociedad que esté compuesta por personas de  distintas 
  - _(+9 more)_

**`MIG__migration_attitudes`** — Migration Attitudes (26 questions)
  - `p3_1|MIG`: ¿Qué tantas oportunidades tienes para tener una buena educación?
  - `p3_2|MIG`: ¿Qué tantas oportunidades tienes para contar con un trabajo?
  - `p3_3|MIG`: ¿Qué tantas oportunidades tienes para poner un negocio propio?
  - _(+23 more)_

**`MIG__cultural_heritage`** — Cultural Heritage (6 questions)
  - `p4_1|MIG`: Con la palabra maíz, yo asocio comida, mercado, animales. ¿Podría decirme, por favor, tres palabras que asocie con la pa
  - `p8|MIG`: Con la palabra maíz, yo asocio comida, mercado, animales. ¿Podría decirme, por favor, una palabra que asocie con la expr
  - `p8_2|MIG`: Con la palabra maíz, yo asocio comida, mercado, animales. ¿Podría decirme, por favor, una palabra que asocie con la expr
  - _(+3 more)_

**`MIG__trust_confidence`** — Trust and Confidence (15 questions)
  - `p10_1|MIG`: En una escala de 0 a 10, como en la escuela, donde 0 es no confío nada y 10 es confío mucho, en general, ¿qué tanto conf
  - `p10_2|MIG`: En una escala de 0 a 10, como en la escuela, donde 0 es no confío nada y 10 es confío mucho, en general, ¿qué tanto conf
  - `p10_3|MIG`: En una escala de 0 a 10, como en la escuela, donde 0 es no confío nada y 10 es confío mucho, en general, ¿qué tanto conf
  - _(+12 more)_

**`MIG__migration_experience`** — Migration Experience (10 questions)
  - `p16|MIG`: ¿Ha vivido en otro país?
  - `p16_1|MIG`:  16.1 ¿En qué país?
  - `p16_2|MIG`:  16.2 ¿Cuánto tiempo?
  - _(+7 more)_

**`MIG__attitudes_toward_others`** — Attitudes Toward Others (10 questions)
  - `p7_1|MIG`: ¿Estaría dispuesto o no estaría dispuesto a permitir que en su casa vivieran personas de otra religión?
  - `p7_2|MIG`: ¿Estaría dispuesto o no estaría dispuesto a permitir que en su casa vivieran personas de otra raza (negro, chino,etc.)?
  - `p7_3|MIG`: ¿Estaría dispuesto o no estaría dispuesto a permitir que en su casa vivieran personas indígenas?
  - _(+7 more)_

### NIN — ninos adolescentes y jovenes

**`NIN__perceptions_of_rights`** — Perceptions of Children's Rights (15 questions)
  - `p5|NIN`: En su opinión, desde el año 2010 hasta la hoy, ¿la situación general de los niños en México ha mejorado o ha empeorado?
  - `p19|NIN`: Por lo que usted cree, los niños deben tener...
  - `p20|NIN`: En su opinión los niños deben ser considerados como:
  - _(+12 more)_

**`NIN__children_problems`** — Problems Faced by Children (6 questions)
  - `p4_1|NIN`: ¿Cuál considera Ud. que es el principal problema que enfrentan hoy los niños en México? ¿Y el segundo más importante? 1°
  - `p4_1a_1|NIN`: ¿Cuál considera Ud. que es el principal problema que enfrentan hoy los niños en México? ¿Y el segundo más importante? 1°
  - `p7_1|NIN`: Pensando en la educación que reciben los niños en la actualidad, ¿cuáles cree que son los principales problemas?  1° MEN
  - _(+3 more)_

**`NIN__institutional_trust`** — Trust in Institutions Supporting Children (22 questions)
  - `p10_1|NIN`: ¿Qué instituciones cree usted que ayudarían a los niños en México en caso de que tuvieran que resolver situaciones como 
  - `p10_2|NIN`: ¿Qué instituciones cree usted que ayudarían a los niños en México en caso de que tuvieran que resolver situaciones como 
  - `p10_3|NIN`: ¿Qué instituciones cree usted que ayudarían a los niños en México en caso de que tuvieran que resolver situaciones como 
  - _(+19 more)_

**`NIN__opinions_on_participation`** — Opinions on Children's Participation (5 questions)
  - `p6|NIN`: En su opinión, que es preferible para los niños en la actualidad ¿mantener el sistema educativo tal como está o cambiarl
  - `p12|NIN`: En general, ¿qué tanto piensa Ud. que deberían tomarse en cuenta las opiniones de los niños en las decisiones familiares
  - `p13|NIN`: Y en general, ¿qué tanto piensa Ud. que deberían tomarse en cuenta las opiniones de los niños en lo que afecta a su escu
  - _(+2 more)_

**`NIN__social_attitudes`** — Social Attitudes Toward Children and Youth (22 questions)
  - `p1|NIN`: Comparada con la situación política que tenía el país hace un año ¿Cómo cree usted que es la situación política actual d
  - `p2|NIN`: Y comparada con la situación económica que tenía el país hace un año, ¿cree usted que la situación económica del país ha
  - `p3_1|NIN`: Con la palabra maíz, yo asocio comida, mercado, animales. Dígame por favor tres palabras que asocie con la palabra NIÑO.
  - _(+19 more)_

**`NIN__government_intervention`** — Views on Government Intervention in Children's Issues (11 questions)
  - `p9_1|NIN`: Por lo que usted piensa, ¿el gobierno debería o no debería intervenir en los siguientes temas:  Lo que se enseña a los n
  - `p9_2|NIN`: Por lo que usted piensa, ¿el gobierno debería o no debería intervenir en los siguientes temas:  La educación sexual de l
  - `p9_3|NIN`: Por lo que usted piensa, ¿el gobierno debería o no debería intervenir en los siguientes temas:  Los niños abandonados o 
  - _(+8 more)_

### POB — pobreza

**`POB__economic_status`** — Economic Status (12 questions)
  - `p1|POB`: Hablemos un poco sobre el trabajo. Dígame, la semana pasada usted…
  - `p2|POB`: Además de lo que señaló en la pregunta anterior, la semana pasada usted…
  - `p3|POB`: Usted se dedica a su trabajo principal:
  - _(+9 more)_

**`POB__perceptions_of_poverty`** — Perceptions of Poverty (20 questions)
  - `p10|POB`: ¿A qué clase social diría que pertenece usted?
  - `p11|POB`: ¿Y su papá de qué clase social era cuando usted tenía 18 años (o cuando murió)?
  - `p12|POB`: ¿Y sus hijos de qué clase social son (o cree que serán)?
  - _(+17 more)_

**`POB__social_attitudes`** — Social Attitudes (22 questions)
  - `p30|POB`: Para ayudar a resolver el problema de la pobreza, ¿con quién preferiría colaborar?
  - `p31|POB`: En su opinión, ¿qué se necesita para acabar con la pobreza?
  - `p32|POB`: En su opinión, ¿cree que en México hay mexicanos de primera y segunda o que todos son iguales?
  - _(+19 more)_

**`POB__social_cohesion`** — Social Cohesion (9 questions)
  - `p46_1|POB`: Voy a pedirle que para calificar las siguientes situaciones responda pensando en usted y la relación que tiene con los v
  - `p46_2|POB`: Voy a pedirle que para calificar las siguientes situaciones responda pensando en usted y la relación que tiene con los v
  - `p46_3|POB`: Voy a pedirle que para calificar las siguientes situaciones responda pensando en usted y la relación que tiene con los v
  - _(+6 more)_

**`POB__personal_resilience`** — Personal Resilience (17 questions)
  - `p13|POB`: ¿Qué tan fuerte se considera usted frente a las adversidades de la vida?
  - `p15|POB`: ¿Qué tanto depende de usted mismo (misma) que le vaya bien este año y el próximo?
  - `p16|POB`: ¿Qué tan feliz diría que es usted?
  - _(+14 more)_

### REL — religion secularizacion y laicidad

**`REL__religious_affiliation`** — Religious Affiliation (5 questions)
  - `p1_1|REL`: ¿A qué religión, creencia o culto pertenece usted? 1° MENCIÓN
  - `p2|REL`: ¿En el pasado fue miembro de una iglesia o denominación religiosa?
  - `p3|REL`: ¿Tiene usted la misma religión de su papá?
  - _(+2 more)_

**`REL__religious_practices`** — Religious Practices (9 questions)
  - `p6|REL`: ¿Recibió alguna educación religiosa?
  - `p7_1|REL`: ¿En cuáles de los siguientes lugares recibió una educación religiosa? 1° MENCIÓN
  - `p10|REL`: ¿Acostumbra orar o hacer peticiones a un poder superior fuera del templo o de las celebraciones religiosas?
  - _(+6 more)_

**`REL__religious_beliefs`** — Religious Beliefs (34 questions)
  - `p8_1|REL`: Hablando en general, ¿piensa usted que su iglesia tiene una respuesta adecuada para los problemas y necesidades morales 
  - `p8_2|REL`: Hablando en general, ¿piensa usted que su iglesia tiene una respuesta adecuada para los problemas de la vida familiar?
  - `p8_3|REL`: Hablando en general, ¿piensa usted que su iglesia tiene una respuesta adecuada para las necesidades espirituales de la g
  - _(+31 more)_

**`REL__religious_values`** — Religious Values (22 questions)
  - `p13_1|REL`: ¿Por lo general, usted toma o no toma en cuenta los valores de la religión para manejar su comportamiento en la familia?
  - `p13_2|REL`: ¿Por lo general, usted toma o no toma en cuenta los valores de la religión para manejar su comportamiento en el trabajo?
  - `p13_3|REL`: ¿Por lo general, usted toma o no toma en cuenta los valores de la religión para manejar su comportamiento en los amigos?
  - _(+19 more)_

**`REL__religious_importance`** — Importance of Religion (1 questions)
  - `p18|REL`: En una escala de 0 a 10, en donde 0 es nada y 10 es mucha, ¿qué tanta importancia tiene Dios en su vida?

**`REL__attitudes_towards_morality`** — Attitudes Towards Morality and Ethical Issues (9 questions)
  - `p29_1|REL`: Usted aprueba o desaprueba el aborto en las siguientes circunstancias..  Cuando la mujer no está casada
  - `p29_2|REL`: Usted aprueba o desaprueba el aborto en las siguientes circunstancias..  Cuando la salud de la madre peligra
  - `p29_3|REL`: Usted aprueba o desaprueba el aborto en las siguientes circunstancias..  Cuando es probable que el niño nazca con malfor
  - _(+6 more)_

### SAL — salud

**`SAL__self_reported_health`** — Self-Reported Health Status (13 questions)
  - `p1|SAL`: En general, usted diría que su salud es:
  - `p11|SAL`: ¿Tuvo algún problema de salud en el último mes?
  - `p12_1|SAL`: Podría decirme, ¿cuál fue el último problema de salud que tuvo usted en el último mes? Puede mencionar hasta tres opcion
  - _(+10 more)_

**`SAL__physical_limitations`** — Physical Limitations (5 questions)
  - `p2|SAL`: ¿Su estado de salud actual le limita realizar esfuerzos físicos moderados, como caminar 30 minutos o hacer limpieza en s
  - `p3|SAL`: ¿Su estado de salud actual le limita subir varios pisos por la escalera?
  - `p4|SAL`: Durante las últimas 4 semanas, ¿hizo menos cosas de lo que hubiera querido hacer a causa de su estado de salud física?
  - _(+2 more)_

**`SAL__mental_health`** — Mental and Emotional Well-being (15 questions)
  - `p6|SAL`: Durante las últimas 4 semanas, ¿hizo menos cosas de las que hubiera querido hacer, por algún problema emocional (como es
  - `p8_1|SAL`: Durante las últimas 4 semanas ¿qué tanto se sintió calmado y tranquilo?
  - `p8_2|SAL`: Durante las últimas 4 semanas ¿qué tanto tuvo mucha energía?
  - _(+12 more)_

**`SAL__health_services_access`** — Access to Health Services (6 questions)
  - `p9|SAL`: ¿Cuenta con afiliación a alguna institución de salud?
  - `p10|SAL`: ¿A cuál institución?
  - `p10a|SAL`: ¿A cuál institución?
  - _(+3 more)_

**`SAL__lifestyle_behaviors`** — Lifestyle and Behavioral Factors (21 questions)
  - `p21|SAL`: ¿Además de acudir al médico realizó otras actividades no indicadas por el médico para atender su problema de salud?
  - `p21_1|SAL`:  21.1 ¿Cuáles?
  - `p27_1|SAL`: De la siguiente lista indique ¿qué tan seguido realiza las siguientes actividades? Comer verduras
  - _(+18 more)_

**`SAL__quality_of_life`** — Perceived Quality of Life (2 questions)
  - `p37|SAL`: En general, ¿cómo considera usted que es su calidad de vida?
  - `p38|SAL`: ¿Qué tan satisfecho está con su vida?

**`SAL__trust_in_health_system`** — Trust In Health System (2 questions)
  - `p23_1|SAL`: ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases? Cuando usted o alguien de su familia buscan y 
  - `p23_2|SAL`: ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases? Cuando tiene necesidad de ir al médico le resu

**`SAL__satisfaction_with_care`** — Satisfaction With Care (5 questions)
  - `p25_1|SAL`: ¿Qué tan satisfecho se siente usted con la atención otorgada por los servicios de salud cuando acude por algún problema?
  - `p25_2|SAL`: ¿Qué tan satisfecho se siente usted con la atención otorgada por los servicios de salud cuando acude por algún problema?
  - `p25_3|SAL`: ¿Qué tan satisfecho se siente usted con la atención otorgada por los servicios de salud cuando acude por algún problema?
  - _(+2 more)_

**`SAL__perceived_benefits`** — Perceived Benefits (11 questions)
  - `p26_1|SAL`: De la siguiente lista enumere del 1 al 11, considerando el número 1 "lo que más beneficia" y el 11 "lo que menos benefic
  - `p26_2|SAL`: De la siguiente lista enumere del 1 al 11, considerando el número 1 "lo que más beneficia" y el 11 "lo que menos benefic
  - `p26_3|SAL`: De la siguiente lista enumere del 1 al 11, considerando el número 1 "lo que más beneficia" y el 11 "lo que menos benefic
  - _(+8 more)_

### SEG — seguridad publica

**`SEG__perceived_threats`** — Perceived Threats and Fear of Crime (24 questions)
  - `p1_1|SEG`: ¿Cuáles son los TRES problemas más graves de México?  1° MENCIÓN
  - `p2_1|SEG`: ¿Cuáles son las TRES principales causas de la INSEGURIDAD que existe actualmente en el país?  1° MENCIÓN
  - `p3|SEG`: Hablando en términos de seguridad pública, ¿qué tan seguro o inseguro se siente usted en la actualidad con respecto a ha
  - _(+21 more)_

**`SEG__crime_experience`** — Personal Experience with Crime (11 questions)
  - `p10_1|SEG`: A su juicio, durante el último año, los delitos en su colonia / localidad...
  - `p10_2|SEG`: A su juicio, durante el último año, los delitos en su municipio...
  - `p10_3|SEG`: A su juicio, durante el último año, los delitos en el estado...
  - _(+8 more)_

**`SEG__community_cohesion`** — Community Cohesion and Mutual Help (18 questions)
  - `p7|SEG`: Dígame por favor, ¿cuánto tiempo hace que vive en esta colonia (localidad)?
  - `p8_1|SEG`: En su opinión y en relación a la delincuencia, ¿qué tan seguro o inseguro es vivir en su colonia / localidad?
  - `p8_2|SEG`: En su opinión y en relación a la delincuencia, ¿qué tan seguro o inseguro es vivir en su municipio?
  - _(+15 more)_

**`SEG__avoidance_behaviors`** — Avoidance and Activity Cessation Due to Crime (18 questions)
  - `p22_1|SEG`: ¿Evita usted ir o transitar por algunos de los siguientes lugares para no ser víctima de un delito o situación violenta?
  - `p22_2|SEG`: ¿Evita usted ir o transitar por algunos de los siguientes lugares para no ser víctima de un delito o situación violenta?
  - `p22_3|SEG`: ¿Evita usted ir o transitar por algunos de los siguientes lugares para no ser víctima de un delito o situación violenta?
  - _(+15 more)_

**`SEG__personal_crime_experience`** — Personal Crime Experience (9 questions)
  - `p9_1|SEG`: Según su experiencia y en relación a la delincuencia, dígame si se siente seguro o inseguro en su casa
  - `p9_2|SEG`: Según su experiencia y en relación a la delincuencia, dígame si se siente seguro o inseguro en su trabajo
  - `p9_3|SEG`: Según su experiencia y en relación a la delincuencia, dígame si se siente seguro o inseguro en la calle
  - _(+6 more)_

### SOC — sociedad de la informacion

**`SOC__digital_access`** — Access to Digital Technologies (6 questions)
  - `p1_1|SOC`: Con la palabra maíz, yo asocio comida, mercado, animales, ¿podría decirme tres palabras que asocie con la frase DESARROL
  - `p1_1a_1|SOC`: Con la palabra maíz, yo asocio comida, mercado, animales, ¿podría decirme tres palabras que asocie con la frase DESARROL
  - `p2|SOC`: En su opinión, ¿usted diría que los mexicanos tienen: mucho, algo, poco o nada  de acceso a las nuevas tecnologías (comp
  - _(+3 more)_

**`SOC__media_consumption`** — Media Consumption and Information Sources (45 questions)
  - `p5_1|SOC`: Por favor, ¿podría decirme si alguien en esta vivienda cuenta con radio?
  - `p5_2|SOC`: Por favor, ¿podría decirme si alguien en esta vivienda cuenta con televisión?
  - `p5_3|SOC`: Por favor, ¿podría decirme si alguien en esta vivienda cuenta con DVD/BluRay?
  - _(+42 more)_

**`SOC__digital_media_use`** — Use of Digital Media and Devices (15 questions)
  - `p23_1|SOC`: Para ver películas, ¿usted acostumbra comprar DVD/Bluray piratas?
  - `p23_2|SOC`: Para ver películas, ¿usted acostumbra rentar DVD/Bluray en videoclubs?
  - `p23_3|SOC`: Para ver películas, ¿usted acostumbra ir al cine?
  - _(+12 more)_

**`SOC__traditional_media`** — Traditional Media Usage (14 questions)
  - `p13|SOC`: ¿Ve usted televisión?
  - `p14|SOC`: ¿Con que frecuencia acostumbra ver televisión?
  - `p15|SOC`: ¿Aproximadamente cuántas horas a la semana ve televisión?
  - _(+11 more)_

**`SOC__perception_of_information`** — Perception and Awareness of Information (3 questions)
  - `p6|SOC`: En su opinión, ¿qué tanto considera que los mexicanos están informados sobre lo que sucede en el país?
  - `p7|SOC`: ¿Qué tan seguido acostumbras leer, ver o escuchar programas sobre lo que sucede en el país?
  - `p22|SOC`: De acuerdo a su experiencia, ¿usted considera que la publicidad que se presenta en los medios de comunicación es…?

## PRIORITY 3 — Uncertain Question Mappings (confidence < 0.7)  
Spot-check these 8 items. Each could belong to an alternative construct.

| Question ID | Text | Assigned Construct | Confidence |
|-------------|------|--------------------|------------|
| `p4_1|MIG` | Con la palabra maíz, yo asocio comida, mercado, animales. ¿Podría decirme, por f | `MIG__cultural_heritage` | 0.60 |
| `p8|MIG` | Con la palabra maíz, yo asocio comida, mercado, animales. ¿Podría decirme, por f | `MIG__cultural_heritage` | 0.60 |
| `p8_2|MIG` | Con la palabra maíz, yo asocio comida, mercado, animales. ¿Podría decirme, por f | `MIG__cultural_heritage` | 0.60 |
| `p9|ENV` | Por lo que usted ha visto, desde el año 2010 hasta hoy, ¿la situación general de | `ENV__age_perceptions` | 0.60 |
| `p10|ENV` | En su opinión, en 10 años, ¿la situación general de los adultos mayores en Méxic | `ENV__age_perceptions` | 0.60 |
| `p11|ENV` | Algunas personas creen que la población está envejeciendo. ¿En qué medida le pre | `ENV__age_perceptions` | 0.60 |
| `p23_1|SAL` | ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases? Cuando | `SAL__trust_in_health_system` | 0.60 |
| `p23_2|SAL` | ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes frases? Cuando | `SAL__trust_in_health_system` | 0.60 |

---
## How to Edit
- **Rename construct**: change `label` in the `constructs` array of `kg_ontology.json`
- **Reassign question**: change `construct` in a `questions` entry
- **Delete cross-domain link**: remove the entry from `relationships`
- **Merge constructs**: update all question `construct` fields, remove stale construct entry
- After editing, reload with: `from survey_kg import kg; kg.load_from_json('data/kg_ontology.json')`
