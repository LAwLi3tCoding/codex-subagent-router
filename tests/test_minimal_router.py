import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class RouterScopeTest(unittest.TestCase):
    def test_no_role_or_hook_definitions_are_shipped(self):
        self.assertEqual(list((REPO_ROOT / 'agents').glob('*.toml')), [])
        self.assertEqual(list((REPO_ROOT / 'hooks').glob('*.py')), [])


if __name__ == '__main__':
    unittest.main()
