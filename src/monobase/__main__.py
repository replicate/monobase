import sys
import textwrap

if __name__ == '__main__':
    print(
        textwrap.dedent(
            """\
    Running monobase directly does not do anything 🙀.
    You probably want one of these instead:

        python -m monobase.build

        python -m monobase.cuda

        python -m monobase.diff

        python -m monobase.monogen

        python -m monobase.update
    """
        )
    )
    sys.exit(2)
