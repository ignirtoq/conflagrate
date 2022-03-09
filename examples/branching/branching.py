from conflagrate import BlockingBehavior, BranchingStrategy, nodetype, run
from typing import Tuple


@nodetype('salutation')
def salutation() -> str:
    return input('Hello, what is your name?\n')


@nodetype('matcher', BranchingStrategy.matcher, BlockingBehavior.NON_BLOCKING)
def matcher(name: str) -> Tuple[str, str]:
    return '1' if name == 'Guido' else '2', name


@nodetype('generic_greeting', blocking_behavior=BlockingBehavior.NON_BLOCKING)
def generic_greeting(name: str) -> None:
    print(f'Welcome {name}!')


@nodetype('special_greeting', blocking_behavior=BlockingBehavior.NON_BLOCKING)
def special_greeting(name: str) -> None:
    print(f'All hail our overlord, {name}!')


if __name__ == '__main__':
    run(__file__[:-3] + '.gv', 'start')
