#!/usr/bin/env python3
"""Command-line entrypoint for the lightweight SRW UI toolkit.

Small CLI to inspect git info, or list/run visualizers. Keep arguments
and behaviour simple for personal use.
"""
import argparse
import json
import sys
from srw_tools import git_helper, visualizer



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


def cmd_annex(args):
    # Use the git_helper annex helpers
    json_out = bool(getattr(args, 'json_output', False))

    def _print(obj):
        if json_out:
            print(json.dumps(obj))
        else:
            # simple pretty output for humans
            if isinstance(obj, dict):
                # small tidy formatting
                if 'available' in obj:
                    print('available' if obj['available'] else 'not-available')
                elif 'success' in obj and 'message' in obj:
                    print(obj['message'])
                else:
                    print(obj)
            else:
                print(obj)

    if args.sub == 'available':
        ok = git_helper.annex_available(path=args.path)
        _print({'available': ok})
        return
    elif args.sub == 'init':
        ok = git_helper.init_annex(path=args.path, name=args.name)
        _print({'success': ok, 'message': 'OK' if ok else 'FAILED'})
        return
    elif args.sub == 'add':
        if not getattr(args, 'files', None):
            _print({'success': False, 'message': 'No files provided for annex add'})
            return
        ok, out = git_helper.annex_add(args.files, path=args.path)
        _print({'success': ok, 'message': out})
        return
    elif args.sub == 'get':
        if not getattr(args, 'files', None):
            _print({'success': False, 'message': 'No files provided for annex get'})
            return
        ok, out = git_helper.annex_get(args.files, path=args.path)
        _print({'success': ok, 'message': out})
        return
    elif args.sub == 'drop':
        if not getattr(args, 'files', None):
            _print({'success': False, 'message': 'No files provided for annex drop'})
            return
        ok, out = git_helper.annex_drop(args.files, path=args.path)
        _print({'success': ok, 'message': out})
        return


def build_parser():
    p = argparse.ArgumentParser(prog='srw_tools')
    sp = p.add_subparsers(dest='cmd')

    gitp = sp.add_parser('git')
    git_subp = gitp.add_subparsers(dest='sub')

    git_commit = git_subp.add_parser('commit')
    git_commit.add_argument('--path', default=None)
    git_commit.set_defaults(func=cmd_git)

    git_status = git_subp.add_parser('status')
    git_status.add_argument('--path', default=None)
    git_status.set_defaults(func=cmd_git)

    git_tags = git_subp.add_parser('tags')
    git_tags.add_argument('--path', default=None)
    git_tags.set_defaults(func=cmd_git)

    # nested annex under `git` also supported: `srw_tools git annex <...>`
    git_annex = git_subp.add_parser('annex')
    git_annex.add_argument('sub', choices=['init', 'add', 'get', 'drop', 'available'])
    git_annex.add_argument('--path', default=None)
    git_annex.add_argument('--name', default=None)
    git_annex.add_argument('--json', action='store_true', dest='json_output')
    git_annex.add_argument('files', nargs='*')
    git_annex.set_defaults(func=cmd_annex)

    vis = sp.add_parser('visualizer')
    vis.add_argument('sub', choices=['list', 'run'])
    vis.add_argument('--name', default='sine')
    vis.set_defaults(func=cmd_vis)

    annexp = sp.add_parser('annex')
    annexp.add_argument('sub', choices=['init', 'add', 'get', 'drop', 'available'])
    annexp.add_argument('--path', default=None)
    annexp.add_argument('--name', default=None, help='name to use when init annex (optional)')
    annexp.add_argument('--json', action='store_true', dest='json_output')
    annexp.add_argument('files', nargs='*', help='files to operate on (for add/get/drop)')
    annexp.set_defaults(func=cmd_annex)

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
