### Publication hygiene — preserve evidence, gate new artifacts

Existing experiments, FAILs, result stores, compiled research artifacts, tags and manifests remain preserved. No historical artifact is deleted or untracked by this change.

`.gitignore` reduces accidental additions; it cannot stop force-add or affect already tracked files. The publication-hygiene PR check inspects new destinations, including copies/renames, for bytecode, SQLite sidecars, compiled outputs, local-state filenames and ELF signatures. It does not execute submitted files. Existing tracked artifacts are grandfathered; review is still required for modifications to them. This is not a comprehensive secret scanner or malware detector.

### Activation and bootstrap

The workflow executes only the guard already present in the trusted PR base, with read-only permissions and no persisted checkout credentials. It never checks out or executes PR project code. During the initial PR, the guard is not yet on the default branch: the check deliberately fails closed with a bootstrap message if it runs. The owner must review the locally validated introduction before authorizing the initial merge. No automatic merge or bootstrap bypass is supplied.

After that merge, an administrator must make `publication-hygiene` a required check in the relevant branch rules and confirm direct pushes/bypass permissions match the intended policy. Until then, this is a proposed check, not enforced repository protection. The initial branch-rule change and any exception are owner-controlled. New intentionally published compiled evidence needs a separate reviewed policy exception, never a silent disable.

The workflow fetches at most 50 commits per ref. Missing ancestry fails closed; a maintainer may supply adequate history through an explicitly reviewed workflow change rather than accepting an uninspected diff.

### Local validation

Run only the new guard tests: `python .github/scripts/test_publication_hygiene.py -v`. They create small synthetic Git fixtures and do not run research programs, shipped executables or network calls. For a prepared commit, use `python .github/scripts/publication_hygiene.py --base <full-base-SHA> --head <full-head-SHA>`.
