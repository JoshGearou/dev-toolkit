import datetime
import io
import unittest
from unittest.mock import patch

from jwt_example import create_simple_jwt, decode_simple_jwt, get_verified_header, main

import jwt  # Ensure jwt is imported


class TestJWTExample(unittest.TestCase):
    def test_jwt_creation_and_decoding(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        decoded = decode_simple_jwt(token, secret)
        self.assertEqual(decoded, payload, "Decoded payload should match the original")

    def test_invalid_secret_fails(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        wrong_secret = "wrongsecret"
        with self.assertRaises(jwt.exceptions.InvalidSignatureError):  # type: ignore[attr-defined]
            decode_simple_jwt(token, wrong_secret)

    def test_expired_token(self) -> None:
        payload = {
            "hello": "world",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1),
        }
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        with self.assertRaises(jwt.exceptions.ExpiredSignatureError):  # type: ignore[attr-defined]
            decode_simple_jwt(token, secret)

    def test_malformed_token(self) -> None:
        secret = "mysecret"
        malformed_token = "this.is.not.a.valid.token"
        with self.assertRaises(jwt.exceptions.DecodeError):  # type: ignore[attr-defined]
            decode_simple_jwt(malformed_token, secret)

    def test_token_tampering(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        tampered_token = token + "tampered"
        with self.assertRaises(jwt.exceptions.InvalidSignatureError):  # type: ignore[attr-defined]
            decode_simple_jwt(tampered_token, secret)


class TestJWTMain(unittest.TestCase):
    def test_main_default(self) -> None:
        with patch("sys.stdout", new=io.StringIO()) as fake_output:
            main(["--payload", '{"hello": "world"}', "--secret", "mysecret"])
            output = fake_output.getvalue()
            self.assertIn("Generated JWT token:", output)
            self.assertIn("Decoded payload:", output)
            self.assertIn("'hello': 'world'", output)

    def test_invalid_json(self) -> None:
        with patch("sys.stdout", new=io.StringIO()) as fake_output:
            with self.assertRaises(SystemExit) as cm:
                main(["--payload", "invalid_json", "--secret", "mysecret"])
            output = fake_output.getvalue()
            self.assertIn("Invalid JSON for payload:", output)
            self.assertEqual(cm.exception.code, 1)

    def test_verified_header_failure(self) -> None:
        # Patch get_verified_header to force it to raise an exception.
        with patch(
            "jwt_example.get_verified_header",
            side_effect=Exception("Verification error"),
        ):
            with patch("sys.stdout", new=io.StringIO()) as fake_output:
                main(["--payload", '{"hello": "world"}', "--secret", "mysecret"])
                output = fake_output.getvalue()
                self.assertIn("Header verification failed: Verification error", output)

    def test_main_decode_success(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        with patch("sys.stdout", new=io.StringIO()) as fake_output:
            main(["--decode", "--token", token, "--secret", secret])
            output = fake_output.getvalue()
            self.assertIn("Decoded payload:", output)
            self.assertIn("Verified header:", output)
            self.assertIn("'hello': 'world'", output)

    def test_main_decode_no_token(self) -> None:
        with patch("sys.stdout", new=io.StringIO()) as fake_output:
            with self.assertRaises(SystemExit) as cm:
                main(["--decode", "--secret", "mysecret"])
            output = fake_output.getvalue()
            self.assertIn("Error: --decode flag requires a --token argument", output)
            self.assertEqual(cm.exception.code, 1)

    def test_main_decode_no_verify_success(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        with patch("sys.stdout", new=io.StringIO()) as fake_output:
            main(["--decode", "--no-verify", "--token", token, "--secret", secret])
            output = fake_output.getvalue()
            self.assertIn("Decoded payload:", output)
            self.assertIn("Verified header:", output)
            self.assertIn("'hello': 'world'", output)

    def test_main_decode_no_verify_invalid_token(self) -> None:
        secret = "mysecret"
        invalid_token = "invalid.token.value"
        with patch("sys.stdout", new=io.StringIO()) as fake_output:
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "--decode",
                        "--no-verify",
                        "--token",
                        invalid_token,
                        "--secret",
                        secret,
                    ]
                )
            output = fake_output.getvalue()
            self.assertIn("Decoding failed:", output)
            self.assertEqual(cm.exception.code, 1)

    def test_main_decode_wrong_secret(self) -> None:
        # Generate a valid token.
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        wrong_secret = "wrongsecret"
        with patch("sys.stdout", new=io.StringIO()) as fake_output:
            with self.assertRaises(SystemExit) as cm:
                main(["--decode", "--token", token, "--secret", wrong_secret])
            output = fake_output.getvalue()
            self.assertIn("Decoding failed:", output)
            self.assertEqual(cm.exception.code, 1)

    def test_main_no_verify_header_extraction_failure(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        # Force header extraction to fail in no-verify mode.
        with patch("jwt.get_unverified_header", side_effect=Exception("Extraction error")):
            with patch("sys.stdout", new=io.StringIO()) as fake_output:
                main(["--decode", "--no-verify", "--token", token, "--secret", secret])
                output = fake_output.getvalue()
                self.assertIn("Header extraction failed: Extraction error", output)


class TestJWTAdditionalFunctionality(unittest.TestCase):
    def test_token_with_nbf_future(self) -> None:
        payload = {
            "hello": "world",
            "nbf": datetime.datetime.utcnow() + datetime.timedelta(seconds=10),
        }
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        with self.assertRaises(jwt.exceptions.ImmatureSignatureError):  # type: ignore[attr-defined]
            decode_simple_jwt(token, secret)

    def test_token_with_issuer(self) -> None:
        payload = {"hello": "world", "iss": "test_issuer"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        decoded = jwt.decode(token, secret, algorithms=["HS256"], issuer="test_issuer")
        self.assertEqual(decoded.get("iss"), "test_issuer")

    def test_token_with_audience(self) -> None:
        payload = {"hello": "world", "aud": "test_audience"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="test_audience")
        self.assertEqual(decoded.get("aud"), "test_audience")

    def test_token_with_kid(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        kid = "key-id-1"
        token = create_simple_jwt(payload, secret, kid=kid)
        header = jwt.get_unverified_header(token)
        self.assertEqual(header.get("kid"), kid)


class TestJWTHeaderVerification(unittest.TestCase):
    def test_get_verified_header_with_kid(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        kid = "test-kid"
        token = create_simple_jwt(payload, secret, kid=kid)
        header = get_verified_header(token, secret)
        self.assertEqual(header.get("kid"), kid)

    def test_get_verified_header_invalid_signature(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        wrong_secret = "wrongsecret"
        with self.assertRaises(Exception):
            get_verified_header(token, wrong_secret)


class TestJWTExtendedFunctionality(unittest.TestCase):
    def test_token_with_iat(self) -> None:
        import time

        payload = {"hello": "world", "iat": int(time.time())}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        decoded = decode_simple_jwt(token, secret)
        self.assertIn("iat", decoded)
        self.assertAlmostEqual(decoded["iat"], int(time.time()), delta=5)

    def test_token_with_jti(self) -> None:
        payload = {"hello": "world", "jti": "unique-token-id-123"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        decoded = decode_simple_jwt(token, secret)
        self.assertEqual(decoded.get("jti"), "unique-token-id-123")

    def test_token_with_custom_header(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        headers = {"custom": "custom-value", "kid": "custom-kid"}
        token = jwt.encode(payload, secret, algorithm="HS256", headers=headers)
        header = jwt.get_unverified_header(token)
        self.assertEqual(header.get("custom"), "custom-value")
        self.assertEqual(header.get("kid"), "custom-kid")

    def test_algorithm_mismatch(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        token = create_simple_jwt(payload, secret)
        with self.assertRaises(jwt.exceptions.InvalidAlgorithmError):  # type: ignore[attr-defined]
            jwt.decode(token, secret, algorithms=["RS256"])


class TestJWTAlgorithmParameter(unittest.TestCase):
    def test_algorithm_parameter(self) -> None:
        payload = {"hello": "world"}
        secret = "mysecret"
        # Use a different algorithm, for example "HS384"
        algorithm = "HS384"
        token = create_simple_jwt(payload, secret, algorithm=algorithm)
        header = jwt.get_unverified_header(token)
        self.assertEqual(header.get("alg"), algorithm)
        # Also verify that decode works with the specified algorithm.
        decoded = decode_simple_jwt(token, secret, algorithm=algorithm)
        self.assertEqual(decoded, payload)


if __name__ == "__main__":
    unittest.main()
