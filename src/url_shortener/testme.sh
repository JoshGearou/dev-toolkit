#!/bin/bash
set -e

# Minimum required Node.js version
MIN_NODE_VERSION="16.0.0"

# Function to compare semantic versions
version_gte() {
    printf '%s\n' "$1" "$2" | sort -V | head -n1 | grep -q "^$2$"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js to run the tests."
    exit 1
fi

# Check Node.js version
node -v
NODE_VERSION=$(node -v | sed 's/v//')
if ! version_gte "$NODE_VERSION" "$MIN_NODE_VERSION"; then
    echo "Node.js version $MIN_NODE_VERSION or higher is required. You have $NODE_VERSION."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm to run the tests."
    exit 1
fi

# Install specific versions of dependencies for Node.js v16.19.0
echo "Ensuring compatible versions of dependencies..."
npm install --save-dev chai-http@4.3.0
npm install --save-dev @types/chai-http@3.0.5
npm install --save-dev chai@4.3.6
npm install --save-dev @types/chai@4.3.4
npm install --save-dev typescript@4.7.4
npm install --save-dev ts-node@10.9.1
npm install --save-dev mocha@9.2.2
npm install --save-dev @types/mocha@9.1.1
npm install --save-dev murmurhash3js@3.0.1
npm install --save-dev @types/murmurhash3js@3.0.1

# Check and update tsconfig.json
if [ ! -f "tsconfig.json" ]; then
    echo "Creating tsconfig.json..."
    cat <<EOF > tsconfig.json
{
    "compilerOptions": {
        "module": "commonjs",
        "target": "es6",
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "types": ["node", "mocha", "chai-http"],
        "moduleResolution": "node"
    },
    "include": ["./test/**/*.ts"]
}
EOF
else
    echo "tsconfig.json exists. Ensure it includes 'mocha' and 'chai-http' in 'types'."
fi

# Run the tests with Mocha
echo "Running tests..."
if ! NODE_OPTIONS="--loader ts-node/esm" npx mocha --extension ts --exit "test/**/*.test.ts"; then
    echo "Tests failed."
    exit 1
fi

echo "Tests passed successfully."
exit 0
