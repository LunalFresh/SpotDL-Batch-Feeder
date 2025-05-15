# SpotDL Batch Feeder

A robust, multi-process batch controller for [SpotDL](https://github.com/spotDL/spotify-downloader), allowing high-volume Spotify playlist/track downloading with duplicate/skip detection and full progress logs.
**Optimized for large libraries and heavy automation.**

---

## Features

* Multi-process, high-speed downloading (Python multiprocessing)
* Automatic skip for already-downloaded tracks
* Retry logic for failed downloads
* Detailed logging (track log, failed URLs, summary)
* Configurable via `config.json`
* [No shady browser cookie extensions required](#extracting-cookies-safely)

---

## Requirements

* Python 3.9+
* [SpotDL](https://github.com/spotDL/spotify-downloader) (`pip install spotdl`)
* [yt-dlp](https://github.com/yt-dlp/yt-dlp) (`pip install yt-dlp`)
* A Spotify account

**No manual FFmpeg installation is required for most users.**
SpotDL bundles FFmpeg on Windows and usually works out of the box.

---

## Setup

1. **Clone or Download the Repo**
   Download this script and place it in its own folder.

2. **Install Dependencies**
   Open CMD or Terminal in that folder and run:

   ```sh
   pip install spotdl yt-dlp
   ```

3. **Configure Your Download Settings**
   Copy and edit the provided `config.json` template:

   ```json
   {
       "input_file": "spotdl_list.txt",
       "download_dir": "downloads",
       "thread_count": 3,
       "check_interval": 1,
       "spotdl_timeout": 120,
       "cookies_file": "cookies.txt"
   }
   ```

   * `input_file`: List of Spotify URLs (one per line)
   * `download_dir`: Output folder for downloads
   * `thread_count`: Number of concurrent downloaders

4. **Prepare Your Playlist File**

   * Create or update `spotdl_list.txt` with Spotify track or playlist URLs, one per line.

5. **\[Optional] Use Your Own Spotify API Credentials**
   SpotDL shares a default Client ID and secret among all users. For large playlists or heavy use,
   **you should set your own credentials to avoid hitting global rate limits**.

   * Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   * Create a new app and copy your Client ID and Client Secret
   * Add these to SpotDL’s config (`.spotdl/config.json`) or as environment variables:

     ```
     set SPOTIPY_CLIENT_ID=your_client_id
     set SPOTIPY_CLIENT_SECRET=your_client_secret
     ```

     (Use `export` instead of `set` on macOS/Linux.)

---

## Extracting Cookies Safely (YouTube/yt-dlp)

**You do *not* need any third-party browser extensions or shady “cookies.txt” exporters.**
Instead, you can have `yt-dlp` extract cookies from your (logged-in) Firefox profile automatically:

```sh
yt-dlp --cookies-from-browser firefox https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

* The above command downloads a YouTube video using your logged-in Firefox cookies.
* If you ever need to save these cookies to a file (for advanced SpotDL or yt-dlp use):

  ```sh
  yt-dlp --cookies-from-browser firefox --cookies cookies.txt https://www.youtube.com/watch?v=...
  ```
* **Never download or install any “cookies.txt” Chrome/Firefox extensions.
  These are often privacy risks or scams.**

---

## Usage

1. Place your playlist URLs in `spotdl_list.txt`.
2. Edit `config.json` as needed.
3. Run the script:

   ```sh
   python spotdl_batch_feeder.py
   ```

* Logs are saved to `track_log.txt` (all downloads) and `failed_tracks.txt` (any that failed).
* Downloaded files will be in your `download_dir`.

---

## Troubleshooting

* **SpotDL or yt-dlp not found?**
  Make sure both are installed (`pip install spotdl yt-dlp`) and available in your environment.

* **FFmpeg errors?**
  SpotDL bundles FFmpeg on Windows. If you see “ffmpeg not found” errors on Linux/macOS,
  install it using your system’s package manager (e.g., `sudo apt install ffmpeg`).

* **API rate limits?**
  Use your own Spotify API credentials (see above).

---

## Legal & Ethical Notes

- This script is provided for **educational and personal use only**.
- Downloading copyrighted material you do not own or have rights to may violate the terms of service of Spotify, YouTube, or other platforms, and could be illegal in your jurisdiction.
- **By using this script, you accept full responsibility for your usage.**
- The author provides this script for educational purposes only and disclaims all liability.