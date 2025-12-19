#!/usr/bin/env python3
"""Command-line entrypoint for the lightweight SRW UI toolkit.

Small CLI to list and run visualizers. Keep arguments and behaviour simple for
personal use.
"""
import argparse
import json
import sys
from srw_tools import visualizer



def cmd_vis(args):
    if args.sub == 'list':
        for n in visualizer.list_visualizers():
            print(n)
    elif args.sub == 'run':
        cls = visualizer.get_visualizer(args.name)
        inst = cls()
        out = inst.run({})
        print('OK' if out is True else out)




def build_parser():
    p = argparse.ArgumentParser(prog='srw_tools')
    sp = p.add_subparsers(dest='cmd')



    vis = sp.add_parser('visualizer')
    vis.add_argument('sub', choices=['list', 'run'])
    vis.add_argument('--name', default='sine')
    vis.set_defaults(func=cmd_vis)


    return p


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, 'func', None):
        parser.print_help()
        return 2
    args.func(args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
