param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot 'tei_build_config.json'),
    [string]$Author
)

$ErrorActionPreference = 'Stop'

$teiNamespace = 'http://www.tei-c.org/ns/1.0'
$xmlNamespace = 'http://www.w3.org/XML/1998/namespace'
$xiNamespace = 'http://www.w3.org/2001/XInclude'
$buildDate = Get-Date

function Set-XmlId {
    param([System.Xml.XmlElement]$Element, [string]$Value)
    [void]$Element.SetAttribute('id', $xmlNamespace, $Value)
}

function Get-XmlId {
    param([System.Xml.XmlElement]$Element)
    return $Element.GetAttribute('id', $xmlNamespace)
}

function ConvertTo-XmlIdToken {
    param([string]$Value)

    $token = $Value.Trim().TrimStart('#')
    $token = [System.Text.RegularExpressions.Regex]::Replace($token, "[^\p{L}\p{Nd}_.-]+", '-')
    $token = [System.Text.RegularExpressions.Regex]::Replace($token, '-+', '-').Trim('-')
    if (-not $token) { $token = 'item' }
    if ($token -notmatch '^[\p{L}_]') { $token = "id-$token" }
    return $token
}

function ConvertTo-IdComponent {
    param([string]$Value)

    $token = $Value.Trim().TrimStart('#')
    $token = [System.Text.RegularExpressions.Regex]::Replace($token, "[^\p{L}\p{Nd}_.-]+", '-')
    $token = [System.Text.RegularExpressions.Regex]::Replace($token, '-+', '-').Trim('-')
    if (-not $token) { return 'item' }
    return $token
}

function Get-TeiNamespaceManager {
    param([System.Xml.XmlDocument]$Document)

    $namespaces = New-Object System.Xml.XmlNamespaceManager($Document.NameTable)
    $namespaces.AddNamespace('tei', $teiNamespace)
    $namespaces.AddNamespace('xi', $xiNamespace)
    return ,$namespaces
}

function New-TeiElement {
    param([System.Xml.XmlDocument]$Document, [string]$Name)
    return $Document.CreateElement($Name, $teiNamespace)
}

function Rename-TeiElement {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$Element,
        [string]$Name
    )

    $replacement = New-TeiElement $Document $Name
    foreach ($attribute in @($Element.Attributes)) {
        [void]$replacement.Attributes.Append($attribute.CloneNode($true))
    }
    while ($Element.HasChildNodes) {
        [void]$replacement.AppendChild($Element.FirstChild)
    }
    [void]$Element.ParentNode.ReplaceChild($replacement, $Element)
    return $replacement
}

function Ensure-HeaderOrder {
    param([System.Xml.XmlDocument]$Document, [System.Xml.XmlElement]$Header)

    $namespaces = Get-TeiNamespaceManager $Document
    $fileDesc = [System.Xml.XmlElement]$Header.SelectSingleNode('./tei:fileDesc', $namespaces)
    if (-not $fileDesc) {
        $fileDesc = New-TeiElement $Document 'fileDesc'
        [void]$Header.PrependChild($fileDesc)
    }

    $titleStmt = [System.Xml.XmlElement]$fileDesc.SelectSingleNode('./tei:titleStmt', $namespaces)
    if (-not $titleStmt) {
        $titleStmt = New-TeiElement $Document 'titleStmt'
        $title = New-TeiElement $Document 'title'
        $title.InnerText = 'Untitled source text'
        [void]$titleStmt.AppendChild($title)
        [void]$fileDesc.PrependChild($titleStmt)
    }

    $editionStmt = [System.Xml.XmlElement]$fileDesc.SelectSingleNode('./tei:editionStmt', $namespaces)
    if (-not $editionStmt) {
        $editionStmt = New-TeiElement $Document 'editionStmt'
        $edition = New-TeiElement $Document 'edition'
        [void]$edition.SetAttribute('n', '1.0')
        $edition.InnerText = 'Bookstacks TEI edition, based on the source electronic edition'
        [void]$editionStmt.AppendChild($edition)
        [void]$fileDesc.InsertAfter($editionStmt, $titleStmt)
    }

    $publicationStmt = [System.Xml.XmlElement]$fileDesc.SelectSingleNode('./tei:publicationStmt', $namespaces)
    if (-not $publicationStmt) {
        $publicationStmt = New-TeiElement $Document 'publicationStmt'
        [void]$fileDesc.InsertAfter($publicationStmt, $editionStmt)
    }

    $sourceDesc = [System.Xml.XmlElement]$fileDesc.SelectSingleNode('./tei:sourceDesc', $namespaces)
    if (-not $sourceDesc) {
        $sourceDesc = New-TeiElement $Document 'sourceDesc'
        $sourceParagraph = New-TeiElement $Document 'p'
        $sourceParagraph.InnerText = 'Derived from the electronic source identified by the build configuration.'
        [void]$sourceDesc.AppendChild($sourceParagraph)
        [void]$fileDesc.AppendChild($sourceDesc)
    }

    # TEI fileDesc has a prescribed sequence.
    $order = @{
        titleStmt = 10; editionStmt = 20; extent = 30; publicationStmt = 40
        seriesStmt = 50; notesStmt = 60; sourceDesc = 70
    }
    $children = @($fileDesc.ChildNodes | Where-Object { $_ -is [System.Xml.XmlElement] })
    $sorted = @($children | Sort-Object { if ($order.ContainsKey($_.LocalName)) { $order[$_.LocalName] } else { 65 } })
    foreach ($child in $sorted) { [void]$fileDesc.AppendChild($child) }
    return $fileDesc
}

function Add-BookstacksMetadata {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$Header,
        [string]$TextId,
        [string]$LicenceTarget = 'https://creativecommons.org/licenses/by-sa/4.0/',
        [string]$LicenceText = 'This derived TEI file is made available under the Creative Commons Attribution-ShareAlike 4.0 International License; source rights remain as recorded in sourceDesc.'
    )

    $namespaces = Get-TeiNamespaceManager $Document
    $fileDesc = Ensure-HeaderOrder $Document $Header
    $titleStmt = [System.Xml.XmlElement]$fileDesc.SelectSingleNode('./tei:titleStmt', $namespaces)

    foreach ($node in @($titleStmt.SelectNodes('./tei:respStmt[@xml:id="bookstacks-encoding"]', $namespaces))) {
        [void]$titleStmt.RemoveChild($node)
    }
    $respStmt = New-TeiElement $Document 'respStmt'
    Set-XmlId $respStmt 'bookstacks-encoding'
    $resp = New-TeiElement $Document 'resp'
    $resp.InnerText = 'TEI P5 normalization, structural identifiers, and speaker-reference integrity'
    $name = New-TeiElement $Document 'name'
    $name.InnerText = 'Bookstacks project'
    [void]$respStmt.AppendChild($resp)
    [void]$respStmt.AppendChild($name)
    [void]$titleStmt.AppendChild($respStmt)

    $publicationStmt = [System.Xml.XmlElement]$fileDesc.SelectSingleNode('./tei:publicationStmt', $namespaces)
    $publicationStmt.RemoveAll()
    $publisher = New-TeiElement $Document 'publisher'
    $publisher.InnerText = 'Bookstacks project'
    $pubPlace = New-TeiElement $Document 'pubPlace'
    $pubPlace.InnerText = 'United States'
    $date = New-TeiElement $Document 'date'
    [void]$date.SetAttribute('when', $buildDate.ToString('yyyy-MM-dd'))
    $date.InnerText = $buildDate.ToString('dd MMMM yyyy', [System.Globalization.CultureInfo]::InvariantCulture)
    $localId = New-TeiElement $Document 'idno'
    [void]$localId.SetAttribute('type', 'local')
    $localId.InnerText = $TextId
    $availability = New-TeiElement $Document 'availability'
    [void]$availability.SetAttribute('status', 'free')
    $licence = New-TeiElement $Document 'licence'
    [void]$licence.SetAttribute('target', $LicenceTarget)
    $licence.InnerText = $LicenceText
    [void]$availability.AppendChild($licence)
    foreach ($node in @($publisher, $pubPlace, $date, $localId, $availability)) {
        [void]$publicationStmt.AppendChild($node)
    }

    $revisionDesc = [System.Xml.XmlElement]$Header.SelectSingleNode('./tei:revisionDesc', $namespaces)
    if (-not $revisionDesc) {
        $revisionDesc = New-TeiElement $Document 'revisionDesc'
        [void]$Header.AppendChild($revisionDesc)
    }
    foreach ($oldChange in @($revisionDesc.SelectNodes('./tei:change[@who="#bookstacks-encoding"]', $namespaces))) {
        [void]$revisionDesc.RemoveChild($oldChange)
    }
    $change = New-TeiElement $Document 'change'
    [void]$change.SetAttribute('when', $buildDate.ToString('yyyy-MM-dd'))
    [void]$change.SetAttribute('who', '#bookstacks-encoding')
    $change.InnerText = 'Normalized to standalone TEI P5; added granular structural identifiers and resolvable speaker references.'
    [void]$revisionDesc.PrependChild($change)
}

function Normalize-ImportedTei {
    param([System.Xml.XmlDocument]$Document, [System.Xml.XmlElement]$Root)

    $namespaces = Get-TeiNamespaceManager $Document

    # These XIncludes point outside the distributed corpus and cannot resolve in
    # a standalone Bookstacks file.
    foreach ($include in @($Root.SelectNodes('.//xi:include', $namespaces))) {
        $parent = $include.ParentNode
        [void]$parent.RemoveChild($include)
        $elementChildren = @($parent.ChildNodes | Where-Object { $_ -is [System.Xml.XmlElement] })
        if ($parent.LocalName -eq 'classDecl' -and $elementChildren.Count -eq 0) {
            [void]$parent.ParentNode.RemoveChild($parent)
        }
    }

    # Normalize HTML/custom-source constructs to TEI equivalents.
    foreach ($span in @($Root.SelectNodes('.//tei:span', $namespaces))) {
        [void](Rename-TeiElement $Document $span 'seg')
    }
    foreach ($heading in @($Root.SelectNodes('.//tei:h1 | .//tei:h2 | .//tei:h3 | .//tei:h4 | .//tei:h5 | .//tei:h6', $namespaces))) {
        [void](Rename-TeiElement $Document $heading 'head')
    }
    foreach ($strong in @($Root.SelectNodes('.//tei:strong', $namespaces))) {
        $renamed = Rename-TeiElement $Document $strong 'hi'
        if (-not $renamed.HasAttribute('rend')) { [void]$renamed.SetAttribute('rend', 'bold') }
    }
    foreach ($emphasis in @($Root.SelectNodes('.//tei:em', $namespaces))) {
        $renamed = Rename-TeiElement $Document $emphasis 'hi'
        if (-not $renamed.HasAttribute('rend')) { [void]$renamed.SetAttribute('rend', 'italic') }
    }
    foreach ($superscript in @($Root.SelectNodes('.//tei:sup', $namespaces))) {
        $renamed = Rename-TeiElement $Document $superscript 'hi'
        if (-not $renamed.HasAttribute('rend')) { [void]$renamed.SetAttribute('rend', 'superscript') }
    }
    foreach ($anchor in @($Root.SelectNodes('.//tei:a', $namespaces))) {
        $renamed = Rename-TeiElement $Document $anchor 'ref'
        if ($renamed.HasAttribute('href')) {
            [void]$renamed.SetAttribute('target', $renamed.GetAttribute('href'))
            $renamed.RemoveAttribute('href')
        }
    }
    foreach ($break in @($Root.SelectNodes('.//tei:br', $namespaces))) {
        [void](Rename-TeiElement $Document $break 'lb')
    }
    foreach ($image in @($Root.SelectNodes('.//tei:img', $namespaces))) {
        $renamed = Rename-TeiElement $Document $image 'graphic'
        if ($renamed.HasAttribute('src')) {
            [void]$renamed.SetAttribute('url', $renamed.GetAttribute('src'))
            $renamed.RemoveAttribute('src')
        }
    }
    foreach ($graphic in @($Root.SelectNodes('.//tei:div/tei:graphic', $namespaces))) {
        $figure = New-TeiElement $Document 'figure'
        [void]$graphic.ParentNode.InsertBefore($figure, $graphic)
        [void]$figure.AppendChild($graphic)
    }

    foreach ($element in @($Root.SelectNodes('.//*'))) {
        if ($element.HasAttribute('id') -and -not $element.HasAttribute('id', $xmlNamespace)) {
            Set-XmlId $element (ConvertTo-XmlIdToken $element.GetAttribute('id'))
        }
        if ($element.HasAttribute('id')) { $element.RemoveAttribute('id') }
        if ($element.HasAttribute('data-class')) {
            if (-not $element.HasAttribute('type')) {
                [void]$element.SetAttribute('type', $element.GetAttribute('data-class'))
            }
            $element.RemoveAttribute('data-class')
        }
        if ($element.HasAttribute('index')) { $element.RemoveAttribute('index') }
        if ($element.HasAttribute('placement')) { $element.RemoveAttribute('placement') }
        if ($element.HasAttribute('class')) {
            if (-not $element.HasAttribute('rend')) {
                [void]$element.SetAttribute('rend', $element.GetAttribute('class'))
            }
            $element.RemoveAttribute('class')
        }
        if ($element.HasAttribute('style')) {
            if (-not $element.HasAttribute('rend')) {
                [void]$element.SetAttribute('rend', $element.GetAttribute('style'))
            }
            $element.RemoveAttribute('style')
        }
        if ($element.HasAttribute('alt')) { $element.RemoveAttribute('alt') }
        if ($element.HasAttribute('type') -and $element.GetAttribute('type') -match '\s') {
            [void]$element.SetAttribute('type', (ConvertTo-XmlIdToken $element.GetAttribute('type')))
        }
        $language = $element.GetAttribute('lang', $xmlNamespace)
        if ($language -eq 'eng') { [void]$element.SetAttribute('lang', $xmlNamespace, 'en') }
        if ($language -eq 'rus') { [void]$element.SetAttribute('lang', $xmlNamespace, 'ru') }
        if ($element.LocalName -eq 'language' -and $element.HasAttribute('ident')) {
            if ($element.GetAttribute('ident') -eq 'eng') { [void]$element.SetAttribute('ident', 'en') }
            if ($element.GetAttribute('ident') -eq 'rus') { [void]$element.SetAttribute('ident', 'ru') }
        }
    }

    # One Austen source has a transcription slip, certainty/@locus="false";
    # every other attribution certainty in the six files uses locus="name".
    foreach ($certainty in @($Root.SelectNodes('.//tei:certainty[@locus="false"]', $namespaces))) {
        [void]$certainty.SetAttribute('locus', 'name')
    }

    # Source HTML ids sometimes repeat (typically glossary anchors). XML IDs
    # must be document-unique, so retain the first and suffix later instances.
    $seenIds = @{}
    foreach ($element in @($Root.SelectNodes('.//*[@xml:id]', $namespaces))) {
        $id = Get-XmlId $element
        if (-not $seenIds.ContainsKey($id)) {
            $seenIds[$id] = 1
            continue
        }
        $seenIds[$id]++
        Set-XmlId $element "$id-$($seenIds[$id])"
    }

    # A TEI div head precedes the div's other content.
    foreach ($div in @($Root.SelectNodes('.//tei:div[tei:head]', $namespaces))) {
        $heads = @($div.SelectNodes('./tei:head', $namespaces))
        for ($i = $heads.Count - 1; $i -ge 0; $i--) {
            [void]$div.PrependChild($heads[$i])
        }
    }

    # TEI does not permit a division to mix child divisions with ungrouped
    # paragraphs. Wrap each contiguous block run as a granular section while
    # retaining the source order.
    foreach ($div in @($Root.SelectNodes('.//tei:div[tei:div]', $namespaces))) {
        $hasMixedBlocks = @($div.ChildNodes | Where-Object {
            $_ -is [System.Xml.XmlElement] -and $_.LocalName -notin @('head', 'div')
        }).Count -gt 0
        if (-not $hasMixedBlocks) { continue }
        $wrapper = $null
        foreach ($node in @($div.ChildNodes)) {
            if ($node -is [System.Xml.XmlElement] -and $node.LocalName -in @('head', 'div')) {
                $wrapper = $null
                continue
            }
            if ($node -is [System.Xml.XmlElement]) {
                if (-not $wrapper) {
                    $wrapper = New-TeiElement $Document 'div'
                    [void]$wrapper.SetAttribute('type', 'section')
                    [void]$div.InsertBefore($wrapper, $node)
                }
                [void]$wrapper.AppendChild($node)
            } elseif ($wrapper -and $node.NodeType -in @([System.Xml.XmlNodeType]::Text, [System.Xml.XmlNodeType]::Whitespace, [System.Xml.XmlNodeType]::SignificantWhitespace, [System.Xml.XmlNodeType]::Comment)) {
                [void]$wrapper.AppendChild($node)
            }
        }
    }

    # Remove empty optional header components left after unresolved includes.
    foreach ($container in @($Root.SelectNodes('.//tei:encodingDesc | .//tei:classDecl', $namespaces))) {
        $elementChildren = @($container.ChildNodes | Where-Object { $_ -is [System.Xml.XmlElement] })
        if ($elementChildren.Count -eq 0) { [void]$container.ParentNode.RemoveChild($container) }
    }
}

function Add-StructuralIds {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$Body,
        [string]$Lang,
        [string]$TextId
    )

    $namespaces = Get-TeiNamespaceManager $Document
    $edition = [System.Xml.XmlElement]$Body.SelectSingleNode('./tei:div[@type="edition"] | ./tei:div[@type="translation"]', $namespaces)
    if ($edition) { Set-XmlId $edition "$TextId-$Lang-text" }

    $volumeNumber = 0
    foreach ($volume in @($Body.SelectNodes('./tei:div[@type="volume"]', $namespaces))) {
        $volumeNumber++
        if (-not $volume.GetAttribute('n')) { [void]$volume.SetAttribute('n', $volumeNumber.ToString()) }
        Set-XmlId $volume "$TextId-$Lang-volume-$volumeNumber"
        $partNumber = 0
        foreach ($part in @($volume.SelectNodes('./tei:div[@type="part"]', $namespaces))) {
            $partNumber++
            if (-not $part.GetAttribute('n')) { [void]$part.SetAttribute('n', $partNumber.ToString()) }
            Set-XmlId $part "$TextId-$Lang-volume-$volumeNumber-part-$partNumber"
        }
    }

    foreach ($div in @($Body.SelectNodes('.//tei:div', $namespaces))) {
        if (Get-XmlId $div) { continue }
        $parentDiv = [System.Xml.XmlElement]$div.SelectSingleNode('ancestor::tei:div[1]', $namespaces)
        $parentId = if ($parentDiv) { Get-XmlId $parentDiv } else { "$TextId-$Lang" }
        $kind = if ($div.GetAttribute('subtype')) { $div.GetAttribute('subtype') } elseif ($div.GetAttribute('type')) { $div.GetAttribute('type') } else { 'division' }
        $siblings = @($div.ParentNode.SelectNodes('./tei:div', $namespaces))
        $position = [Array]::IndexOf($siblings, $div) + 1
        $number = if ($div.GetAttribute('n')) { $div.GetAttribute('n') } else { $position.ToString('000') }
        Set-XmlId $div ((ConvertTo-XmlIdToken $parentId) + '-' + (ConvertTo-IdComponent $kind) + '-' + (ConvertTo-IdComponent $number))
    }

    $paragraphNumber = 0
    foreach ($paragraph in @($Body.SelectNodes('.//tei:p', $namespaces))) {
        $paragraphNumber++
        if (-not (Get-XmlId $paragraph)) {
            Set-XmlId $paragraph ("$Lang-p-" + $paragraphNumber.ToString('000000'))
        }
    }

    $utteranceNumber = 0
    foreach ($said in @($Body.SelectNodes('.//tei:said | .//tei:q[@type="spoken" or @who or @toWhom]', $namespaces))) {
        $utteranceNumber++
        if (-not (Get-XmlId $said)) {
            Set-XmlId $said ("$Lang-utterance-" + $utteranceNumber.ToString('000000'))
        }
    }
}

function Add-MilestoneIds {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$Body,
        [string]$Lang,
        [string]$MilestoneType
    )

    $namespaces = Get-TeiNamespaceManager $Document
    if ($MilestoneType -eq 'stephanus') {
        $seen = @{}
        foreach ($milestone in @($Body.SelectNodes('.//tei:milestone[translate(@resp,"STEPHANUS","stephanus")="stephanus"]', $namespaces))) {
            $unit = ConvertTo-IdComponent $milestone.GetAttribute('unit')
            $number = ConvertTo-IdComponent $milestone.GetAttribute('n')
            $baseId = "$Lang-stephanus-$unit-$number"
            if (-not $seen.ContainsKey($baseId)) { $seen[$baseId] = 0 }
            $seen[$baseId]++
            $id = if ($seen[$baseId] -eq 1) { $baseId } else { "$baseId-$($seen[$baseId])" }
            Set-XmlId $milestone $id
        }
    } elseif ($MilestoneType -eq 'bekker') {
        $currentPage = 'unknown-page'
        $seen = @{}
        foreach ($milestone in @($Body.SelectNodes('.//tei:milestone[translate(@resp,"BEKKER","bekker")="bekker"]', $namespaces))) {
            $unit = $milestone.GetAttribute('unit').ToLowerInvariant()
            $number = ConvertTo-IdComponent $milestone.GetAttribute('n')
            if ($unit -eq 'page') {
                $currentPage = $number
                $baseId = "$Lang-bekker-page-$currentPage"
            } else {
                $baseId = "$Lang-bekker-$currentPage-$unit-$number"
            }
            if (-not $seen.ContainsKey($baseId)) { $seen[$baseId] = 0 }
            $seen[$baseId]++
            $id = if ($seen[$baseId] -eq 1) { $baseId } else { "$baseId-$($seen[$baseId])" }
            Set-XmlId $milestone $id
        }
    }
}

function Normalize-SpeakerReferences {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$Header,
        [System.Xml.XmlElement]$Text
    )

    $namespaces = Get-TeiNamespaceManager $Document
    $existingIds = @{}
    foreach ($element in @($Document.SelectNodes('//*[@xml:id]', $namespaces))) {
        $existingId = Get-XmlId $element
        if ($existingId) { $existingIds[$existingId] = $true }
    }
    $existingParticipantIds = @{}
    foreach ($participant in @($Document.SelectNodes('//tei:person | //tei:personGrp', $namespaces))) {
        $participantId = Get-XmlId $participant
        if ($participantId) { $existingParticipantIds[$participantId] = $true }
    }
    $referencedPeople = [ordered]@{}
    foreach ($speech in @($Text.SelectNodes('.//tei:said[@who or @toWhom] | .//tei:q[@who or @toWhom]', $namespaces))) {
        foreach ($attributeName in @('who', 'toWhom')) {
            if (-not $speech.HasAttribute($attributeName)) { continue }
            $rawValue = $speech.GetAttribute($attributeName).Trim()
            if (-not $rawValue -or $rawValue -eq '#') {
                $speech.RemoveAttribute($attributeName)
                continue
            }

            # Digital Dostoevsky uses whitespace-separated #pointers for
            # multiple speakers/addressees. Older sources sometimes use a
            # single unprefixed display name containing spaces.
            $sourceNames = if ($rawValue.Contains('#')) {
                @($rawValue -split '\s+' | Where-Object { $_.Trim().TrimStart('#') })
            } else {
                @($rawValue)
            }
            $normalizedPointers = @()
            foreach ($sourceValue in $sourceNames) {
                $sourceName = $sourceValue.Trim().TrimStart('#')
                if (-not $sourceName) { continue }
                $personId = ConvertTo-XmlIdToken $sourceName
                # Some source attributions point to a place, object, or list
                # item used metonymically as a voice. Preserve that authority
                # record and use a distinct participant alias for @who.
                if ($existingIds.ContainsKey($personId) -and -not $existingParticipantIds.ContainsKey($personId)) {
                    $personId = ConvertTo-XmlIdToken "participant-$personId"
                }
                $normalizedPointers += "#$personId"
                if (-not $referencedPeople.Contains($personId)) { $referencedPeople[$personId] = $sourceName }
            }
            if ($normalizedPointers.Count) {
                [void]$speech.SetAttribute($attributeName, ($normalizedPointers -join ' '))
            } else {
                $speech.RemoveAttribute($attributeName)
            }
        }
    }

    if ($referencedPeople.Count -eq 0) { return }

    $profileDesc = [System.Xml.XmlElement]$Header.SelectSingleNode('./tei:profileDesc', $namespaces)
    if (-not $profileDesc) {
        $profileDesc = New-TeiElement $Document 'profileDesc'
        $revisionDesc = $Header.SelectSingleNode('./tei:revisionDesc', $namespaces)
        if ($revisionDesc) { [void]$Header.InsertBefore($profileDesc, $revisionDesc) } else { [void]$Header.AppendChild($profileDesc) }
    }
    $particDesc = [System.Xml.XmlElement]$profileDesc.SelectSingleNode('./tei:particDesc', $namespaces)
    if (-not $particDesc) {
        $particDesc = New-TeiElement $Document 'particDesc'
        [void]$profileDesc.AppendChild($particDesc)
    }
    $listPerson = [System.Xml.XmlElement]$particDesc.SelectSingleNode('./tei:listPerson', $namespaces)
    if (-not $listPerson) {
        $listPerson = New-TeiElement $Document 'listPerson'
        foreach ($person in @($particDesc.SelectNodes('./tei:person', $namespaces))) {
            [void]$listPerson.AppendChild($person)
        }
        [void]$particDesc.AppendChild($listPerson)
    }

    $declared = @{}
    # A source may partition characters and narrator/conjoined voices across
    # multiple lists, including root-level standOff registers. Treat every
    # declared person or group as available before adding missing records.
    foreach ($person in @($Document.SelectNodes('//tei:person | //tei:personGrp', $namespaces))) {
        $personId = Get-XmlId $person
        if (-not $personId) {
            $personName = $person.SelectSingleNode('./tei:persName[1] | ./tei:name[1]', $namespaces)
            if ($personName) {
                $personId = ConvertTo-XmlIdToken $personName.InnerText
                Set-XmlId $person $personId
            }
        }
        if ($personId) { $declared[$personId] = $true }
    }

    foreach ($personId in $referencedPeople.Keys) {
        if ($declared.ContainsKey($personId)) { continue }
        $person = New-TeiElement $Document 'person'
        Set-XmlId $person $personId
        $persName = New-TeiElement $Document 'persName'
        $persName.InnerText = $referencedPeople[$personId]
        [void]$person.AppendChild($persName)
        [void]$listPerson.AppendChild($person)
    }

    if (@($listPerson.SelectNodes('./tei:person | ./tei:personGrp', $namespaces)).Count -eq 0) {
        [void]$particDesc.RemoveChild($listPerson)
        if (@($particDesc.ChildNodes | Where-Object { $_ -is [System.Xml.XmlElement] }).Count -eq 0) {
            [void]$profileDesc.RemoveChild($particDesc)
        }
    }
}

function Merge-StandOff {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$TargetStandOff,
        [System.Xml.XmlElement]$SourceStandOff
    )

    if (-not $SourceStandOff) { return }
    $namespaces = Get-TeiNamespaceManager $Document
    $knownIds = @{}
    foreach ($record in @($TargetStandOff.SelectNodes('.//tei:person | .//tei:personGrp', $namespaces))) {
        $recordId = Get-XmlId $record
        if ($recordId) { $knownIds[$recordId] = $true }
    }

    foreach ($sourceList in @($SourceStandOff.SelectNodes('./tei:listPerson', $namespaces))) {
        $listType = $sourceList.GetAttribute('type')
        $targetList = $null
        foreach ($candidate in @($TargetStandOff.SelectNodes('./tei:listPerson', $namespaces))) {
            if ($candidate.GetAttribute('type') -eq $listType) {
                $targetList = [System.Xml.XmlElement]$candidate
                break
            }
        }
        if (-not $targetList) {
            $targetList = New-TeiElement $Document 'listPerson'
            foreach ($attribute in @($sourceList.Attributes)) {
                [void]$targetList.Attributes.Append($attribute.CloneNode($true))
            }
            [void]$TargetStandOff.AppendChild($targetList)
        }
        foreach ($record in @($sourceList.SelectNodes('./tei:person | ./tei:personGrp', $namespaces))) {
            $recordId = Get-XmlId $record
            if ($recordId -and $knownIds.ContainsKey($recordId)) { continue }
            [void]$targetList.AppendChild($Document.ImportNode($record, $true))
            if ($recordId) { $knownIds[$recordId] = $true }
        }
    }
}

function Add-IdentifierPrefix {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$Root,
        [string]$Prefix
    )

    $namespaces = Get-TeiNamespaceManager $Document
    $idMap = @{}
    foreach ($element in @($Root.SelectNodes('.//*[@xml:id or @id]', $namespaces))) {
        $oldId = if ($element.HasAttribute('id', $xmlNamespace)) { $element.GetAttribute('id', $xmlNamespace) } else { $element.GetAttribute('id') }
        if (-not $oldId) { continue }
        $newId = (ConvertTo-IdComponent $Prefix) + '-' + (ConvertTo-IdComponent $oldId)
        if (-not $idMap.ContainsKey($oldId)) { $idMap[$oldId] = $newId }
        if ($element.HasAttribute('id', $xmlNamespace)) {
            Set-XmlId $element $newId
        } else {
            [void]$element.SetAttribute('id', $newId)
        }
    }

    $pointerAttributes = @('target', 'who', 'corresp', 'sameAs', 'copyOf', 'next', 'prev')
    foreach ($element in @($Root.SelectNodes('.//*'))) {
        foreach ($attributeName in $pointerAttributes) {
            if (-not $element.HasAttribute($attributeName)) { continue }
            $tokens = @($element.GetAttribute($attributeName) -split '\s+')
            $changed = $false
            for ($i = 0; $i -lt $tokens.Count; $i++) {
                if ($tokens[$i].StartsWith('#')) {
                    $oldTarget = $tokens[$i].Substring(1)
                    if ($idMap.ContainsKey($oldTarget)) {
                        $tokens[$i] = '#' + $idMap[$oldTarget]
                        $changed = $true
                    }
                }
            }
            if ($changed) { [void]$element.SetAttribute($attributeName, ($tokens -join ' ')) }
        }
    }
}

function Set-CombinedHeader {
    param(
        [System.Xml.XmlDocument]$Document,
        [System.Xml.XmlElement]$Header,
        [object[]]$Sources,
        [string]$Title,
        [string]$TextId
    )

    $namespaces = Get-TeiNamespaceManager $Document
    $titleStmt = [System.Xml.XmlElement]$Header.SelectSingleNode('./tei:fileDesc/tei:titleStmt', $namespaces)
    if ($titleStmt -and $Title) {
        foreach ($oldTitle in @($titleStmt.SelectNodes('./tei:title', $namespaces))) {
            [void]$titleStmt.RemoveChild($oldTitle)
        }
        $newTitle = New-TeiElement $Document 'title'
        [void]$newTitle.SetAttribute('type', 'main')
        [void]$newTitle.SetAttribute('lang', $xmlNamespace, 'ru')
        Set-XmlId $newTitle "$TextId-title"
        $newTitle.InnerText = $Title
        [void]$titleStmt.PrependChild($newTitle)
    }

    $targetSourceDesc = [System.Xml.XmlElement]$Header.SelectSingleNode('./tei:fileDesc/tei:sourceDesc', $namespaces)
    if ($targetSourceDesc -and $Sources.Count -gt 1) {
        $targetSourceDesc.RemoveAll()
        $listBibl = New-TeiElement $Document 'listBibl'
        foreach ($sourceInfo in $Sources) {
            foreach ($bibliography in @($sourceInfo.Header.SelectNodes('./tei:fileDesc/tei:sourceDesc/tei:biblStruct | ./tei:fileDesc/tei:sourceDesc/tei:bibl', $sourceInfo.Namespaces))) {
                [void]$listBibl.AppendChild($Document.ImportNode($bibliography, $true))
            }
        }
        [void]$targetSourceDesc.AppendChild($listBibl)
    }
}

function Build-TeiFile {
    param(
        [string[]]$SourcePath,
        [string]$OutputPath,
        [string]$Lang,
        [string]$XmlLang,
        [string]$TextId,
        [string]$MilestoneType,
        [string]$CombinedTitle,
        [string]$CombineMode = 'sequence',
        [string]$SupplementTitle,
        [string]$LicenceTarget = 'https://creativecommons.org/licenses/by-sa/4.0/',
        [string]$LicenceText = 'This derived TEI file is made available under the Creative Commons Attribution-ShareAlike 4.0 International License; source rights remain as recorded in sourceDesc.'
    )

    $sources = @()
    foreach ($path in $SourcePath) {
        $source = New-Object System.Xml.XmlDocument
        $source.PreserveWhitespace = $true
        $source.Load((Resolve-Path $path))
        $sourceNamespaces = Get-TeiNamespaceManager $source
        $sourceHeader = $source.SelectSingleNode('/tei:TEI/tei:teiHeader', $sourceNamespaces)
        $sourceFront = $source.SelectSingleNode('/tei:TEI/tei:text/tei:front', $sourceNamespaces)
        $sourceBody = $source.SelectSingleNode('/tei:TEI/tei:text/tei:body', $sourceNamespaces)
        $sourceBack = $source.SelectSingleNode('/tei:TEI/tei:text/tei:back', $sourceNamespaces)
        $sourceStandOff = $source.SelectSingleNode('/tei:TEI/tei:standOff', $sourceNamespaces)
        if (-not $sourceBody) { throw "The source document does not contain a TEI body: $path" }
        $sources += [pscustomobject]@{
            Document = $source
            Header = $sourceHeader
            Front = $sourceFront
            Body = $sourceBody
            Back = $sourceBack
            StandOff = $sourceStandOff
            Namespaces = $sourceNamespaces
        }
    }

    $output = New-Object System.Xml.XmlDocument
    $output.PreserveWhitespace = $true
    [void]$output.AppendChild($output.CreateXmlDeclaration('1.0', 'UTF-8', $null))
    [void]$output.AppendChild($output.CreateProcessingInstruction('xml-model', 'href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"'))
    $root = New-TeiElement $output 'TEI'
    Set-XmlId $root $TextId
    [void]$output.AppendChild($root)

    $header = if ($sources[0].Header) { [System.Xml.XmlElement]$output.ImportNode($sources[0].Header, $true) } else { New-TeiElement $output 'teiHeader' }
    [void]$root.AppendChild($header)
    $text = New-TeiElement $output 'text'
    [void]$text.SetAttribute('lang', $xmlNamespace, $XmlLang)
    [void]$root.AppendChild($text)
    if ($sources[0].Front) {
        [void]$text.AppendChild($output.ImportNode($sources[0].Front, $true))
    }
    $body = [System.Xml.XmlElement]$output.ImportNode($sources[0].Body, $true)
    if ($sources.Count -gt 1) {
        if ($CombineMode -ne 'supplement') { Add-IdentifierPrefix $output $body 'source-1' }
        for ($sourceIndex = 1; $sourceIndex -lt $sources.Count; $sourceIndex++) {
            $additionalBody = [System.Xml.XmlElement]$output.ImportNode($sources[$sourceIndex].Body, $true)
            if ($CombineMode -ne 'supplement') {
                Add-IdentifierPrefix $output $additionalBody ("source-" + ($sourceIndex + 1))
            }
            if ($CombineMode -eq 'supplement') {
                $supplement = New-TeiElement $output 'div'
                [void]$supplement.SetAttribute('type', 'supplement')
                [void]$supplement.SetAttribute('subtype', 'suppressed-chapter')
                $supplementHead = New-TeiElement $output 'head'
                $supplementHead.InnerText = if ($SupplementTitle) { $SupplementTitle } else { 'Textual supplement' }
                [void]$supplement.AppendChild($supplementHead)
                foreach ($child in @($additionalBody.ChildNodes | Where-Object { $_ -is [System.Xml.XmlElement] })) {
                    [void]$supplement.AppendChild($child)
                }
                [void]$body.AppendChild($supplement)
                continue
            }
            foreach ($child in @($additionalBody.ChildNodes | Where-Object { $_ -is [System.Xml.XmlElement] })) {
                # War and Peace repeats the same title/editor front matter in
                # every source volume. Retain it only from the first volume.
                if ($child.LocalName -eq 'div' -and $child.GetAttribute('type') -eq 'section') {
                    $candidateHeadNode = $child.SelectSingleNode('./tei:head', (Get-TeiNamespaceManager $output))
                    $candidateHead = if ($candidateHeadNode) { [string]::Join(' ', ($candidateHeadNode.InnerText -split '\s+')) } else { '' }
                    $duplicate = $false
                    foreach ($existing in @($body.SelectNodes('./tei:div[@type="section"]', (Get-TeiNamespaceManager $output)))) {
                        $existingHead = $existing.SelectSingleNode('./tei:head', (Get-TeiNamespaceManager $output))
                        if ($existingHead -and ([string]::Join(' ', ($existingHead.InnerText -split '\s+')) -eq $candidateHead)) { $duplicate = $true; break }
                    }
                    if ($duplicate) { continue }
                }
                [void]$body.AppendChild($child)
            }
        }
    }
    [void]$text.AppendChild($body)
    if ($sources[0].Back) {
        [void]$text.AppendChild($output.ImportNode($sources[0].Back, $true))
    }

    $standOff = $null
    if ($sources[0].StandOff) {
        $standOff = [System.Xml.XmlElement]$output.ImportNode($sources[0].StandOff, $true)
        [void]$root.AppendChild($standOff)
    }
    if ($CombineMode -eq 'supplement' -and $sources.Count -gt 1) {
        if (-not $standOff) {
            $standOff = New-TeiElement $output 'standOff'
            [void]$root.AppendChild($standOff)
        }
        for ($sourceIndex = 1; $sourceIndex -lt $sources.Count; $sourceIndex++) {
            if ($sources[$sourceIndex].StandOff) {
                $importedStandOff = [System.Xml.XmlElement]$output.ImportNode($sources[$sourceIndex].StandOff, $true)
                Merge-StandOff $output $standOff $importedStandOff
            }
        }
    }

    if ($sources.Count -gt 1) { Set-CombinedHeader $output $header $sources $CombinedTitle $TextId }
    Normalize-ImportedTei $output $root
    Add-BookstacksMetadata $output $header $TextId $LicenceTarget $LicenceText
    Add-StructuralIds $output $text $Lang $TextId
    Add-MilestoneIds $output $text $Lang $MilestoneType
    Normalize-SpeakerReferences $output $header $text

    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Encoding = New-Object System.Text.UTF8Encoding($false)
    $settings.Indent = $true
    $settings.IndentChars = '  '
    $settings.NewLineChars = "`n"
    $settings.NewLineHandling = [System.Xml.NewLineHandling]::Replace
    $resolvedOutputPath = [System.IO.Path]::GetFullPath($OutputPath)
    $outDir = Split-Path $resolvedOutputPath
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
    $writer = [System.Xml.XmlWriter]::Create($resolvedOutputPath, $settings)
    try { $output.Save($writer) } finally { $writer.Dispose() }
    Write-Output "Generated $resolvedOutputPath"
}

$config = Get-Content $ConfigPath | ConvertFrom-Json
if ($Author) {
    $config = @($config | Where-Object { $_.author -eq $Author })
    if ($config.Count -eq 0) { throw "No configured TEI works found for author: $Author" }
}
foreach ($item in $config) {
    $authorSlug = $item.author.ToLowerInvariant()
    $baseName = $authorSlug + '_' + $item.id
    Write-Output "Processing $($item.title) by $($item.author)..."
    if ($item.source_format -eq 'middlemarch_annotated_fragments') {
        if ($item.sources.Count -ne 1) { throw "Middlemarch must have exactly one source repository directory." }
        $src = $item.sources[0]
        $srcPath = Join-Path $PSScriptRoot $src.path
        $outPath = Join-Path $PSScriptRoot (Join-Path $authorSlug "${baseName}_$($src.lang).xml")
        & python (Join-Path $PSScriptRoot 'build_middlemarch.py') `
            --source-dir $srcPath `
            --output $outPath `
            --schema (Join-Path $PSScriptRoot 'tei_all.rng')
        if ($LASTEXITCODE -ne 0) { throw "Failed to convert the annotated Middlemarch source corpus." }
        continue
    }
    if ($item.source_format -eq 'gutenberg_epub') {
        if ($item.sources.Count -ne 1) { throw "Gutenberg EPUB work $($item.title) must have exactly one source." }
        $src = $item.sources[0]
        $srcPath = Join-Path $PSScriptRoot $src.path
        $outPath = Join-Path $PSScriptRoot (Join-Path $authorSlug "${baseName}_$($src.lang).xml")
        & python (Join-Path $PSScriptRoot 'build_gutenberg_epub.py') `
            --source $srcPath `
            --output $outPath `
            --schema (Join-Path $PSScriptRoot 'tei_all.rng') `
            --text-id $baseName
        if ($LASTEXITCODE -ne 0) { throw "Failed to convert Gutenberg EPUB for $($item.title)." }
        continue
    }
    if ($item.combine) {
        $languages = @($item.sources.lang | Select-Object -Unique)
        if ($languages.Count -ne 1) { throw "Combined work $($item.title) must use one language per output." }
        $lang = $languages[0]
        $firstSource = $item.sources[0]
        $xmlLang = if ($firstSource.xml_lang) { $firstSource.xml_lang } elseif ($lang -eq 'eng') { 'en' } elseif ($lang -eq 'rus') { 'ru' } else { $lang }
        $srcPaths = @($item.sources | ForEach-Object { Join-Path $PSScriptRoot $_.path })
        $outPath = Join-Path $PSScriptRoot (Join-Path $authorSlug "${baseName}_${lang}.xml")
        $combineMode = if ($item.combine_mode) { $item.combine_mode } else { 'sequence' }
        $licenceTarget = if ($item.licence_target) { $item.licence_target } else { 'https://creativecommons.org/licenses/by-sa/4.0/' }
        $licenceText = if ($item.licence_text) { $item.licence_text } else { 'This derived TEI file is made available under the Creative Commons Attribution-ShareAlike 4.0 International License; source rights remain as recorded in sourceDesc.' }
        Build-TeiFile -SourcePath $srcPaths -OutputPath $outPath -Lang $lang -XmlLang $xmlLang -TextId $baseName -MilestoneType $item.milestone_type -CombinedTitle $item.combined_title -CombineMode $combineMode -SupplementTitle $item.supplement_title -LicenceTarget $licenceTarget -LicenceText $licenceText

        $authorOutputDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $authorSlug))
        foreach ($obsoleteName in @($item.obsolete_outputs | Where-Object { $_ })) {
            $obsoletePath = [System.IO.Path]::GetFullPath((Join-Path $authorOutputDirectory $obsoleteName))
            if (-not $obsoletePath.StartsWith($authorOutputDirectory + [System.IO.Path]::DirectorySeparatorChar)) {
                throw "Refusing to remove output outside $authorOutputDirectory`: $obsoletePath"
            }
            if (Test-Path -LiteralPath $obsoletePath) {
                [System.IO.File]::Delete($obsoletePath)
                Write-Output "Removed obsolete generated fragment $obsoletePath"
            }
        }
        continue
    }
    foreach ($src in $item.sources) {
        $lang = $src.lang
        $xmlLang = if ($src.xml_lang) { $src.xml_lang } elseif ($lang -eq 'eng') { 'en' } elseif ($lang -eq 'rus') { 'ru' } else { $lang }
        $srcPath = Join-Path $PSScriptRoot $src.path
        $outPath = Join-Path $PSScriptRoot (Join-Path $authorSlug "${baseName}_${lang}.xml")
        $licenceTarget = if ($item.licence_target) { $item.licence_target } else { 'https://creativecommons.org/licenses/by-sa/4.0/' }
        $licenceText = if ($item.licence_text) { $item.licence_text } else { 'This derived TEI file is made available under the Creative Commons Attribution-ShareAlike 4.0 International License; source rights remain as recorded in sourceDesc.' }
        Build-TeiFile -SourcePath @($srcPath) -OutputPath $outPath -Lang $lang -XmlLang $xmlLang -TextId $baseName -MilestoneType $item.milestone_type -LicenceTarget $licenceTarget -LicenceText $licenceText
    }
}

if (-not $Author -or $Author -eq 'Plato') {
    & (Join-Path $PSScriptRoot 'build_plato_republic.ps1')
}

Write-Output 'Done building all TEI files.'
