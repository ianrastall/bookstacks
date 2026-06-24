import os
import re

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ru_file = os.path.join(repo_root, 'tei-source', '2600-ru.xml')
    
    with open(ru_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = content.replace(
        "Он говорил по-французски. Je ne connais dans la vie que maux bien réels: c'est le remord et la maladie. Il n'est de bien que l'absence de ces maux.<note>",
        "Он говорил по-французски. <foreign xml:lang=\"fr\">Je ne connais dans la vie que maux bien réels: c'est le remord et la maladie. Il n'est de bien que l'absence de ces maux.</foreign><note>"
    )

    content = content.replace(
        "а другие, <emph>ближние</emph>, le prochain, как вы с княжной <persName ref=\"#princess-mary\">Марьей</persName> называете, это главный источник заблуждения и зла. Le prochain<note>",
        "а другие, <emph>ближние</emph>, <foreign xml:lang=\"fr\">le prochain</foreign>, как вы с княжной <persName ref=\"#princess-mary\">Марьей</persName> называете, это главный источник заблуждения и зла. <foreign xml:lang=\"fr\">Le prochain</foreign><note>"
    )

    content = content.replace(
        "— Да, mais ce n'est pas comme vous l'entendez,<note>",
        "— Да, <foreign xml:lang=\"fr\">mais ce n'est pas comme vous l'entendez,</foreign><note>"
    )

    with open(ru_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    main()
