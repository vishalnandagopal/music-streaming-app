// To be used in player.html

// When user clicks on the play button, the audio should start playing
// When user clicks on the pause button, the audio should pause

function playSong(music_id) {
    document.getElementById("audio-player-section").style.display = "flex";
    d = document.getElementById("audio-player");
    d.src = "/static/audio/" + music_id;
    d.play();

    // When the audio ends, the audio player should disappear
    document
        .getElementById("audio-player")
        .addEventListener("ended", function () {
            document.getElementById("audio-player-section").style.display =
                "none";
        });

    // Update the details of the song in the audio player
    updateAudioDetails(music_id);
}
function updateAudioDetails(music_id) {
    // Fetch song details from the db and update the audio player by sending a post request to /fetch_song_details/ with the music_id as a parameter.

    fetch("/fetch_song_details", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ music_id: music_id }),
    })
        .then((response) => response.json())
        .then((data) => {
            document.getElementById("current-song-name").innerText =
                data["name"];
            document.getElementById("current-song-artist").innerText =
                data["artist"];
            document.getElementById("current-song-album").innerText =
                data["album"];
            document.getElementById("current-song-lyrics").innerText =
                data["lyrics"];
        });
}
function showLyrics() {
    if (
        document.getElementById("current-song-lyrics").style.display == "block"
    ) {
        document.getElementById("current-song-lyrics").style.display = "none";
        return;
    } else {
        document.getElementById("current-song-lyrics").style.display = "block";
    }
}

async function autoPlay(music_id) {
    await new Promise((r) => setTimeout(r, 1000));
    playSong(music_id);
}
