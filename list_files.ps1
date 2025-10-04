function Escape-Xml {
    param([string]$text)
    $text -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;' -replace '"', '&quot;' -replace "'", '&apos;'
}

# List all files, then filter by extension
$allFiles = Get-ChildItem -Path . -File -Force
$files = $allFiles | Where-Object { $_.Extension -eq '.py' -or $_.Extension -eq '.md' }

Write-Output "DEBUG: Found $($files.Count) files matching *.py or *.md"
if ($files.Count -eq 0) {
    Write-Output "DEBUG: All files in folder:"
    $allFiles | ForEach-Object { Write-Output "  - $($_.Name) (Extension: $($_.Extension))" }
}

Write-Output "<?xml version=`"1.0`" encoding=`"UTF-8`"?>"
Write-Output "<files>"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $escapedContent = Escape-Xml $content
    Write-Output "<file name=`"$($file.Name)`">"
    Write-Output "<content>$escapedContent</content>"
    Write-Output "</file>"
}

Write-Output "</files>"