#!/bin/bash

set -e

trap 'kill $SERVER_PID' EXIT

pushd server > /dev/null
cargo test -- --nocapture
popd > /dev/null

pushd server > /dev/null
cargo run &
SERVER_PID=$!
sleep 2
popd > /dev/null

pushd client > /dev/null
cargo test -- --nocapture
popd > /dev/null
