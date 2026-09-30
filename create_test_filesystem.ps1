# ==============================================================
# MOCKAPP Filesystem Agent Test Data Generator
# ==============================================================
#
# Creates:
#
# X:\MOCKAPP\test_filesystem\
#   ├── Level_1\
#   │   ├── File_1.txt
#   │   ├── File_2.txt
#   │   ├── ...
#   │   └── Level_2\
#   │       └── ...
#   │
#   └── ...
#
# Each folder contains 5 text files.
# Each text file contains dictionary words and meanings.
#
# ==============================================================

$Root = "X:\MOCKAPP\test_filesystem"

$Depth = 5
$FilesPerFolder = 5

# --------------------------------------------------------------
# Dictionary data
# --------------------------------------------------------------

$Dictionary = @(
    "Abundant - existing in large quantities",
    "Benevolent - well meaning and kindly",
    "Candid - truthful and straightforward",
    "Diligent - showing careful and persistent effort",
    "Eloquent - fluent or persuasive in speaking or writing",
    "Ephemeral - lasting for a very short time",
    "Frugal - economical with money or resources",
    "Gregarious - sociable and fond of company",
    "Impartial - treating all sides fairly",
    "Jubilant - feeling or expressing great happiness",
    "Keen - having an eager interest or enthusiasm",
    "Lucid - expressed clearly and easy to understand",
    "Meticulous - showing great attention to detail",
    "Novice - a person new to a particular activity",
    "Obsolete - no longer produced or used",
    "Pragmatic - dealing with problems realistically",
    "Resilient - able to recover quickly from difficulty",
    "Serene - calm, peaceful, and untroubled",
    "Tenacious - persistent and determined",
    "Ubiquitous - present or found everywhere",
    "Vigilant - keeping careful watch for danger or problems",
    "Wary - cautious about possible dangers",
    "Zealous - showing great energy or enthusiasm",
    "Ambiguous - open to more than one interpretation",
    "Coherent - logical and consistent",
    "Deteriorate - become progressively worse",
    "Endeavor - an attempt or effort to do something",
    "Formidable - inspiring fear or respect through being powerful",
    "Inevitable - certain to happen",
    "Versatile - able to adapt or be used for many purposes"
)

# --------------------------------------------------------------
# Create root
# --------------------------------------------------------------

if (-not (Test-Path -LiteralPath $Root)) {

    New-Item `
        -ItemType Directory `
        -Path $Root `
        -Force | Out-Null

    Write-Host "Created root: $Root"
}
else {

    Write-Host "Root already exists: $Root"
}

# --------------------------------------------------------------
# Helper: create a dictionary file
# --------------------------------------------------------------

function New-DictionaryFile {

    param (
        [string]$FilePath,
        [int]$FileNumber,
        [int]$Level
    )

    # Select five deterministic words based on file/level.
    $StartIndex = (($Level - 1) * 5 + ($FileNumber - 1) * 5) % $Dictionary.Count

    $Entries = @()

    for ($i = 0; $i -lt 5; $i++) {

        $Index = ($StartIndex + $i) % $Dictionary.Count

        $Entries += $Dictionary[$Index]
    }

    $Content = @(
        "MOCKAPP Filesystem Agent Test File"
        "=================================="
        ""
        "Level: $Level"
        "File: $FileNumber"
        ""
        "Dictionary Entries"
        "------------------"
        ""
    )

    $Content += $Entries

    $Content += @(
        ""
        "End of dictionary entries."
    )

    Set-Content `
        -LiteralPath $FilePath `
        -Value $Content `
        -Encoding UTF8
}

# --------------------------------------------------------------
# Create nested folders
# --------------------------------------------------------------

$CurrentPath = $Root

for ($Level = 1; $Level -le $Depth; $Level++) {

    $FolderName = "Level_$Level"

    $CurrentPath = Join-Path `
        -Path $CurrentPath `
        -ChildPath $FolderName

    New-Item `
        -ItemType Directory `
        -Path $CurrentPath `
        -Force | Out-Null

    Write-Host ""
    Write-Host "Created: $CurrentPath"

    # ----------------------------------------------------------
    # Create five text files in this folder
    # ----------------------------------------------------------

    for ($FileNumber = 1; $FileNumber -le $FilesPerFolder; $FileNumber++) {

        $FileName = "Dictionary_$FileNumber.txt"

        $FilePath = Join-Path `
            -Path $CurrentPath `
            -ChildPath $FileName

        New-DictionaryFile `
            -FilePath $FilePath `
            -FileNumber $FileNumber `
            -Level $Level

        Write-Host "  Created: $FileName"
    }
}

# --------------------------------------------------------------
# Summary
# --------------------------------------------------------------

$FolderCount = (
    Get-ChildItem `
        -LiteralPath $Root `
        -Directory `
        -Recurse
).Count

$FileCount = (
    Get-ChildItem `
        -LiteralPath $Root `
        -File `
        -Recurse `
        -Filter "*.txt"
).Count

Write-Host ""
Write-Host "=============================================================="
Write-Host "MOCKAPP test filesystem created successfully."
Write-Host "=============================================================="
Write-Host "Root:    $Root"
Write-Host "Folders: $FolderCount"
Write-Host "Files:   $FileCount"
Write-Host "=============================================================="