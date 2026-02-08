#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

id-tool grestin sign-test --output-dir "$pwd"
openssl x509 -in ./identity.cert -pubkey -noout -out public.pem

# Create the virtual environment if it doesn't exist.
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate the virtual environment.
# shellcheck disable=SC1091
source venv/bin/activate

# Install (or upgrade) required packages.
echo "Installing/upgrading dependencies..."
pip install --upgrade pip
pip install --upgrade PyJWT coverage cryptography

# Determine the name of the main Python script from the shell script's name.
script_name=$(basename "${BASH_SOURCE[0]}" .sh)
py_script="${script_name}.py"

echo "------------------------------"
echo "Running ${py_script} WITHOUT kid using the virtual environment..."
python3 "$py_script" --payload '{"hello": "world"}' --secret "mysecret"

echo "------------------------------"
echo "Running ${py_script} WITH kid using the virtual environment..."
python3 "$py_script" --payload '{"hello": "world"}' --secret "mysecret" --kid "key-id-1"

echo "------------------------------"
echo "Running ${py_script} DECODE with secret using the virtual environment..."
python3 "$py_script" --decode --secret "mysecret" --token "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtleS1pZC0xIiwidHlwIjoiSldUIn0.eyJoZWxsbyI6IndvcmxkIn0.BZaw1w0xzhOotPdjkyrmQk32tjx70VFjTldXrda-Bwg"

echo "------------------------------"
echo "Running ${py_script} DECODE without secret using the virtual environment..."
python3 "$py_script" --decode --no-verify --token "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtleS1pZC0xIiwidHlwIjoiSldUIn0.eyJoZWxsbyI6IndvcmxkIn0.BZaw1w0xzhOotPdjkyrmQk32tjx70VFjTldXrda-Bwg"

echo "------------------------------"
echo "Running ${py_script} WITH RSA512 using the virtual environment..."
python3 "$py_script" --payload '{"sub": "spiffe://dev.lipki/v/2wl/login-server", "app": "login-server"}' --secret ./identity.key --pubkey ./public.pem --kid "8eb9d5256235926632fe02838e6c7062" --algorithm RS256

echo "------------------------------"
echo "Running unit tests with coverage..."
python3 -m coverage run -m unittest discover -v

echo "------------------------------"
echo "Coverage report:"
python3 -m coverage report -m

# Deactivate the virtual environment.
deactivate

rm -f identity.*
rm -f public.pem