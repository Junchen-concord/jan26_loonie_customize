#
# Script to run Model Factory test suite for Chirp
#

$Date = Get-Date -Format "MMddyyyy-HHmmss"
$FullDate = Get-Date
$Repo = "IAModelV16"
$RootDir = "C:\CIPModels"
$Python = "C:\Anaconda3\envs\MDLV16\python.exe"

$CodeDir = $RootDir + "\PythonService\" + $Repo
$LogDir = $RootDir + "\" + "Logs"

$TestUtility = "Chirp"
$TestUtilityFP = "C:\CIPModels\PythonService\IAModelV16\test_scripts\ChirpIPMTestUtility.py"

$ErrorLog = $LogDir + "\" + $TestUtility + "_err_" + $Date
$OutputLog = $LogDir + "\" + $TestUtility + "_out_" + $Date

Set-Item -Path env:PYTHONPATH -Value $CodeDir
Write-Host "Running" $TestUtility "in" $CodeDir "at" $FullDate
Start-Process -FilePath $Python -NoNewWindow -ArgumentList "$TestUtilityFP" -RedirectStandardError $ErrorLog -RedirectStandardOutput $OutputLog -WorkingDirectory $CodeDir -Wait
#
# Refresh FullDate for exec completion
#
$FullDate = Get-Date
Write-Host "Completed running" $TestUtility "in" $CodeDir "at" $FullDate

