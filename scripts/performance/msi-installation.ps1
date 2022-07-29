function SendTelemetry($totalSeconds)
{
    $os = [Environment]::OSVersion.Platform.ToString()
    $osVersion = [Environment]::OSVersion.Version.ToString()

    $telemetryObject = @{
        iKey = '02b91c82-6729-4241-befc-e6d02ca4fbba';
        name = 'azurecli/extension';
        time = [DateTime]::UtcNow.ToString('o');
        data = @{
                baseType = 'EventData';
                baseData = @{
                        ver = 2;
                        name = 'azurecli/extension';
                        properties = @{
                                'Context.Default.VS.Core.OS.Type' = $os;
                                'Context.Default.VS.Core.OS.Version' = $osVersion;
                                'Context.Default.AzureCLI.InstallationTime' = $totalSeconds;
                        };
                }
        }
    }

    Invoke-RestMethod `
        -Uri 'https://eastus-2.in.applicationinsights.azure.com//v2/track' `
        -ContentType 'application/json' `
        -Method Post `
        -Body (ConvertTo-Json -InputObject $telemetryObject -Depth 100 -Compress)
}


$i=1
for(;$i -le 10;$i++)
{
    Write-Host "Testing MSI round $i"

    Write-Host Uninstalling
    Uninstall-Package -Name "Microsoft Azure CLI"

    Write-Host Installing
    $startTime = Get-Date
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi
    Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'
    Write-Host "Exit code:" $LASTEXITCODE
    rm .\AzureCLI.msi

    $finishTime= Get-Date
    $totalTime = $finishTime - $startTime
    $totalSeconds = $totalTime.TotalSeconds
    Write-Host "Sending telemetry:" $totalSeconds
    SendTelemetry $totalSeconds
}
