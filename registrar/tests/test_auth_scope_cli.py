"""Focused fail-closed checks for the offline token issuer CLI."""
import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from registrar.app import auth


class _Db:
    def execute(self, *args, **kwargs):
        return self

    def close(self):
        pass


class AuthScopeCliTests(unittest.TestCase):
    def _run(self, *scope_args):
        captured = []
        with patch("registrar.app.db.connect", return_value=_Db()), patch("registrar.app.db.verify_schema"), patch.object(auth, "create_token", side_effect=lambda db, principal, scopes: captured.append((principal, scopes)) or "token-id.secret"), patch.object(sys, "argv", ["auth", "--db", "ignored.db", "--principal", "test-principal", *scope_args]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            auth.main()
        return captured[0]

    def test_omitted_scope_exits_before_minting(self):
        with patch("registrar.app.db.connect") as connect, patch.object(auth, "create_token") as mint, patch.object(sys, "argv", ["auth", "--db", "ignored.db", "--principal", "test-principal"]), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                auth.main()
        self.assertEqual(2, raised.exception.code)
        connect.assert_not_called(); mint.assert_not_called()

    def test_explicit_read_scope_is_preserved_without_writer_scope(self):
        principal, scopes = self._run("--scope", "post:read")
        self.assertEqual("test-principal", principal)
        self.assertEqual(["post:read"], scopes)
        self.assertNotIn("post:write", scopes)

    def test_explicit_write_scope_requires_deliberate_argument(self):
        _, scopes = self._run("--scope", "post:write")
        self.assertEqual(["post:write"], scopes)

    def test_invalid_empty_scope_exits_before_minting(self):
        for invalid in ("", "   "):
            with self.subTest(invalid=invalid), patch("registrar.app.db.connect") as connect, patch.object(auth, "create_token") as mint, patch.object(sys, "argv", ["auth", "--db", "ignored.db", "--principal", "test-principal", "--scope", invalid]), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    auth.main()
            self.assertEqual(2, raised.exception.code)
            connect.assert_not_called(); mint.assert_not_called()

    def test_whitespace_bearing_scope_exits_before_database_or_minting(self):
        for invalid in ("post:read post:write", " post:write "):
            with self.subTest(invalid=invalid), patch("registrar.app.db.connect") as connect, patch.object(auth, "create_token") as mint, patch.object(sys, "argv", ["auth", "--db", "ignored.db", "--principal", "test-principal", "--scope", invalid]), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    auth.main()
            self.assertEqual(2, raised.exception.code)
            connect.assert_not_called(); mint.assert_not_called()

    def test_create_token_rejects_whitespace_bearing_direct_scope(self):
        for invalid in ("post:read post:write", " post:write "):
            with self.subTest(invalid=invalid):
                with self.assertRaises(auth.Forbidden):
                    auth.create_token(_Db(), "test-principal", [invalid])


if __name__ == "__main__":
    unittest.main()
