// To be used in player.html

// When user clicks on the play button, the audio should start playing
// When user clicks on the pause button, the audio should pause

function playAudio() {
    document.getElementById("audio").play();
}

function loadAudio(music_id) {
    document.getElementById("audio-player-section").style.display = "flex";
    d = document.getElementById("audio-player");
    d.src = "/static/audio/" + music_id + ".mp4";
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
            document.getElementById("current-song-artist").innerHTML =
                data["artist"];
            document.getElementById("current-song-album").innerHTML =
                data["album"];
        });
}
