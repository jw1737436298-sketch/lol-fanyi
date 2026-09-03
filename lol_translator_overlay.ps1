Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvPath = Join-Path $ProjectDir ".env"

if (-not (Test-Path -LiteralPath $EnvPath)) {
    "OPENAI_API_KEY=sk-your-key-here`r`nOPENAI_MODEL=gpt-4o-mini" | Set-Content -LiteralPath $EnvPath -Encoding ASCII
}

function Read-EnvFile {
    $Values = @{}
    foreach ($Line in Get-Content -LiteralPath $EnvPath -Encoding UTF8) {
        $Text = $Line.Trim()
        if (-not $Text -or $Text.StartsWith("#") -or -not $Text.Contains("=")) { continue }
        $Parts = $Text.Split("=", 2)
        $Values[$Parts[0].Trim()] = $Parts[1].Trim().Trim('"')
    }
    return $Values
}

function Invoke-Translation {
    param([string]$Mode, [string]$Text)

    $Env = Read-EnvFile
    $ApiKey = $Env["OPENAI_API_KEY"]
    if (-not $ApiKey -or $ApiKey.StartsWith("sk-your-key")) {
        throw "Please fill OPENAI_API_KEY in .env first."
    }

    $Model = $Env["OPENAI_MODEL"]
    if (-not $Model) { $Model = "gpt-4o-mini" }

    if ($Mode -eq "zh") {
        $Prompt = "Translate English or German League of Legends chat into short natural Simplified Chinese. Output only the translation."
    } else {
        $Prompt = "Translate Simplified Chinese into short natural League of Legends in-game English. Output only the English message."
    }

    $Body = @{
        model = $Model
        input = @(
            @{ role = "system"; content = $Prompt },
            @{ role = "user"; content = $Text }
        )
    } | ConvertTo-Json -Depth 8

    $Headers = @{
        Authorization = "Bearer $ApiKey"
        "Content-Type" = "application/json"
    }

    $Response = Invoke-RestMethod -Method Post -Uri "https://api.openai.com/v1/responses" -Headers $Headers -Body $Body -TimeoutSec 45
    if ($Response.output_text) { return [string]$Response.output_text }

    $Chunks = New-Object System.Collections.Generic.List[string]
    foreach ($Item in $Response.output) {
        foreach ($Content in $Item.content) {
            if ($Content.text) { [void]$Chunks.Add([string]$Content.text) }
        }
    }

    $Result = ($Chunks -join "").Trim()
    if (-not $Result) { throw "No translation returned." }
    return $Result
}

Add-Type -ReferencedAssemblies System.Windows.Forms -Language CSharp @"
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class HotkeyOverlayForm : Form
{
    public event Action<int> HotkeyPressed;

    protected override void WndProc(ref Message m)
    {
        if (m.Msg == 0x0312)
        {
            Action<int> handler = HotkeyPressed;
            if (handler != null) handler(m.WParam.ToInt32());
        }
        base.WndProc(ref m);
    }

    [DllImport("user32.dll")]
    public static extern bool RegisterHotKey(IntPtr hWnd, int id, uint modifiers, uint key);
}
"@

$Form = New-Object HotkeyOverlayForm
$Form.Text = "LOL Translator"
$Form.Size = New-Object System.Drawing.Size(360, 330)
$Form.StartPosition = "CenterScreen"
$Form.TopMost = $true
$Form.FormBorderStyle = "FixedToolWindow"
$Form.BackColor = [System.Drawing.Color]::FromArgb(248, 249, 251)

$Font = New-Object System.Drawing.Font("Segoe UI", 9)
$Form.Font = $Font

$Input = New-Object System.Windows.Forms.TextBox
$Input.Multiline = $true
$Input.ScrollBars = "Vertical"
$Input.Location = New-Object System.Drawing.Point(10, 10)
$Input.Size = New-Object System.Drawing.Size(324, 82)
$Input.PlaceholderText = "Paste chat or type Chinese..."

$Result = New-Object System.Windows.Forms.TextBox
$Result.Multiline = $true
$Result.ScrollBars = "Vertical"
$Result.ReadOnly = $true
$Result.Location = New-Object System.Drawing.Point(10, 100)
$Result.Size = New-Object System.Drawing.Size(324, 82)
$Result.PlaceholderText = "Result"

$ToChinese = New-Object System.Windows.Forms.Button
$ToChinese.Text = "To CN"
$ToChinese.Location = New-Object System.Drawing.Point(10, 192)
$ToChinese.Size = New-Object System.Drawing.Size(75, 32)

$ToEnglish = New-Object System.Windows.Forms.Button
$ToEnglish.Text = "EN + Copy"
$ToEnglish.Location = New-Object System.Drawing.Point(91, 192)
$ToEnglish.Size = New-Object System.Drawing.Size(92, 32)

$ClipboardButton = New-Object System.Windows.Forms.Button
$ClipboardButton.Text = "Clipboard"
$ClipboardButton.Location = New-Object System.Drawing.Point(189, 192)
$ClipboardButton.Size = New-Object System.Drawing.Size(82, 32)

$CopyButton = New-Object System.Windows.Forms.Button
$CopyButton.Text = "Copy"
$CopyButton.Location = New-Object System.Drawing.Point(277, 192)
$CopyButton.Size = New-Object System.Drawing.Size(57, 32)

$Status = New-Object System.Windows.Forms.Label
$Status.Text = "Ctrl+Alt+T hide, Ctrl+Alt+C clipboard, Ctrl+Alt+E EN+copy"
$Status.Location = New-Object System.Drawing.Point(10, 234)
$Status.Size = New-Object System.Drawing.Size(324, 42)

$Form.Controls.AddRange(@($Input, $Result, $ToChinese, $ToEnglish, $ClipboardButton, $CopyButton, $Status))

function Set-Busy([bool]$Busy) {
    $ToChinese.Enabled = -not $Busy
    $ToEnglish.Enabled = -not $Busy
    $ClipboardButton.Enabled = -not $Busy
    $CopyButton.Enabled = -not $Busy
}

function Run-Job([string]$Mode, [bool]$CopyAfter) {
    $Text = $Input.Text.Trim()
    if (-not $Text) {
        $Status.Text = "No text."
        return
    }

    try {
        Set-Busy $true
        $Status.Text = "Translating..."
        [System.Windows.Forms.Application]::DoEvents()
        $Translated = Invoke-Translation $Mode $Text
        $Result.Text = $Translated
        if ($CopyAfter) {
            [System.Windows.Forms.Clipboard]::SetText($Translated)
            $Status.Text = "Copied. Paste in LOL."
        } else {
            $Status.Text = "Done."
        }
    } catch {
        $Status.Text = "Failed: $($_.Exception.Message)"
        [System.Windows.Forms.MessageBox]::Show($Status.Text, "LOL Translator") | Out-Null
    } finally {
        Set-Busy $false
    }
}

$ToChinese.Add_Click({ Run-Job "zh" $false })
$ToEnglish.Add_Click({ Run-Job "en" $true })

$ClipboardButton.Add_Click({
    if ([System.Windows.Forms.Clipboard]::ContainsText()) {
        $Input.Text = [System.Windows.Forms.Clipboard]::GetText()
        Run-Job "zh" $false
    } else {
        $Status.Text = "Clipboard has no text."
    }
})

$CopyButton.Add_Click({
    $Text = $Result.Text.Trim()
    if ($Text) {
        [System.Windows.Forms.Clipboard]::SetText($Text)
        $Status.Text = "Copied."
    }
})

$Form.Add_Shown({
    [HotkeyOverlayForm]::RegisterHotKey($Form.Handle, 1, 0x0003, [uint32][char]'T') | Out-Null
    [HotkeyOverlayForm]::RegisterHotKey($Form.Handle, 2, 0x0003, [uint32][char]'C') | Out-Null
    [HotkeyOverlayForm]::RegisterHotKey($Form.Handle, 3, 0x0003, [uint32][char]'E') | Out-Null
})

$Form.add_HotkeyPressed({
    param($Id)
    if ($Id -eq 1) {
        if ($Form.Visible) { $Form.Hide() } else { $Form.Show(); $Form.Activate() }
    } elseif ($Id -eq 2) {
        $Form.Show()
        $Form.Activate()
        $ClipboardButton.PerformClick()
    } elseif ($Id -eq 3) {
        $Form.Show()
        $Form.Activate()
        $ToEnglish.PerformClick()
    }
})

$Form.Add_FormClosing({
    $_.Cancel = $true
    $Form.Hide()
})

if ((Read-EnvFile)["OPENAI_API_KEY"] -like "sk-your-key*") {
    [System.Windows.Forms.MessageBox]::Show("Fill OPENAI_API_KEY in .env before translating.", "LOL Translator") | Out-Null
}

[System.Windows.Forms.Application]::EnableVisualStyles()
[System.Windows.Forms.Application]::Run($Form)

