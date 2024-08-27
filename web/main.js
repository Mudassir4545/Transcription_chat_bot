import { streamGemini } from './gemini-api.js';

let form = document.querySelector('form');
let output = document.querySelector('.output');
let audioFileInput = document.querySelector('input[name="audio_file"]');

form.onsubmit = async (ev) => {
  ev.preventDefault();
  output.textContent = 'Processing...';
  
  try {
    // Log form data before sending
    console.log('Preparing to send audio file:', audioFileInput.files[0]);

    // Create a FormData object to hold the audio file
    let formData = new FormData();
    formData.append('audio_file', audioFileInput.files[0]);

    // Send the audio file to the Flask backend for transcription and option selection
    let response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    // Log the response status
    console.log('Response status:', response.status);

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    let result = await response.json();
    let selectedOption = result.selected_option;

    // Log the response data
    console.log('Received result:', result);

    // Display the transcription and the selected option
    output.innerHTML = `
      <p>Transcription: ${result.transcription}</p>
      <p>Correct Option: ${selectedOption}</p>
    `;

  } catch (e) {
    console.error('Error occurred:', e);
    output.innerHTML = '<hr>' + e;
  }
};
