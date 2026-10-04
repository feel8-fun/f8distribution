# F8 Distribution

This repository selects and assembles official Feel8 releases. It contains no
launcher, SDK, WebStudio, Gateway or service source checkouts. Publishers own their
builds, tests, dependency solving and versioned artifacts.

A `f8platformRelease/1` lock pins launcher and extension identities, versions,
SHA-256 hashes, artifact locations and startup applications. The assembler loads
its SDK/platform tooling from the verified launcher artifact. It never compiles an
extension, builds a frontend, or solves application dependencies.

```sh
pixi run --locked assemble releases/<reviewed-lock>.json
pixi run --locked verify build/dist/f8-linux-x86_64.tar.gz
pixi run --locked test
```

Use `--output` for an empty output directory. Existing nonempty directories are
rejected. `--no-offline --no-archive` prepares a directory for inspection without
bundling the launcher interpreter. Launcher and applications are separate runtime
prefixes sharing the package cache; fully offline application preparation requires
prepopulating that cache.

The development workspace is the separate `f8studio` repository. Clone it when
changing code or jointly debugging extensions; this repository consumes releases.

There is no production release lock until the publisher artifacts have real release
locations and reviewed hashes. `releases/README.md` describes creating a lock from
local publisher artifacts for integration validation.
