$env:AZ_INSTALLER="PIP"

if (Test-Path "$PSScriptRoot\python.exe") {
    # Perfer python.exe in venv
    & "$PSScriptRoot\python.exe" -m azure.cli @args
}
else {
    # Run system python.exe
    python.exe -m azure.cli $args
}
