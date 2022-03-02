from conflagrate import nodetype, run


@nodetype('salutation')
def salutation() -> str:
    return input('Hello, what is your name?\n')


@nodetype('greeting')
def generic_greeting(name: str) -> None:
    print(f'Welcome {name}!')


if __name__ == '__main__':
    run(__file__[:-3] + '.gv', 'start')
