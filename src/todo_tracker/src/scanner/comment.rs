/// Comment syntax definitions per language.
///
/// Maps file extensions to their comment delimiters so the scanner
/// can identify comment regions before extracting TODO patterns.
#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct CommentSyntax {
    /// Line comment prefixes for this language.
    pub line_comment: Vec<&'static str>,
    /// Block comment delimiter pairs (start, end) for this language.
    pub block_comment: Vec<(&'static str, &'static str)>,
}

impl CommentSyntax {
    /// Look up comment syntax by file extension.
    /// Returns a permissive fallback for unknown extensions.
    pub fn for_extension(ext: &str) -> Self {
        match ext {
            // C-family: // and /* */
            "rs" | "go" | "java" | "js" | "jsx" | "ts" | "tsx" | "c" | "cpp" | "cc" | "h"
            | "hpp" | "cs" | "swift" | "kt" | "kts" | "scala" | "groovy" | "dart" | "m" | "mm"
            | "zig" => Self {
                line_comment: vec!["//"],
                block_comment: vec![("/*", "*/")],
            },

            // Hash comment languages
            "py" | "rb" | "sh" | "bash" | "zsh" | "fish" | "pl" | "pm" | "r" | "R" | "yaml"
            | "yml" | "toml" | "ini" | "conf" | "cfg" | "tf" | "tfvars" | "Makefile" | "mk"
            | "cmake" | "dockerfile" | "Dockerfile" | "gitignore" | "dockerignore"
            | "editorconfig" => Self {
                line_comment: vec!["#"],
                block_comment: vec![],
            },

            // Python also has docstrings, but we treat # as the comment marker.
            // Docstring TODOs are a known limitation in regex mode.

            // HTML/XML family
            "html" | "htm" | "xml" | "xhtml" | "svg" | "vue" | "svelte" => Self {
                line_comment: vec![],
                block_comment: vec![("<!--", "-->")],
            },

            // CSS family
            "css" | "scss" | "sass" | "less" => Self {
                line_comment: vec!["//"],
                block_comment: vec![("/*", "*/")],
            },

            // SQL
            "sql" => Self {
                line_comment: vec!["--"],
                block_comment: vec![("/*", "*/")],
            },

            // Haskell
            "hs" => Self {
                line_comment: vec!["--"],
                block_comment: vec![("{-", "-}")],
            },

            // Lisp family
            "lisp" | "cl" | "el" | "clj" | "cljs" | "cljc" | "edn" | "scm" | "rkt" => Self {
                line_comment: vec![";"],
                block_comment: vec![],
            },

            // Lua
            "lua" => Self {
                line_comment: vec!["--"],
                block_comment: vec![("--[[", "]]")],
            },

            // Erlang/Elixir
            "erl" | "hrl" => Self {
                line_comment: vec!["%"],
                block_comment: vec![],
            },
            "ex" | "exs" => Self {
                line_comment: vec!["#"],
                block_comment: vec![],
            },

            // Vim
            "vim" => Self {
                line_comment: vec!["\""],
                block_comment: vec![],
            },

            // Batch
            "bat" | "cmd" => Self {
                line_comment: vec!["REM", "::"],
                block_comment: vec![],
            },

            // PowerShell
            "ps1" | "psm1" | "psd1" => Self {
                line_comment: vec!["#"],
                block_comment: vec![("<#", "#>")],
            },

            // Fallback: try common delimiters
            _ => Self {
                line_comment: vec!["//", "#", "--"],
                block_comment: vec![("/*", "*/")],
            },
        }
    }

    /// Check if a line (trimmed) starts with any known line comment prefix.
    #[allow(dead_code)]
    pub fn is_line_comment(&self, trimmed_line: &str) -> bool {
        self.line_comment
            .iter()
            .any(|prefix| trimmed_line.starts_with(prefix))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rust_syntax() {
        let syntax = CommentSyntax::for_extension("rs");
        assert_eq!(syntax.line_comment, vec!["//",]);
        assert_eq!(syntax.block_comment, vec![("/*", "*/")]);
    }

    #[test]
    fn python_syntax() {
        let syntax = CommentSyntax::for_extension("py");
        assert_eq!(syntax.line_comment, vec!["#"]);
        assert!(syntax.block_comment.is_empty());
    }

    #[test]
    fn unknown_extension_uses_fallback() {
        let syntax = CommentSyntax::for_extension("obscurelang");
        assert!(!syntax.line_comment.is_empty());
    }
}
