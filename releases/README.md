# Official combinations

Add reviewed `f8platformRelease/1` JSON locks here after publisher artifacts are
available. Artifact kinds are `runtime` (launcher) and `extension` (all capabilities).
Applications are extensions with an `application` launch declaration, not a second
package ecosystem. `startup` contains their extension IDs.

Example structure (replace placeholders with real artifact metadata before use):

```json
{
  "schemaVersion": "f8platformRelease/1",
  "platform": "linux-x86_64",
  "baseRuntime": "platform-runtime",
  "startup": ["webstudio"],
  "artifacts": [
    {"artifactId": "platform-runtime", "version": "<version>", "kind": "runtime", "location": "<HTTPS URL or local ZIP>", "sha256": "<SHA-256>"},
    {"artifactId": "media-gateway", "version": "<version>", "kind": "extension", "location": "<HTTPS URL or local ZIP>", "sha256": "<SHA-256>"},
    {"artifactId": "webstudio", "version": "<version>", "kind": "extension", "location": "<HTTPS URL or local ZIP>", "sha256": "<SHA-256>"}
  ]
}
```

A desktop combination starts WebStudio and its declared providers. A headless
combination omits the UI and selects only the required service/tool extensions.
Use `local-*.json` for unpublished local artifact tests; they are not committed.
