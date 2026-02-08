// Sample Go file for testing TODO extraction.
package main

import "fmt"

func main() {
	// TODO: add CLI argument parsing
	fmt.Println("hello")

	// FIXME: goroutine leak when context is cancelled
	go worker()

	// HACK(PROJ-567): bypass rate limiter for internal calls
}

func worker() {
	// XXX: placeholder implementation
}
