import lark
import argparse
import warnings
import os
import json
import shutil

import builtinCommands

args = argparse.ArgumentParser()
args.add_argument('file', help='Fishy file to compile')
args.add_argument('-o', '--output', help='Generated datapack folder name')
args.add_argument('--force', help='Force datapack even if theres already a folder', action='store_true')
args = args.parse_args()

with open(args.file, 'r', encoding='utf-8') as f:
    source = f.read() + '\n'

with open('grammar.lark', 'r') as f:
    grammar = f.read()

parser = lark.Lark(grammar)
parse_tree = parser.parse(source)

namespace = f'candy_{os.path.basename(args.file)[:-6]}'
functions = {}
stack = []
indent = ' '*4

def addSource(src):
    functions[stack[-1]]['source'] += src

def parse(stmt):
    # Check indentation level
    if isinstance(stmt.children[0], lark.lexer.Token) and stmt.children[0].type == 'INDENT':
        indentLevel = stmt.children[0].count(indent)
        if indentLevel > len(stack):
            raise IndentationError(f'Indentation error while parsing {stmt} in line {stmt.children[0].line}')
        if indentLevel < len(stack):
            for _ in range(len(stack) - indentLevel): stack.pop()
        # Remove the indent token since its not needed anymore
        stmt.children.pop(0)
    else:
        indentLevel = 0
        stack.clear()

    print(indentLevel, stmt)

    if stmt.data == 'keyword':
        keyword = stmt.children[0]
        if keyword.data == 'def':
            fname = keyword.children[0].value
            functions[fname] = {'source': '', 'children': []}
            stack.append(fname)
        elif keyword.data == 'if':
            name = f'{stack[0]}_gen{str(len(functions[stack[0]]["children"]))}'
            functions[stack[0]]['children'].append(name)
            functions[name] = {'source': ''}
            prefix = ''
            condition = parseExpr(keyword.children[0])
            if isinstance(condition, tuple):
                condition, prefix = condition
                prefix += ' '
            functions[name]['condition'] = condition
            functions[name]['conditionPrefix'] = prefix
            addSource(f'\nexecute {prefix}if {condition} run function {namespace}:{name}')

            stack.append(name)
        elif keyword.data == 'else':
            name = f'{stack[0]}_gen{str(len(functions[stack[0]]["children"]))}'
            functions[stack[0]]['children'].append(name)
            functions[name] = {'source': ''}
            condition = functions[functions[stack[0]]['children'][-2]]['condition']
            conditionPrefix = functions[functions[stack[0]]['children'][-2]]['conditionPrefix']
            addSource(f'\nexecute {conditionPrefix}unless {condition} run function {namespace}:{name}')

            stack.append(name)
    elif stmt.data == 'expression':
        addSource('\n' + parseExpr(stmt))
    elif stmt.data == 'raw_expr':
        addSource('\n' + stmt.children[0].value)

def parseExpr(expr):
    if expr.data == 'expression':
        return parseExpr(expr.children[0])

    if expr.data == 'func_call':
        return parseFuncCall(expr)        

def parseValue(t):
    if isinstance(t, lark.Tree):
        if t.data == 'func_call': return parseFuncCall(t)
    elif isinstance(t, lark.lexer.Token):
        # Probably should check if they are valid instead of just returning them
        if t.type == 'STRING': return t.value[1:-1]
        elif t.type == 'POSITION': return t.value[1:-1]
        elif t.type == 'BLOCK': return t.value

def parseFuncCall(expr):
    tmp = 0
    if expr.children[0].type == 'F_ORIGIN': 
        funcOrigin = expr.children[0]
        tmp = 1
    else: funcOrigin = 'builtin'
    
    func = expr.children[tmp].value
    raw_args = expr.children[tmp + 1].children if len(expr.children) > tmp + 1 else ()
    del tmp

    if expr.children[0].value == 'self':
        return f'function {namespace}:{expr.children[1].value}'

    kwargs = {}
    args = []
    for i in raw_args:
        if isinstance(i, lark.Tree) and i.data == 'kw_arg':
            name = i.children[0].value
            val = parseValue(i.children[1])
            kwargs[name] = val
        else:
            args.append(parseValue(i))
    args = tuple(args) 
    
    if hasattr(builtinCommands, func):
        return getattr(builtinCommands, func)(args, kwargs)
    else:
        warnings.warn(f'Unknwon function {func} in line {expr.children[0].line}')
        return f'# unknown function {func}'

for statement in parse_tree.children:
    parse(statement)

#print('Stack: ', stack)
#print('Functions: ', functions)

def prettyFunctions(functions):
    for fname, f in functions.items():
        print(fname)
        for i in f['source'].lstrip().splitlines():
            print('  '+i)
        print()
        
prettyFunctions(functions)

def makeDatapack(functions, path, description='A Candy generated datapack', force=False):
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
        os.makedirs(os.path.join(dataPath, 'minecraft/tags/functions'))
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