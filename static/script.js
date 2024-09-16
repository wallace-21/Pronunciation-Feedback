let mediaRecorder;
let audioChunks = [];
let recordingCounter = 1;
let currentRecordingBlob = null; // Store the most recent recording

// Start recording
async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = []; // Reset audio chunks for each recording session

    document.getElementById('recordIndicator').style.display = 'inline'; // Show recording indicator

    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data); // Collect audio data
    };

    mediaRecorder.start();
}

// Stop recording
function stopRecording() {
    mediaRecorder.stop();
    document.getElementById('recordIndicator').style.display = 'none'; // Hide indicator

    mediaRecorder.onstop = () => {
        currentRecordingBlob = new Blob(audioChunks, { type: 'audio/mp3' });
        const audioURL = URL.createObjectURL(currentRecordingBlob);

        // Create audio element for playback
        const audioElement = document.createElement('audio');
        audioElement.controls = true;
        audioElement.src = audioURL;

        const audioList = document.getElementById('audioList');
        audioList.appendChild(document.createElement('br'));
        audioList.appendChild(audioElement);

        recordingCounter++;
    };
}

// Activate translation by sending the audio to the server
function activateTranslation() {
    if (!currentRecordingBlob) {
        alert("No recording available for translation!");
        return;
    }

    const formData = new FormData();
    formData.append('audio', currentRecordingBlob, `recording_${recordingCounter - 1}.mp3`);

    fetch('/translate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log("Transcription result:", data.transcription);

        // Display transcription in the feedback section
        const translationDisplay = document.getElementById('translationDisplay');
        translationDisplay.textContent = data.transcription;

        // Call the getFeedback function to display feedback based on the transcription
        getFeedback(data.transcription);

        // Show feedback section
        const feedbackSection = document.getElementById('feedbackSection');
        feedbackSection.classList.remove('hidden');
        feedbackSection.classList.add('show');
    })
    .catch(error => {
        console.error("Error during translation:", error);
    });
}

function getFeedback(transcription) {
    const expectedText = "This is the expected correct sentence."; // Example expected text

    fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcription, expected_text: expectedText })
    })
    .then(response => response.json())
    .then(data => {
        const feedback = data.feedback;
        let feedbackContainer = document.getElementById('feedbackContainer');
        feedbackContainer.innerHTML = '';  // Clear previous feedback
        feedback.forEach(msg => {
            let p = document.createElement('p');
            p.innerText = msg;
            feedbackContainer.appendChild(p);
        });
    })
    .catch(error => {
        console.error("Error getting feedback:", error);
    });
}

