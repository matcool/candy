import re

functions = {}

def parseFunction(string):
    return re.match(r'(\w+?)\((.+)\)', string).groups()

def parseIf(string, function):
    name, args = parseFunction(string)
    result = functions[name](args)
    return f'execute if {result} run function {function}'
    
def parse_getBlock(string):
    # execute if block <pos> <block>
    pos, block = string.split(',')
    pos = pos.strip()[1:-1]
    block = block.strip()
    return f'block {pos} {block}'
functions['getBlock'] = parse_getBlock

def parse_say(string):
    # say <message>
    return f'say {string.strip()[1:-1]}'
functions['say'] = parse_say