# Create or Update PR Command

Create a new pull request or update an existing PR for the current branch.

Usage: `/pr`

## What this does

1. Commits and pushes the current branch to the remote repository
2. Checks if a PR already exists for the current branch
3. If PR exists:
   - Updates the existing PR with any new commits
   - Updates the PR title and description to reflect the full git diff between the current branhc and the main brnach
4. If no PR exists:
   - Creates a new pull request using GitHub CLI
   - Auto-generates title and description based on commits

## Requirements

- Current branch must have unpushed commits (for new PRs) or new commits (for updates)
- GitHub CLI must be authenticated
- Branch must be different from main

## Example

```
/pr
```

This will either create a new PR or update an existing one, ensuring the PR title and description comprehensively reflects the current state of all changes in the branch.
