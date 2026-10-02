
# ============================================================
# MOCKAPP - Employees.csv Test Data Generator
# ============================================================
#
# Run from:
#   PS X:\MOCKAPP>
#
# Generates exactly 1,000 employee records and overwrites:
#
# X:\MOCKAPP\test_filesystem\Level_1\Level_2\Level_3\Employees.csv
#
# ============================================================

$ErrorActionPreference = "Stop"

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

$OutputFile = Join-Path $PSScriptRoot "test_filesystem\Level_1\Level_2\Level_3\Employees.csv"

$TotalEmployees = 1000

$StartingSalary = 45000
$SalaryIncrement = 2000

# ------------------------------------------------------------
# Convert number to alphabetic sequence.
#
# 1  -> A
# 2  -> B
# ...
# 26 -> Z
# 27 -> AA
# 28 -> AB
# ...
# 1000 -> ALM
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

        $Number = [math]::Floor($Number / 26)
    }

    return $result
}

# ------------------------------------------------------------
# Ensure destination directory exists.
# ------------------------------------------------------------

$outputDirectory = Split-Path -Parent $OutputFile

if (-not (Test-Path $outputDirectory)) {

    Write-Host "Creating directory:"
    Write-Host "  $outputDirectory"

    New-Item `
        -ItemType Directory `
        -Path $outputDirectory `
        -Force |
        Out-Null
}

# ------------------------------------------------------------
# Generate rows.
# ------------------------------------------------------------

$rows = New-Object System.Collections.Generic.List[string]

# Header

$rows.Add(
    '"Employee_Name","Employee_ID","Monthly_Salary"'
)

# ------------------------------------------------------------
# Generate employees.
# ------------------------------------------------------------

for ($i = 1; $i -le $TotalEmployees; $i++) {

    # --------------------------------------------------------
    # Pseudo name
    # --------------------------------------------------------

    $letterCode = Convert-ToAlphabeticName $i

    $employeeName = "Employee_$letterCode"

    # --------------------------------------------------------
    # Employee ID
    #
    # EMP001
    # EMP002
    # ...
    # EMP999
    # EMP1000
    # --------------------------------------------------------

    $employeeId = "EMP{0:D3}" -f $i

    # --------------------------------------------------------
    # Salary
    #
    # EMP001 = 45000
    # EMP002 = 47000
    # EMP003 = 49000
    # ...
    # EMP1000 = 2043000
    # --------------------------------------------------------

    $salary = $StartingSalary + (($i - 1) * $SalaryIncrement)

    # --------------------------------------------------------
    # Create CSV row.
    #
    # Keep this on ONE line so PowerShell's -f operator
    # cannot be confused by line continuation.
    # --------------------------------------------------------

    $csvRow = '"{0}","{1}","{2}"' -f $employeeName, $employeeId, $salary

    $rows.Add($csvRow)
}

# ------------------------------------------------------------
# Write complete CSV.
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

$firstSalary = $StartingSalary

$lastSalary = $StartingSalary + (($TotalEmployees - 1) * $SalaryIncrement)

$firstName = "Employee_$(Convert-ToAlphabeticName 1)"
$lastName = "Employee_$(Convert-ToAlphabeticName $TotalEmployees)"

$firstId = "EMP{0:D3}" -f 1
$lastId = "EMP{0:D3}" -f $TotalEmployees

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
Write-Host "  $firstName / $firstId / $firstSalary"
Write-Host ""

Write-Host "Last employee:"
Write-Host "  $lastName / $lastId / $lastSalary"
Write-Host ""

Write-Host "============================================"
