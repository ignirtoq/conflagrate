from conflagrate import BlockingBehavior, nodetype, run


@nodetype('salutation')
def salutation() -> str:
    return input('Hello, what is your name?\n')


@nodetype('first_greeting', blocking_behavior=BlockingBehavior.NON_BLOCKING)
def generic_greeting(name: str) -> None:
    print(f'Welcome {name}!')


@nodetype('second_greeting', blocking_behavior=BlockingBehavior.NON_BLOCKING)
def special_greeting(_: str) -> None:
    print(f'This is a control flow graph based application.')


if __name__ == '__main__':
    run(__file__[:-3] + '.gv', 'start')
