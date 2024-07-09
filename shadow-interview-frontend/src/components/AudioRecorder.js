import React, { useState } from 'react';
import axios from 'axios';

const AudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState('');

  const startRecording = () => {
    axios.post('/api/start_recording')
      .then(() => setIsRecording(true))
      .catch(error => console.error('Error starting recording:', error));
  };

  const stopRecording = () => {
    axios.post('/api/stop_recording')
      .then(response => {
        setIsRecording(false);
        setTranscription(response.data.transcription);
      })
      .catch(error => console.error('Error stopping recording:', error));
  };

  return (
    <div className="audio-recorder">
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>
      {transcription && (
        <div className="transcription">
          <h3>Transcription</h3>
          <p>{transcription}</p>
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;
