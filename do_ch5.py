import re

en_text_5 = """				<div type="version" xml:lang="en" subtype="translation">
					<head>Volume I, Part One, Chapter V</head>
					<p>Having thanked Anna Pávlovna for her <foreign xml:lang="fr" n="charming evening">charmante soirée</foreign>, the guests began to take their leave.</p>
					<p>Pierre was clumsy. Stout, above the average height, broad, with huge red hands, he did not know, as the saying is, how to enter a drawing room and still less how to leave one; that is, how to say something particularly agreeable before going away. Besides this, he was absent-minded. When rising, instead of his own, he caught up a three-cornered hat with a general's plume, and held it, pulling at the plume, till the general asked him to return it. But all his absent-mindedness and inability to enter a room and converse in it were redeemed by his expression of good nature, simplicity, and modesty. Anna Pávlovna turned to him and, with a Christian mildness expressing forgiveness for his outburst, nodded to him and said:</p>
					<p>— I hope to see you again, but I also hope you will change your opinions, my dear Monsieur Pierre, — she said.</p>
					<p>When she said this to him, he did not reply, but only bowed and once again showed everyone his smile, which said nothing except perhaps: "Opinions are opinions, but you see what a good, fine fellow I am." And everyone, including Anna Pávlovna, felt this involuntarily.</p>
					<p>Prince Andréi went out into the anteroom and, turning his shoulders to the footman who was putting his cloak on him, listened indifferently to his wife's chatter with Prince Hippolyte, who had also come into the anteroom. Prince Hippolyte stood close to the pretty, pregnant little princess, and stared fixedly at her through his lorgnette.</p>
					<p>— Go, Annette, you will catch cold, — the little princess was saying, taking leave of Anna Pávlovna. — <foreign xml:lang="fr" n="It is settled">C'est arrêté</foreign>, — she added softly.</p>
					<p>Anna Pávlovna had already managed to speak to Lise about the match she was planning between Anatole and the little princess's sister-in-law.</p>
					<p>— I rely on you, my dear friend, — Anna Pávlovna said also softly, — you will write to her and tell me <foreign xml:lang="fr" n="how the father will view the matter. Goodbye">comment le père envisagera la chose. Au revoir</foreign>, — and she left the anteroom.</p>
					<p>Prince Hippolyte approached the little princess and, bending his face close to hers, began whispering something to her.</p>
					<p>Two footmen, the princess's and his own, stood holding a shawl and a redingote, waiting for them to finish talking, and listened to their French babble, which they did not understand, with faces as though they understood what was being said but did not want to show it. The princess, as always, spoke smiling and listened laughing.</p>
					<p>— I am very glad I did not go to the ambassador's, — Prince Hippolyte was saying: — boredom... A beautiful evening, is it not, beautiful?</p>
					<p>— They say the ball will be very good, — answered the princess, drawing up her downy little lip. — All the beautiful women in society will be there.</p>
					<p>— Not all, because you will not be there; not all, — said Prince Hippolyte, laughing joyfully, and snatching the shawl from the footman, he even pushed him aside and began putting it on the princess. From awkwardness or intentionally (no one could have said which) he did not take his hands away for a long time when the shawl was already on, and seemed to be embracing the young woman.</p>
					<p>She gracefully, but still smiling, drew back, turned, and glanced at her husband. Prince Andréi's eyes were closed: he seemed so tired and sleepy.</p>
					<p>— Are you ready? — he asked his wife, looking past her.</p>
					<p>Prince Hippolyte hastily put on his redingote, which, in the new fashion, reached below his heels, and, getting tangled in it, ran out onto the porch after the princess, whom the footman was helping into the carriage.</p>
					<p>— <foreign xml:lang="fr" n="Princess, goodbye">Princesse, au revoir</foreign>, — he shouted, getting his tongue tangled as well as his feet.</p>
					<p>The princess, gathering up her dress, was taking her seat in the dark carriage; her husband was adjusting his saber; Prince Hippolyte, under the pretense of helping, was getting in everyone's way.</p>
					<p>— Al-low me, sir, — Prince Andréi addressed Prince Hippolyte in Russian, dryly and disagreeably, as Hippolyte was blocking his way.</p>
					<p>— I am waiting for you, Pierre, — the same voice of Prince Andréi said affectionately and tenderly.</p>
					<p>The postilion started, and the carriage wheels rattled. Prince Hippolyte laughed jerkily as he stood on the porch waiting for the vicomte, whom he had promised to take home.</p>
					<p>— <foreign xml:lang="fr" n="Well, my dear, your little princess is very nice! Very nice">Eh bien, mon cher, votre petite princesse est très bien, très bien</foreign>, — said the vicomte, having seated himself in the carriage with Hippolyte. — <foreign xml:lang="fr" n="But very nice">Mais très bien</foreign>. — He kissed his fingertips. — <foreign xml:lang="fr" n="And altogether French">Et tout-à-fait franèaise</foreign>.</p>
					<p>Hippolyte snorted and laughed.</p>
					<p>— <foreign xml:lang="fr" n="And do you know you are terrible with your innocent little air">Et savez-vous que vous êtes terrible avec votre petit air innocent</foreign>, — continued the vicomte. — <foreign xml:lang="fr" n="I pity the poor husband, that little officer, who gives himself the airs of a reigning prince">Je plains le pauvre mari, ce petit officier, qui se donne des airs de prince régnant</foreign>.</p>
					<p>Hippolyte snorted again and articulated through his laughter:</p>
					<p>— <foreign xml:lang="fr" n="And you were saying that Russian ladies were not worth French ones. One has to know how to set about it">Et vous disiez, que les dames russes ne valaient pas les dames franèaises. Il faut savoir s'y prendre</foreign>.</p>
					<p>Pierre, having arrived first, as a member of the household, went into Prince Andréi's study and immediately, from habit, lay down on the sofa, took the first book that came to hand from the shelf (it was Caesar's Commentaries), and, propping himself on his elbow, began reading it from the middle.</p>
					<p>— What have you done to M-lle Schérer? She will fall quite ill now, — said Prince Andréi, entering the study and rubbing his small, white hands.</p>
					<p>Pierre turned his whole body, making the sofa creak, turned his animated face to Prince Andréi, smiled, and waved his hand.</p>
					<p>— No, that Abbé is very interesting, only he does not understand the matter... In my opinion, perpetual peace is possible, but I do not know how to express it... But certainly not by a political balance...</p>
					<p>Prince Andréi was evidently not interested in these abstract conversations.</p>
					<p>— One cannot, <foreign xml:lang="fr" n="my dear">mon cher</foreign>, say everywhere all that one thinks. Well, have you finally decided on anything? Are you going to be a horse guardsman or a diplomat? — asked Prince Andréi after a moment's silence.</p>
					<p>Pierre sat up on the sofa, tucking his legs under him.</p>
					<p>— Can you imagine, I still don't know. Neither the one nor the other appeals to me.</p>
					<p>— But you must decide on something? Your father is waiting.</p>
					<p>Pierre had been sent abroad with an abbé tutor at the age of ten, and remained there till he was twenty. When he returned to Moscow, his father dismissed the abbé and said to the young man: "Now you go to Petersburg, look round, and choose. I agree to anything. Here is a letter to Prince Vasíli, and here is money for you. Write about everything, I will help you in everything." Pierre had been choosing a career for three months already and had done nothing. It was of this choice that Prince Andréi was speaking to him. Pierre rubbed his forehead.</p>
					<p>— But he must be a Freemason, — he said, referring to the Abbé he had met at the party.</p>
					<p>— All that is nonsense, — Prince Andréi stopped him again, — let us talk business. Have you been to the Horse Guards?...</p>
					<p>— No, I haven't, but this is what occurred to me, and I wanted to tell you. There is a war against Napoleon now. If it were a war for freedom, I could understand it, I should be the first to enter military service; but to help England and Austria against the greatest man in the world... that is not good...</p>
					<p>Prince Andréi only shrugged his shoulders at Pierre's childish remarks. He pretended that such stupidities could not be answered; but in fact it was difficult to answer this naive question with anything other than what Prince Andréi did answer.</p>
					<p>— If everyone fought only on their own convictions, there would be no war, — he said.</p>
					<p>— That would be splendid, — said Pierre.</p>
					<p>Prince Andréi smiled.</p>
					<p>— Very likely it would be splendid, but it will never happen...</p>
					<p>— Well, what are you going to war for? — asked Pierre.</p>
					<p>— What for? I don't know. It must be so. Besides, I am going... — He paused. — I am going because this life I lead here, this life — is not for me!</p>
				</div>"""

es_text_5 = """				<div type="version" xml:lang="es" subtype="translation-es">
					<head>Volumen I, Primera Parte, Capítulo V</head>
					<p>Tras dar las gracias a Anna Pávlovna por su <foreign xml:lang="fr" n="encantadora velada">charmante soirée</foreign>, los invitados empezaron a despedirse.</p>
					<p>Pierre era torpe. Robusto, de estatura superior a la media, ancho, con unas manos rojas enormes, no sabía, como suele decirse, entrar en un salón y menos aún salir de él; es decir, decir algo especialmente agradable antes de marcharse. Además, era distraído. Al levantarse, en vez del suyo, cogió un sombrero de tres picos con penacho de general, y lo sostuvo, tirando del penacho, hasta que el general le pidió que se lo devolviera. Pero toda su distracción y su incapacidad para entrar en un salón y conversar en él se veían redimidas por su expresión de buen natural, sencillez y modestia. Anna Pávlovna se volvió hacia él y, con una dulzura cristiana que expresaba el perdón por su exabrupto, asintió con la cabeza y le dijo:</p>
					<p>— Espero volver a verle, pero también espero que cambie usted de opinión, mi querido monsieur Pierre, — dijo ella.</p>
					<p>Cuando ella le dijo esto, él no respondió, sino que se limitó a hacer una reverencia y volvió a mostrar a todos su sonrisa, que no decía nada, salvo tal vez: "Las opiniones son opiniones, pero ya veis qué buen muchacho soy". Y todos, incluida Anna Pávlovna, lo sintieron involuntariamente.</p>
					<p>El príncipe Andréi salió a la antesala y, volviendo los hombros hacia el lacayo que le ponía la capa, escuchó con indiferencia la charla de su mujer con el príncipe Hippolyte, que también había salido a la antesala. El príncipe Hippolyte, de pie junto a la bella y embarazada princesita, la miraba fijamente a través de sus impertinentes.</p>
					<p>— Váyase, Annette, se va a resfriar, — decía la princesita, despidiéndose de Anna Pávlovna. — <foreign xml:lang="fr" n="Está decidido">C'est arrêté</foreign>, — añadió en voz baja.</p>
					<p>Anna Pávlovna ya había logrado hablar con Lise del enlace que planeaba entre Anatole y la cuñada de la princesita.</p>
					<p>— Confío en usted, mi querida amiga, — dijo también Anna Pávlovna en voz baja, — le escribirá y me dirá <foreign xml:lang="fr" n="cómo verá el asunto el padre. Adiós">comment le père envisagera la chose. Au revoir</foreign>, — y salió de la antesala.</p>
					<p>El príncipe Hippolyte se acercó a la princesita y, acercando el rostro al de ella, empezó a susurrarle algo.</p>
					<p>Dos lacayos, el de la princesa y el suyo, que sostenían un chal y un redingote, esperaban a que terminaran de hablar, y escuchaban su balbuceo en francés, que no entendían, con cara de entender lo que se decía, pero sin querer demostrarlo. La princesa, como siempre, hablaba sonriendo y escuchaba riendo.</p>
					<p>— Me alegro mucho de no haber ido a casa del embajador, — decía el príncipe Hippolyte: — aburrimiento... Una velada hermosa, ¿verdad, hermosa?</p>
					<p>— Dicen que el baile será muy bueno, — contestó la princesa, frunciendo su labio velludo. — Todas las mujeres hermosas de la sociedad estarán allí.</p>
					<p>— No todas, porque no estará usted; no todas, — dijo el príncipe Hippolyte, riendo alegremente, y arrebatándole el chal al lacayo, incluso le apartó de un empujón y empezó a ponérselo a la princesa. Por torpeza o intencionadamente (nadie sabría decirlo) no apartó las manos durante mucho tiempo cuando ya tenía puesto el chal, y pareció abrazar a la joven.</p>
					<p>Ella retrocedió con gracia, pero sin dejar de sonreír, se dio la vuelta y miró a su marido. El príncipe Andréi tenía los ojos cerrados: parecía muy cansado y soñoliento.</p>
					<p>— ¿Estás lista? — preguntó a su mujer, mirando más allá de ella.</p>
					<p>El príncipe Hippolyte se puso apresuradamente su redingote, que, según la nueva moda, le llegaba por debajo de los talones, y, enredándose en él, salió corriendo al porche tras la princesa, a la que el lacayo ayudaba a subir al carruaje.</p>
					<p>— <foreign xml:lang="fr" n="Princesa, adiós">Princesse, au revoir</foreign>, — gritó él, enredándosele la lengua además de los pies.</p>
					<p>La princesa, recogiéndose el vestido, tomaba asiento en la oscuridad del carruaje; su marido se ajustaba el sable; el príncipe Hippolyte, con el pretexto de ayudar, se interponía en el camino de todos.</p>
					<p>— Per-mítame, señor, — se dirigió el príncipe Andréi al príncipe Hippolyte en ruso, con sequedad y desagrado, ya que Hippolyte le bloqueaba el paso.</p>
					<p>— Le espero, Pierre, — dijo la misma voz del príncipe Andréi con afecto y ternura.</p>
					<p>El postillón arrancó y las ruedas del carruaje traquetearon. El príncipe Hippolyte se rió a sacudidas mientras estaba de pie en el porche esperando al vizconde, a quien había prometido llevar a casa.</p>
					<p>— <foreign xml:lang="fr" n="¡Bueno, amigo mío, su princesita es muy agradable! Muy agradable">Eh bien, mon cher, votre petite princesse est très bien, très bien</foreign>, — dijo el vizconde, habiéndose sentado en el carruaje con Hippolyte. — <foreign xml:lang="fr" n="Pero muy agradable">Mais très bien</foreign>. — Se besó las puntas de los dedos. — <foreign xml:lang="fr" n="Y totalmente francesa">Et tout-à-fait franèaise</foreign>.</p>
					<p>Hippolyte resopló y se echó a reír.</p>
					<p>— <foreign xml:lang="fr" n="Y sabe usted que es terrible con su airecito inocente">Et savez-vous que vous êtes terrible avec votre petit air innocent</foreign>, — continuó el vizconde. — <foreign xml:lang="fr" n="Compadezco al pobre marido, a ese oficialito, que se da aires de príncipe reinante">Je plains le pauvre mari, ce petit officier, qui se donne des airs de prince régnant</foreign>.</p>
					<p>Hippolyte volvió a resoplar y articuló a través de su risa:</p>
					<p>— <foreign xml:lang="fr" n="Y usted decía que las damas rusas no valían lo que las francesas. Hay que saber cómo hacerlo">Et vous disiez, que les dames russes ne valaient pas les dames franèaises. Il faut savoir s'y prendre</foreign>.</p>
					<p>Pierre, habiendo llegado el primero, como miembro de la casa, entró en el despacho del príncipe Andréi e inmediatamente, por costumbre, se tumbó en el sofá, cogió el primer libro que le vino a la mano de la estantería (eran los Comentarios de César) y, apoyándose en el codo, empezó a leerlo por la mitad.</p>
					<p>— ¿Qué le ha hecho a M-lle Schérer? Ahora caerá bastante enferma, — dijo el príncipe Andréi, entrando en el despacho y frotándose las manitas blancas.</p>
					<p>Pierre giró todo el cuerpo, haciendo crujir el sofá, volvió su rostro animado hacia el príncipe Andréi, sonrió y agitó la mano.</p>
					<p>— No, ese abate es muy interesante, sólo que no comprende el asunto... En mi opinión, la paz perpetua es posible, pero no sé cómo expresarlo... Pero desde luego no mediante un equilibrio político...</p>
					<p>El príncipe Andréi, evidentemente, no estaba interesado en estas conversaciones abstractas.</p>
					<p>— No se puede, <foreign xml:lang="fr" n="amigo mío">mon cher</foreign>, decir en todas partes todo lo que uno piensa. Bueno, ¿se ha decidido finalmente por algo? ¿Va a ser usted guardia de corps o diplomático? — preguntó el príncipe Andréi tras un momento de silencio.</p>
					<p>Pierre se incorporó en el sofá y metió las piernas debajo.</p>
					<p>— ¿Se imagina usted que todavía no lo sé? No me atrae ni lo uno ni lo otro.</p>
					<p>— ¿Pero debe decidirse por algo? Su padre está esperando.</p>
					<p>Pierre había sido enviado al extranjero con un tutor abate a la edad de diez años, y permaneció allí hasta los veinte. Cuando regresó a Moscú, su padre despidió al abate y dijo al joven: "Ahora vete a Petersburgo, mira a tu alrededor y elige. Estoy de acuerdo con cualquier cosa. Aquí tienes una carta para el príncipe Vasíli, y aquí tienes dinero. Escríbeme sobre todo, te ayudaré en todo". Pierre llevaba ya tres meses eligiendo carrera y no había hecho nada. De esta elección le hablaba el príncipe Andréi. Pierre se frotó la frente.</p>
					<p>— Pero debe de ser masón, — dijo, refiriéndose al abate que había conocido en la fiesta.</p>
					<p>— Todo eso son tonterías, — le atajó de nuevo el príncipe Andréi, — hablemos de negocios. ¿Ha estado usted en la Guardia a Caballo?...</p>
					<p>— No, no he estado, pero se me ha ocurrido esto, y quería decírselo. Ahora hay una guerra contra Napoleón. Si fuera una guerra por la libertad, lo comprendería, sería el primero en entrar en el servicio militar; pero ayudar a Inglaterra y a Austria contra el hombre más grande del mundo... eso no está bien...</p>
					<p>El príncipe Andréi se limitó a encogerse de hombros ante los comentarios infantiles de Pierre. Fingió que tales estupideces no se podían contestar; pero, de hecho, era difícil contestar a esta ingenua pregunta con otra cosa que no fuera lo que contestó el príncipe Andréi.</p>
					<p>— Si todos lucharan sólo por sus propias convicciones, no habría guerra, — dijo.</p>
					<p>— Eso sería espléndido, — dijo Pierre.</p>
					<p>El príncipe Andréi sonrió.</p>
					<p>— Es muy probable que fuera espléndido, pero nunca sucederá...</p>
					<p>— Bueno, ¿para qué vas tú a la guerra? — preguntó Pierre.</p>
					<p>— ¿Para qué? No lo sé. Debe ser así. Además, me voy... — Hizo una pausa. — ¡Me voy porque esta vida que llevo aquí, esta vida, no es para mí!</p>
				</div>"""

with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

ch5_start = text.find('<div type="version" xml:lang="ru" subtype="original">', text.find('<div type="chapter" n="5">'))
text = text[:ch5_start] + en_text_5 + '\n' + es_text_5 + '\n' + text[ch5_start:]

with open('tei-source/2600-full.xml', 'w', encoding='utf-8') as f:
    f.write(text)
