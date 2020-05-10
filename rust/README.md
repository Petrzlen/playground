it has the annoying `;` after statements lol
variables are immutable by default, use `mut`, otherwise will get:
  `cannot borrow as mutable`
reference is a variable, so immutable by default, use `&mut`
`String` is utf-8 and growable
`associated function` in Rust are `static functions` in other langs, accessed by `::`
common return value is *enum* `Result`, with *variant* as possible values
*macros* have `!`
TODO: *bind*, *borrow*, *owned*
`traits`: functionality a type must provide (similar to Go interfaces, but explicit impl), like `impl HasArea for Circle`
`->` mypy like returns
WOW: `cardo doc --open`: shows docs for the accessible functionality, great to explore! much easier than jumping libraries online
TODO: Function overload? E.g. return variable determines which will be used: `let x u32: parse(...)` 
`loop` equals to `while(true)` in other languages

I kinda like how they updated established keywords to the new semantics (loop for while(true))

Error/Result Handling:
`.expect` (Result)
`match` is like swtich, has *arms* which have *pattern*, tldr: make sure you handle all options

Compiler:
the compiler has nice hints (like "consider adding `mut` to it)
warning: unused variable: `result`
return values must be used? otherwise: `warning: unused ... that must be used`
`std::prelude`: a set of standard libraries are inserted (`std`, `Result, `cmp`, `Vec`, ...)
`Cargo.lock` ensures reproducible builds (i.e. one has to explicitly upgrade a library with `cargo update`)
Type Checking
Can *shadow* previous variable names (e.g. `let guess: u32 = guess.trim ...`)
`RUST_BACKTRACE`

Crates:
A collection of Rust source code files. TODO: *binary crate* and *library crate*
*dependency* "5.0.0" is actually "^5.0.0" which is " "any version that has a public API compatible with version 0.5.5."
Semantic Versioning TLDR: MAJOR.MINOR.PATCH (semver.org)
