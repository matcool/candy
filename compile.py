# PS: This is the old code, this will all be somewhat moved to the lark parser
import argparse
import os
import shutil
import json
import re
import parsers

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', help='Print debug info', action='store_true')
parser.add_argument('file', help='Fishy file to compile')
parser.add_argument('-o', '--output', help='Generated datapack folder name')
parser.add_argument('--force', help='Force datapack even if theres already a folder', action='store_true')
args = parser.parse_args()

def debugPrint(*a):
    if args.debug: print(*a)

with open(args.file, 'r', encoding='utf-8') as file:
    source = file.read()

def indentationLevel(string, indent):
    if not string.startswith(indent): return 0
    return string.count(indent) - string.lstrip().count(indent)

namespace = f'fishy_{args.file[:-6]}'
functions = {}
stack = []
indent = ' '*4
for line in source.splitlines():
    if line.strip() == '': continue
    if line.lstrip().startswith('#'): continue
    indentLevel = indentationLevel(line, indent)
    if indentLevel > len(stack):
        raise IndentationError(line)
    if indentLevel < len(stack):
        stack.pop()
    line = line[len(indent)*indentLevel:]
    debugPrint(indentLevel, line)
    if line.startswith('/'):
        functions[stack[-1]]['source'] += '\n'+line[1:]
        continue
    if line.startswith('def '):
        fname = line[4:-1]
        functions[fname] = {'source': '', 'children': []}
        stack.append(fname)
        continue
    elif line.startswith('if '):
        name = f'{stack[0]}_gen{str(len(functions[stack[0]]["children"]))}'
        functions[stack[0]]['children'].append(name)
        functions[name] = {'source': ''}

        functions[stack[-1]]['source'] += '\n' + parsers.parseIf(line.rstrip()[3:-1], f'{namespace}:{name}')

        stack.append(name)
        continue
    else:
        if line.startswith('self:') and line.rstrip().endswith('()'):
            name = line[5:-2]
            functions[stack[-1]]['source'] += f'\nfunction {namespace}:{name}'
        else:
            match = parsers.parseFunction(line)
            if match:
                functions[stack[-1]]['source'] += '\n' + parsers.functions[match[0]](match[1])


debugPrint('Functions:', functions)

def makeDatapack(functions, path, description='A Fishy generated datapack', force=False):
    if os.path.isdir(path):
        if force: shutil.rmtree(path)
        else: raise Exception(f'{path} is already a folder.')
    os.mkdir(path)
    with open(os.path.join(path, 'pack.mcmeta'), 'w', encoding='utf-8') as file:
        json.dump({
            "pack": {
                "pack_format": 1,
                "description": description
            }
        }, file)
    dataPath = os.path.join(path, 'data')
    os.mkdir(dataPath)

    if functions.get('load') or functions.get('tick'):
        os.mkdir(os.path.join(dataPath, 'minecraft'))
        os.mkdir(os.path.join(dataPath, 'minecraft/tags'))
        os.mkdir(os.path.join(dataPath, 'minecraft/tags/functions'))
        if functions.get('load'):
            with open(os.path.join(dataPath, 'minecraft/tags/functions/load.json'), 'w', encoding='utf-8') as file:
                json.dump({'values': [f'{namespace}:load']}, file)
        if functions.get('tick'):
            with open(os.path.join(dataPath, 'minecraft/tags/functions/tick.json'), 'w', encoding='utf-8') as file:
                json.dump({'values': [f'{namespace}:tick']}, file)

    os.mkdir(os.path.join(dataPath, namespace))
    functionPath = os.path.join(dataPath, namespace+'/functions')
    os.mkdir(functionPath)

    for name, function in functions.items():
        with open(os.path.join(functionPath, name+'.mcfunction'), 'w', encoding='utf-8') as file:
            file.write(function['source'])

if args.output:
    makeDatapack(functions, args.output, force=args.force)