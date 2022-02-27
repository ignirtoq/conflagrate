🔥 Conflagrate
=============

Build applications from control flow graphs, rather than the other way around.

1. Define your application flow with a [Graphviz](https://www.graphviz.org/) diagram
2. Write the code for each node as a decorated Python function
3. Run

💾 Installation
--------------
Currently `conflagrate` is only available from source:

`pip install .`

See the examples directory for sample code.

💻 Dependencies
--------------
`conflagrate` is built entirely in Python and only depends on external 
libraries for diagram parsing.  Currently only [Graphviz](https://www.graphviz.org/)
is supported:
* [pydot](https://github.com/pydot/pydot): for parsing the control flow graph