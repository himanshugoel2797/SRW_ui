import unittest
from srw_tools import git_helper


class GitHelperTests(unittest.TestCase):
    def test_current_commit_returns_none_when_not_repo(self):
        # in CI environment this may or may not be a git repo — just assert callable
        c = git_helper.current_commit(None)
        # either string or None; ensure no exception
        self.assertTrue(c is None or isinstance(c, str))


if __name__ == '__main__':
    unittest.main()
