let currentCharacter = null;
let currentCounts = { left: 0, right: 0 };
let config = {};

document.addEventListener("DOMContentLoaded", async () => {
    await loadConfig();
    await updateVotes();
    setInterval(updateVotes, 3000);
});

async function loadConfig() {
    const resp = await fetch("/api/config");
    config = await resp.json();
    document.getElementById("modal-wallet").textContent = config.wallet_address;
    document.getElementById("modal-amount").textContent = config.usdt_amount;
    document.getElementById("footer-wallet").textContent = config.wallet_address;
    document.getElementById("footer-amount").textContent = config.usdt_amount;
}

async function updateVotes() {
    try {
        const resp = await fetch("/api/votes");
        const data = await resp.json();
        animateCounter("left-count", currentCounts.left, data.left);
        animateCounter("right-count", currentCounts.right, data.right);
        currentCounts = { left: data.left, right: data.right };
        updateProgressBar(data.left, data.right);
    } catch (e) {}
}

function animateCounter(id, from, to) {
    if (from === to) return;
    const el = document.getElementById(id);
    const duration = 600;
    const start = performance.now();

    function step(ts) {
        const p = Math.min((ts - start) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.floor(from + (to - from) * eased).toLocaleString();
        if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function updateProgressBar(left, right) {
    const total = left + right;
    const leftPct = total === 0 ? 50 : (left / total) * 100;
    document.getElementById("progress-left").style.width = leftPct + "%";
    document.getElementById("progress-right").style.width = (100 - leftPct) + "%";
}

function startVote(character) {
    currentCharacter = character;
    const name = character === "left" ? config.left_name : config.right_name;
    document.getElementById("modal-character-name").textContent = name;
    document.getElementById("tx-hash-input").value = "";
    document.getElementById("vote-status").textContent = "";
    document.getElementById("vote-status").className = "vote-status";
    document.getElementById("vote-modal").classList.add("active");
}

function closeModal() {
    document.getElementById("vote-modal").classList.remove("active");
    currentCharacter = null;
}

async function submitVote() {
    const txHash = document.getElementById("tx-hash-input").value.trim();
    const statusEl = document.getElementById("vote-status");
    const btn = document.getElementById("submit-vote-btn");

    if (!txHash || !txHash.startsWith("0x") || txHash.length !== 66) {
        statusEl.textContent = "Please enter a valid transaction hash (0x + 64 hex characters)";
        statusEl.className = "vote-status error";
        return;
    }

    btn.disabled = true;
    btn.textContent = "Verifying...";
    statusEl.textContent = "Checking transaction on BSC... This may take a moment.";
    statusEl.className = "vote-status pending";

    try {
        const resp = await fetch("/api/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ character: currentCharacter, tx_hash: txHash }),
        });

        const data = await resp.json();

        if (resp.ok) {
            statusEl.textContent = data.message;
            statusEl.className = "vote-status success";
            await updateVotes();
            setTimeout(closeModal, 2500);
        } else {
            statusEl.textContent = data.detail || "Verification failed";
            statusEl.className = "vote-status error";
        }
    } catch (err) {
        statusEl.textContent = "Network error. Please try again.";
        statusEl.className = "vote-status error";
    } finally {
        btn.disabled = false;
        btn.textContent = "Verify & Vote";
    }
}

function copyAddress() {
    navigator.clipboard.writeText(config.wallet_address);
    const btn = event.target;
    const original = btn.textContent;
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(() => {
        btn.textContent = original;
        btn.classList.remove("copied");
    }, 1500);
}

document.getElementById("vote-modal").addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) closeModal();
});
