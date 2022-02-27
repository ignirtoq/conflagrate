from conflagrate import BranchType, nodetype, run
from typing import Tuple


@nodetype('get_directive')
def get_directive() -> str:
    return input('Do you want to exit?\n')


@nodetype('matcher', BranchType.matcher)
def exit_check(directive: str) -> Tuple[str, None]:
    exit_vals = {'y', 'Y', 'yes', 'Yes', 'YES'}
    return 'exit' if directive in exit_vals else 'continue', None


@nodetype('exit')
def exit_message(*_) -> None:
    print('Goodbye!')


if __name__ == '__main__':
    run(__file__[:-3] + '.gv', 'start')
