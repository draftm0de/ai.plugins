"""Git problems are explained in plain words with the command to run, never as a raw tool error."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support.workflow_fixture import WorkflowFixture, flow


class GitMessageTests(WorkflowFixture, unittest.TestCase):
    def raises(self, call, *needles):
        with self.assertRaises(ValueError) as caught:
            call()
        message = str(caught.exception)
        for needle in needles:
            self.assertIn(needle, message)
        for raw in ('returned non-zero', 'CalledProcessError', "['git'"):
            self.assertNotIn(raw, message)
        return message

    def test_a_folder_that_is_no_git_repository_names_git_init(self):
        plain = self.root / 'plain'
        plain.mkdir()
        message = self.raises(lambda: flow.create_marketplace(plain, 'plain', 'Plain', 'Publisher'), 'not recognised as a Git repository', '`git init`')
        self.assertIn(str(plain), message)
        self.raises(lambda: flow.git_tracked(plain, '.local'), '`git init`')

    def test_a_plugin_folder_without_a_github_address_names_the_remote_command(self):
        bare = self.root / 'bare-plugin'
        bare.mkdir()
        subprocess.run(['git', 'init', '-q', str(bare)], check=True)  # a repository, but no origin
        self.raises(lambda: flow.git_repository(bare), 'no GitHub address yet', '`git remote add origin https://github.com/<owner>/<name>.git`')

    def test_a_subfolder_of_a_repository_is_not_accepted_as_the_repository(self):
        sub = self.plugin / 'nested'
        sub.mkdir()
        self.raises(lambda: flow.git_root(sub), 'lies inside the Git repository', 'is itself the repository')

    def test_a_non_github_address_is_explained(self):
        self.raises(lambda: flow.repository_url('https://example.com/x/y.git'), 'is not a plain GitHub address', 'https://github.com/<owner>/<name>.git')
        self.raises(lambda: flow.repository_url(''), 'A GitHub address is needed')

    def test_a_given_address_that_differs_from_the_origin_is_named(self):
        self.raises(lambda: flow.git_repository(self.plugin, 'https://github.com/other/place.git'), 'differs from the GitHub address of the folder')


if __name__ == '__main__':
    unittest.main()
