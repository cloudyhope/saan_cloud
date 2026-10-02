param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))

if ((git branch --show-current) -ne 'test') { throw 'Run from the private test branch.' }
if (git status --porcelain) { throw 'Commit all intended changes before syncing.' }
if ((git remote get-url origin) -ne 'https://git.cloubit.com/saanapp/mono.git') {
    throw 'Unexpected private origin remote.'
}
if ((git remote get-url github) -ne 'https://github.com/cloudyhope/saan_cloud.git') {
    throw 'Unexpected public GitHub remote.'
}

python scripts/check_public_snapshot.py HEAD
if ($LASTEXITCODE -ne 0) { throw 'Public snapshot audit failed.' }

$source = (git rev-parse HEAD).Trim()
$tree = (git rev-parse 'HEAD^{tree}').Trim()
$remoteLine = git ls-remote --heads github test
if ($LASTEXITCODE -ne 0) { throw 'Cannot read the GitHub branch.' }
$previous = if ($remoteLine) { ($remoteLine -split '\s+')[0] } else { $null }
if ($previous) {
    git fetch github refs/heads/test:refs/remotes/github/test
    if ($LASTEXITCODE -ne 0) { throw 'Cannot fetch the GitHub branch.' }
    $previousTree = (git rev-parse 'refs/remotes/github/test^{tree}').Trim()
}

if ($DryRun) {
    Write-Output "Ready to push private test $source and a public snapshot from tree $tree."
    exit 0
}

git push origin HEAD:refs/heads/test
if ($LASTEXITCODE -ne 0) { throw 'Private push failed; public push was not attempted.' }

if ($previousTree -eq $tree) {
    Write-Output 'GitHub already has the same sanitized tree.'
    exit 0
}

$message = "Synchronize sanitized Saan source from private test $source"
$snapshot = if ($previous) {
    (git commit-tree $tree -p $previous -m $message).Trim()
} else {
    (git commit-tree $tree -m $message).Trim()
}
if ($LASTEXITCODE -ne 0 -or -not $snapshot) { throw 'Could not create public snapshot commit.' }

git push github "${snapshot}:refs/heads/test"
if ($LASTEXITCODE -ne 0) { throw 'GitHub push failed; private push succeeded. Rerun to retry.' }

Write-Output "Both test branches now contain the same source tree $tree."
