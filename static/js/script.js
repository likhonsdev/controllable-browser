/**
 * BrowserAGENT Frontend Script
 * Handles the interaction with the Flask backend and updates the UI
 */

// DOM Elements
const commandInput = document.getElementById('commandInput');
const sendCommandBtn = document.getElementById('sendCommandBtn');
const clearLogBtn = document.getElementById('clearLogBtn');
const logContainer = document.getElementById('logContainer');
const resultContainer = document.getElementById('resultContainer');
const browserUrl = document.getElementById('browserUrl');
const browserContent = document.getElementById('browserContent');
const loadingOverlay = document.getElementById('loadingOverlay');
const statusIndicator = document.getElementById('status-indicator');
const screenshotOverlay = document.getElementById('screenshotOverlay');
const screenshotImg = document.getElementById('screenshotImg');
const closeScreenshotBtn = document.getElementById('closeScreenshotBtn');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    sendCommandBtn.addEventListener('click', handleSendCommand);
    commandInput.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendCommand();
        }
    });
    
    clearLogBtn.addEventListener('click', () => {
        logContainer.innerHTML = '<p class="text-slate-500">Log cleared. Enter a command to begin.</p>';
    });
    
    closeScreenshotBtn.addEventListener('click', () => {
        screenshotOverlay.classList.add('hidden');
    });
    
    // Set focus to command input
    commandInput.focus();
});

/**
 * Handles sending a command to the backend
 */
async function handleSendCommand() {
    const command = commandInput.value.trim();
    
    if (!command) {
        showToast('Please enter a command');
        return;
    }
    
    // Show loading state
    setLoadingState(true);
    
    // Clear previous results
    resultContainer.innerHTML = '<p class="text-slate-500">Processing your command...</p>';
    browserContent.innerHTML = '<p class="text-slate-500">Waiting for results...</p>';
    browserUrl.value = '';
    
    // Add the command to the log
    addLogEntry('info', `Command: "${command}"`, 'command');
    
    try {
        // Send command to backend
        const response = await fetch('/api/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Process the response
        processResponse(data);
        
        // Clear the command input
        commandInput.value = '';
    } catch (error) {
        console.error('Error:', error);
        addLogEntry('error', `Error: ${error.message}`);
        resultContainer.innerHTML = `<p class="text-red-400">Error: ${error.message}</p>`;
        setStatusText('Error');
    } finally {
        setLoadingState(false);
    }
}

/**
 * Processes the response from the backend
 */
function processResponse(data) {
    // Display logs
    if (data.logs && data.logs.length > 0) {
        // Clear the log first if it only has the initial message
        const initialLogText = logContainer.innerText.trim();
        if (initialLogText === 'Agent is ready. Enter a command to begin.' || 
            initialLogText === 'Log cleared. Enter a command to begin.') {
            logContainer.innerHTML = '';
        }
        
        // Add all log entries
        data.logs.forEach(log => {
            addLogEntry(log.type, log.message, log.url);
        });
    }
    
    // Display result
    if (data.final_result) {
        const formattedResult = formatResultContent(data.final_result);
        resultContainer.innerHTML = formattedResult;
    } else {
        resultContainer.innerHTML = '<p class="text-red-400">No result received from the agent.</p>';
    }
    
    // Update browser URL
    if (data.processed_url) {
        browserUrl.value = data.processed_url;
        
        // Update browser content with a link to the URL
        browserContent.innerHTML = `
            <div class="mb-3">
                <p class="text-sm text-slate-300">Processed URL: 
                    <a href="${data.processed_url}" target="_blank" class="text-primary-400 hover:underline">${data.processed_url}</a>
                </p>
            </div>
            <div class="prose prose-invert prose-sm max-w-none">
                ${formatResultContent(data.final_result)}
            </div>
        `;
    } else {
        browserContent.innerHTML = '<p class="text-slate-400">No URL was processed for this command.</p>';
        if (data.final_result) {
            browserContent.innerHTML += `
                <div class="mt-3 prose prose-invert prose-sm max-w-none">
                    ${formatResultContent(data.final_result)}
                </div>
            `;
        }
    }
    
    // Display screenshot if available
    if (data.screenshot) {
        showScreenshot(`/static/${data.screenshot}`);
    }
    
    // Update status
    setStatusText('Ready');
}

/**
 * Adds a log entry to the log container
 */
function addLogEntry(type, message, url) {
    const logEntry = document.createElement('div');
    logEntry.className = 'py-1 px-2 border-l-2 my-1 bg-slate-800 rounded fade-in text-xs';
    
    // Set the log type style
    switch (type) {
        case 'error':
            logEntry.classList.add('log-error');
            logEntry.classList.add('text-red-300');
            break;
        case 'browser':
        case 'web':
            logEntry.classList.add('log-browser');
            logEntry.classList.add('text-blue-300');
            break;
        case 'ai':
            logEntry.classList.add('log-ai');
            logEntry.classList.add('text-purple-300');
            break;
        case 'info':
        default:
            logEntry.classList.add('log-info');
            logEntry.classList.add('text-slate-300');
            break;
    }
    
    // Create the content
    let content = message;
    
    // If URL is provided, add a link
    if (url && type === 'browser') {
        content += ` <a href="${url}" target="_blank" class="text-primary-400 hover:underline text-xs">(${url})</a>`;
    }
    
    logEntry.innerHTML = content;
    logContainer.appendChild(logEntry);
    
    // Scroll to the bottom
    logContainer.scrollTop = logContainer.scrollHeight;
}

/**
 * Sets the loading state of the UI
 */
function setLoadingState(isLoading) {
    if (isLoading) {
        loadingOverlay.classList.remove('hidden');
        loadingOverlay.classList.add('flex');
        sendCommandBtn.disabled = true;
        sendCommandBtn.classList.add('opacity-50', 'cursor-not-allowed');
        setStatusText('Processing...');
    } else {
        loadingOverlay.classList.add('hidden');
        loadingOverlay.classList.remove('flex');
        sendCommandBtn.disabled = false;
        sendCommandBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        setStatusText('Ready');
    }
}

/**
 * Sets the status text
 */
function setStatusText(text) {
    statusIndicator.textContent = text;
}

/**
 * Shows the screenshot overlay
 */
function showScreenshot(url) {
    screenshotImg.src = url;
    screenshotOverlay.classList.remove('hidden');
    
    // Add log entry about the screenshot
    addLogEntry('info', 'Screenshot captured. Click to view.', url);
    
    // Set up the screenshot image click event
    screenshotImg.onclick = (e) => {
        e.stopPropagation();
        window.open(url, '_blank');
    };
}

/**
 * Formats the result content for display
 */
function formatResultContent(content) {
    if (!content) return '';
    
    // Convert line breaks to <br>
    let formatted = content.replace(/\n/g, '<br>');
    
    // Simple markdown-like formatting for code blocks
    formatted = formatted.replace(/```([^`]+)```/g, '<pre class="bg-slate-900 p-2 rounded overflow-x-auto my-2">$1</pre>');
    
    // Inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="bg-slate-900 px-1 rounded">$1</code>');
    
    // Links
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-primary-400 hover:underline">$1</a>');
    
    return formatted;
}

/**
 * Shows a toast message
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 py-2 px-4 rounded-md shadow-lg fade-in z-50 text-white';
    
    // Set background color based on type
    if (type === 'error') {
        toast.classList.add('bg-red-500');
    } else if (type === 'success') {
        toast.classList.add('bg-green-500');
    } else {
        toast.classList.add('bg-slate-700');
    }
    
    toast.innerText = message;
    
    // Add to document
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 500);
    }, 3000);
}
