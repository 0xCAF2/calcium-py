# calcium-py

A Calcium language intepreter on Python

## What is Calcium language?

Calcium is a programming language that takes a JSON array as input. It is interoperable with the Python language, allowing you to utilize Python's standard libraries and more. It is primarily designed as a subset of Python.

## How to create the interpreter and run Calcium code

```python
from calciumlang.runtime import Runtime

# Calcium code is given as a JSON array.
calcium_code = [
  [1, [], "#", "0.0.5"],
  [1, [], "expr", ["call", ["var", "print"], ["Hello, World."]]],
  [1, [], "end"],
]

# The Runtime executes Calcium code.
r = Runtime(calcium_code)
r.run()  # outputs 'Hello, World.'
```

## Applications using Calcium

With Blockly, [you can generate Calcium code in the visual environment](https://capg.app/). This editor produces Calcium code (a JSON array) that can be executed by the calcium-py runtime.
