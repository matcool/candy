# candy (WIP)
<p align="center">A language that compiles into minecraft functions</p>

[![Demo video](https://imgur.com/f142R0P.png)](https://streamable.com/063av)

Basic example, which compiles to 3 functions
```python
def main:
# Lines starting with a / are not compiled, just put in as is
    /say Hello world!
    if checkBlock("~ ~-1 ~", minecraft:stone):
        say('You are standing on stone!')
    self:test()

# This function will say hi
def test:
    say('I am from another function')
```
```python
# main.mcfunction
say Hello World!
execute if block ~ ~-1 ~ minecraft:stone run function candy_basic:main_gen0
function candy_basic:test

# main_gen0.mcfunction
say You are standing on stone!

# test.mcfunction
say I am from another function
```
For more examples check the examples folder

# Usage
Run the candy.py file with the desired arguments
```
usage: candy.py [-h] [-o OUTPUT] [--force] file

positional arguments:
  file                  Candy file to compile

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path for the generated datapack, if omitted will not
                        be saved anywhere
  --force               Force datapack even if theres already a folder
```

# Extra info
- Functions with the name of `load` or `tick` will run upon loading (or /reload) and on every tick, respectively