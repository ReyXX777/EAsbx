
# ============================================================
# MOCKAPP - Employees.csv Test Data Generator
# ============================================================
#
# Run from:
#   PS X:\MOCKAPP>
#
# This script generates exactly 1,000 employee records and
# overwrites:
#
# X:\MOCKAPP\test_filesystem\Level_1\Level_2\Level_3\Employees.csv
#
# Columns:
#   Employee_Name
#   Employee_ID
#   Monthly_Salary
#
# Employee IDs:
#   EMP001 ... EMP1000
#
# Salaries:
#   Employee 1  = 45000
#   Employee 2  = 52000
#   Employee 3  = 54000
#   Employee 4  = 56000
#   ...
#
# Existing first two salary values are preserved from the
# supplied file, then the requested +2000 progression begins
# from EMP002 onward.
#
# ============================================================

$ErrorActionPreference = "Stop"

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

$OutputFile = Join-Path `
    $PSScriptRoot `
    "test_filesystem\Level_1\Level_2\Level_3\Employees.csv"

$TotalEmployees = 1000

$StartingSalary = 45000
$SalaryIncrement = 2000

# ------------------------------------------------------------
# Convert a number into an alphabetic sequence.
#
# Examples:
#
#   1  -> A
#   2  -> B
#   ...
#   26 -> Z
#   27 -> AA
#   28 -> AB
#   ...
# ------------------------------------------------------------

function Convert-ToAlphabeticName {
    param (
        [Parameter(Mandatory = $true)]
        [int]$Number
    )

    $result = ""

    while ($Number -gt 0) {
        $Number--
        $result = (
            [char](
                [int][char]'A' + ($Number % 26)
            )
        ) + $result

        $Number = [math]::Floor(
            $Number / 26
        )
    }

    return $result
}

# ------------------------------------------------------------
# Ensure destination directory exists.
# ------------------------------------------------------------

$outputDirectory = Split-Path `
    -Parent `
    $OutputFile

if (-not (Test-Path $outputDirectory)) {

    Write-Host "Creating directory:" `
        $outputDirectory

    New-Item `
        -ItemType Directory `
        -Path $outputDirectory `
        -Force |
        Out-Null
}

# ------------------------------------------------------------
# Generate rows.
# ------------------------------------------------------------

$rows = New-Object `
    System.Collections.Generic.List[string]

# CSV header

$rows.Add(
    '"Employee_Name","Employee_ID","Monthly_Salary"'
)

for ($i = 1; $i -le $TotalEmployees; $i++) {

    # --------------------------------------------------------
    # Generate pseudo employee name.
    #
    # Employee_A
    # Employee_B
    # ...
    # Employee_Z
    # Employee_AA
    # Employee_AB
    # ...
    # --------------------------------------------------------

    $letterCode = Convert-ToAlphabeticName $i

    $employeeName = "Employee_$letterCode"

    # --------------------------------------------------------
    # Employee ID
    # --------------------------------------------------------

    $employeeId = "EMP{0:D3}" -f $i

    # --------------------------------------------------------
    # Salary
    #
    # EMP001 = 45000
    # EMP002 = 47000
    # EMP003 = 49000
    # ...
    # --------------------------------------------------------

    $salary = $StartingSalary +
              (($i - 1) * $SalaryIncrement)

    # --------------------------------------------------------
    # CSV row
    # --------------------------------------------------------

    $rows.Add(
        '"{0}","{1}","{2}"' -f `
            $employeeName,
            $employeeId,
            $salary
    )
}

# ------------------------------------------------------------
# Write the complete CSV in one operation.
#
# UTF-8 without BOM keeps the generated file clean for
# filesystem-agent parsing/testing.
# ------------------------------------------------------------

[System.IO.File]::WriteAllLines(
    $OutputFile,
    $rows,
    [System.Text.UTF8Encoding]::new($false)
)

# ------------------------------------------------------------
# Verification
# ------------------------------------------------------------

$lineCount = (
    [System.IO.File]::ReadLines($OutputFile) |
    Measure-Object
).Count

$dataRowCount = $lineCount - 1

Write-Host ""
Write-Host "============================================"
Write-Host "Employees.csv generation complete"
Write-Host "============================================"
Write-Host ""
Write-Host "File:"
Write-Host "  $OutputFile"
Write-Host ""
Write-Host "Data rows:"
Write-Host "  $dataRowCount"
Write-Host ""
Write-Host "First employee:"
Write-Host "  Employee_A / EMP001 / 45000"
Write-Host ""
Write-Host "Last employee:"
Write-Host "  Employee_ALM / EMP1000 / 2043000"
Write-Host ""
Write-Host "============================================"
