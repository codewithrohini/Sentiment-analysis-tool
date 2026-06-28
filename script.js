const textInput = document.getElementById('textInput');
const charCount = document.getElementById('charCount');
const analyzeBtn = document.getElementById('analyzeBtn');
const analyzeBtnText = document.getElementById('analyzeBtnText');
const results = document.getElementById('results');
const errorMsg = document.getElementById('errorMsg');

const SAMPLES = [
  "I love the new update but the loading screen still drives me crazy.",
  "Honestly not sure this was worth the price — support took three days to reply and the bug is still there.",
  "This is hands down the best onboarding experience I've had. The team was responsive, the docs were clear, and everything just worked."
];

textInput.addEventListener('input', () => {
  charCount.textContent = textInput.value.length;
});

document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const idx = parseInt(chip.dataset.sample, 10);
    textInput.value = SAMPLES[idx];
    charCount.textContent = textInput.value.length;
    runAnalysis();
  });
});

document.getElementById('scrollToAnalyze').addEventListener('click', () => {
  document.getElementById('analyze').scrollIntoView({ behavior: 'smooth', block: 'center' });
  textInput.focus();
});

analyzeBtn.addEventListener('click', runAnalysis);
textInput.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') runAnalysis();
});

async function runAnalysis() {
  const text = textInput.value.trim();
  errorMsg.hidden = true;

  if (!text) {
    showError('Please paste some text to analyze.');
    return;
  }

  setLoading(true);
  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || 'Something went wrong. Try again.');
      return;
    }
    renderResults(data);
  } catch (err) {
    showError('Could not reach the server. Is the Flask app running?');
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtnText.textContent = isLoading ? 'Analyzing…' : 'Analyze sentiment';
}

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.hidden = false;
  results.hidden = true;
}

function renderResults(data) {
  results.hidden = false;

  document.getElementById('resultVerdict').textContent = data.verdict;

  // Confidence ring
  const circumference = 264;
  const offset = circumference - (circumference * data.confidence) / 100;
  document.getElementById('ringFg').style.strokeDashoffset = offset;
  document.getElementById('confidenceValue').textContent = data.confidence + '%';

  // Polarity bars
  document.getElementById('barPos').style.width = data.polarity.positive + '%';
  document.getElementById('barNeu').style.width = data.polarity.neutral + '%';
  document.getElementById('barNeg').style.width = data.polarity.negative + '%';
  document.getElementById('valPos').textContent = data.polarity.positive + '%';
  document.getElementById('valNeu').textContent = data.polarity.neutral + '%';
  document.getElementById('valNeg').textContent = data.polarity.negative + '%';

  // Emotions
  const emotionTags = document.getElementById('emotionTags');
  emotionTags.innerHTML = '';
  data.emotions.forEach(e => {
    const pill = document.createElement('span');
    pill.className = 'tag-pill';
    pill.textContent = `${e.emotion} ${Math.round(e.strength * 100)}%`;
    emotionTags.appendChild(pill);
  });

  // Signal words
  const signalWords = document.getElementById('signalWords');
  signalWords.innerHTML = '';
  if (!data.signals.length) {
    signalWords.textContent = 'No strongly polarized words detected.';
  } else {
    data.signals.forEach(s => {
      const span = document.createElement('span');
      span.className = `signal-word signal-word--${s.polarity}`;
      span.textContent = s.word;
      signalWords.appendChild(span);
      signalWords.appendChild(document.createTextNode(' '));
    });
  }

  results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}