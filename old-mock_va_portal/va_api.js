/**
 * va_api.js — Mock VA Portal Frontend Logic
 *
 * Two responsibilities:
 * 1. Fetch the veteran's service branch from the real VA Benefits Reference
 *    Data API and show a "✓ VA Verified" badge (proves live VA connectivity)
 * 2. Poll the mock VA portal server for new appeal submissions from VetClaim AI
 *    and show a notification banner on the dashboard when one arrives
 *
 * The mock VA portal server runs at http://localhost:5050 (server.py).
 * The real VA sandbox API runs at https://sandbox-api.va.gov.
 */

const VA_SANDBOX_BASE  = "https://sandbox-api.va.gov/services/benefits-reference-data/v1";
const VA_PORTAL_BASE   = "http://localhost:5050";

// Read the API key from the <meta> tag so it's not hardcoded in JS source.
// In production this would be injected server-side.
const VA_API_KEY = document.querySelector('meta[name="va-api-key"]')?.content || "";

// The demo veteran's branch code as stored in the VA system
const DEMO_VETERAN_BRANCH_CODE = "ARMY";

// How often (ms) to poll the portal server for new submissions.
// 3 seconds is fast enough to feel live without hammering the server.
const POLL_INTERVAL_MS = 3000;


/* ── 1. VA Benefits Reference Data API ─────────────────────────── */

/**
 * Fetch service branches from the real VA API and update the Branch field
 * with the official VA description + a "✓ VA Verified" badge.
 * Falls back gracefully if the API is unreachable during the demo.
 */
async function initVABranchVerification() {
  const branchEl = document.getElementById("va-service-branch");
  if (!branchEl) return;

  branchEl.textContent = "Loading...";

  try {
    const response = await fetch(`${VA_SANDBOX_BASE}/service-branches`, {
      headers: { "apiKey": VA_API_KEY }
    });

    if (!response.ok) throw new Error(`VA API ${response.status}`);

    const data = await response.json();
    const match = data.items.find(b => b.code === DEMO_VETERAN_BRANCH_CODE);
    branchEl.textContent = match ? match.description : "Army";

    // Add the verified badge — visual proof of live VA API connection
    const badge = document.createElement("span");
    badge.className = "va-verified-badge";
    badge.title = "Verified against VA Benefits Reference Data API";
    badge.textContent = "✓ VA Verified";
    branchEl.parentNode.appendChild(badge);

  } catch (err) {
    // API unreachable — fall back silently so the demo isn't blocked
    console.warn("VA API unavailable, using fallback:", err.message);
    branchEl.textContent = "Army";
  }
}


/* ── 2. Submission polling ──────────────────────────────────────── */

/**
 * Poll the mock VA portal server every 3 seconds for new submissions.
 * When a submission arrives from VetClaim AI, show a notification banner
 * on the dashboard with a link to the confirmation page.
 *
 * We track which submission IDs we've already shown so we don't
 * re-show the banner on every poll cycle.
 */
function startSubmissionPolling() {
  // Only poll on the dashboard page (index.html)
  const notificationArea = document.getElementById("submission-notification");
  if (!notificationArea) return;

  const seenIds = new Set();

  async function poll() {
    try {
      const response = await fetch(`${VA_PORTAL_BASE}/submissions`);
      if (!response.ok) return; // server not running yet — try again next cycle

      const submissions = await response.json();

      // Find the most recent submission we haven't shown yet
      const newSubmission = submissions.find(s => !seenIds.has(s.id));
      if (!newSubmission) return;

      seenIds.add(newSubmission.id);
      showSubmissionBanner(newSubmission);

    } catch (err) {
      // Server not running — this is expected before the demo starts
      // Don't log anything so the console stays clean
    }
  }

  setInterval(poll, POLL_INTERVAL_MS);
  poll(); // run immediately on page load too
}

/**
 * Inject a green notification banner into the dashboard when a new
 * submission is detected. The banner links to the confirmation page.
 */
function showSubmissionBanner(submission) {
  const notificationArea = document.getElementById("submission-notification");
  if (!notificationArea) return;

  notificationArea.innerHTML = `
    <div class="submission-banner">
      <div class="submission-banner__icon">📬</div>
      <div class="submission-banner__text">
        <strong>New appeal documents received from VetClaim AI.</strong>
        Confirmation: <code>${submission.confirmation_number}</code>
        &nbsp;&bull;&nbsp; ${submission.submitted_at}
      </div>
      <a href="confirmation.html?id=${submission.id}" class="va-btn va-btn--primary submission-banner__btn">
        View Submission →
      </a>
    </div>
  `;
}


/* ── Init ───────────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  initVABranchVerification();
  startSubmissionPolling();
});
