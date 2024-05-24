#!/bin/bash

# ? NOTE: generated script with ChatGPT - no problems upon a quick review but be careful
# ? NOTE: found an issue that was causing issues - follow this: https://stackoverflow.com/a/75602237
# ? NOTE: the script is extensible so that any other youtube-dl commands can be added when executing in a terminal

# Function to download video using youtube-dl
download_video() {
    local video_url="$1"
    shift  # Shift arguments so that the remaining arguments can be treated as flags
    local flags=("$@")
    youtube-dl "$video_url" \
        --hls-prefer-ffmpeg \
        --write-info-json \
        --write-description \
        --restrict-filenames \
        -f "mp4 best" \
        -o "videos/%(id)s/%(id)s.mp4" \
        "${flags[@]}"
}

# Main function to handle command-line arguments
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <video_url> [additional_flags]"
        exit 1
    fi
    local video_url="$1"
    shift
    download_video "$video_url" "$@"
}

# Execute main function
main "$@"
