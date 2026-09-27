<#
Start a work session on Windows: attach the webcam to WSL, start the container,
configure the camera and open a shell in RT-COSMIK.

Usage (PowerShell, from the repository root):
    powershell -ExecutionPolicy Bypass -File scripts\tools\start_session.ps1
    powershell -ExecutionPolicy Bypass -File scripts\tools\start_session.ps1 -Container cosmik -NoShell
#>
param(
    [string]$Container = "cosmik",
    [string]$VidPid = "0c45:2283",
    [switch]$NoShell
)

function Step($msg) { Write-Host "[session] $msg" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "[session] $msg" -ForegroundColor Red; exit 1 }

# Docker Desktop also brings up the WSL 2 backend that usbipd attaches to
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Step "starting Docker Desktop"
    Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 2
        docker info *> $null
        if ($LASTEXITCODE -eq 0) { break }
    }
    if ($LASTEXITCODE -ne 0) { Fail "Docker Desktop did not start" }
}

$line = usbipd list | Where-Object { $_ -match "^\s*\S+\s+$VidPid\s" } | Select-Object -First 1
if (-not $line) { Fail "camera $VidPid not found; is it plugged in?" }
$null = $line -match "^\s*(\S+)\s"
$busid = $Matches[1]

if ($line -match "Attached") {
    Step "camera already attached (busid $busid)"
} else {
    if ($line -match "Not shared") {
        Step "sharing the camera (busid $busid)"
        usbipd bind --busid $busid
        if ($LASTEXITCODE -ne 0) { Fail "usbipd bind needs an administrator PowerShell, once" }
    }
    Step "attaching the camera to WSL (busid $busid)"
    usbipd attach --wsl --busid $busid
    if ($LASTEXITCODE -ne 0) {
        # usbipd needs a running WSL 2 distribution; keep one alive in the background
        Start-Process wsl.exe -ArgumentList "--exec", "sleep", "infinity" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        usbipd attach --wsl --busid $busid
        if ($LASTEXITCODE -ne 0) { Fail "could not attach the camera" }
    }
}

$running = docker inspect -f "{{.State.Running}}" $Container 2>$null
if ($LASTEXITCODE -ne 0) { Fail "container '$Container' not found (see: docker ps -a)" }
if ($running -ne "true") {
    Step "starting container $Container"
    docker start $Container | Out-Null
}

$found = $false
for ($i = 0; $i -lt 10; $i++) {
    docker exec $Container test -e /dev/video0
    if ($LASTEXITCODE -eq 0) { $found = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $found) { Fail "/dev/video0 did not show up in the container" }

docker exec $Container v4l2-ctl -d /dev/video0 -c exposure_dynamic_framerate=0
Step "camera ready: /dev/video0, exposure_dynamic_framerate=0"

if (-not $NoShell) {
    docker exec -it -e YOLO_VERBOSE=False -w /root/workspace/ros_ws/RT-COSMIK-main $Container bash
}
