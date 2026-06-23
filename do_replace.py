import re

with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

# We only want to replace in Chapter 1 English and Spanish tabs.
ch1_start = text.find('<div type="chapter" n="1">')
ch1_end = text.find('<div type="chapter" n="2">')

ch1_text = text[ch1_start:ch1_end]

mappings = [
    ("Eh bien, mon prince. Gênes et Lucques ne sont plus que des apanages, des propriétés, de la famille Buonaparte. Non, je vous préviens, que si vous ne me dites pas, que nous avons la guerre, si vous vous permettez encore de pallier toutes les infamies, toutes les atrocités de cet Antichrist (ma parole, j'y crois) — je ne vous connais plus, vous n'êtes plus mon ami, vous n'êtes plus mon fidèle esclave, comme vous dites.",
     "Well, Prince, so Genoa and Lucca are now nothing more than appanages, estates, of the Buonaparte family. No, I warn you: if you do not tell me that we are at war, if you still permit yourself to gloss over all the infamies, all the atrocities of this Antichrist (upon my word, I believe in him) — then I no longer know you, you are no longer my friend, you are no longer my faithful slave, as you call yourself.",
     "Bueno, príncipe, así que Génova y Lucca ahora no son más que infantazgos, propiedades, de la familia Buonaparte. No, le advierto: si no me dice que estamos en guerra, si todavía se permite encubrir todas las infamias, todas las atrocidades de este Anticristo (palabra de honor, creo en él) — entonces ya no le conozco, ya no es mi amigo, ya no es mi fiel esclavo, como usted mismo se llama."),
    
    ("Je vois que je vous fais peur", "I see that I am frightening you", "Veo que le estoy asustando"),
    
    ("\"Si vous n'avez rien de mieux à faire, M. le comte (ou mon prince), et si la perspective de passer la soirée chez une pauvre malade ne vous effraye pas trop, je serai charmée de vous voir chez moi entre 7 et 10 heures. Annette Scherer\".",
     "\"If you have nothing better to do, Monsieur le Comte (or my Prince), and if the prospect of spending an evening with a poor invalid does not alarm you too greatly, I shall be charmed to see you at my house between 7 and 10 o'clock. Annette Schérer.\"",
     "\"Si no tiene nada mejor que hacer, señor Conde (o mi Príncipe), y si la perspectiva de pasar una velada con una pobre enferma no le alarma demasiado, me encantaría verle en mi casa entre las 7 y las 10. Annette Schérer.\""),

    ("Dieu, quelle virulente sortie!", "Heavens, what a virulent sally!", "¡Cielos, qué virulenta embestida!"),
    ("Avant tout dites moi, comment vous allez, chère amie?", "Before all else, tell me how you are, dear friend.", "Antes de nada, dígame cómo está, querida amiga."),
    ("Je vous avoue que toutes ces fêtes et tous ces feux d'artifice commencent à devenir insipides.", "I confess that all these fêtes and fireworks are beginning to grow insipid.", "Confieso que todas estas fiestas y fuegos artificiales empiezan a resultarme insípidos."),
    ("Ne me tourmentez pas. Eh bien, qu'a-t-on décidé par rapport à la dépêche de Novosilzoff? Vous savez tout.", "Don't torment me. Well, what has been decided about Novosíltsev's dispatch? You know everything.", "No me atormente. Bueno, ¿qué se ha decidido sobre el despacho de Novosíltsev? Usted lo sabe todo."),
    ("Qu'a-t-on décidé? On a décidé que Buonaparte a brûlé ses vaisseaux, et je crois que nous sommes en train de brûler les notres.", "What has been decided? It has been decided that Buonaparte has burned his boats, and I believe that we are about to burn ours.", "¿Qué se ha decidido? Se ha decidido que Buonaparte ha quemado sus naves, y creo que nosotros estamos a punto de quemar las nuestras."),
    ("Cette fameuse neutralité prussienne, ce n'est qu'un piège.", "This famous Prussian neutrality is nothing but a snare.", "Esta famosa neutralidad prusiana no es más que una trampa."),
    ("A propos", "À propos", "À propos"),
    ("le vicomte de Mortemart, il est allié aux Montmorency par les Rohans,", "the Vicomte de Mortemart, who is connected with the Montmorencys through the Rohans,", "el Vizconde de Mortemart, que está emparentado con los Montmorency a través de los Rohan,"),
    ("l'abbé Morio:", "the Abbé Morio:", "el abate Morio:"),
    ("l'impératrice-mère", "Dowager Empress", "Emperatriz Viuda"),
    ("C'est un pauvre sire, ce baron, à ce qu'il paraît.", "He is a poor specimen, this baron, by all accounts.", "Es un espécimen pobre, este barón, por lo que dicen."),
    ("Monsieur le baron de Funke a été recommandé à l'impératrice-mère par sa soeur,", "Baron de Funke was recommended to the Dowager Empress by her sister,", "El barón de Funke fue recomendado a la Emperatriz Viuda por su hermana,"),
    ("beaucoup d'estime,", "much esteem,", "mucha estima,"),
    ("Mais à propos de votre famille,", "But à propos of your family,", "Pero à propos de su familia,"),
    ("fait les délices de tout le monde. On la trouve belle, comme le jour.", "has been the delight of everyone? People find her as lovely as the day.", "ha sido el deleite de todos? La gente la encuentra tan hermosa como el día."),
    ("Que voulez-vous? Lavater aurait dit que je n'ai pas la bosse de la paternité,", "What would you have? Lavater would have said that I lack the bump of paternity,", "¿Qué quiere? Lavater habría dicho que me falta el chichón de la paternidad,"),
    ("des imbéciles.", "imbeciles.", "imbéciles."),
    ("Je suis votre", "I am your", "Soy su"),
    ("et à vous seule je puis l'avouer. Mes enfants sont les entraves de mon existence.", "and to you alone can I confess it. My children are the shackles of my existence.", "y sólo a usted puedo confesarlo. Mis hijos son los grilletes de mi existencia."),
    ("Que voulez vous?..", "What would you have?..", "¿Qué quiere?.."),
    ("ont la manie des mariages.", "have a mania for matchmaking.", "tienen manía por hacer matrimonios."),
    ("petite personne", "little person", "personita"),
    ("une parente à nous, une princesse", "a relation of ours, a princess", "una pariente nuestra, una princesa"),
    ("Voilà l'avantage d'être père.", "There you have the advantage of being a father.", "Ahí tiene la ventaja de ser padre."),
    ("La pauvre petite est malheureuse, comme les pierres.", "The poor little thing is wretched as the stones.", "La pobrecita es más desdichada que las piedras."),
    ("Ecoutez, chère Annette,", "Listen, dear Annette,", "Escuche, querida Annette,"),
    ("Arrangez-moi cette affaire et je suis votre", "arrange this affair for me, and I am your", "arrégleme este asunto, y soy su"),
    ("à tout jamais", "for ever and ever", "por los siglos de los siglos"),
    ("Attendez,", "Wait,", "Espere,"),
    ("Lise (la femme du jeune", "Lise (the wife of young", "Lise (la esposa del joven"),
    ("Ce sera dans votre famille, que je ferai mon apprentissage de vieille fille.", "It is in your family that I shall serve my apprenticeship as an old maid.", "Será en su familia donde haré mi aprendizaje como solterona.")
]

for fr, en, es in mappings:
    ch1_text = ch1_text.replace(f'<seg type="origfr">{en}</seg>', f'<foreign xml:lang="fr" n="{en}">{fr}</foreign>')
    ch1_text = ch1_text.replace(f'<seg type="origfr">{es}</seg>', f'<foreign xml:lang="fr" n="{es}">{fr}</foreign>')

text = text[:ch1_start] + ch1_text + text[ch1_end:]

with open('tei-source/2600-full.xml', 'w', encoding='utf-8') as f:
    f.write(text)
