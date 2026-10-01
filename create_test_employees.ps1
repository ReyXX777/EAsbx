
# ============================================================
# ADD EMPLOYEE CSV FILES TO EXISTING TEST FILESYSTEM
# ============================================================
#
# Run from:
#   X:\MOCKAPP
#
# IMPORTANT:
#   This script DOES NOT create test_filesystem.
#   This script DOES NOT create Level_1 ... Level_5.
#   This script DOES NOT modify existing Dictionary files.
#
# It only adds:
#
#   Employees.csv
#
# to the already-existing:
#
#   test_filesystem\Level_1
#   test_filesystem\Level_2
#   test_filesystem\Level_3
#   test_filesystem\Level_4
#   test_filesystem\Level_5
#
# ============================================================


# ------------------------------------------------------------
# Existing filesystem
# ------------------------------------------------------------

$RootFolder = Join-Path (Get-Location) "test_filesystem"


# ------------------------------------------------------------
# Safety check
# ------------------------------------------------------------

if (-not (Test-Path -LiteralPath $RootFolder -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR: Existing test_filesystem folder was not found." `
        -ForegroundColor Red

    Write-Host ""
    Write-Host "Expected:"
    Write-Host "  $RootFolder"

    Write-Host ""
    exit 1
}


# ------------------------------------------------------------
# Employee data
# ------------------------------------------------------------

$Employees = @(
    [PSCustomObject]@{
        Employee_Name  = "Aarav Sharma"
        Employee_ID    = "EMP001"
        Monthly_Salary = 45000
    }

    [PSCustomObject]@{
        Employee_Name  = "Priya Verma"
        Employee_ID    = "EMP002"
        Monthly_Salary = 52000
    }

    [PSCustomObject]@{
        Employee_Name  = "Rohan Kumar"
        Employee_ID    = "EMP003"
        Monthly_Salary = 48000
    }

    [PSCustomObject]@{
        Employee_Name  = "Ananya Singh"
        Employee_ID    = "EMP004"
        Monthly_Salary = 61000
    }

    [PSCustomObject]@{
        Employee_Name  = "Vikram Patel"
        Employee_ID    = "EMP005"
        Monthly_Salary = 57500
    }

    [PSCustomObject]@{
        Employee_Name  = "Neha Gupta"
        Employee_ID    = "EMP006"
        Monthly_Salary = 49500
    }

    [PSCustomObject]@{
        Employee_Name  = "Aditya Mehta"
        Employee_ID    = "EMP007"
        Monthly_Salary = 68000
    }

    [PSCustomObject]@{
        Employee_Name  = "Sneha Rao"
        Employee_ID    = "EMP008"
        Monthly_Salary = 55500
    }

    [PSCustomObject]@{
        Employee_Name  = "Karan Malhotra"
        Employee_ID    = "EMP009"
        Monthly_Salary = 63000
    }

    [PSCustomObject]@{
        Employee_Name  = "Isha Kapoor"
        Employee_ID    = "EMP010"
        Monthly_Salary = 72000
    }
)


# ------------------------------------------------------------
# Expected existing levels
# ------------------------------------------------------------

$Levels = @(
    "Level_1",
    "Level_2",
    "Level_3",
    "Level_4",
    "Level_5"
)


$CsvFileName = "Employees.csv"


# ------------------------------------------------------------
# Process each existing level
# ------------------------------------------------------------

Write-Host ""
Write-Host "Adding employee CSV files..." -ForegroundColor Cyan
Write-Host ""


foreach ($Level in $Levels) {

    # Build path to the existing level.
    #
    # Level_1:
    #   test_filesystem\Level_1
    #
    # Level_2:
    #   test_filesystem\Level_1\Level_2
    #
    # etc.

    $LevelNumber = [int]($Level -replace "Level_", "")

    $LevelPath = $RootFolder

    for ($i = 1; $i -le $LevelNumber; $i++) {

        $LevelPath = Join-Path `
            $LevelPath `
            "Level_$i"
    }


    # --------------------------------------------------------
    # Safety check:
    # Never create a missing level.
    # --------------------------------------------------------

    if (-not (Test-Path -LiteralPath $LevelPath -PathType Container)) {

        Write-Host ""
        Write-Host "ERROR: Expected existing folder is missing:" `
            -ForegroundColor Red

        Write-Host "  $LevelPath"
        Write-Host ""

        Write-Host "No new folder will be created."
        Write-Host ""

        exit 1
    }


    # --------------------------------------------------------
    # CSV path
    # --------------------------------------------------------

    $CsvPath = Join-Path `
        $LevelPath `
        $CsvFileName


    # --------------------------------------------------------
    # Safety check:
    # Don't overwrite an existing CSV.
    # --------------------------------------------------------

    if (Test-Path -LiteralPath $CsvPath -PathType Leaf) {

        Write-Host "SKIPPED:" -ForegroundColor Yellow
        Write-Host "  $CsvPath"
        Write-Host "  Employees.csv already exists."
        Write-Host ""

        continue
    }


    # --------------------------------------------------------
    # Create CSV
    # --------------------------------------------------------

    $Employees |
        Export-Csv `
            -LiteralPath $CsvPath `
            -NoTypeInformation `
            -Encoding UTF8


    Write-Host "ADDED:" -ForegroundColor Green
    Write-Host "  $CsvPath"
    Write-Host ""
}


# ------------------------------------------------------------
# Calculate expected total
# ------------------------------------------------------------

$ExpectedTotal = (
    $Employees |
        Measure-Object `
            -Property Monthly_Salary `
            -Sum
).Sum


# ------------------------------------------------------------
# Final report
# ------------------------------------------------------------

Write-Host "============================================================" `
    -ForegroundColor Cyan

Write-Host "EMPLOYEE CSV SETUP COMPLETE" `
    -ForegroundColor Green

Write-Host "============================================================" `
    -ForegroundColor Cyan

Write-Host ""

Write-Host "CSV:"
Write-Host "  Employees.csv"

Write-Host ""

Write-Host "Employees per CSV:"
Write-Host "  $($Employees.Count)"

Write-Host ""

Write-Host "Expected monthly salary total per CSV:"
Write-Host "  $ExpectedTotal"

Write-Host ""

Write-Host "Existing filesystem was preserved."
Write-Host "No Dictionary files were modified."
Write-Host "No new directories were created."

Write-Host ""
