from conflagrate import BlockingBehavior, Graph, Node, nodetype, run


class NativePythonGraph(Graph):
    start = Node(label="Get Name", type="salutation")
    welcome = Node(label="Greeting", type="greeting")

    start > welcome


@nodetype("salutation", blocking_behavior=BlockingBehavior.BLOCKING)
def salutation() -> str:
    print("Hello, what is your name?")
    return input()


@nodetype("greeting")
def greeting(name: str) -> None:
    print(f"Welcome {name}!")


if __name__ == "__main__":
    run(NativePythonGraph(), "start")
