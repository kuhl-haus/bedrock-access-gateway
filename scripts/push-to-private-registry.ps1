
[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]$RegistryName,

    [Parameter(Mandatory)]
    [string]$Tag,

    [string]$ImageName="bedrock-proxy-api",

    [string]$DockerfilePath="."
)

New-Variable -Name LatestTag -Option Constant -Value "latest"
$BuildPlatform = "linux/amd64"
[Environment]::SetEnvironmentVariable("BUILDPLATFORM", $BuildPlatform)

$LocalImageName = $("{0}:{1}" -f $ImageName, $Tag)
$RemoteImageName = $("{0}/{1}" -f $RegistryName, $LocalImageName)
$LatestLocalImage = $("{0}:{1}" -f $ImageName, $LatestTag)
$LatestRemoteImage = $("{0}/{1}" -f $RegistryName, $LatestLocalImage)

if ($DockerfilePath -eq '.'){
    $Dockerfile = "Dockerfile_ecs"
    $DockerfileDirectory = "."
}else {
    if (Test-Path $DockerfilePath) {
        $DockerfileDirectory = Split-Path -Path $DockerfilePath -Parent
        $Dockerfile = Split-Path -Path $DockerfilePath -Leaf
        Push-Location $DockerfileDirectory
    }else {
        throw "Invalid path $DockerfilePath"
    }
}

try {
    docker buildx build --platform $BuildPlatform -t $LocalImageName -f $Dockerfile --load $DockerfileDirectory

    docker tag $LocalImageName $RemoteImageName
    # Push the image to registry
    docker push $RemoteImageName
    Write-Host "Pushed $LocalImageName to $RemoteImageName"

    if ($Tag -ne $LatestTag) {
        docker tag $LocalImageName $LatestLocalImage
        docker tag $LocalImageName $LatestRemoteImage
        docker push $LatestRemoteImage
    }
}
finally {
    if ($DockerfilePath -ne '.'){ Pop-Location }

}
