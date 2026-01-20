#
# Script to Archive current code before release for Model Factory
#
$RootDir = "C:\CIPModels"
$Repo = "PythonService\IAModel"
$CodeDir = $RootDir + "\" + $Repo
$ArchiveDir = $RootDir + "\Archive"
$7Zip = "C:\Program Files\7-zip\7z.exe"
$Date = Get-Date -Format "MMddyyyy-HHmmss"
$FullDate = Get-Date

$7ZTargetFile = $ArchiveDir + "\" + $Repo + "_" + $Date

Write-Host "Archiving" $Repo "in" $CodeDir "at" $FullDate
Start-Process -FilePath $7Zip -NoNewWindow -ArgumentList "a $7ZTargetFile $CodeDir" -Wait
#
# Refresh FullDate for exec completion
#
$FullDate = Get-Date
Write-Host "Completed archiving" $Repo "in" $CodeDir "at" $FullDate
