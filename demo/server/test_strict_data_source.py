import os
import unittest
from fastapi.testclient import TestClient

import app as server


class TestStrictDataSource(unittest.TestCase):
    """A data source that fails to start falls back to mock unless strict mode is on."""

    def setUp(self):
        self._config = server.config
        server.config = {"data_source": {"type": "no-such-source", "config": {}}}
        os.environ.pop("I3X_STRICT_DATA_SOURCE", None)

    def tearDown(self):
        server.config = self._config
        os.environ.pop("I3X_STRICT_DATA_SOURCE", None)

    def test_falls_back_to_mock_by_default(self):
        with TestClient(server.app) as client:
            self.assertEqual(client.get("/namespaces").status_code, 200)

    def test_strict_mode_refuses_to_start(self):
        os.environ["I3X_STRICT_DATA_SOURCE"] = "1"
        with self.assertRaises(Exception):
            with TestClient(server.app):
                pass


if __name__ == "__main__":
    unittest.main()
