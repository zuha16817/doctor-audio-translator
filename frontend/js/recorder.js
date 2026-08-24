/**
 * AudioRecorder: Handles microphone audio capture, Web Audio API frequency visualization,
 * and audio blob preparation for upload.
 */
class AudioRecorder {
  constructor(canvasElement, onStateChange) {
    this.canvas = canvasElement;
    this.canvasCtx = canvasElement ? canvasElement.getContext('2d') : null;
    this.onStateChange = onStateChange || (() => {});
    
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioStream = null;
    this.audioContext = null;
    this.analyser = null;
    this.animationFrameId = null;
    this.startTime = null;
    this.timerInterval = null;
    this.recordedBlob = null;
    this.isRecording = false;
  }

  async start() {
    if (this.isRecording) return;
    
    try {
      this.audioChunks = [];
      this.recordedBlob = null;
      
      // Request microphone stream
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      });
      
      // Initialize Web Audio API for waveform
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      const source = this.audioContext.createMediaStreamSource(this.audioStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);
      
      // Setup MediaRecorder
      const mimeType = this._getSupportedMimeType();
      this.mediaRecorder = new MediaRecorder(this.audioStream, mimeType ? { mimeType } : {});
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };
      
      this.mediaRecorder.onstop = () => {
        const type = this.mediaRecorder.mimeType || 'audio/webm';
        this.recordedBlob = new Blob(this.audioChunks, { type });
        this.onStateChange({ status: 'stopped', blob: this.recordedBlob });
      };
      
      this.mediaRecorder.start(250); // collect 250ms chunks
      this.isRecording = true;
      this.startTime = Date.now();
      
      // Start visualizer and timer
      this._drawVisualizer();
      this._startTimer();
      
      this.onStateChange({ status: 'recording' });
      
    } catch (err) {
      console.error('Microphone access error:', err);
      let errorMsg = 'Microphone permission was denied or not found.';
      if (err.name === 'NotAllowedError') {
        errorMsg = 'Microphone permission was denied. Please allow microphone access in browser settings.';
      } else if (err.name === 'NotFoundError') {
        errorMsg = 'No microphone device found on your system.';
      }
      this.onStateChange({ status: 'error', error: errorMsg });
      throw new Error(errorMsg);
    }
  }

  stop() {
    if (!this.isRecording) return;
    
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
    
    this._stopTimer();
    this.isRecording = false;
    this._clearVisualizer();
  }

  _getSupportedMimeType() {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/wav'
    ];
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return '';
  }

  _startTimer() {
    this._stopTimer();
    this.timerInterval = setInterval(() => {
      if (!this.startTime) return;
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const secs = String(elapsed % 60).padStart(2, '0');
      this.onStateChange({ status: 'tick', time: `${mins}:${secs}`, elapsed });
    }, 500);
  }

  _stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  _drawVisualizer() {
    if (!this.canvas || !this.canvasCtx || !this.analyser) return;
    
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      if (!this.isRecording) return;
      this.animationFrameId = requestAnimationFrame(draw);
      
      this.analyser.getByteFrequencyData(dataArray);
      
      const width = this.canvas.width;
      const height = this.canvas.height;
      
      this.canvasCtx.fillStyle = 'rgba(10, 15, 29, 0.4)';
      this.canvasCtx.fillRect(0, 0, width, height);
      
      const barWidth = (width / bufferLength) * 2.2;
      let x = 0;
      
      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * height;
        
        // Gradient from cyan to medical emerald
        const grad = this.canvasCtx.createLinearGradient(0, height, 0, 0);
        grad.addColorStop(0, '#0284c7');
        grad.addColorStop(0.5, '#06b6d4');
        grad.addColorStop(1, '#34d399');
        
        this.canvasCtx.fillStyle = grad;
        this.canvasCtx.fillRect(x, height - barHeight, barWidth - 1, barHeight);
        
        x += barWidth;
      }
    };
    
    draw();
  }

  _clearVisualizer() {
    if (!this.canvas || !this.canvasCtx) return;
    this.canvasCtx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }
}

window.AudioRecorder = AudioRecorder;
