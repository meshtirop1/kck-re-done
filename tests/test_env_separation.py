"""Guardrail tests: ensure we never regress the env/secrets separation."""
from pathlib import Path

from django.test import TestCase


BASE_DIR = Path(__file__).resolve().parent.parent


class SettingsLeakageTest(TestCase):
    """settings.py must not hardcode any real secret."""

    def test_settings_has_no_gmail_username_literal(self):
        src = (BASE_DIR / 'kck_project' / 'settings.py').read_text(encoding='utf-8')
        self.assertNotIn('mtirop345@gmail.com', src,
            'Real Gmail username must not be hardcoded in settings.py')

    def test_settings_has_no_gmail_app_password(self):
        src = (BASE_DIR / 'kck_project' / 'settings.py').read_text(encoding='utf-8')
        for leak in ('sljm ifeg zyqh nekv', 'sljmifegzyqhnekv'):
            self.assertNotIn(leak, src,
                f'Gmail app password {leak!r} must not be hardcoded in settings.py')

    def test_gitignore_protects_env(self):
        gitignore = BASE_DIR / '.gitignore'
        self.assertTrue(gitignore.exists(), '.gitignore must exist')
        text = gitignore.read_text(encoding='utf-8')
        self.assertIn('.env', text, '.env must be listed in .gitignore')
        self.assertIn('venv/', text)
        self.assertIn('*.sqlite3', text)

    def test_env_example_is_safe_to_commit(self):
        """The .env.example should contain placeholders, not real credentials."""
        example = BASE_DIR / '.env.example'
        self.assertTrue(example.exists(), '.env.example must exist')
        text = example.read_text(encoding='utf-8')
        self.assertNotIn('mtirop345@gmail.com', text)
        self.assertNotIn('sljmifegzyqhnekv', text)
        self.assertNotIn('sljm ifeg zyqh nekv', text)
