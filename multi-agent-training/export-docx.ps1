param([string]$Source)
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
if (-not $Source) {
    $Source = Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.md' -File |
        Where-Object { [IO.File]::ReadAllText($_.FullName, $utf8).StartsWith('# AI Agent ') } |
        Select-Object -First 1 -ExpandProperty FullName
}
if (-not $Source) { throw 'Training manuscript was not found' }
$Source = [IO.Path]::GetFullPath($Source)
$destination = [IO.Path]::ChangeExtension($Source, '.docx')
$lines = [IO.File]::ReadAllLines($Source, $utf8)
$w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

function New-XmlText([scriptblock]$Body) {
    $builder = New-Object System.Text.StringBuilder
    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.OmitXmlDeclaration = $true
    $settings.Indent = $false
    $writer = [System.Xml.XmlWriter]::Create($builder, $settings)
    try { & $Body $writer; $writer.Flush() } finally { $writer.Dispose() }
    return $builder.ToString()
}

function Write-Paragraph($x, [string]$text, [string]$style = 'Normal') {
    $x.WriteStartElement('w', 'p', $w)
    $x.WriteStartElement('w', 'pPr', $w)
    $x.WriteStartElement('w', 'pStyle', $w)
    $x.WriteAttributeString('w', 'val', $w, $style)
    $x.WriteEndElement()
    $x.WriteEndElement()
    $x.WriteStartElement('w', 'r', $w)
    $x.WriteStartElement('w', 't', $w)
    $x.WriteAttributeString('xml', 'space', 'http://www.w3.org/XML/1998/namespace', 'preserve')
    $x.WriteString($text)
    $x.WriteEndElement()
    $x.WriteEndElement()
    $x.WriteEndElement()
}

function Write-Table($x, [string[]]$rows) {
    $x.WriteStartElement('w', 'tbl', $w)
    $x.WriteStartElement('w', 'tblPr', $w)
    $x.WriteStartElement('w', 'tblW', $w)
    $x.WriteAttributeString('w', 'w', $w, '5000')
    $x.WriteAttributeString('w', 'type', $w, 'pct')
    $x.WriteEndElement()
    $x.WriteStartElement('w', 'tblBorders', $w)
    foreach ($border in @('top', 'left', 'bottom', 'right', 'insideH', 'insideV')) {
        $x.WriteStartElement('w', $border, $w)
        $x.WriteAttributeString('w', 'val', $w, 'single')
        $x.WriteAttributeString('w', 'sz', $w, '4')
        $x.WriteAttributeString('w', 'color', $w, 'CBD5E1')
        $x.WriteEndElement()
    }
    $x.WriteEndElement()
    $x.WriteEndElement()
    $index = 0
    foreach ($row in $rows) {
        if ($row -match '^[| :\-]+$') { continue }
        $cells = $row.Trim().Trim('|').Split('|')
        $x.WriteStartElement('w', 'tr', $w)
        if ($index -eq 0) {
            $x.WriteStartElement('w', 'trPr', $w)
            $x.WriteStartElement('w', 'tblHeader', $w)
            $x.WriteEndElement()
            $x.WriteEndElement()
        }
        foreach ($cell in $cells) {
            $x.WriteStartElement('w', 'tc', $w)
            $x.WriteStartElement('w', 'tcPr', $w)
            $x.WriteStartElement('w', 'tcW', $w)
            $x.WriteAttributeString('w', 'w', $w, [string][int](5000 / $cells.Length))
            $x.WriteAttributeString('w', 'type', $w, 'pct')
            $x.WriteEndElement()
            if ($index -eq 0) {
                $x.WriteStartElement('w', 'shd', $w)
                $x.WriteAttributeString('w', 'fill', $w, 'F1F5F9')
                $x.WriteEndElement()
            }
            $x.WriteEndElement()
            $style = if ($index -eq 0) { 'TableHeader' } else { 'TableText' }
            Write-Paragraph $x ($cell.Trim() -replace '[`*]', '') $style
            $x.WriteEndElement()
        }
        $x.WriteEndElement()
        $index++
    }
    $x.WriteEndElement()
}

$document = New-XmlText {
    param($x)
    $x.WriteStartElement('w', 'document', $w)
    $x.WriteStartElement('w', 'body', $w)
    $code = $false
    for ($i = 0; $i -lt $lines.Length; $i++) {
        $line = $lines[$i]
        if ($line.StartsWith('```')) { $code = -not $code; continue }
        if ($code) { Write-Paragraph $x $line 'Code'; continue }
        if ($line.StartsWith('|')) {
            $rows = New-Object 'System.Collections.Generic.List[string]'
            while ($i -lt $lines.Length -and $lines[$i].StartsWith('|')) {
                $rows.Add($lines[$i]); $i++
            }
            $i--
            Write-Table $x $rows.ToArray()
            continue
        }
        if (-not $line.Trim()) { continue }
        if ($line.StartsWith('# ')) { Write-Paragraph $x $line.Substring(2) 'Title' }
        elseif ($line.StartsWith('## ')) { Write-Paragraph $x $line.Substring(3) 'Heading1' }
        elseif ($line.StartsWith('### ')) { Write-Paragraph $x $line.Substring(4) 'Heading2' }
        else { Write-Paragraph $x ($line -replace '[`*]', '') }
    }
    $x.WriteStartElement('w', 'sectPr', $w)
    $x.WriteStartElement('w', 'pgSz', $w)
    $x.WriteAttributeString('w', 'w', $w, '11906')
    $x.WriteAttributeString('w', 'h', $w, '16838')
    $x.WriteEndElement()
    $x.WriteStartElement('w', 'pgMar', $w)
    foreach ($side in @('top', 'right', 'bottom', 'left')) { $x.WriteAttributeString('w', $side, $w, '1100') }
    $x.WriteAttributeString('w', 'header', $w, '500')
    $x.WriteAttributeString('w', 'footer', $w, '500')
    $x.WriteAttributeString('w', 'gutter', $w, '0')
    $x.WriteEndElement()
    $x.WriteEndElement()
    $x.WriteEndElement()
    $x.WriteEndElement()
}

$styles = New-XmlText {
    param($x)
    $x.WriteStartElement('w', 'styles', $w)
    foreach ($definition in @(
        @('Normal', '22', '203040', '0'), @('Title', '36', '111827', '1'),
        @('Heading1', '28', '111827', '1'), @('Heading2', '24', '111827', '1'),
        @('Code', '17', '263238', '0'), @('TableText', '19', '203040', '0'),
        @('TableHeader', '19', '111827', '1'))) {
        $id, $size, $color, $bold = $definition
        $x.WriteStartElement('w', 'style', $w)
        $x.WriteAttributeString('w', 'type', $w, 'paragraph')
        $x.WriteAttributeString('w', 'styleId', $w, $id)
        if ($id -eq 'Normal') { $x.WriteAttributeString('w', 'default', $w, '1') }
        $x.WriteStartElement('w', 'name', $w)
        $x.WriteAttributeString('w', 'val', $w, $id)
        $x.WriteEndElement()
        if ($id -ne 'Normal') {
            $x.WriteStartElement('w', 'basedOn', $w)
            $x.WriteAttributeString('w', 'val', $w, 'Normal')
            $x.WriteEndElement()
        }
        $x.WriteStartElement('w', 'pPr', $w)
        if ($id -like 'Heading*' -or $id -eq 'Title') {
            $x.WriteStartElement('w', 'keepNext', $w); $x.WriteEndElement()
            if ($id -like 'Heading*') {
                $x.WriteStartElement('w', 'outlineLvl', $w)
                $x.WriteAttributeString('w', 'val', $w, $(if ($id -eq 'Heading1') { '0' } else { '1' }))
                $x.WriteEndElement()
            }
        }
        $x.WriteStartElement('w', 'spacing', $w)
        $x.WriteAttributeString('w', 'after', $w, $(if ($id -eq 'Code') { '0' } else { '120' }))
        $x.WriteAttributeString('w', 'line', $w, '300')
        $x.WriteAttributeString('w', 'lineRule', $w, 'auto')
        $x.WriteEndElement()
        $x.WriteEndElement()
        $x.WriteStartElement('w', 'rPr', $w)
        $x.WriteStartElement('w', 'rFonts', $w)
        $font = if ($id -eq 'Code') { 'Consolas' } else { 'Calibri' }
        $x.WriteAttributeString('w', 'ascii', $w, $font)
        $x.WriteAttributeString('w', 'hAnsi', $w, $font)
        $x.WriteAttributeString('w', 'eastAsia', $w, 'Microsoft YaHei')
        $x.WriteEndElement()
        $x.WriteStartElement('w', 'sz', $w)
        $x.WriteAttributeString('w', 'val', $w, $size)
        $x.WriteEndElement()
        $x.WriteStartElement('w', 'color', $w)
        $x.WriteAttributeString('w', 'val', $w, $color)
        $x.WriteEndElement()
        if ($bold -eq '1') { $x.WriteStartElement('w', 'b', $w); $x.WriteEndElement() }
        $x.WriteEndElement()
        $x.WriteEndElement()
    }
    $x.WriteEndElement()
}

$types = New-XmlText {
    param($x)
    $ns = 'http://schemas.openxmlformats.org/package/2006/content-types'
    $x.WriteStartElement('Types', $ns)
    foreach ($pair in @(@('rels', 'application/vnd.openxmlformats-package.relationships+xml'), @('xml', 'application/xml'))) {
        $x.WriteStartElement('Default', $ns)
        $x.WriteAttributeString('Extension', $pair[0]); $x.WriteAttributeString('ContentType', $pair[1])
        $x.WriteEndElement()
    }
    foreach ($pair in @(@('/word/document.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'),
                        @('/word/styles.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml'))) {
        $x.WriteStartElement('Override', $ns)
        $x.WriteAttributeString('PartName', $pair[0]); $x.WriteAttributeString('ContentType', $pair[1])
        $x.WriteEndElement()
    }
    $x.WriteEndElement()
}

function New-Relationships([string]$id, [string]$type, [string]$target) {
    New-XmlText {
        param($x)
        $ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
        $x.WriteStartElement('Relationships', $ns)
        $x.WriteStartElement('Relationship', $ns)
        $x.WriteAttributeString('Id', $id)
        $x.WriteAttributeString('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/' + $type)
        $x.WriteAttributeString('Target', $target)
        $x.WriteEndElement()
        $x.WriteEndElement()
    }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stream = [IO.File]::Open($destination, [IO.FileMode]::Create, [IO.FileAccess]::Write)
$archive = New-Object System.IO.Compression.ZipArchive($stream, [IO.Compression.ZipArchiveMode]::Create)
try {
    $parts = @{
        '[Content_Types].xml' = $types
        '_rels/.rels' = (New-Relationships 'rId1' 'officeDocument' 'word/document.xml')
        'word/document.xml' = $document
        'word/styles.xml' = $styles
        'word/_rels/document.xml.rels' = (New-Relationships 'rId1' 'styles' 'styles.xml')
    }
    foreach ($name in $parts.Keys) {
        $entry = $archive.CreateEntry($name)
        $entryStream = $entry.Open()
        try {
            $bytes = $utf8.GetBytes($parts[$name])
            $entryStream.Write($bytes, 0, $bytes.Length)
        } finally { $entryStream.Dispose() }
    }
} finally { $archive.Dispose(); $stream.Dispose() }
Write-Output "Generated: $destination"
