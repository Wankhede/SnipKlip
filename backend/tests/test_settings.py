import os
import tempfile
import unittest
from pathlib import Path

from app.settings import env


class EnvLoaderTests(unittest.TestCase):
    def test_load_env_file_populates_environment(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env"
            env_file.write_text("TEST_SETTING=hello\n", encoding="utf-8")

            previous_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                env.load_env_file(env_file)
                self.assertEqual(os.environ["TEST_SETTING"], "hello")
            finally:
                os.chdir(previous_cwd)
                os.environ.pop("TEST_SETTING", None)


if __name__ == "__main__":
    unittest.main()
