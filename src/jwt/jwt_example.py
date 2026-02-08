#!/usr/bin/env python3
import argparse
import base64
import json
import os
from typing import Any, Optional, cast

import jwt


def load_key(key_param: str) -> str:
    # If key_param is a path to an existing file, load its contents.
    if os.path.exists(key_param):
        try:
            with open(key_param, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Failed to load key from {key_param}: {e}")
            exit(1)
    return key_param


def create_simple_jwt(
    payload: dict[str, Any],
    key: str,
    kid: Optional[str] = None,
    algorithm: str = "HS256",
) -> str:
    headers = {"kid": kid} if kid is not None else None
    token = jwt.encode(payload, key, algorithm=algorithm, headers=headers)
    # jwt.encode returns str in PyJWT 2.x, but type stubs say bytes
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def decode_simple_jwt(token: str, key: str, algorithm: str = "HS256") -> dict[str, Any]:
    decoded = jwt.decode(token, key, algorithms=[algorithm])
    return decoded


def get_verified_header(token: str, key: str, algorithm: str = "HS256") -> dict[str, Any]:
    """
    Verifies the JWT token's signature using the provided key and specified algorithm,
    then extracts and returns the header.
    """
    # Verify token signature (will raise an exception if invalid)
    jwt.decode(token, key, algorithms=[algorithm])
    # Extract and decode the header segment (it's the first part of the token)
    header_segment = token.split(".")[0]
    header_segment += "=" * (-len(header_segment) % 4)  # Add padding if necessary.
    header_bytes = base64.urlsafe_b64decode(header_segment)
    header = cast(dict[str, Any], json.loads(header_bytes))
    return header


def main(args: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Create or decode a simple JWT token.")
    parser.add_argument(
        "--payload",
        type=str,
        default='{"hello": "world"}',
        help='JSON formatted payload (e.g., \'{"hello": "world"}\').',
    )
    parser.add_argument(
        "--secret",
        type=str,
        default="mysecret",
        help="Secret or private key for encoding the JWT. If this is a file path, the file will be read.",
    )
    parser.add_argument(
        "--pubkey",
        type=str,
        default=None,
        help="Path to a public key file to use for verifying the JWT (used when decoding with an asymmetric algorithm).",
    )
    parser.add_argument(
        "--kid",
        type=str,
        default=None,
        help="Optional key id to include in the JWT header.",
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="HS256",
        help="The algorithm to use for creating and decoding the JWT (default: HS256).",
    )
    parser.add_argument(
        "--decode",
        action="store_true",
        help="If set, decode an existing JWT token instead of creating one.",
    )
    parser.add_argument("--token", type=str, help="JWT token to decode when using --decode flag.")
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="If set (with --decode), skip signature verification when decoding.",
    )
    parsed_args = parser.parse_args(args)

    # Load the key from file if applicable.
    secret = load_key(parsed_args.secret)

    # If a public key is provided, load it.
    pubkey = None
    if parsed_args.pubkey:
        pubkey = load_key(parsed_args.pubkey)

    kid = parsed_args.kid
    algorithm = parsed_args.algorithm

    # For verification during decode, if a public key was provided, use that;
    # otherwise, use the secret.
    key_for_verification = pubkey if pubkey is not None else secret

    if parsed_args.decode:
        if not parsed_args.token:
            print("Error: --decode flag requires a --token argument to be provided.")
            exit(1)
        token = parsed_args.token
        if parsed_args.no_verify:
            try:
                # Decode without verifying the signature.
                decoded_payload = jwt.decode(token, options={"verify_signature": False})
            except Exception as e:
                print("Decoding failed:", e)
                exit(1)
            try:
                # Extract header without verifying the signature.
                header = jwt.get_unverified_header(token)
            except Exception as e:
                print("Header extraction failed:", e)
                header = None
        else:
            try:
                decoded_payload = decode_simple_jwt(token, key_for_verification, algorithm=algorithm)
            except Exception as e:
                print("Decoding failed:", e)
                exit(1)
            try:
                header = get_verified_header(token, key_for_verification, algorithm=algorithm)
            except Exception as e:
                print("Header verification failed:", e)
                header = None
        print("Decoded payload:")
        print(decoded_payload)
        if header is not None:
            print("Verified header:")
            print(header)
    else:
        try:
            payload = json.loads(parsed_args.payload)
        except json.JSONDecodeError as e:
            print("Invalid JSON for payload:", e)
            exit(1)
        token = create_simple_jwt(payload, secret, kid=kid, algorithm=algorithm)
        print("Generated JWT token:")
        print(token)
        try:
            decoded_payload = decode_simple_jwt(token, secret, algorithm=algorithm)
        except Exception as e:
            print("Decoding failed:", e)
            exit(1)
        print("Decoded payload:")
        print(decoded_payload)
        try:
            header = get_verified_header(token, secret, algorithm=algorithm)
        except Exception as e:
            print("Header verification failed:", e)
            header = None
        if header is not None:
            print("Verified header:")
            print(header)


if __name__ == "__main__":
    main()
