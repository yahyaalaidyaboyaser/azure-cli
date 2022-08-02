#!/usr/bin/env bash

set -e
os="Ubuntu"
osVersion="20.04"

for i in {1..10}; do
    sudo apt-get remove azure-cli

    startTime=$(date +%s)
    curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null
    echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
    sudo apt-get update
    sudo apt-get install azure-cli
    finishTime=$(date +%s)
    totalTime=$(($finishTime-$startTime))
    echo "Total installation time is $totalTime seconds"

    telemetryObject="{\"iKey\":\"02b91c82-6729-4241-befc-e6d02ca4fbba\",\"name\":\"azurecli/extension\",\"time\":\"$(date --utc +"%Y-%m-%dT%H:%M:%SZ")\",\"data\":{\"baseType\":\"EventData\",\"baseData\":{\"ver\":2,\"name\":\"azurecli/extension\",\"properties\":{\"Context.Default.VS.Core.OS.Type\":\"${os}\",\"Context.Default.VS.Core.OS.Version\":\"${osVersion}\",\"Context.Default.AzureCLI.InstallationTime\":${totalTime}}}}}"

    echo $telemetryObject

    curl -X POST https://eastus-2.in.applicationinsights.azure.com//v2/track -d "${telemetryObject}"
done
