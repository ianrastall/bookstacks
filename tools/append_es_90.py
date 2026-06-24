import os
import xml.etree.ElementTree as ET

NS = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'xml': 'http://www.w3.org/XML/1998/namespace'
}

def register_all_namespaces():
    ET.register_namespace('', 'http://www.tei-c.org/ns/1.0')
    ET.register_namespace('xml', 'http://www.w3.org/XML/1998/namespace')

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    es_file = os.path.join(repo_root, 'tei-source', '2600-es.xml')
    
    register_all_namespaces()
    tree = ET.parse(es_file)
    root = tree.getroot()
    body = root.find('.//tei:body', NS)
    
    # Check if Chapter 90 exists
    chap = root.find('.//tei:div[@type="chapter"][@n="90"]', NS)
    if chap is not None:
        print("Chapter 90 already exists!")
        return

    # XML for Chapter 90
    chapter_xml = """<div type="chapter" n="90" xmlns="http://www.tei-c.org/ns/1.0">
  <head>Volume II, Part Two, Chapter XI</head>
  <div type="version" xml:lang="es" subtype="translation">
<p>En el estado de ánimo más feliz, regresando de su viaje por el sur, <persName ref="#pierre">Pierre</persName> cumplió su antigua intención de visitar a su amigo <persName ref="#andrew">Bolkonsky</persName>, a quien no había visto en dos años.</p>

<p><placeName ref="#bogucharovo">Bogucharovo</placeName> estaba en una zona fea y plana, cubierta de campos y bosques de abetos y abedules, algunos talados y otros no. El patio de la hacienda se encontraba al final de un pueblo situado en línea recta a lo largo del camino principal, detrás de un estanque recién excavado y rebosante, con orillas aún sin hierba, en medio de un bosque joven donde se alzaban algunos pinos grandes.</p>

<p>El patio de la hacienda constaba de una era, dependencias, caballerizas, una casa de baños, un ala menor y una gran casa de piedra con un frontón semicircular que aún estaba en construcción. Alrededor de la casa había un jardín recién plantado. Las cercas y portones eran fuertes y nuevos; bajo un cobertizo había dos bombas de incendio y un barril pintado de verde; los caminos eran rectos, los puentes sólidos y con barandillas. Todo llevaba el sello del orden y la buena administración. Los siervos que encontró, al preguntarles dónde vivía el príncipe, le indicaron un ala pequeña y nueva, construida justo al borde del estanque. El viejo tutor del príncipe <persName ref="#andrew">Andrey</persName>, <persName ref="#anton">Anton</persName>, ayudó a <persName ref="#pierre">Pierre</persName> a bajar del carruaje, le dijo que el príncipe estaba en casa y lo condujo a un recibidor pequeño y limpio.</p>

<p>A <persName ref="#pierre">Pierre</persName> le sorprendió la modestia de aquella casita, limpia pero pequeña, después de las espléndidas condiciones en las que había visto a su amigo por última vez en <placeName ref="#st-petersburg">Petersburgo</placeName>. Entró apresuradamente en una sala pequeña, aún sin enyesar y que olía a pino, y quiso seguir adelante, pero <persName ref="#anton">Anton</persName> se adelantó de puntillas y llamó a la puerta.</p>

<p>— ¿Qué hay? — se oyó una voz áspera y desagradable.</p>

<p>— Una visita — respondió <persName ref="#anton">Anton</persName>.</p>

<p>— Pídele que espere — y se oyó cómo apartaban una silla. <persName ref="#pierre">Pierre</persName> caminó rápidamente hacia la puerta y se encontró cara a cara con el príncipe <persName ref="#andrew">Andrey</persName>, quien salía a su encuentro, con el ceño fruncido y envejecido. <persName ref="#pierre">Pierre</persName> lo abrazó y, levantándose los anteojos, lo besó en las mejillas mirándolo de cerca.</p>

<p>— No me lo esperaba, me alegro mucho — dijo el príncipe <persName ref="#andrew">Andrey</persName>. <persName ref="#pierre">Pierre</persName> no dijo nada; miraba a su amigo con asombro, sin apartar los ojos de él. Le sorprendía el cambio que se había operado en el príncipe <persName ref="#andrew">Andrey</persName>. Las palabras eran cariñosas, había una sonrisa en sus labios y en su rostro, pero la mirada estaba apagada, muerta; una mirada a la que, a pesar de su evidente deseo, el príncipe <persName ref="#andrew">Andrey</persName> no lograba dar un brillo de alegría y animación. No es que su amigo hubiera adelgazado, palidecido o madurado; pero aquella mirada y la arruga de su frente, que expresaba una larga concentración en una sola cosa, sorprendieron a <persName ref="#pierre">Pierre</persName> y lo distanciaron, hasta que se acostumbró a ellas.</p>

<p>Al encontrarse tras una larga separación, como siempre ocurre, la conversación no logró fijarse por mucho tiempo; preguntaban y respondían brevemente sobre cosas que ambos sabían que requerirían largas charlas. Finalmente, la conversación comenzó a centrarse poco a poco en lo que antes se había mencionado fragmentariamente: preguntas sobre su vida pasada, planes para el futuro, el viaje de <persName ref="#pierre">Pierre</persName>, sus ocupaciones, la guerra, etc. Aquella concentración y abatimiento que <persName ref="#pierre">Pierre</persName> había notado en la mirada del príncipe <persName ref="#andrew">Andrey</persName> se expresaba ahora aún más intensamente en la sonrisa con la que escuchaba a <persName ref="#pierre">Pierre</persName>, sobre todo cuando este hablaba con alegre entusiasmo sobre el pasado o el futuro. Era como si el príncipe <persName ref="#andrew">Andrey</persName> deseara participar en lo que decía, pero no pudiera. <persName ref="#pierre">Pierre</persName> comenzó a sentir que ante el príncipe <persName ref="#andrew">Andrey</persName> el entusiasmo, los sueños, las esperanzas de felicidad y de bien estaban fuera de lugar. Le daba vergüenza expresar todos sus nuevos pensamientos masónicos, especialmente los que su último viaje había renovado y despertado en él. Se contenía, temeroso de parecer ingenuo; pero al mismo tiempo sentía un deseo incontenible de mostrar cuanto antes a su amigo que ahora era otro, un <persName ref="#pierre">Pierre</persName> mejor que aquel de <placeName ref="#st-petersburg">Petersburgo</placeName>.</p>

<p>— No te imaginas cuánto he vivido durante este tiempo. Ni yo mismo me reconocería.</p>

<p>— Sí, hemos cambiado mucho, mucho desde entonces — dijo el príncipe <persName ref="#andrew">Andrey</persName>.</p>

<p>— Bueno, ¿y tú? — preguntó <persName ref="#pierre">Pierre</persName> —. ¿Cuáles son tus planes?</p>

<p>— ¿Planes? — repitió irónicamente el príncipe <persName ref="#andrew">Andrey</persName> —. ¿Mis planes? — repitió, como si le sorprendiera el significado de semejante palabra —. Pues ya ves, estoy construyendo; el año que viene quiero mudarme definitivamente...</p>

<p><persName ref="#pierre">Pierre</persName> miró en silencio y con fijeza el rostro envejecido de <persName ref="#andrew">Andrey</persName>.</p>

<p>— No, te pregunto — dijo <persName ref="#pierre">Pierre</persName>... — pero el príncipe <persName ref="#andrew">Andrey</persName> lo interrumpió:</p>

<p>— Pero ¿qué se puede decir de mí?... Cuéntame tú, cuéntame de tu viaje, de todo lo que has hecho por allí en tus haciendas.</p>

<p><persName ref="#pierre">Pierre</persName> empezó a relatar lo que había hecho en sus propiedades, intentando ocultar en la medida de lo posible su propia participación en las mejoras introducidas. El príncipe <persName ref="#andrew">Andrey</persName> se anticipaba varias veces al relato de <persName ref="#pierre">Pierre</persName>, como si todo lo que este hubiera hecho fuera una historia conocida desde hacía tiempo, y escuchaba no solo sin interés, sino casi como si se avergonzara de lo que <persName ref="#pierre">Pierre</persName> contaba.</p>

<p>A <persName ref="#pierre">Pierre</persName> le resultó incómodo y hasta penoso estar en compañía de su amigo. Se quedó callado.</p>

<p>— Oye, alma mía — dijo el príncipe <persName ref="#andrew">Andrey</persName>, a quien también se le hacía evidentemente difícil y embarazosa la situación con su invitado —, aquí estoy como en un campamento, sólo he venido a echar un vistazo. Hoy mismo vuelvo a casa de mi hermana. Te presentaré con ella. Ah, me parece que ya la conoces — dijo, tratando visiblemente de entretener a un invitado con quien ahora no sentía tener nada en común —. Iremos después de cenar. Y ahora, ¿quieres ver mi hacienda? — Salieron y pasearon hasta la hora de cenar, charlando sobre noticias políticas y conocidos en común, como personas poco cercanas. El príncipe <persName ref="#andrew">Andrey</persName> hablaba con cierta animación e interés únicamente sobre su nueva hacienda y las construcciones; pero incluso allí, en medio de la conversación, sobre los andamios, cuando describía a <persName ref="#pierre">Pierre</persName> la futura distribución de la casa, se detuvo de repente —. De todos modos, aquí no hay nada interesante; vamos a cenar y nos vamos. — Durante la cena, la conversación recayó en el matrimonio de <persName ref="#pierre">Pierre</persName>.</p>

<p>— Me sorprendió mucho cuando me enteré — dijo el príncipe <persName ref="#andrew">Andrey</persName>.</p>

<p><persName ref="#pierre">Pierre</persName> se sonrojó, como siempre le ocurría con ese tema, y se apresuró a decir:</p>

<p>— Algún día te contaré cómo pasó todo. Pero ya sabes que se ha acabado, y para siempre.</p>

<p>— ¿Para siempre? — dijo el príncipe <persName ref="#andrew">Andrey</persName> —. Nada ocurre para siempre.</p>

<p>— Pero ¿sabes cómo terminó todo? ¿Te enteraste del duelo?</p>

<p>— Sí, también has pasado por eso.</p>

<p>— Lo único por lo que le doy gracias a Dios es por no haber matado a ese hombre — dijo <persName ref="#pierre">Pierre</persName>.</p>

<p>— ¿Por qué? — dijo el príncipe <persName ref="#andrew">Andrey</persName> —. Matar a un perro rabioso está muy bien.</p>

<p>— No, matar a un hombre no está bien, es injusto...</p>

<p>— ¿Por qué injusto? — repitió el príncipe <persName ref="#andrew">Andrey</persName> —; decidir lo que es justo o injusto no les está dado a los hombres. Los hombres se han equivocado siempre y seguirán equivocándose, y en nada se equivocan tanto como en lo que consideran justo o injusto.</p>

<p>— Injusto es aquello que representa un mal para otro hombre — dijo <persName ref="#pierre">Pierre</persName>, sintiendo con satisfacción que, por primera vez desde su llegada, el príncipe <persName ref="#andrew">Andrey</persName> se animaba, empezaba a hablar y deseaba expresar todo lo que le había convertido en lo que era ahora.</p>

<p>— ¿Y quién te ha dicho qué es el mal para otro hombre? — preguntó él.</p>

<p>— ¿El mal? ¿El mal? — dijo <persName ref="#pierre">Pierre</persName> —, todos sabemos qué es el mal para nosotros mismos.</p>

<p>— Sí, lo sabemos, pero el mal que yo conozco para mí, no se lo puedo causar a otro hombre — dijo el príncipe <persName ref="#andrew">Andrey</persName>, animándose cada vez más, deseando evidentemente exponerle a <persName ref="#pierre">Pierre</persName> su nueva visión de las cosas. Hablaba en francés. <foreign xml:lang="fr" n="En la vida solo conozco dos desgracias muy reales: el remordimiento y la enfermedad. No existe más bien que la ausencia de estos males.">Je ne connais dans la vie que maux bien réels: c'est le remord et la maladie. Il n'est de bien que l'absence de ces maux.</foreign> Vivir para mí mismo, evitando solo estos dos males: en eso consiste toda mi sabiduría ahora.</p>

<p>— ¿Y qué hay del amor al prójimo y el sacrificio personal? — comenzó <persName ref="#pierre">Pierre</persName> —. ¡No, no puedo estar de acuerdo contigo! Vivir solo para no hacer el mal, para no tener de qué arrepentirse, es muy poco. Yo he vivido así, he vivido para mí, y arruiné mi vida. Y solo ahora, cuando vivo, o al menos lo intento — se corrigió <persName ref="#pierre">Pierre</persName> por modestia —, vivir para los demás, solo ahora he comprendido toda la felicidad de la vida. No, no estoy de acuerdo contigo, y tú mismo no crees lo que estás diciendo. — El príncipe <persName ref="#andrew">Andrey</persName> miraba a <persName ref="#pierre">Pierre</persName> en silencio, con una sonrisa burlona.</p>

<p>— Ya verás a mi hermana, la princesa <persName ref="#princess-mary">Marya</persName>. Te llevarás bien con ella — dijo él —. Puede que tengas razón para ti — continuó tras una pausa —, pero cada uno vive a su manera: tú has vivido para ti y dices que por poco arruinas tu vida, y que has conocido la felicidad solo al empezar a vivir para los demás. Yo he experimentado lo contrario. Yo viví para la gloria. (Porque, ¿qué es la gloria? Es el mismo amor hacia los demás, el deseo de hacer algo por ellos, el anhelo de sus alabanzas). Así que viví para los demás, y no es que estuviera a punto, sino que arruiné por completo mi vida. Y desde entonces me siento más tranquilo, porque vivo solo para mí.</p>

<p>— ¿Pero cómo se puede vivir solo para uno mismo? — preguntó <persName ref="#pierre">Pierre</persName> acaloradamente —. ¿Y tu hijo, y tu hermana, y tu padre?</p>

<p>— Todo eso sigo siendo yo, no son "los demás" — dijo el príncipe <persName ref="#andrew">Andrey</persName> —, mientras que los demás, los <emph>prójimos</emph>, <foreign xml:lang="fr" n="el prójimo">le prochain</foreign>, como los llamáis tú y la princesa <persName ref="#princess-mary">Marya</persName>, son la principal fuente de error y maldad. <foreign xml:lang="fr" n="El prójimo">Le prochain</foreign> son esos siervos de Kiev tuyos, a los que quieres hacer el bien.</p>

<p>Y miró a <persName ref="#pierre">Pierre</persName> con una mirada de burla y desafío. Evidentemente, lo estaba provocando.</p>

<p>— Estás bromeando — dijo <persName ref="#pierre">Pierre</persName>, animándose más y más —. ¿Qué error o qué mal puede haber en que yo deseara (lo he hecho muy poco y mal), pero deseara hacer el bien, y que haya hecho, al menos, alguna cosa? ¿Qué mal puede haber en que personas desdichadas, nuestros campesinos, personas como nosotros, que crecen y mueren sin más idea de Dios y de la verdad que ritos y rezos sin sentido, sean instruidas en las consoladoras creencias de una vida futura, de la recompensa y el consuelo? ¿Qué mal y qué error puede haber en que la gente muera de enfermedades, sin atención, cuando es tan fácil ayudarles materialmente, y yo les proporcione un médico, un hospital y un asilo para la vejez? ¿Acaso no es un bien palpable, indudable, que un campesino, o una mujer con su hijo no tengan descanso ni de día ni de noche, y yo les dé reposo y tiempo libre?... — decía <persName ref="#pierre">Pierre</persName>, dándose prisa y ceceando —. Y esto lo he hecho, aunque mal y poco, pero he hecho algo; y no solo no vas a disuadirme de que lo que he hecho está bien, sino que tampoco vas a disuadirme de que tú mismo no piensas igual. Y lo más importante — continuó <persName ref="#pierre">Pierre</persName> —, esto es lo que sé y lo sé con certeza: que el placer de hacer este bien es la única felicidad verdadera en la vida.</p>

<p>— Claro, si planteas la cuestión de ese modo, es otra cosa — dijo el príncipe <persName ref="#andrew">Andrey</persName> —. Yo construyo una casa, planto un jardín, y tú construyes hospitales. Ambas cosas pueden servir para pasar el tiempo. Pero en cuanto a lo que es justo y lo que es bueno... deja que lo juzgue quien todo lo sabe, y no nosotros. Bueno, ya que quieres discutir — añadió —, adelante. — Se levantaron de la mesa y se sentaron en el porche, que hacía las veces de balcón.</p>

<p>— Muy bien, vamos a discutir — dijo el príncipe <persName ref="#andrew">Andrey</persName> —. Hablas de escuelas — prosiguió doblando un dedo —, instrucción y demás; es decir, quieres sacarle — dijo, señalando a un campesino que pasaba y se quitaba el sombrero — de su estado animal y darle necesidades morales; pero a mí me parece que la única felicidad posible es la felicidad animal, y tú se la quieres quitar. Yo le envidio, y tú quieres convertirlo en mí, pero sin darle mis recursos. También dices que quieres aliviarle el trabajo. Pero a mi modo de ver, el trabajo físico es para él una necesidad tan imperiosa, una condición de existencia tan vital, como lo es para ti y para mí el trabajo mental. Tú no puedes dejar de pensar. Yo me acuesto a las tres de la madrugada, me vienen pensamientos y no puedo dormir, doy vueltas en la cama, sin pegar ojo hasta la mañana porque pienso y no puedo evitar pensar, del mismo modo que él no puede evitar arar o segar; de lo contrario irá a la taberna o enfermará. Así como yo no podría soportar su terrible trabajo físico y me moriría en una semana, él no soportaría mi ociosidad física: engordaría y moriría. Y lo tercero... ¿qué más has dicho?</p>

<p>El príncipe <persName ref="#andrew">Andrey</persName> dobló su tercer dedo.</p>

<p>— Ah, sí, hospitales, medicinas. Le da un ataque, se está muriendo, y tú vas y le sangras, le curas. Se quedará cojo y arrastrará diez años su existencia, siendo una carga para todos. Es mucho más tranquilo y sencillo para él morir. Nacerán otros, y ya son muchos. Si lamentaras haber perdido un peón de más... así es como yo lo veo; pero tú quieres curarlo por el amor que le tienes. Y él no necesita eso. Además, ¡qué ilusión creer que la medicina ha curado a alguien alguna vez! Matar, ¡eso sí! — dijo frunciendo el ceño con enfado y apartándose de <persName ref="#pierre">Pierre</persName>.</p>

<p>El príncipe <persName ref="#andrew">Andrey</persName> exponía sus pensamientos con tal claridad y precisión que resultaba evidente que había reflexionado sobre ello más de una vez, y hablaba rápida y gustosamente, como alguien que lleva mucho tiempo sin hablar. Su mirada se animaba tanto más cuanto más desesperanzados eran sus juicios.</p>

<p>— ¡Oh, esto es horrible, horrible! — dijo <persName ref="#pierre">Pierre</persName> —. Sencillamente no comprendo cómo puedes vivir con semejantes pensamientos. A mí también me han asaltado momentos así, no hace mucho, en Moscú y durante el viaje, pero entonces me hundo hasta el punto de no sentirme vivo, todo me da asco... y, sobre todo, yo mismo. Entonces ni como, ni me lavo... pero tú, ¿qué?...</p>

<p>— ¿Por qué no lavarse? No es higiénico — dijo el príncipe <persName ref="#andrew">Andrey</persName> —; por el contrario, hay que intentar hacer la vida lo más agradable posible. Yo vivo y no tengo la culpa de ello, así que debo vivir de la mejor manera que pueda, hasta que llegue la muerte, sin molestar a nadie.</p>

<p>— ¿Pero qué te motiva a vivir con esas ideas? Te quedarás sentado sin moverte, sin emprender nada...</p>

<p>— La vida tampoco te deja en paz. Me gustaría no hacer nada, pero fíjate: por un lado, la nobleza de aquí me ha hecho el honor de elegirme mariscal; a duras penas pude zafarme. No lograban comprender que me falta lo necesario, esa consabida vulgaridad bonachona y atareada indispensable para ese puesto. Luego esta casa, que tuve que construir para tener un rincón propio donde estar tranquilo. Y ahora la milicia.</p>

<p>— ¿Por qué no sirves en el ejército?</p>

<p>— ¡Después de <placeName ref="#austerlitz">Austerlitz</placeName>! — dijo sombríamente el príncipe <persName ref="#andrew">Andrey</persName> —. No; muchas gracias, me he prometido a mí mismo no servir en el ejército ruso activo. Y no lo haría, aunque <persName ref="#bonaparte">Bonaparte</persName> estuviera aquí al lado, en <placeName ref="#smolensk">Smolensk</placeName>, amenazando a <placeName ref="#bald_hills">Bald Hills</placeName>, ni siquiera entonces serviría en el ejército ruso. Bueno, como te decía — prosiguió el príncipe <persName ref="#andrew">Andrey</persName>, calmándose —. Ahora la milicia; mi padre es comandante en jefe del tercer distrito, y el único medio que tengo para librarme del servicio es estar a sus órdenes.</p>

<p>— ¿Así que estás sirviendo?</p>

<p>— Sirvo. — Se quedó callado un momento.</p>

<p>— Entonces, ¿por qué sirves?</p>

<p>— Pues por esto. Mi padre es uno de los hombres más notables de su siglo. Pero envejece, y no es que sea cruel, sino que tiene un carácter demasiado activo. Es temible por su costumbre al poder absoluto, y ahora con la autoridad que el <persName ref="#emperor-alexander">soberano</persName> le ha conferido como comandante en jefe de la milicia. Si yo me hubiera retrasado dos horas hace quince días, habría mandado ahorcar al archivero en <placeName ref="#yukhnov">Yukhnov</placeName> — dijo el príncipe <persName ref="#andrew">Andrey</persName> con una sonrisa —; así que sirvo porque, aparte de mí, nadie tiene influencia sobre mi padre, y así en ocasiones lo salvaré de cometer actos que luego le remorderían.</p>

<p>— ¡Ah, ya ves!</p>

<p>— Sí, <foreign xml:lang="fr" n="pero no de la manera que piensas,">mais ce n'est pas comme vous l'entendez,</foreign> — prosiguió el príncipe <persName ref="#andrew">Andrey</persName> —. Yo no le deseaba ni le deseo el menor bien a ese canalla de archivero, que robó unas botas a los milicianos; incluso me habría alegrado mucho verle ahorcado, pero me da lástima mi padre, es decir, de nuevo yo mismo.</p>

<p>El príncipe <persName ref="#andrew">Andrey</persName> se animaba más y más. Sus ojos brillaban febrilmente mientras se esforzaba por demostrar a <persName ref="#pierre">Pierre</persName> que en sus actos jamás hubo la menor intención de hacer el bien al prójimo.</p>

<p>— Oye, tú quieres emancipar a los campesinos — continuó —. Está muy bien; pero no para ti (supongo que no habrás azotado a nadie ni enviado a nadie a Siberia), y menos aún para los campesinos. Si los golpean, los azotan y los envían a Siberia, creo que a ellos no les va a ir peor por eso. En Siberia seguirán llevando su misma vida bestial, y las cicatrices del cuerpo se curarán, y serán tan felices como lo eran antes. Esto es necesario para aquellas personas que perecen moralmente, que acumulan remordimientos, que los reprimen y se vuelven insensibles por tener la capacidad de castigar con o sin razón. De esos es de quienes me compadezco, y por ellos querría liberar a los siervos. Tú quizá no lo hayas visto, pero yo he visto a personas buenas, educadas en estas tradiciones de poder absoluto, que, con el paso de los años, al volverse más irritables, se hacen crueles, brutales, lo saben, no pueden contenerse y se vuelven cada vez más desdichadas.</p>

<p>El príncipe <persName ref="#andrew">Andrey</persName> dijo todo esto con tanta pasión que <persName ref="#pierre">Pierre</persName> pensó instintivamente que estas ideas le habían sido sugeridas por su padre. No respondió nada.</p>

<p>— Así pues, de quienes me compadezco es de la dignidad humana, la tranquilidad de conciencia y la pureza; y no de sus espaldas y sus frentes, que, por mucho que las azoten y por mucho que las afeiten, seguirán siendo las mismas espaldas y frentes.</p>

<p>— ¡No, no y mil veces no! Jamás estaré de acuerdo contigo — dijo <persName ref="#pierre">Pierre</persName>.</p>
  </div>
</div>"""
    
    chapter_elem = ET.fromstring(chapter_xml)
    
    # insert chapter in correct order
    chapters = body.findall('tei:div[@type="chapter"]', NS)
    insert_idx = len(chapters)
    for i, c in enumerate(chapters):
        if int(c.get('n')) > 90:
            insert_idx = i
            break
            
    body.insert(insert_idx, chapter_elem)
    
    # Save the file back
    tree.write(es_file, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    main()
