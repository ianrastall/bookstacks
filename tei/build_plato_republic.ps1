param(
    [string]$SourceGrcPath = (Join-Path $PSScriptRoot '..\assets\canonical-greekLit-renamed\xml\plato_republic_grc_burnet.xml'),
    [string]$SourceEngPath = (Join-Path $PSScriptRoot '..\assets\canonical-greekLit-renamed\xml\plato_republic_eng_shorey.xml'),
    [string]$OutputGrcPath = (Join-Path $PSScriptRoot 'plato_the-republic_grc_orig.xml'),
    [string]$OutputEngPath = (Join-Path $PSScriptRoot 'plato_the-republic_eng_shorey.xml')
)

$ErrorActionPreference = 'Stop'

$teiNamespace = 'http://www.tei-c.org/ns/1.0'
$xmlNamespace = 'http://www.w3.org/XML/1998/namespace'

function Set-XmlId {
    param(
        [System.Xml.XmlElement]$Element,
        [string]$Value
    )
    [void]$Element.SetAttribute('id', $xmlNamespace, $Value)
}

function Build-TeiFile {
    param(
        [string]$SourcePath,
        [string]$OutputPath,
        [string]$Lang,
        [string]$HeaderXml,
        [string]$TextId
    )

    $source = New-Object System.Xml.XmlDocument
    $source.PreserveWhitespace = $true
    $source.Load((Resolve-Path $SourcePath))

    $sourceNamespaces = New-Object System.Xml.XmlNamespaceManager($source.NameTable)
    $sourceNamespaces.AddNamespace('tei', $teiNamespace)
    $sourceBody = $source.SelectSingleNode('/tei:TEI/tei:text/tei:body', $sourceNamespaces)
    if ($null -eq $sourceBody) {
        throw "The source document does not contain a TEI body: $SourcePath"
    }
    
    $headerDocument = New-Object System.Xml.XmlDocument
    $headerDocument.PreserveWhitespace = $true
    $headerDocument.LoadXml($HeaderXml)

    $output = New-Object System.Xml.XmlDocument
    $output.PreserveWhitespace = $true
    $declaration = $output.CreateXmlDeclaration('1.0', 'UTF-8', $null)
    [void]$output.AppendChild($declaration)
    [void]$output.AppendChild($output.CreateProcessingInstruction('xml-model', 'href="tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"'))

    $root = $output.CreateElement('TEI', $teiNamespace)
    Set-XmlId -Element $root -Value $TextId
    [void]$output.AppendChild($root)
    [void]$root.AppendChild($output.ImportNode($headerDocument.DocumentElement, $true))

    $outerText = $output.CreateElement('text', $teiNamespace)
    [void]$outerText.SetAttribute('lang', $xmlNamespace, $Lang)
    [void]$root.AppendChild($outerText)

    $body = [System.Xml.XmlElement]$output.ImportNode($sourceBody, $true)
    $bodyNamespaces = New-Object System.Xml.XmlNamespaceManager($output.NameTable)
    $bodyNamespaces.AddNamespace('tei', $teiNamespace)

    $edition = [System.Xml.XmlElement]$body.SelectSingleNode('./tei:div[@type="edition"] | ./tei:div[@type="translation"]', $bodyNamespaces)
    if ($null -eq $edition) {
        throw 'The imported body does not contain the expected edition or translation division.'
    }
    
    if ($Lang -eq 'grc') {
        Set-XmlId -Element $edition -Value 'republic-grc-edition'
    } else {
        Set-XmlId -Element $edition -Value 'republic-eng-translation'
    }

    $books = $body.SelectNodes('.//tei:div[@subtype="book"]', $bodyNamespaces)
    foreach ($book in $books) {
        $bookNumber = $book.GetAttribute('n')
        Set-XmlId -Element $book -Value "$Lang-book-$bookNumber"
        foreach ($section in $book.SelectNodes('./tei:div[@subtype="section"]', $bodyNamespaces)) {
            $sectionNumber = $section.GetAttribute('n')
            Set-XmlId -Element $section -Value "$Lang-b$bookNumber-page-$sectionNumber"
        }
    }

    $pageMilestones = $body.SelectNodes('.//tei:milestone[@unit="page" and @resp="Stephanus"]', $bodyNamespaces)
    foreach ($milestone in $pageMilestones) {
        Set-XmlId -Element $milestone -Value ("$Lang-stephanus-page-" + $milestone.GetAttribute('n'))
    }

    $sectionMilestones = $body.SelectNodes('.//tei:milestone[@unit="section" and @resp="Stephanus"]', $bodyNamespaces)
    foreach ($milestone in $sectionMilestones) {
        Set-XmlId -Element $milestone -Value ("$Lang-stephanus-" + $milestone.GetAttribute('n'))
    }

    [void]$outerText.AppendChild($body)

    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Encoding = New-Object System.Text.UTF8Encoding($false)
    $settings.Indent = $true
    $settings.IndentChars = '  '
    $settings.NewLineChars = "`n"
    $settings.NewLineHandling = [System.Xml.NewLineHandling]::Replace

    $resolvedOutputPath = [System.IO.Path]::GetFullPath($OutputPath)
    $writer = [System.Xml.XmlWriter]::Create($resolvedOutputPath, $settings)
    try {
        $output.Save($writer)
    }
    finally {
        $writer.Dispose()
    }
    
    Write-Output "Generated $resolvedOutputPath"
    Write-Output "Books: $($books.Count); Stephanus pages: $($pageMilestones.Count); Stephanus sections: $($sectionMilestones.Count)"
}

$grcHeader = @'
<teiHeader xmlns="http://www.tei-c.org/ns/1.0" xml:lang="en">
  <fileDesc>
    <titleStmt>
      <title type="main" xml:lang="en">The Republic</title>
      <title type="uniform" xml:lang="grc">Πολιτεία</title>
      <title type="alternative" xml:lang="lat">Respublica</title>
      <author ref="https://viaf.org/viaf/108159964" xml:lang="en">Plato</author>
      <editor ref="https://viaf.org/viaf/71461286">John Burnet</editor>
      <sponsor>Perseus Digital Library, Tufts University</sponsor>
      <principal>Gregory Crane</principal>
      <respStmt xml:id="perseus-digitization">
        <resp>digitization and original electronic text encoding</resp>
        <name ref="https://www.perseus.tufts.edu/">Perseus Digital Library, Tufts University</name>
      </respStmt>
      <respStmt xml:id="perseus-supervision">
        <resp>preparation under the supervision of</resp>
        <name>Lisa Cerrato</name>
        <name>William Merrill</name>
        <name>Elli Mylonas</name>
        <name>David Smith</name>
      </respStmt>
      <respStmt xml:id="bookstacks-encoding">
        <resp>TEI P5 restructuring, metadata enrichment, and stable identifiers</resp>
        <name>Bookstacks project</name>
      </respStmt>
      <funder>The Annenberg/CPB Project</funder>
    </titleStmt>
    <editionStmt>
      <edition n="1.0">Bookstacks TEI edition, based on the Perseus Greek electronic edition</edition>
    </editionStmt>
    <extent>
      <measure unit="book" quantity="10">10 books</measure>
      <measure unit="StephanusPage" quantity="278">278 Stephanus pages encoded as textual divisions</measure>
    </extent>
    <publicationStmt>
      <publisher>Bookstacks project</publisher>
      <pubPlace>United States</pubPlace>
      <date when="2026-08-20">20 August 2026</date>
      <idno type="CTS-URN">urn:cts:greekLit:tlg0059.tlg030.perseus-grc2</idno>
      <idno type="local">plato_republic_grc_orig</idno>
      <availability status="free">
        <licence target="https://creativecommons.org/licenses/by-sa/4.0/">The Perseus source encoding and this derived TEI file are made available under the Creative Commons Attribution-ShareAlike 4.0 International License.</licence>
      </availability>
    </publicationStmt>
    <notesStmt>
      <note type="scope">This file contains the complete Ancient Greek text.</note>
    </notesStmt>
    <sourceDesc>
      <biblStruct xml:id="burnet-1905" type="printedEdition">
        <monogr>
          <author>Plato</author>
          <title xml:lang="lat" level="m">Platonis Opera</title>
          <editor>John Burnet</editor>
          <edition>Oxford Classical Text</edition>
          <imprint>
            <pubPlace>Oxford</pubPlace>
            <publisher>Clarendon Press</publisher>
            <date when="1905">1905</date>
          </imprint>
          <biblScope unit="volume">4</biblScope>
        </monogr>
      </biblStruct>
      <bibl xml:id="perseus-grc2" type="digitalSource">
        <title xml:lang="grc">Πολιτεία</title>, edited by <name>John Burnet</name>; Perseus Digital Library.
      </bibl>
    </sourceDesc>
  </fileDesc>
  <encodingDesc>
    <projectDesc>
      <p>The document preserves the complete Perseus transcription of Burnet's Greek edition.</p>
    </projectDesc>
    <refsDecl n="CTS">
      <cRefPattern n="section" matchPattern="(\w+)\.(\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2'])">
        <p>This pointer pattern resolves book and section references.</p>
      </cRefPattern>
    </refsDecl>
  </encodingDesc>
  <profileDesc>
    <langUsage>
      <language ident="grc">Ancient Greek (to 1453)</language>
      <language ident="en">English (metadata)</language>
      <language ident="lat">Latin (bibliographic titles)</language>
    </langUsage>
    <particDesc>
      <listPerson>
        <person xml:id="Σωκράτης">
          <persName xml:lang="grc">Σωκράτης</persName>
          <persName xml:lang="en">Socrates</persName>
          <note>Primary narrator. Full turn-by-turn attribution for other participants is currently missing from this edition.</note>
        </person>
      </listPerson>
    </particDesc>
  </profileDesc>
</teiHeader>
'@

$engHeader = @'
<teiHeader xmlns="http://www.tei-c.org/ns/1.0" xml:lang="en">
  <fileDesc>
    <titleStmt>
      <title type="main" xml:lang="en">The Republic</title>
      <author ref="https://viaf.org/viaf/108159964" xml:lang="en">Plato</author>
      <editor role="translator">Paul Shorey</editor>
      <sponsor>Perseus Project, Tufts University</sponsor>
      <principal>Gregory Crane</principal>
      <respStmt xml:id="perseus-digitization">
        <resp>digitization and original electronic text encoding</resp>
        <name ref="https://www.perseus.tufts.edu/">Perseus Digital Library, Tufts University</name>
      </respStmt>
      <respStmt xml:id="bookstacks-encoding">
        <resp>TEI P5 restructuring, metadata enrichment, and stable identifiers</resp>
        <name>Bookstacks project</name>
      </respStmt>
      <funder>The Annenberg/CPB Project</funder>
    </titleStmt>
    <editionStmt>
      <edition n="1.0">Bookstacks TEI edition, based on the Perseus English electronic edition</edition>
    </editionStmt>
    <extent>
      <measure unit="book" quantity="10">10 books</measure>
    </extent>
    <publicationStmt>
      <publisher>Bookstacks project</publisher>
      <pubPlace>United States</pubPlace>
      <date when="2026-08-20">20 August 2026</date>
      <idno type="CTS-URN">urn:cts:greekLit:tlg0059.tlg030.perseus-eng2</idno>
      <idno type="local">plato_republic_eng_shorey</idno>
      <availability status="free">
        <licence target="https://creativecommons.org/licenses/by-sa/4.0/">The Perseus source encoding and this derived TEI file are made available under the Creative Commons Attribution-ShareAlike 4.0 International License.</licence>
      </availability>
    </publicationStmt>
    <notesStmt>
      <note type="scope">This file contains the complete Paul Shorey English translation.</note>
    </notesStmt>
    <sourceDesc>
      <biblStruct>
        <monogr>
          <author>Plato</author>
          <title>Plato in Twelve Volumes</title>
          <editor role="translator">Paul Shorey</editor>
          <imprint>
            <pubPlace>Cambridge, MA</pubPlace>
            <publisher>Harvard University Press</publisher>
            <date from="1935" to="1937" type="printing">1935-37</date>
          </imprint>
          <biblScope unit="volume">5-6</biblScope>
        </monogr>                    
      </biblStruct>
    </sourceDesc>
  </fileDesc>
  <encodingDesc>
    <projectDesc>
      <p>The document preserves the complete Perseus transcription of Shorey's English translation.</p>
    </projectDesc>
    <refsDecl n="CTS">
      <cRefPattern n="section" matchPattern="(\w+)\.(\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2'])">
        <p>This pointer pattern resolves book and section references.</p>
      </cRefPattern>
    </refsDecl>
  </encodingDesc>
  <profileDesc>
    <langUsage>
      <language ident="eng">English</language>
    </langUsage>
    <particDesc>
      <listPerson>
        <person xml:id="Socrates">
          <persName>Socrates</persName>
          <note>Primary narrator. Full turn-by-turn attribution for other participants is currently missing from this edition.</note>
        </person>
      </listPerson>
    </particDesc>
  </profileDesc>
</teiHeader>
'@

Build-TeiFile -SourcePath $SourceGrcPath -OutputPath $OutputGrcPath -Lang 'grc' -HeaderXml $grcHeader -TextId 'plato-republic-grc-orig'
Build-TeiFile -SourcePath $SourceEngPath -OutputPath $OutputEngPath -Lang 'eng' -HeaderXml $engHeader -TextId 'plato-republic-eng-shorey'

Write-Output "Done building TEI files."
