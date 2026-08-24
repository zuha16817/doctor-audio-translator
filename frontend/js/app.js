document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const tabUpload = document.getElementById('tabUpload');
  const tabRecord = document.getElementById('tabRecord');
  const uploadSection = document.getElementById('uploadSection');
  const recordSection = document.getElementById('recordSection');
  
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const selectedFileCard = document.getElementById('selectedFileCard');
  const selectedFileName = document.getElementById('selectedFileName');
  const selectedFileSize = document.getElementById('selectedFileSize');
  const removeFileBtn = document.getElementById('removeFileBtn');
  
  const recordBtn = document.getElementById('recordBtn');
  const recordTimer = document.getElementById('recordTimer');
  const recordStatusText = document.getElementById('recordStatusText');
  const waveformCanvas = document.getElementById('waveformCanvas');
  const audioPreview = document.getElementById('audioPreview');
  const previewContainer = document.getElementById('previewContainer');
  
  const sourceLangSelect = document.getElementById('sourceLanguage');
  const targetLangSelect = document.getElementById('targetLanguage');
  const processBtn = document.getElementById('processBtn');
  const processBtnText = document.getElementById('processBtnText');
  const processSpinner = document.getElementById('processSpinner');
  const processingStatus = document.getElementById('processingStatus');
  
  // Transcription Elements
  const transLabel = document.getElementById('transcriptionLabel');
  const transBadge = document.getElementById('transcriptionBadge');
  const confidenceBadge = document.getElementById('confidenceBadge');
  const transTextarea = document.getElementById('transcriptionText');
  const transCharCount = document.getElementById('transCharCount');
  const copyTransBtn = document.getElementById('copyTransBtn');
  const downloadTransBtn = document.getElementById('downloadTransBtn');
  
  // Summary Elements (Phase 2)
  const summaryCard = document.getElementById('summaryCard');
  const summaryText = document.getElementById('summaryText');
  const copySummaryBtn = document.getElementById('copySummaryBtn');

  // Translation Elements
  const translLabel = document.getElementById('translationLabel');
  const translBadge = document.getElementById('translationBadge');
  const translTextarea = document.getElementById('translationText');
  const translCharCount = document.getElementById('translCharCount');
  const copyTranslBtn = document.getElementById('copyTranslBtn');
  const downloadTranslBtn = document.getElementById('downloadTranslBtn');
  const speakTranslBtn = document.getElementById('speakTranslBtn');
  
  // Samples & Toasts
  const sampleArabicBtn = document.getElementById('sampleArabicBtn');
  const sampleUrduBtn = document.getElementById('sampleUrduBtn');
  const toastContainer = document.getElementById('toastContainer');

  // History Drawer Elements (Phase 2)
  const openHistoryBtn = document.getElementById('openHistoryBtn');
  const closeHistoryBtn = document.getElementById('closeHistoryBtn');
  const historyDrawerBackdrop = document.getElementById('historyDrawerBackdrop');
  const historyDrawer = document.getElementById('historyDrawer');
  const historyList = document.getElementById('historyList');
  const historyCountBadge = document.getElementById('historyCountBadge');
  const emptyHistoryMsg = document.getElementById('emptyHistoryMsg');
  const exportHistoryBtn = document.getElementById('exportHistoryBtn');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');

  // State
  let currentFile = null;
  let recordedBlob = null;
  let activeTab = 'upload';
  let recorder = null;
  let consultationHistory = JSON.parse(localStorage.getItem('doc_consult_history') || '[]');

  // Initialize Canvas
  if (waveformCanvas) {
    waveformCanvas.width = waveformCanvas.offsetWidth || 380;
    waveformCanvas.height = waveformCanvas.offsetHeight || 64;
  }

  // Initialize Audio Recorder
  recorder = new AudioRecorder(waveformCanvas, (state) => {
    if (state.status === 'recording') {
      recordBtn.classList.add('recording');
      recordStatusText.textContent = 'Recording in progress... Click to stop';
      recordBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
    } else if (state.status === 'tick') {
      recordTimer.textContent = state.time;
    } else if (state.status === 'stopped') {
      recordBtn.classList.remove('recording');
      recordStatusText.textContent = 'Recording completed. Ready to transcribe!';
      recordBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>';
      recordedBlob = state.blob;
      setAudioPreview(state.blob, 'mic_recording.webm');
      showToast('Audio recorded successfully!', 'success');
    } else if (state.status === 'error') {
      recordBtn.classList.remove('recording');
      recordStatusText.textContent = 'Microphone ready';
      showToast(state.error, 'error');
    }
  });

  // Tab switching
  tabUpload.addEventListener('click', () => {
    activeTab = 'upload';
    tabUpload.classList.add('active');
    tabRecord.classList.remove('active');
    uploadSection.style.display = 'block';
    recordSection.style.display = 'none';
  });

  tabRecord.addEventListener('click', () => {
    activeTab = 'record';
    tabRecord.classList.add('active');
    tabUpload.classList.remove('active');
    uploadSection.style.display = 'none';
    recordSection.style.display = 'block';
  });

  // Dropzone Events
  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    const validExtensions = ['.mp3', '.wav', '.m4a', '.webm', '.ogg', '.opus'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(ext)) {
      showToast(`Unsupported format "${ext}". Please use .mp3, .wav, .m4a, or .webm.`, 'error');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      showToast(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max limit is 50 MB.`, 'error');
      return;
    }

    currentFile = file;
    recordedBlob = null;
    selectedFileName.textContent = file.name;
    selectedFileSize.textContent = formatBytes(file.size);
    selectedFileCard.style.display = 'flex';
    dropzone.style.display = 'none';
    
    setAudioPreview(file, file.name);
    showToast(`Loaded "${file.name}"`, 'success');
  }

  removeFileBtn.addEventListener('click', () => {
    currentFile = null;
    fileInput.value = '';
    selectedFileCard.style.display = 'none';
    dropzone.style.display = 'block';
    previewContainer.style.display = 'none';
    audioPreview.src = '';
  });

  // Record Button Click
  recordBtn.addEventListener('click', async () => {
    if (recorder.isRecording) {
      recorder.stop();
    } else {
      currentFile = null;
      selectedFileCard.style.display = 'none';
      dropzone.style.display = 'block';
      await recorder.start();
    }
  });

  function setAudioPreview(blobOrFile, name) {
    const url = URL.createObjectURL(blobOrFile);
    audioPreview.src = url;
    previewContainer.style.display = 'block';
  }

  // Sample Audio Loaders
  sampleArabicBtn.addEventListener('click', () => loadSampleAudio('arabic_medical_sample.wav', 'ar'));
  sampleUrduBtn.addEventListener('click', () => loadSampleAudio('urdu_medical_sample.wav', 'ur'));

  async function loadSampleAudio(filename, langCode) {
    try {
      showToast(`Loading ${langCode === 'ar' ? 'Arabic' : 'Urdu'} medical sample...`, 'success');
      const response = await fetch(`/static/samples/${filename}`);
      if (!response.ok) {
        throw new Error('Sample audio file not found on server.');
      }
      const blob = await response.blob();
      const file = new File([blob], filename, { type: 'audio/wav' });
      
      tabUpload.click();
      handleFileSelected(file);
      sourceLangSelect.value = langCode;
    } catch (err) {
      showToast('Could not load sample audio: ' + err.message, 'error');
    }
  }

  // Transcribe & Translate Main Workflow
  processBtn.addEventListener('click', async () => {
    let audioToSubmit = null;
    let filename = 'audio.wav';

    if (activeTab === 'upload') {
      if (!currentFile) {
        showToast('Please upload an audio file or switch to microphone recording.', 'error');
        return;
      }
      audioToSubmit = currentFile;
      filename = currentFile.name;
    } else {
      if (!recordedBlob) {
        showToast('Please record audio using the microphone before submitting.', 'error');
        return;
      }
      audioToSubmit = recordedBlob;
      filename = 'microphone_recording.webm';
    }

    const sourceLang = sourceLangSelect.value;
    const targetLang = targetLangSelect.value;

    const formData = new FormData();
    formData.append('audioFile', audioToSubmit, filename);
    formData.append('sourceLanguage', sourceLang);
    formData.append('targetLanguage', targetLang);

    // UI Loading State (Section 2.2 G)
    setProcessingState(true, 'Uploading audio file...');

    try {
      setTimeout(() => { if (processBtn.disabled) setStatusLabel('Transcribing speech (Arabic/Urdu)...'); }, 600);
      setTimeout(() => { if (processBtn.disabled) setStatusLabel('Translating & generating clinical summary...'); }, 1800);

      const response = await fetch('/api/audio/transcribe-translate', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        const errorMsg = result.message || 'Failed to process audio.';
        showToast(errorMsg, 'error');
        setStatusLabel(`Failed: ${errorMsg}`);
        return;
      }

      // Populate Results
      renderResults(result);
      addToHistory(result, filename);
      showToast(`Completed in ${result.durationSeconds}s!`, 'success');
      setStatusLabel(`Completed in ${result.durationSeconds}s`);

    } catch (err) {
      console.error('API Error:', err);
      showToast('Network error connecting to backend service.', 'error');
      setStatusLabel('Processing failed');
    } finally {
      setProcessingState(false);
    }
  });

  function renderResults(result) {
    const src = (result.sourceLanguage || 'ar').toLowerCase();
    const tgt = (result.targetLanguage || 'en').toLowerCase();

    // 1. Transcription text & dynamic styling (Section 2.2 E & 3)
    transTextarea.value = result.transcription || '';
    transCharCount.textContent = `${(result.transcription || '').length} characters`;

    if (src === 'ur') {
      transLabel.textContent = 'Urdu Transcription';
      transBadge.textContent = 'Urdu (اردو)';
      transTextarea.className = 'result-textarea rtl-urdu';
    } else if (src === 'ar') {
      transLabel.textContent = 'Arabic Transcription';
      transBadge.textContent = 'Arabic (العربية)';
      transTextarea.className = 'result-textarea rtl-arabic';
    } else {
      transLabel.textContent = `${result.detectedLanguageLabel || 'Source'} Transcription`;
      transBadge.textContent = result.detectedLanguageLabel || src.toUpperCase();
      transTextarea.className = 'result-textarea rtl-arabic';
    }

    // Confidence Badge
    if (result.confidenceScore !== undefined && result.confidenceScore !== null) {
      confidenceBadge.style.display = 'inline-block';
      const score = result.confidenceScore;
      confidenceBadge.textContent = `${score}% Confidence`;
      if (score < 80) {
        confidenceBadge.className = 'px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30';
      } else {
        confidenceBadge.className = 'px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30';
      }
    } else {
      confidenceBadge.style.display = 'none';
    }

    // AI Clinical Summary (Phase 2 Enhancement)
    if (result.summary) {
      summaryText.textContent = result.summary;
      summaryCard.style.display = 'flex';
    } else {
      summaryCard.style.display = 'none';
    }

    // 2. Translation text & dynamic styling (Section 2.2 F & 3)
    translTextarea.value = result.translation || '';
    translCharCount.textContent = `${(result.translation || '').length} characters`;
    
    translLabel.textContent = `Translation (${getTargetLangName(tgt)})`;
    translBadge.textContent = getTargetLangName(tgt);

    if (tgt === 'ar') {
      translTextarea.className = 'result-textarea rtl-arabic';
    } else if (tgt === 'ur') {
      translTextarea.className = 'result-textarea rtl-urdu';
    } else {
      translTextarea.className = 'result-textarea ltr-english';
    }
  }

  function getTargetLangName(code) {
    const map = {
      'en': 'English',
      'ar': 'Arabic (العربية)',
      'ur': 'Urdu (اردو)',
      'fr': 'French',
      'es': 'Spanish',
      'de': 'German'
    };
    return map[code] || code.toUpperCase();
  }

  function setProcessingState(isProcessing, statusMsg = '') {
    processBtn.disabled = isProcessing;
    if (isProcessing) {
      processSpinner.style.display = 'inline-block';
      processBtnText.textContent = 'Processing...';
      processingStatus.textContent = statusMsg;
      processingStatus.style.display = 'block';
    } else {
      processSpinner.style.display = 'none';
      processBtnText.textContent = 'Transcribe & Translate';
    }
  }

  function setStatusLabel(msg) {
    if (processingStatus) {
      processingStatus.textContent = msg;
    }
  }

  // Copy Buttons
  copyTransBtn.addEventListener('click', () => {
    if (!transTextarea.value) return;
    navigator.clipboard.writeText(transTextarea.value);
    showToast('Original transcription copied to clipboard!', 'success');
  });

  copyTranslBtn.addEventListener('click', () => {
    if (!translTextarea.value) return;
    navigator.clipboard.writeText(translTextarea.value);
    showToast('Translation copied to clipboard!', 'success');
  });

  copySummaryBtn.addEventListener('click', () => {
    if (!summaryText.textContent) return;
    navigator.clipboard.writeText(summaryText.textContent);
    showToast('Clinical summary copied to clipboard!', 'success');
  });

  // Download Transcription as .txt (Phase 2 Enhancement)
  downloadTransBtn.addEventListener('click', () => {
    const text = transTextarea.value;
    if (!text) {
      showToast('No original transcript to download.', 'error');
      return;
    }
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medical_transcription_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Downloaded original transcript (.txt)', 'success');
  });

  // Download Translation as .txt (Phase 2 Enhancement)
  downloadTranslBtn.addEventListener('click', () => {
    const text = translTextarea.value;
    if (!text) {
      showToast('No translated text to download.', 'error');
      return;
    }
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medical_translation_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Downloaded translation file (.txt)', 'success');
  });

  // Text-to-Speech Web Synthesis (Phase 2 Enhancement)
  speakTranslBtn.addEventListener('click', () => {
    const text = translTextarea.value;
    if (!text) return;
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = targetLangSelect.value === 'en' ? 'en-US' : targetLangSelect.value;
      window.speechSynthesis.speak(utterance);
      showToast('Speaking translation...', 'success');
    } else {
      showToast('Browser does not support text-to-speech synthesis.', 'error');
    }
  });

  // History Drawer Logic (Phase 2 Enhancement)
  function renderHistoryDrawer() {
    historyCountBadge.textContent = consultationHistory.length;
    if (consultationHistory.length === 0) {
      emptyHistoryMsg.style.display = 'block';
      historyList.innerHTML = '';
      historyList.appendChild(emptyHistoryMsg);
      return;
    }

    emptyHistoryMsg.style.display = 'none';
    historyList.innerHTML = '';

    consultationHistory.forEach((item, index) => {
      const card = document.createElement('div');
      card.className = 'p-3.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition cursor-pointer flex flex-col gap-2';
      
      const timeStr = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-bold text-sky-400 uppercase">${item.sourceLanguage} → ${item.targetLanguage}</span>
            <span class="text-[10px] text-slate-500">• ${timeStr}</span>
          </div>
          <span class="text-[11px] font-semibold text-emerald-400">${item.confidenceScore || 98}%</span>
        </div>
        <p class="text-xs text-slate-200 line-clamp-2 italic">${item.translation || item.transcription}</p>
        <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400">
          <span>${item.durationSeconds}s duration</span>
          <span class="text-sky-400 font-semibold hover:underline">Restore →</span>
        </div>
      `;

      card.addEventListener('click', () => {
        renderResults(item);
        sourceLangSelect.value = item.sourceLanguage;
        targetLangSelect.value = item.targetLanguage;
        closeHistory();
        showToast('Restored past consultation into panels!', 'success');
      });

      historyList.appendChild(card);
    });
  }

  function addToHistory(result, filename) {
    const item = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      filename: filename,
      sourceLanguage: result.sourceLanguage,
      targetLanguage: result.targetLanguage,
      transcription: result.transcription,
      translation: result.translation,
      summary: result.summary,
      confidenceScore: result.confidenceScore,
      durationSeconds: result.durationSeconds,
      detectedLanguageLabel: result.detectedLanguageLabel
    };

    consultationHistory.unshift(item);
    if (consultationHistory.length > 50) consultationHistory.pop();
    localStorage.setItem('doc_consult_history', JSON.stringify(consultationHistory));
    renderHistoryDrawer();
  }

  function openHistory() {
    historyDrawerBackdrop.classList.remove('opacity-0', 'pointer-events-none');
    historyDrawerBackdrop.classList.add('opacity-100');
    historyDrawer.classList.remove('translate-x-full');
    renderHistoryDrawer();
  }

  function closeHistory() {
    historyDrawerBackdrop.classList.remove('opacity-100');
    historyDrawerBackdrop.classList.add('opacity-0', 'pointer-events-none');
    historyDrawer.classList.add('translate-x-full');
  }

  openHistoryBtn.addEventListener('click', openHistory);
  closeHistoryBtn.addEventListener('click', closeHistory);
  historyDrawerBackdrop.addEventListener('click', (e) => {
    if (e.target === historyDrawerBackdrop) closeHistory();
  });

  clearHistoryBtn.addEventListener('click', () => {
    if (confirm('Clear all consultation history?')) {
      consultationHistory = [];
      localStorage.removeItem('doc_consult_history');
      renderHistoryDrawer();
      showToast('Cleared consultation history.', 'success');
    }
  });

  exportHistoryBtn.addEventListener('click', () => {
    if (consultationHistory.length === 0) {
      showToast('No history available to export.', 'error');
      return;
    }
    const blob = new Blob([JSON.stringify(consultationHistory, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `consultations_history_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Exported consultation history (.json)', 'success');
  });

  // Initial history render on load
  renderHistoryDrawer();

  // Helpers
  function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' 
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

    toast.innerHTML = `${icon}<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
});
