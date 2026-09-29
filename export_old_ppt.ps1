$srcPptx = "C:\Users\jitin\Downloads\SIHPS2\SIH2026_PS26122_Oil_India_Presentation.pptx"
$outPdf = "C:\Users\jitin\Downloads\SIHPS2\SIH2026_PS26122_Oil_India_Presentation.pdf"
$outPdfLocal = "C:\Users\jitin\.gemini\antigravity\scratch\sih-ps26122-bridge\SIH2026_PS26122_Oil_India_Presentation.pdf"
$outDir4K = "C:\Users\jitin\Downloads\SIHPS2\old_slides_4k"
$outDir8K = "C:\Users\jitin\Downloads\SIHPS2\old_slides_8k"

if (!(Test-Path $outDir4K)) { New-Item -ItemType Directory -Path $outDir4K | Out-Null }
if (!(Test-Path $outDir8K)) { New-Item -ItemType Directory -Path $outDir8K | Out-Null }

$ppt = New-Object -ComObject PowerPoint.Application

try {
    $pres = $ppt.Presentations.Open($srcPptx, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    
    $slideNames = @(
        "Slide_1_Title",
        "Slide_2_Proposed_Solution",
        "Slide_3_Platform_Preview",
        "Slide_4_Feasibility_Viability",
        "Slide_5_Impact_Benefits",
        "Slide_6_Research_References"
    )
    
    Write-Host "Presentation opened successfully. Total slides: $($pres.Slides.Count)"
    
    # Export PDF
    Write-Host "Exporting native PDF..."
    $pres.SaveAs($outPdf, 32)
    $pres.SaveAs($outPdfLocal, 32)
    Write-Host "  -> PDF saved: $outPdf"
    
    for ($i = 1; $i -le $pres.Slides.Count; $i++) {
        $slide = $pres.Slides.Item($i)
        $name = if ($i -le $slideNames.Count) { $slideNames[$i-1] } else { "Slide_$i" }
        
        $path4k = Join-Path $outDir4K "$($name)_4K.png"
        $path8k = Join-Path $outDir8K "$($name)_8K.png"
        
        Write-Host "Exporting Slide $i ($name)..."
        $slide.Export($path4k, "PNG", 3840, 2160)
        $slide.Export($path8k, "PNG", 7680, 4320)
        Write-Host "  -> 4K saved: $path4k"
        Write-Host "  -> 8K saved: $path8k"
    }
    
    $pres.Close()
}
finally {
    $ppt.Quit()
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
Write-Host "All old slides and PDF successfully exported!"
