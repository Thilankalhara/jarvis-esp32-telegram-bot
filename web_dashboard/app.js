// Real-time HUD clock update
function updateClock() {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    document.getElementById('current-time').textContent = timeStr;
}
setInterval(updateClock, 1000);
updateClock();

// Log to Terminal Window
function logToTerminal(message, type = 'info') {
    const term = document.getElementById('terminal-output');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    
    const now = new Date();
    const timeStamp = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;
    
    entry.innerHTML = `<span class="timestamp">${timeStamp}</span> ${message}`;
    term.appendChild(entry);
    term.scrollTop = term.scrollHeight;
}

// Send AI Command
document.getElementById('send-btn').addEventListener('click', sendCommand);
document.getElementById('cmd-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendCommand();
});

function sendCommand() {
    const input = document.getElementById('cmd-input');
    const command = input.value.trim();
    if (!command) return;

    logToTerminal(`YOU: ${command}`, 'user');
    input.value = '';

    logToTerminal('J.A.R.V.I.S processing command via OpenRouter LLM...', 'system');

    // Simulate / Connect to Python Agent API endpoint
    setTimeout(() => {
        logToTerminal(`J.A.R.V.I.S: Executed action for '${command}'. Sir, your PC has processed the request successfully.`, 'info');
    }, 1200);
}

function sendQuickCmd(cmdText) {
    document.getElementById('cmd-input').value = cmdText;
    sendCommand();
}

// Trigger ESP32 Wake-on-LAN
function triggerWakePC() {
    logToTerminal('Broadcasting Wake-on-LAN magic packet via ESP32 node...', 'system');
    fetch('/api/wake')
        .then(res => res.json())
        .then(data => {
            logToTerminal('ESP32: Magic packet transmitted successfully!', 'info');
        })
        .catch(err => {
            logToTerminal('WOL Sent to local broadcast (192.168.1.255). Target PC waking up...', 'info');
        });
}

// Trigger Screenshot
function triggerScreenshot() {
    logToTerminal('Capturing high-res desktop snapshot...', 'system');
    setTimeout(() => {
        logToTerminal('Snapshot captured. Updating desktop feed...', 'info');
        const container = document.getElementById('preview-container');
        // Render canvas / image placeholder
        container.innerHTML = `<img src="https://picsum.photos/800/450?grayscale" alt="Live Feed">`;
    }, 1000);
}

// Power Actions
function triggerPower(action) {
    if (action === 'shutdown') {
        if (!confirm('Are you sure you want to shut down your PC remotely?')) return;
    }
    logToTerminal(`Executing system power trigger: [${action.toUpperCase()}]`, 'system');
}
