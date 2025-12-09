import tempfile
import os
import unittest
from srw_tools import git_helper


def run_git(args, cwd=None):
    import subprocess
    proc = subprocess.run(["git"] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


class GitExtendedTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def _init_repo(self, path, branch='testbranch'):
        os.makedirs(path, exist_ok=True)
        rc, out, err = run_git(['init'], cwd=path)
        # set user config for commits
        run_git(['config', 'user.email', 'dev@example.com'], cwd=path)
        run_git(['config', 'user.name', 'Dev User'], cwd=path)
        # create and switch to branch
        rc, out, err = run_git(['checkout', '-b', branch], cwd=path)
        return rc == 0

    def test_stage_commit_push_pull(self):
        root = self.root
        remote_bare = os.path.join(root, 'remote.git')
        local_a = os.path.join(root, 'a')
        local_b = os.path.join(root, 'b')

        # create bare remote
        os.makedirs(remote_bare, exist_ok=True)
        rc, out, err = run_git(['init', '--bare'], cwd=remote_bare)
        self.assertEqual(rc, 0)

        # init repo A
        self._init_repo(local_a, branch='testbranch')
        fpath = os.path.join(local_a, 'file.txt')
        with open(fpath, 'w') as fh:
            fh.write('v1')

        # stage and commit using git_helper
        self.assertTrue(git_helper.stage_files(['file.txt'], path=local_a))
        self.assertTrue(git_helper.commit('first', path=local_a))

        # add remote and push
        rc, out, err = run_git(['remote', 'add', 'origin', remote_bare], cwd=local_a)
        self.assertEqual(rc, 0)
        ok, out = git_helper.push(remote='origin', branch='testbranch', path=local_a, set_upstream=True)
        self.assertTrue(ok, msg=out)

        # clone remote to B
        rc, out, err = run_git(['clone', remote_bare, local_b], cwd=self.root)
        self.assertEqual(rc, 0)

        # modify in A and push again
        with open(fpath, 'w') as fh:
            fh.write('v2')
        self.assertTrue(git_helper.stage_files(['file.txt'], path=local_a))
        self.assertTrue(git_helper.commit('second', path=local_a))
        ok, out = git_helper.push(remote='origin', branch='testbranch', path=local_a)
        self.assertTrue(ok, msg=out)

        # pull into B
        ok, out = git_helper.pull(remote='origin', branch='testbranch', path=local_b)
        self.assertTrue(ok, msg=out)

        # verify contents in B updated
        with open(os.path.join(local_b, 'file.txt'), 'r') as fh:
            contents = fh.read()
        self.assertEqual(contents, 'v2')


if __name__ == '__main__':
    unittest.main()
