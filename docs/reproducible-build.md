# Offline reproducible build

Build inputs are a reviewed, hash-locked wheelhouse (`wheelhouse.lock.json`) and digest-pinned Python base
image archived with the release. Dockerfiles intentionally have no default base
tag and use `pip --no-index --find-links=/wheelhouse`; a build without that cached
wheelhouse fails rather than downloading current packages. Generate and retain an
SBOM (CycloneDX or SPDX) from that exact wheelhouse, then invoke
`tools/generate-release-artifacts.py` with the commit and immutable image digests.

The checked-in `sbom.cdx.json` is a release-input template, not a claim that the
placeholder images were built. Replace it together with release-manifest.json
only after an offline build, vulnerability scan, and independent review.

## Approved two-phase procedure

Fetch phase (requires an explicit approval and access only to `pypi.org` and
`files.pythonhosted.org`): run `python tools/prepare-wheelhouse.py` to print the
exact commands, then run them in an isolated fetch environment. This resolves
all transitive requirements with hashes and downloads wheels. Return only the
wheelhouse and resolver output for review.

Offline phase: verify/copy that reviewed wheelhouse, run
`python tools/generate-wheelhouse-lock.py --wheelhouse wheelhouse --resolved requirements/resolved.txt`, build with Docker network disabled and `--build-arg PYTHON_IMAGE=<digest>`, export image inspection JSON, then run `tools/generate-sbom.py`. Finally run `tools/generate-release-artifacts.py` with current SHA and image digests. Each generator fails closed on placeholders or empty inputs.
