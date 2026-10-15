// =============================================================================
// Browser webcam preview
// =============================================================================
const videoElement = document.getElementById('webcam');

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 1280, height: 720 } 
        });
        videoElement.srcObject = stream;
    } catch (err) {
        console.error("Error accessing webcam: ", err);
        alert("Please allow camera access to use this app.");
    }
}

startCamera();

// =============================================================================
// Dashboard: exercise selection, stats polling, rep counting
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // ---- DOM references ----
    const valueDisplay = document.getElementById('current-value');
    const progressBar = document.getElementById('progress-bar');
    const labelDisplay = document.getElementById('current-label');
    const videoFeed = document.getElementById('video-feed');
    const maxValDisplay = document.getElementById('max-val');
    const repCountDisplay = document.getElementById('rep-count');

    // ---- Session state ----
    window.currentExercise = 'flexion';
    let maxFlexion = 0;
    let maxOpen = 0;
    let repCount = 0;
    let hasReachedThreshold = false;

    // ---- Controls (called from inline onclick handlers in index.html) ----
    window.changeExercise = function(type, btn) {
        document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        window.currentExercise = type;
        labelDisplay.innerText = type === 'flexion' ? 'Current Angle' : 'Opening Percentage';
        resetSummary(); // Clean slate for new exercise
        
        videoFeed.src = `/video_feed?exercise=${type}`;
    };

    window.resetSummary = function() {
        maxFlexion = 0; maxOpen = 0; repCount = 0;
        hasReachedThreshold = false;
        maxValDisplay.innerText = "0";
        repCountDisplay.innerText = "0";
        valueDisplay.innerText = "---";
        progressBar.style.width = "0%";
    };

    // ---- Polling: fetch /get_stats and update readout, progress bar, reps ----
    async function updateStats() {
        try {
            const response = await fetch('/get_stats');
            const data = await response.json();
            
            // 1. Race Condition Check
            if (data.type !== window.currentExercise) return;

            // 2. Data Persistence Check
            if (data.value > 0 || data.status.includes("%")) {
                const val = data.value;
                const displayVal = data.status.split(': ')[1] || data.status.split(' ')[1] || "0";
                valueDisplay.innerText = displayVal;

                // 3. Exercise Specific Logic
                if (window.currentExercise === 'flexion') {
                    // Update Summary
                    if (val > maxFlexion) maxFlexion = val;
                    maxValDisplay.innerText = maxFlexion;
                    
                    // Rep Counting (Thresholds remain the same)
                    if (val > 120) hasReachedThreshold = true;
                    if (hasReachedThreshold && val < 40) {
                        repCount++;
                        hasReachedThreshold = false;
                        repCountDisplay.innerText = repCount;
                    }

                    // NEW INVERTED LOGIC: 
                    // 180 deg = 0% progress (straight)
                    // 0 deg = 100% progress (fully bent)
                    let invertedPercent = ((180 - val) / 180) * 100;
                    
                    // Clamp between 0 and 100 to prevent bar overflowing
                    progressBar.style.width = `${Math.max(0, Math.min(100, invertedPercent))}%`;
                    
                    if (invertedPercent > 65) {
                        progressBar.style.background = "var(--accent)"; // Green (Success)
                    } else {
                        progressBar.style.background = "var(--primary)"; // Blue (Working)
                    }
                } else {
                    // Open/Close Summary
                    if (val > maxOpen) maxOpen = val;
                    maxValDisplay.innerText = maxOpen;

                    // Rep Counting (Thresholds: <65 closed, >85 open)
                    if (val < 65) hasReachedThreshold = true;
                    if (hasReachedThreshold && val > 85) {
                        repCount++;
                        hasReachedThreshold = false;
                        repCountDisplay.innerText = repCount;
                    }
                    progressBar.style.width = `${val}%`;
                }
            }
        } catch (err) { console.debug("Syncing..."); }
    }

    setInterval(updateStats, 100);
});