def say(args, kwargs):
    # say(message)
    message = args[0]
    return f'say {message}'

def _executeKwargs(kwargs):
    tmp = ''
    for kwarg, value in kwargs.items():
        if kwarg == 'positioned': tmp += f' positioned {value}'
        elif kwarg == 'as': tmp += f' as {value}'
        elif kwarg == 'at': tmp += f' at {value}'
    return tmp

def checkBlock(args, kwargs):
    # checkBlock(position, block)
    pos = args[0]
    block = args[1]
    return f'{_executeKwargs(kwargs).lstrip()} block {pos} {block}'

def execute(args, kwargs):
    # execute(function(), (lots of keyword args))
    return f'execute{_executeKwargs(kwargs)} run {args[0]}'

def setblock(args, kwargs):
    # setblock(position, block, mode=(destroy|keep|replace))
    return f'setblock {args[0]} {args[1]} {kwargs.get("mode", "")}'