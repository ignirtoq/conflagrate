from conflagrate import Graph, Node, run, run_graph, nodetype, BlockingBehavior


class GraphWithSubgraph(Graph):
    start = Node(label="Get name", type="start")
    run_subgraph = Node(label="Run subgraph", type="run_subgraph")
    finish = Node(label="Display subgraph output", type="subgraph_display")

    start > run_subgraph
    run_subgraph > finish


class Subgraph(Graph):
    sub_start = Node(label="Display name", type="sub.start")
    invert = Node(label="Invert name", type="sub.invert")

    sub_start > invert


@nodetype("start")
def start() -> str:
    print('Hello, what is your name?')
    return input()


@nodetype("run_subgraph")
async def run_subgraph(name: str) -> str:
    return await run_graph(Subgraph(), "sub_start", start_node_args=(name,))


@nodetype("subgraph_display")
def subgraph_display(subgraph_output: str) -> None:
    print(f'Subgraph output: {subgraph_output}')


@nodetype("sub.start")
def sub_start(name: str) -> str:
    print(f'Hi {name}, you are now in a subgraph.')
    return name


@nodetype("sub.invert", blocking_behavior=BlockingBehavior.NON_BLOCKING)
def invert(name: str) -> str:
    return name[::-1]


if __name__ == "__main__":
    run(GraphWithSubgraph(), 'start')
