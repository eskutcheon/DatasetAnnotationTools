# ? NOTE: generated script with ChatGPT - no problems upon a quick review but be careful
# ? NOTE: found an issue that was causing issues - follow this: https://stackoverflow.com/a/75602237
# ? NOTE: the script is extensible so that any other youtube-dl commands can be added when executing in a terminal

# ! WARNING: I'm less confident in this one being correct - haven't had to script in Powershell in years

# Function to download video using youtube-dl
function Download-Video {
    param (
        [string]$videoUrl,
        [array]$flags
    )

    # Build the youtube-dl command
    $command = "youtube-dl $videoUrl --hls-prefer-ffmpeg --write-info-json --write-description --restrict-filenames -o `""videos/%(id)s/%(id)s.%(ext)s`""
    $flagsString = $flags -join " "
    $fullCommand = "$command $flagsString"

    # Execute the command
    Invoke-Expression $fullCommand
}

# Main function to handle command-line arguments
function Main {
    param (
        [string]$videoUrl,
        [array]$additionalFlags
    )

    if (-not $videoUrl) {
        Write-Host "Usage: .\download_video.ps1 <video_url> [additional_flags]"
        exit 1
    }

    Download-Video -videoUrl $videoUrl -flags $additionalFlags
}

# Execute main function
Main -videoUrl $args[0] -additionalFlags $args[1..$args.Length]
