# PowerShell loader for workspace copilot skill
# Usage: Open PowerShell in repo root and run: .\scripts\load_copilot_skill.ps1

$skillPath = Join-Path -Path (Get-Location) -ChildPath ".copilot\WORKFLOW_SKILL.md"
if (-Not (Test-Path $skillPath)) {
    Write-Error "Skill file not found: $skillPath"
    exit 1
}

$content = Get-Content -Raw -Path $skillPath
Write-Host "---- RetrOS Copilot Skill: Start ----`n"
Write-Host $content
Write-Host "`n---- RetrOS Copilot Skill: End ----"

# Try to copy to clipboard if available
try {
    Set-Clipboard -Value $content -ErrorAction Stop
    Write-Host "(Copied skill content to clipboard)"
} catch {
    Write-Host "(Clipboard copy not available in this environment)"
}
