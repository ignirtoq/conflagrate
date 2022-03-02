from conflagrate import run
import example_dependencies

if __name__ == '__main__':
    run(__file__[:-3] + '.gv', 'read')
