// Sample Rust file for testing TODO extraction.

fn main() {
    // TODO: implement main logic
    println!("hello");

    // FIXME(JIRA-1234): null pointer when list is empty
    let items: Vec<String> = Vec::new();

    // HACK: workaround for upstream bug
    let _result = items.len() + 1;

    // NOTE: order matters here, see RFC-2119
    process(&items);

    // TODO(rerickso, P1): add error handling for network calls
    fetch_data();
}

fn process(_items: &[String]) {
    // XXX: this is O(n^2), needs optimization
}

fn fetch_data() {
    // BUG: timeout not respected when server is unreachable
    // SAFETY: pointer is valid for the lifetime of the struct
}
