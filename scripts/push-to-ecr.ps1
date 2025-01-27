
[CmdletBinding()]
param (
    [string]$ImageName="bedrock-proxy-api",
    [string]$Tag="latest",
    [string]$AwsRegion="us-west-2",
    [string]$DockerfilePath="."
)

$TaggedImageName = $("{0}:{1}" -f $ImageName, $Tag)
$BuildPlatform = "linux/arm64"
[Environment]::SetEnvironmentVariable("BUILDPLATFORM", $BuildPlatform)

# Get the account ID for the current region
$AwsAccountId = $(aws sts get-caller-identity --region $AwsRegion --query Account --output text)

# Create repository URI
$RepositoryUri="$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ImageName"
$RemoteImageName = $("{0}:{1}" -f $RepositoryUri, $Tag)

if ($DockerfilePath -eq '.'){ 
    $Dockerfile = "Dockerfile"
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
    docker buildx build --platform $BuildPlatform -t $TaggedImageName -f $Dockerfile --load $DockerfileDirectory

    # Create ECR repository if it doesn't exist
    aws ecr create-repository --repository-name $ImageName --region $AwsRegion

    # Log in to ECR
    aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin $RepositoryUri
    
    # Tag the image for the current region
    docker tag $TaggedImageName $RemoteImageName
    # Push the image to ECR
    docker push $RemoteImageName
    
    Write-Host "Pushed $TaggedImageName to $RemoteImageName"
     
}
finally {
    if ($DockerfilePath -ne '.'){ Pop-Location }

}
