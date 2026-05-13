---
name: github-workflow
description: Guide for creating and editing GitHub Actions workflows following project conventions.
when_to_use: Use when creating a new workflow file, editing an existing workflow, or when discussing GitHub Actions configuration.
---

# GitHub Workflows

## Security

### Pinning action versions

Always pin actions to a full commit SHA, never to a tag or `@main`:

```yaml
uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
```

### Permissions

Declare permissions at the job level, not the workflow level. Request only what the job needs:

```yaml
jobs:
  my-job:
    permissions:
      contents: read
      pull-requests: write
```

## Testing

Validate locally before pushing with `act`:

```bash
act -j <job-id>       # run job locally
act -j <job-id> -n    # dry-run
```
