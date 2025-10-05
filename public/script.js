const imageElement = document.getElementById('story-image');
const situationElement = document.getElementById('situation-text');
const choicesElement = document.getElementById('choices');
const loadingElement = document.getElementById('loading-indicator'); // Add a loading spinner/text element
const scoreElement = document.getElementById('score-display'); // Add element to show score
const endScreenElement = document.getElementById('end-screen'); // Add a container for the end screen
const mangaImageElement = document.getElementById('manga-image');
const summaryImageElement = document.getElementById('summary-image');
const endTextElement = document.getElementById('end-text');

// Add these new elements for the share modal
const shareModalElement = document.getElementById('share-modal');
const shareMangaImageElement = document.getElementById('share-manga-image');
const shareLoadingElement = document.getElementById('share-loading');
const closeModalButton = document.querySelector('.close-modal');
const downloadImageButton = document.getElementById('download-image');
const copyImageButton = document.getElementById('copy-image');
const shareTwitterButton = document.getElementById('share-twitter');
const shareFacebookButton = document.getElementById('share-facebook');

function showLoading(isLoading) {
    if (isLoading) {
        // Set up the loading indicator with animation
        loadingElement.textContent = 'Loading your journey';
        loadingElement.style.opacity = '0';
        loadingElement.style.display = 'block';

        setTimeout(() => {
            loadingElement.style.transition = 'opacity 0.3s ease';
            loadingElement.style.opacity = '1';
        }, 50);

        // Hide choices with fade-out
        if (choicesElement.style.display !== 'none') {
            choicesElement.style.transition = 'opacity 0.3s ease';
            choicesElement.style.opacity = '0';

            setTimeout(() => {
                choicesElement.style.display = 'none';
            }, 300);
        } else {
            choicesElement.style.display = 'none';
        }
    } else {
        // Hide loading with fade-out
        loadingElement.style.transition = 'opacity 0.3s ease';
        loadingElement.style.opacity = '0';

        setTimeout(() => {
            loadingElement.style.display = 'none';

            // Show choices with fade-in if they were hidden
            if (choicesElement.style.display === 'none') {
                choicesElement.style.opacity = '0';
                choicesElement.style.display = 'block';

                setTimeout(() => {
                    choicesElement.style.transition = 'opacity 0.5s ease';
                    choicesElement.style.opacity = '1';
                }, 50);
            }
        }, 300);
    }
}

async function updateGameState() {
    showLoading(true);

    // Clear previous state
    endScreenElement.style.display = 'none';
    endTextElement.innerHTML = '';
    situationElement.textContent = '';
    imageElement.src = '';
    mangaImageElement.src = '';
    summaryImageElement.src = '';
    choicesElement.innerHTML = '';

    // Remove any reset containers from the end screen
    const existingEndScreenResetContainers = endScreenElement.querySelectorAll('.reset-container');
    existingEndScreenResetContainers.forEach(container => container.remove());

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

        const response = await fetch('/api/state', {
            signal: controller.signal,
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Validate the data received
        if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
            throw new Error("Received empty response from server");
        }

        renderState(data);
    } catch (error) {
        console.error("Error fetching game state:", error);
        situationElement.textContent = `Error loading game state: ${error.message}. Retrying in 5 seconds...`;

        // Always show the reset button when there's an error
        choicesElement.innerHTML = '';
        const resetContainer = document.createElement('div');
        resetContainer.className = 'reset-container';

        const resetButton = document.createElement('button');
        resetButton.textContent = 'Reset Game';
        resetButton.className = 'reset-button';
        resetButton.addEventListener('click', resetGame);
        resetContainer.appendChild(resetButton);

        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = 'Refresh Page';
        refreshBtn.className = 'reset-button';
        refreshBtn.style.marginLeft = '10px';
        refreshBtn.addEventListener('click', () => window.location.reload());
        resetContainer.appendChild(refreshBtn);

        choicesElement.appendChild(resetContainer);

        // Auto-retry after 5 seconds
        setTimeout(() => {
            situationElement.textContent = "Attempting to reconnect...";
            updateGameState();
        }, 5000);
    } finally {
        showLoading(false);
    }
}

function renderState(data) {
    console.log("Rendering state:", data);

    // Update score - check both current_score and score properties
    const score = data.current_score !== undefined ? data.current_score :
        (data.score !== undefined ? data.score : 0);
    scoreElement.textContent = `Score: ${score}`;

    // Update image with fade-in effect
    imageElement.style.opacity = '0';
    imageElement.src = data.image_url || '';
    imageElement.alt = data.image_prompt || 'Story scene';
    imageElement.onload = () => {
        imageElement.style.transition = 'opacity 0.5s ease';
        imageElement.style.opacity = '1';
    };
    imageElement.style.display = 'block';

    // Animate situation text
    situationElement.style.opacity = '0';
    setTimeout(() => {
        situationElement.textContent = data.situation || 'Loading...';
        situationElement.style.transition = 'opacity 0.8s ease';
        situationElement.style.opacity = '1';
    }, 300);

    // Clear all content in choices
    choicesElement.innerHTML = '';

    // Add a single reset button at the top
    const resetContainer = document.createElement('div');
    resetContainer.className = 'reset-container';

    const resetButton = document.createElement('button');
    resetButton.textContent = 'Reset Game';
    resetButton.className = 'reset-button';
    resetButton.addEventListener('click', resetGame);
    resetContainer.appendChild(resetButton);

    choicesElement.appendChild(resetContainer);

    if (data.is_end) {
        // Handle End Screen
        displayEndScreen(data);
    } else if (data.choices && data.choices.length > 0) {
        // Create choice buttons with staggered animation
        data.choices.forEach((choice, index) => {
            const button = document.createElement('button');
            button.textContent = choice.text || `Choice ${index + 1}`;
            button.dataset.index = index;
            button.addEventListener('click', handleChoiceClick);
            button.style.opacity = '0';
            button.style.transform = 'translateY(20px)';
            choicesElement.appendChild(button);

            // Staggered animation for buttons
            setTimeout(() => {
                button.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                button.style.opacity = '1';
                button.style.transform = 'translateY(0)';
            }, 500 + (index * 100)); // Stagger by 100ms per button
        });
    } else {
        // No choices, maybe an intermediate state or error
        situationElement.textContent += "\n (No choices available)";
    }
}

async function handleChoiceClick(event) {
    const choiceIndex = parseInt(event.target.dataset.index, 10);
    if (isNaN(choiceIndex)) return;

    showLoading(true);
    choicesElement.innerHTML = ''; // Clear choices immediately

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const response = await fetch('/api/choice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ choice_index: choiceIndex }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const nextStateData = await response.json();
        renderState(nextStateData); // Render the new state received
    } catch (error) {
        console.error("Error making choice:", error);
        situationElement.textContent = `Error processing choice: ${error.message}`;

        // Always show the reset button when there's an error
        choicesElement.innerHTML = '';
        const resetContainer = document.createElement('div');
        resetContainer.className = 'reset-container';

        const resetButton = document.createElement('button');
        resetButton.textContent = 'Reset Game';
        resetButton.className = 'reset-button';
        resetButton.addEventListener('click', resetGame);
        resetContainer.appendChild(resetButton);

        choicesElement.appendChild(resetContainer);
    } finally {
        showLoading(false);
    }
}

function displayEndScreen(data) {
    // Hide the main choices
    choicesElement.style.display = 'none';

    // Calculate a star rating based on score (1-5 stars)
    const score = data.current_score !== undefined ? data.current_score :
        (data.score !== undefined ? data.score : 0);
    const maxScore = 10; // Assuming maximum possible score is around 10
    const starRating = Math.max(1, Math.min(5, Math.ceil(score / 2)));

    // Show the end screen container with a fade in
    endScreenElement.style.display = 'block';
    endScreenElement.style.opacity = '0';

    // Prepare the end text content with score and rating
    const endingCategory = data.ending_category || 'Journey Complete';
    const stars = '★'.repeat(starRating) + '☆'.repeat(5 - starRating);

    // Eco metrics & governance weight
    const impacts = data.impacts || data.impact_summary || { co2_kg: 0, plastic_g: 0, water_l: 0, energy_kwh: 0 };
    const governanceWeight = data.governance_weight !== undefined ? data.governance_weight : 0;

    let endTextContent = `
        <h2>${endingCategory}</h2>
        <div class="score-display">
            <span class="score-label">Final Score:</span> 
            <span class="score-value">${score}</span>
            <div class="star-rating">${stars}</div>
        </div>
        <div class="score-display">
            <span class="score-label">Your Impact (↓ is better):</span>
            <div style="margin-top:8px; text-align:center;">
                CO₂: ${impacts.co2_kg?.toFixed ? impacts.co2_kg.toFixed(2) : impacts.co2_kg} kg,
                Plastic: ${impacts.plastic_g} g,
                Water: ${impacts.water_l} L,
                Energy: ${impacts.energy_kwh?.toFixed ? impacts.energy_kwh.toFixed(2) : impacts.energy_kwh} kWh
            </div>
            <div style="margin-top:8px;">Governance Weight: <strong>${governanceWeight}</strong></div>
        </div>
        <p>${data.situation}</p>
    `;

    // Add a personalized message based on score
    if (score >= 8) {
        endTextContent += `<p class="end-message">Remarkable! You've mastered this journey with exceptional choices.</p>`;
    } else if (score >= 5) {
        endTextContent += `<p class="end-message">Well done! Your journey through the city was quite successful.</p>`;
    } else if (score >= 2) {
        endTextContent += `<p class="end-message">You've completed your journey with some wisdom gained along the way.</p>`;
    } else {
        endTextContent += `<p class="end-message">The city has taught you some difficult lessons. Perhaps another path would lead to a different fate.</p>`;
    }

    endTextElement.innerHTML = endTextContent;

    // Load the manga-style image with fade-in effect
    if (data.manga_image_url) {
        mangaImageElement.style.opacity = '0';
        mangaImageElement.src = data.manga_image_url;
        mangaImageElement.onload = () => {
            mangaImageElement.style.transition = 'opacity 0.8s ease';
            mangaImageElement.style.opacity = '1';
        };
    }

    // Load the summary image with fade-in effect
    if (data.summary_image_url) {
        summaryImageElement.style.opacity = '0';
        summaryImageElement.src = data.summary_image_url;
        summaryImageElement.onload = () => {
            summaryImageElement.style.transition = 'opacity 0.8s ease';
            summaryImageElement.style.opacity = '1';
        };
    }

    // Add a reset container with custom styling for the end screen
    const resetContainer = document.createElement('div');
    resetContainer.className = 'reset-container end-reset';

    const resetButton = document.createElement('button');
    resetButton.textContent = 'Play Again';
    resetButton.className = 'reset-button end-reset-button';
    resetButton.addEventListener('click', resetGame);

    const shareButton = document.createElement('button');
    shareButton.textContent = 'Share Your Story';
    shareButton.className = 'reset-button share-button';

    // Update share button click handler to open the modal
    shareButton.addEventListener('click', () => {
        openShareModal(score, endingCategory);
    });

    // Add Save to Blockchain button
    const saveToBlockchainButton = document.createElement('button');
    saveToBlockchainButton.textContent = 'Save to Blockchain';
    saveToBlockchainButton.className = 'reset-button blockchain-button';
    saveToBlockchainButton.style.backgroundColor = '#8B5CF6';
    saveToBlockchainButton.style.marginLeft = '10px';

    saveToBlockchainButton.addEventListener('click', async () => {
        const storyData = {
            endingCategory: endingCategory,
            score: score,
            imageUrl: data.image_url || '',
            mangaImageUrl: data.manga_image_url || '',
            impacts: impacts,
            governanceWeight: governanceWeight
        };

        const storyId = await saveStoryToBlockchain(storyData);
        if (storyId) {
            // Update button to show success
            saveToBlockchainButton.textContent = `Saved! ID: ${storyId}`;
            saveToBlockchainButton.style.backgroundColor = '#10B981';
            saveToBlockchainButton.disabled = true;

            // Show success message
            const successMsg = document.createElement('div');
            successMsg.style.cssText = `
                position: fixed; top: 20px; right: 20px; background: #10B981; color: white; 
                padding: 15px; border-radius: 8px; z-index: 10000; font-weight: bold;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            `;
            successMsg.textContent = `Story saved to blockchain with ID: ${storyId}`;
            document.body.appendChild(successMsg);

            // Remove success message after 5 seconds
            setTimeout(() => {
                if (document.body.contains(successMsg)) {
                    document.body.removeChild(successMsg);
                }
            }, 5000);
        }
    });

    resetContainer.appendChild(resetButton);
    resetContainer.appendChild(shareButton);
    resetContainer.appendChild(saveToBlockchainButton);
    endScreenElement.appendChild(resetContainer);

    // Fade in the end screen
    setTimeout(() => {
        endScreenElement.style.transition = 'opacity 1s ease';
        endScreenElement.style.opacity = '1';
    }, 500);
}

// New function to open the share modal and generate shareable image
async function openShareModal(score, endingCategory) {
    // Show the modal
    shareModalElement.style.display = 'block';

    // Clear any previous image
    shareMangaImageElement.style.display = 'none';
    shareMangaImageElement.src = '';

    // Show loading indicator
    shareLoadingElement.style.display = 'block';

    try {
        // Fetch the shareable image from our API
        const response = await fetch('/api/share-image');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Hide loading and show the image
        shareLoadingElement.style.display = 'none';
        shareMangaImageElement.style.display = 'block';
        shareMangaImageElement.src = data.share_image_url;

        // Setup share buttons with the appropriate data
        setupShareButtons(data.share_image_url, score, endingCategory);

    } catch (error) {
        console.error("Error generating share image:", error);
        shareLoadingElement.textContent = `Error generating image: ${error.message}. Please try again.`;

        // Add a retry button
        const retryButton = document.createElement('button');
        retryButton.textContent = 'Retry';
        retryButton.className = 'action-button';
        retryButton.style.marginTop = '15px';
        retryButton.addEventListener('click', () => {
            openShareModal(score, endingCategory);
        });

        shareLoadingElement.appendChild(retryButton);
    }
}

// Setup the share buttons with the correct URLs and functionality
function setupShareButtons(imageUrl, score, endingCategory) {
    // Setup download button
    downloadImageButton.onclick = () => {
        downloadImage(imageUrl, 'city-of-better-choices.jpg');
    };

    // Setup copy button
    copyImageButton.onclick = () => {
        copyImageToClipboard(imageUrl);
    };

    // Setup social share buttons
    const shareText = `I played City of Better Choices: score ${score}, ending "${endingCategory}". What impact can you make today?`;
    const shareUrl = window.location.href;

    // Twitter share
    shareTwitterButton.onclick = () => {
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
        window.open(twitterUrl, '_blank');
    };

    // Facebook share
    shareFacebookButton.onclick = () => {
        const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(shareText)}`;
        window.open(facebookUrl, '_blank');
    };
}

// Function to download the image
function downloadImage(url, filename) {
    // Create a temporary anchor element
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';

    // Add to body, click it to trigger download, and remove
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Function to copy image to clipboard using Fetch API to get the blob
async function copyImageToClipboard(url) {
    try {
        const response = await fetch(url);
        const blob = await response.blob();

        // Check if the Clipboard API is available and can handle images
        if (navigator.clipboard && navigator.clipboard.write) {
            const item = new ClipboardItem({ [blob.type]: blob });
            await navigator.clipboard.write([item]);
            alert('Image copied to clipboard!');
        } else {
            // Fallback for browsers that don't support copying images
            alert('Your browser doesn\'t support copying images. Please use the Download button instead.');
        }
    } catch (error) {
        console.error('Error copying image to clipboard:', error);
        alert('Failed to copy image. Please try downloading it instead.');
    }
}

// Close the modal when clicking the X
closeModalButton.addEventListener('click', () => {
    shareModalElement.style.display = 'none';
});

// Close the modal when clicking outside the content
window.addEventListener('click', (event) => {
    if (event.target === shareModalElement) {
        shareModalElement.style.display = 'none';
    }
});

// Helper function to copy text to clipboard
function copyToClipboard(text) {
    // Try to use the modern clipboard API first
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                alert('Story copied to clipboard! You can now share it with friends.');
            })
            .catch(err => {
                console.error('Clipboard write failed:', err);
                fallbackCopyToClipboard(text);
            });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// Fallback copy method for older browsers
function fallbackCopyToClipboard(text) {
    // Create a temporary input element
    const input = document.createElement('input');
    input.style.position = 'fixed';
    input.style.opacity = 0;
    input.value = text;
    document.body.appendChild(input);

    // Select and copy
    input.select();
    document.execCommand('copy');

    // Clean up
    document.body.removeChild(input);

    // Notify user
    alert('Story copied to clipboard! You can now share it with friends.');
}

async function resetGame() {
    showLoading(true);

    // Hide end screen
    endScreenElement.style.display = 'none';

    // Clear end screen content to prevent duplicates on subsequent resets
    endTextElement.innerHTML = '';
    mangaImageElement.src = '';
    summaryImageElement.src = '';

    // Remove any existing reset containers from the end screen
    const existingEndScreenResetContainers = endScreenElement.querySelectorAll('.reset-container');
    existingEndScreenResetContainers.forEach(container => container.remove());

    // Show normal image
    imageElement.style.display = 'block';
    situationElement.textContent = 'Resetting game...';

    // Clear the choices area
    choicesElement.innerHTML = '';

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const response = await fetch('/api/reset', {
            method: 'POST',
            signal: controller.signal,
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Check if we got a valid game state
        if (!data || (!data.situation && !data.current_score && !data.choices)) {
            console.error("Invalid state received after reset:", data);
            // If we didn't get a valid state, fetch it explicitly
            await updateGameState();
        } else {
            // Render the state we received
            renderState(data);
        }
    } catch (error) {
        console.error("Error resetting game:", error);
        situationElement.textContent = `Error resetting game: ${error.message}. Please refresh the page.`;

        // Always show a refresh button
        choicesElement.innerHTML = '';
        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = 'Refresh Page';
        refreshBtn.addEventListener('click', () => window.location.reload());
        choicesElement.appendChild(refreshBtn);
    } finally {
        showLoading(false);
    }
}

// Initial load when the page loads
document.addEventListener('DOMContentLoaded', updateGameState);

// ===== VECHAIN SYNC2 (CONNEX) INTEGRATION - TESTNET =====

let connex = null; // Connex runtime instance
let vechainAccount = null; // Address string

// Simple Sync2 detection
function isSync2Available() {
    return typeof window.connex !== 'undefined';
}

// Initialize Connex for testnet
function initConnex() {
    if (!isSync2Available()) {
        return false;
    }

    try {
        connex = new window.connex.Connex({
            node: 'https://testnet.veblocks.net/',
            network: 'test'
        });
        console.log('Connex initialized successfully');
        return true;
    } catch (e) {
        console.error('Failed to initialize Connex:', e);
        return false;
    }
}

// Request a Sync2 connection via certificate signing
async function connectSync2() {
    try {
        console.log('Attempting to connect to Sync2...');

        // Check if Sync2 is available
        if (!isSync2Available()) {
            alert(`Sync2 not detected! Please:
1. Download Sync2 from: https://sync.vecha.in/
2. Install and run the desktop app
3. Refresh this page
4. Try connecting again`);
            return false;
        }

        // Initialize Connex
        if (!initConnex()) {
            alert('Failed to initialize Connex. Please try again.');
            return false;
        }

        // Request certificate for identification
        const vendor = connex.vendor;
        const cert = await vendor.sign('cert', {
            purpose: 'identification',
            payload: {
                type: 'text',
                content: 'City of Better Choices: Connect'
            }
        });

        if (!cert || !cert.annex || !cert.annex.signer) {
            throw new Error('User rejected or no signer returned');
        }

        vechainAccount = cert.annex.signer;
        updateConnectionStatus(true, vechainAccount);
        console.log('Sync2 connected successfully:', vechainAccount);
        return true;
    } catch (error) {
        console.error('Sync2 connect failed:', error);
        alert('Failed to connect Sync2: ' + error.message);
        updateConnectionStatus(false);
        return false;
    }
}

// Sign a proof of story outcome (no mainnet tx; just user-signed payload)
async function saveStoryToBlockchain(storyData) {
    try {
        if (!isSync2Available() || !connex) {
            alert('Sync2 not connected. Please connect first.');
            return null;
        }

        const vendor = connex.vendor;
        const message = JSON.stringify({
            app: 'CityOfBetterChoices',
            action: 'saveOutcome',
            data: storyData,
            timestamp: Date.now()
        });

        const signed = await vendor.sign('message', { message });

        if (!signed || !signed.signature) {
            throw new Error('User canceled signing');
        }

        const id = '0x' + btoa(signed.signature).slice(0, 10);
        console.log('Story saved to blockchain with ID:', id);
        return id;
    } catch (e) {
        console.error('Error signing with Sync2:', e);
        alert('Failed to sign with Sync2: ' + e.message);
        return null;
    }
}

// Update connection status display
function updateConnectionStatus(connected, account = null) {
    const statusElement = document.getElementById('connection-status');
    const connectButton = document.getElementById('connect-sync2');

    if (connected && account) {
        statusElement.textContent = `🟢 Sync2: ${account.slice(0, 6)}...${account.slice(-4)}`;
        statusElement.style.color = '#10B981';
        connectButton.style.display = 'none';
    } else if (connected) {
        statusElement.textContent = '🟡 Sync2 Connected';
        statusElement.style.color = '#F59E0B';
        connectButton.style.display = 'none';
    } else {
        // Check if Sync2 is available but not connected
        if (typeof window.connex !== 'undefined') {
            statusElement.textContent = '🟡 Sync2 Available - Click to Connect';
            statusElement.style.color = '#F59E0B';
        } else {
            statusElement.textContent = '🔴 Sync2 Not Detected - Install Desktop App';
            statusElement.style.color = '#EF4444';
        }
        connectButton.style.display = 'block';
    }
}

// Handle connect Sync2 button
document.addEventListener('DOMContentLoaded', () => {
    const connectButton = document.getElementById('connect-sync2');

    if (connectButton) {
        connectButton.addEventListener('click', async () => {
            const connected = await connectSync2();
            if (!connected) return;
        });
    }
});


// Initialize status on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initial status check
    updateConnectionStatus(false);

    // Check for Sync2 every 1 second
    const checkInterval = setInterval(() => {
        if (isSync2Available() && !vechainAccount) {
            updateConnectionStatus(false);
        }
    }, 1000);

    // Stop checking after 10 seconds
    setTimeout(() => {
        clearInterval(checkInterval);
    }, 10000);
});