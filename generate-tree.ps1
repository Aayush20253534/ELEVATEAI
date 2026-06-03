# Excluded directories
$exclude = @(
    "node_modules",
    ".git",
    ".next",
    "dist",
    "build",
    ".vercel",
    ".cache",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache"
)

function Get-Tree {
    param(
        [string]$Path = ".",
        [string]$Prefix = ""
    )

    Get-ChildItem -Path $Path | Where-Object {
        $_.Name -notin $exclude
    } | Sort-Object -Property @("PSIsContainer", "Name") -Descending | ForEach-Object {
        Write-Output "$Prefix+-- $($_.Name)"
        if ($_.PSIsContainer) {
            Get-Tree -Path $_.FullName -Prefix "$Prefix|   "
        }
    }
}

# Generate the tree and save to file
Get-Tree | Out-File "project-architecture.txt"