# Git Recovery Guide

This guide covers common Git problems for the Cricket Elo repository. The safest general rule is: **inspect the repository, preserve work, and only then change history or files**.

## 1. Start Every Recovery Here

Run these commands before attempting a fix:

```bash
git status
git diff
git diff --staged
git log --oneline --decorate --graph -15
```

They answer four important questions:

- Which branch am I on?
- Which files have changed?
- Which changes are staged?
- What are the most recent commits?

Do not use `git reset --hard`, `git clean -fd`, or force-push while diagnosing a problem. Those commands can make uncommitted work difficult to recover.

## 2. I Have Uncommitted Changes

### The changes belong on the current branch

Review and commit them normally:

```bash
git diff
git add <files>
git diff --staged
git commit -m "Describe the completed change"
```

Prefer listing the files explicitly instead of using `git add .`, particularly when the working directory contains generated data.

### The changes belong on a new branch

Create the branch without discarding the working changes:

```bash
git switch -c <new-branch-name>
```

The uncommitted changes normally move with you to the new branch. Check with `git status` before committing.

### I need to put the changes aside temporarily

Store tracked and untracked changes in a named stash:

```bash
git stash push -u -m "Temporary work before updating main"
git stash list
```

Restore the work with `apply` first:

```bash
git stash apply stash@{0}
git status
```

`git stash apply` keeps the stash as a backup. Once the restored work has been checked and committed, remove the saved stash with:

```bash
git stash drop stash@{0}
```

## 3. My Feature Branch Is Behind `main`

First make sure the working tree is clean. Then update local `main` and merge it into the feature branch:

```bash
git switch main
git pull --ff-only
git switch <feature-branch>
git merge main
```

Run the project checks after the merge. If everything works, push the updated branch:

```bash
git push
```

Merging `main` is the simplest approach while learning. Rebasing can produce a cleaner history, but it also rewrites commit identities and should only be used when its consequences are understood.

## 4. I Have a Merge Conflict

Git pauses the merge instead of guessing which changes to keep.

1. List the conflicted files:

   ```bash
   git status
   ```

2. Open each file and find conflict markers:

   ```text
   <<<<<<< HEAD
   current branch version
   =======
   incoming version
   >>>>>>> main
   ```

3. Edit the file into the correct final version and remove all three marker lines.

4. Mark each resolved file:

   ```bash
   git add <resolved-file>
   ```

5. Confirm that no conflicts remain and complete the merge:

   ```bash
   git status
   git commit
   ```

If the merge was started by mistake, return to the state before it began with:

```bash
git merge --abort
```

If Git reports that a rebase, rather than a merge, is in progress, use `git rebase --abort` instead.

## 5. I Staged the Wrong File

Remove it from the staging area without deleting the working copy:

```bash
git restore --staged <file>
```

Check the result with:

```bash
git status
git diff
```

## 6. I Committed Something Incorrect

### The commit has already been pushed

Create a new commit that reverses it:

```bash
git log --oneline
git revert <commit-hash>
git push
```

`git revert` preserves the existing shared history and is normally safer than resetting or force-pushing.

### The latest commit has not been pushed

If only the commit message is wrong:

```bash
git commit --amend -m "Correct commit message"
```

If files were missing, stage them first and then amend:

```bash
git add <missing-files>
git commit --amend --no-edit
```

Only amend commits that have not been shared with other people.

## 7. I Cannot Find a Commit or Deleted a Branch

Git's reference log records recent movements of `HEAD`:

```bash
git reflog
```

When the missing commit is identified, protect it immediately by creating a recovery branch:

```bash
git branch recovery/<short-description> <commit-hash>
git switch recovery/<short-description>
```

Inspect the files and history before deciding whether to merge or cherry-pick the recovered work.

## 8. I Am in a Detached `HEAD` State

First inspect the current commit:

```bash
git status
git log --oneline -5
```

If the current work should be kept, create a branch before switching away:

```bash
git switch -c recovery/detached-work
```

You can then commit the work and merge it through a normal pull request.

## 9. `main` and GitHub Do Not Match

Inspect the relationship without modifying anything:

```bash
git fetch origin
git status
git log --oneline --left-right main...origin/main
```

If local `main` is simply behind and contains no unique commits:

```bash
git switch main
git pull --ff-only
```

If both sides contain different commits, stop and inspect them before choosing a merge or rebase. Do not force-push `main` merely to make the warning disappear.

## 10. Clean Up a Merged Feature Branch

After its pull request has been merged:

```bash
git switch main
git pull --ff-only
git branch --merged main
git branch -d <feature-branch>
```

The lowercase `-d` refuses to delete a branch Git believes is unmerged, providing an additional safety check.

## 11. Before Every Cricket Elo Pull Request

Use this short checklist:

- [ ] I am on the intended feature branch.
- [ ] `git status` shows only changes relevant to this PR.
- [ ] Raw JSON, processed CSV files, outputs, virtual environments and `__pycache__` are not staged.
- [ ] I reviewed `git diff` before staging.
- [ ] I reviewed `git diff --staged` before committing.
- [ ] The documented commands still run.
- [ ] All available tests pass.
- [ ] Commit messages explain the completed change.
- [ ] I reviewed the pull-request diff before merging.
- [ ] After merging, local `main` was updated with `git pull --ff-only`.

## Emergency Principle

If the correct recovery action is unclear, stop after `git status`, preserve the work with a new branch or named stash, and inspect the history. Most Git mistakes remain recoverable while their commits and working files have not been deliberately discarded.
