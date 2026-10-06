$ErrorActionPreference = 'Stop'

$flutterCommand = Get-Command flutter -ErrorAction SilentlyContinue
if (-not $flutterCommand) {
    throw 'Flutter was not found. Install the Flutter SDK, add its bin folder to PATH, and reopen this terminal.'
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$androidDirectory = Join-Path $projectRoot 'android'
$manifestTemplate = Join-Path $PSScriptRoot 'android\AndroidManifest.xml'
$stringsTemplate = Join-Path $PSScriptRoot 'android\strings.xml'
$iconTemplate = Join-Path $PSScriptRoot 'android\ic_launcher.xml'

if (-not (Test-Path (Join-Path $androidDirectory 'gradlew.bat'))) {
    $scaffoldPath = Join-Path ([IO.Path]::GetTempPath()) (
        'nadeem-electronics-android-' + [guid]::NewGuid().ToString('N')
    )
    try {
        & $flutterCommand.Source create `
            --no-pub `
            --platforms=android `
            --org com.nadeemelectronics `
            --project-name nadeem_electronics_app `
            $scaffoldPath
        if ($LASTEXITCODE -ne 0) {
            throw 'Flutter could not generate the Android build scaffold.'
        }

        Copy-Item -Path (Join-Path $scaffoldPath 'android') `
            -Destination $androidDirectory -Recurse
    }
    finally {
        if (Test-Path $scaffoldPath) {
            Remove-Item -LiteralPath $scaffoldPath -Recurse -Force
        }
    }
}

$manifestPath = Join-Path $androidDirectory 'app\src\main\AndroidManifest.xml'
$stringsPath = Join-Path $androidDirectory 'app\src\main\res\values\strings.xml'
$iconPath = Join-Path $androidDirectory 'app\src\main\res\drawable\ic_launcher.xml'

Copy-Item -LiteralPath $manifestTemplate -Destination $manifestPath -Force
Copy-Item -LiteralPath $stringsTemplate -Destination $stringsPath -Force
Copy-Item -LiteralPath $iconTemplate -Destination $iconPath -Force

Write-Host 'Android project is ready. Next run: flutter pub get'
