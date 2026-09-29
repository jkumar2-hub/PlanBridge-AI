$src = "C:\Users\jitin\Downloads\SIHPS2\SIH2026_PS26122_Slide_Images_Editable.pptx"
$outPdf = "C:\Users\jitin\Downloads\SIHPS2\SIH2026_PS26122_Slide_Images_Editable.pdf"
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pres = $ppt.Presentations.Open($src, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    $pres.SaveAs($outPdf, 32)
    $pres.Close()
    Write-Host "PDF successfully saved to: $outPdf"
}
finally {
    $ppt.Quit()
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
