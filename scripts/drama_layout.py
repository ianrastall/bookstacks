"""Shared Shakespeare layout rules and source-pinned character labels."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
RULES=json.loads((ROOT/'src/data/drama-layout-rules.json').read_text(encoding='utf-8'))
INDEX=json.loads((ROOT/'src/data/drama-layout-index.json').read_text(encoding='utf-8'))
TEI='http://www.tei-c.org/ns/1.0'
local=lambda node: node.tag.rsplit('}',1)[-1]

def cue_text(node):
    if local(node) in {'note','ref'}:return ''
    return (node.text or '')+''.join(cue_text(child)+(child.tail or '') for child in node)


class DramaLayout:
    def __init__(self,source,locale):
        record=INDEX.get(source.name)
        if not record or record['source_sha256']!=hashlib.sha256(source.read_bytes()).hexdigest():
            raise ValueError(f'Refresh the explicit drama layout index for {source.name}')
        self.locale=locale
        alternatives='|'.join(r'\s+'.join(re.escape(word) for word in name.split()) for name in record['names'])
        chars=RULES['wordCharacters']
        self.names=re.compile(f'(?<![{chars}])(?:{alternatives})(?![{chars}])',re.I)

    def kind(self,node):
        declared=node.get('type','')
        if declared in {'entrance','exit','setting'}: return declared
        value=' '.join(cue_text(node).split()).lstrip('([').strip()
        value=self.names.sub('@',value)
        for kind in ['exit','entrance']:
            if re.search(RULES[kind][self.locale],value,re.I):return kind
        return 'business'

    def prepare(self,root):
        parents={child:parent for parent in root.iter() for child in parent}
        for stage in list(root.iter(f'{{{TEI}}}stage')):
            parts=stage_parts(stage);declared=stage.get('type','')
            for part in parts:
                if len(parts)>1:part.set('type','business')
                kind=self.kind(part)
                if len(parts)>1 and kind=='business' and declared in {'entrance','exit','setting'}:kind=declared
                part.set('data-bookstacks-stage-kind',kind)
            if len(parts)>1:
                parent=parents[stage];position=list(parent).index(stage);parent.remove(stage)
                for offset,part in enumerate(parts):parent.insert(position+offset,part)
        for division in root.iter(f'{{{TEI}}}div'):
            previous=None
            for child in list(division):
                if local(child)=='stage' and child.get('data-bookstacks-stage-kind')=='business' and previous is not None and local(previous)=='sp' and not (child.tail or '').strip():
                    value=cue_text(child).strip().lstrip('([').strip()
                    speaker=next((node for node in previous if local(node)=='speaker'),None)
                    label=''.join(speaker.itertext()).split(',')[0].rstrip('. ').strip() if speaker is not None else ''
                    if (label and value.lower().startswith(label.lower())) or re.match(r'^(?:il|elle|he|she|él|ella)\b',value,re.I):
                        division.remove(child);previous.append(child);continue
                previous=child
        def target(node,last=False):
            if local(node)=='p':return node
            if local(node)=='lg':
                lines=list(node.iter(f'{{{TEI}}}l'))
                if lines:return lines[-1] if last else lines[0]
        for speech in root.iter(f'{{{TEI}}}sp'):
            pending=[];previous=None
            def append_pending():
                if previous is not None:
                    for stage in pending:
                        speech.remove(stage)
                        if len(previous):previous[-1].tail=(previous[-1].tail or '')+' '
                        else:previous.text=(previous.text or '')+' '
                        stage.tail=' ';previous.append(stage)
                pending.clear()
            for child in list(speech):
                if local(child)=='stage' and child.get('data-bookstacks-stage-kind')=='business':
                    pending.append(child);continue
                first=target(child)
                if first is not None:
                    text=first.text;first.text=None
                    for position,stage in enumerate(pending):
                        speech.remove(stage);stage.tail=' ';first.insert(position,stage)
                    if pending:pending[-1].tail=' '+(text or '')
                    else:first.text=text
                    pending.clear();previous=target(child,True)
                else:append_pending()
            append_pending()
        # A block exit embedded in a verse line must leave the verse environment
        # before using paragraph alignment commands in the PDF renderer.
        for group in root.iter(f'{{{TEI}}}lg'):
            for line in list(group):
                if local(line)!='l' or not any(local(child)=='stage' and child.get('data-bookstacks-stage-kind') in {'entrance','exit','setting'} for child in line):continue
                position=list(group).index(line);parts=[]
                fragment=ET.Element(line.tag,line.attrib);fragment.text=line.text
                for child in line:
                    if local(child)=='stage' and child.get('data-bookstacks-stage-kind') in {'entrance','exit','setting'}:
                        if ''.join(fragment.itertext()).strip():parts.append(fragment)
                        direction=deepcopy(child);direction.tail=None;parts.append(direction)
                        fragment=ET.Element(line.tag,line.attrib);fragment.text=child.tail
                    else:fragment.append(deepcopy(child))
                if ''.join(fragment.itertext()).strip():parts.append(fragment)
                group.remove(line)
                for offset,part in enumerate(parts):group.insert(position+offset,part)


def stage_clone(node):
    clone=deepcopy(node);leaves=[]
    def collect(element):
        if element.text:leaves.append((element,'text'))
        for child in element:
            if local(child) not in {'note','ref'}:collect(child)
            if child.tail:leaves.append((child,'tail'))
    collect(clone)
    nonempty=[(element,attr) for element,attr in leaves if getattr(element,attr).strip()]
    if nonempty:
        first,fa=nonempty[0];last,la=nonempty[-1]
        opening=re.match(r'^\s*([\[(])',getattr(first,fa))
        closing=re.search(r'([\])])([.,;:]?)\s*$',getattr(last,la))
        if opening and closing and (opening[1],closing[1]) in [('(',')'),('[',']')]:
            setattr(first,fa,re.sub(r'^\s*[\[(]\s*','',getattr(first,fa)))
            setattr(last,la,re.sub(r'[\])]([.,;:]?)\s*$',r'\1',getattr(last,la)))
        setattr(first,fa,re.sub(r'^\s*,\s*','',getattr(first,fa)))
    return clone


def stage_parts(stage):
    parts=[];current=ET.Element(stage.tag,stage.attrib);current.text=stage.text;break_seen=False
    for child in stage:
        is_break=local(child)=='lb'
        if is_break and break_seen:
            current.remove(current[-1])
            if ''.join(current.itertext()).strip():parts.append(current)
            current=ET.Element(stage.tag,stage.attrib);current.text=child.tail;break_seen=False
        else:
            current.append(deepcopy(child))
            break_seen=is_break and not (child.tail or '').strip()
    if ''.join(current.itertext()).strip():parts.append(current)
    return parts if len(parts)>1 else [stage]
