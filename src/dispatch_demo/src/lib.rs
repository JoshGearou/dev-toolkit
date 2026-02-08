// Main library code
pub trait Speak {
    fn speak(&self) -> String;
}

pub struct Dog;

impl Speak for Dog {
    fn speak(&self) -> String {
        "Woof!".to_string()
    }
}

pub struct Cat;

impl Speak for Cat {
    fn speak(&self) -> String {
        "Meow!".to_string()
    }
}

// Static Dispatch
pub fn static_dispatch<T: Speak>(animal: &T) -> String {
    animal.speak()
}

// Dynamic Dispatch
pub fn dynamic_dispatch(animal: &dyn Speak) -> String {
    animal.speak()
}

// Unit tests go inside the same file, under a `#[cfg(test)]` module.
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_static_dispatch() {
        let dog = Dog;
        let cat = Cat;
        assert_eq!(static_dispatch(&dog), "Woof!");
        assert_eq!(static_dispatch(&cat), "Meow!");
    }

    #[test]
    fn test_dynamic_dispatch() {
        let dog = Dog;
        let cat = Cat;
        assert_eq!(dynamic_dispatch(&dog), "Woof!");
        assert_eq!(dynamic_dispatch(&cat), "Meow!");
    }
}
