#!/usr/bin/env python3
"""Command-line entrypoint for the lightweight SRW UI toolkit.

Small CLI to start an RPC server, inspect git info, or list/run visualizers.
Keep arguments and behaviour simple for personal use.
"""
import argparse
import sys
from srw_tools import rpc_server, git_helper, visualizer


def cmd_start_rpc(args):
    # Do not restrict file access by default. Only pass allowed_dirs when the
    # user explicitly supplies --dir. This keeps the server permissive otherwise.
    allowed = [args.dir] if getattr(args, 'dir', None) else None
    server = rpc_server.RPCServer(host=args.host, port=args.port, allowed_dirs=allowed)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('shutting down')


def cmd_git(args):
    if args.sub == 'commit':
        c = git_helper.current_commit(args.path)
        print(c or 'unknown')
    elif args.sub == 'status':
        print(git_helper.show_status(args.path))
    elif args.sub == 'tags':
        for t in git_helper.list_tags(args.path):
            print(t)


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

    rpc = sp.add_parser('start-rpc')
    rpc.add_argument('--host', default='127.0.0.1')
    rpc.add_argument('--port', type=int, default=8000)
    rpc.add_argument('--dir', default=None,
                     help='Optional directory to restrict file operations to. If not set all paths are allowed.')
    rpc.set_defaults(func=cmd_start_rpc)

    gitp = sp.add_parser('git')
    gitp.add_argument('sub', choices=['commit', 'status', 'tags'])
    gitp.add_argument('--path', default=None)
    gitp.set_defaults(func=cmd_git)

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
