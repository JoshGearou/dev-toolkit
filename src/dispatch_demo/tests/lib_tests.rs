// Import the library.
use dispatch_demo::{Dog, Cat, static_dispatch, dynamic_dispatch};

#[test]
fn test_static_dispatch_integration() {
    let dog = Dog;
    let cat = Cat;
    assert_eq!(static_dispatch(&dog), "Woof!");
    assert_eq!(static_dispatch(&cat), "Meow!");
}

#[test]
fn test_dynamic_dispatch_integration() {
    let dog = Dog;
    let cat = Cat;
    assert_eq!(dynamic_dispatch(&dog), "Woof!");
    assert_eq!(dynamic_dispatch(&cat), "Meow!");
}
