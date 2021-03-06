from conflagrate import BlockingBehavior, BranchingStrategy, nodetype, run
from typing import Tuple


@nodetype('get_directive')
def get_directive() -> str:
    return input('Do you want to exit?\n')


@nodetype('matcher', BranchingStrategy.matcher, BlockingBehavior.NON_BLOCKING)
def exit_check(directive: str) -> Tuple[str, None]:
    exit_vals = {'y', 'Y', 'yes', 'Yes', 'YES'}
    return 'exit' if directive in exit_vals else 'continue', None


@nodetype('exit', blocking_behavior=BlockingBehavior.NON_BLOCKING)
def exit_message(*_) -> None:
    print('Goodbye!')


if __name__ == '__main__':
    run(__file__[:-3] + '.gv', 'start')
