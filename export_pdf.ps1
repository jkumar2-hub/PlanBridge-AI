$downloadsPptx = "C:\Users\jitin\Downloads\SIHPS2\SIH2026_PS26122_Oil_India_Presentation.pptx"
$downloadsPdf = "C:\Users\jitin\Downloads\SIHPS2\SIH2026_PS26122_Oil_India_Presentation.pdf"

$localPptx = "C:\Users\jitin\.gemini\antigravity\scratch\sih-ps26122-bridge\SIH2026_PS26122_Oil_India_Presentation.pptx"
$localPdf = "C:\Users\jitin\.gemini\antigravity\scratch\sih-ps26122-bridge\SIH2026_PS26122_Oil_India_Presentation.pdf"

try {
    $app = New-Object -ComObject PowerPoint.Application
    
    # 1. Export Downloads PDF
    $pres1 = $app.Presentations.Open($downloadsPptx, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    $pres1.SaveAs($downloadsPdf, 32)
    $pres1.Close()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres1) | Out-Null
    Write-Host "Exported: $downloadsPdf"
    
    # 2. Export Local Scratch PDF
    $pres2 = $app.Presentations.Open($localPptx, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    $pres2.SaveAs($localPdf, 32)
    $pres2.Close()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres2) | Out-Null
    Write-Host "Exported: $localPdf"
    
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
    Write-Host "ALL_PDF_EXPORTS_SUCCESSFUL"
} catch {
    Write-Host "Error during PDF export:" $_.Exception.Message
    exit 1
}
