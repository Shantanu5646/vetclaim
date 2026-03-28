/**
 * profiles.js — Demo veteran profiles for the mock VA portal
 *
 * WHY: The demo needs to show VetClaim AI works for different veterans,
 * not just one hardcoded person. Clicking the name in the nav swaps the
 * entire dashboard to a different veteran's data — no page reload needed.
 *
 * Each profile mirrors the data shape used in index.html so the
 * renderProfile() function can swap everything in one shot.
 */

const PROFILES = {

  james: {
    name: "James R. Wilson",
    claimNumber: "796-04-3456",
    lastUpdated: "February 14, 2026",
    rating: "30%",
    payment: "$524.31",
    decisionDate: "Jan 9, 2026",
    branchCode: "ARMY",
    service: {
      branch: "U.S. Army",
      dates: "Mar 1991 – Nov 2003",
      era: "Gulf War / Post-9/11",
      deployments: "Iraq (OIF) 2003, Kuwait 1991",
      discharge: "Honorable",
    },
    appealDeadline: "January 9, 2027",
    documents: [
      "📄 Rating Decision Letter (Jan 9, 2026)",
      "📄 C&P Exam Results (Dec 2025)",
      "📄 DBQ — PTSD (Dec 2025)",
      "📄 DBQ — TBI (Dec 2025)",
    ],
    deniedCount: 2,
    conditions: [
      { name: "Post-Traumatic Stress Disorder (PTSD)", code: "9411", decision: "Service Connected", rating: "10%", denied: false },
      { name: "Traumatic Brain Injury (TBI)",          code: "8045", decision: "Service Connected", rating: "10%", denied: false },
      { name: "Lumbar Strain (Lower Back)",            code: "5237", decision: "Service Connected", rating: "20%", denied: false },
      { name: "Tinnitus",                              code: "6260", decision: "Service Connected", rating: "10%", denied: false },
      { name: "Sleep Apnea",                           code: "6847", decision: "Denied — No Nexus", rating: "0%",  denied: true  },
      { name: "Respiratory Condition (Burn Pit Exposure)", code: "6604", decision: "Denied — No Nexus", rating: "0%", denied: true },
    ],
  },

  maria: {
    name: "Maria L. Santos",
    claimNumber: "812-07-9921",
    lastUpdated: "March 3, 2026",
    rating: "20%",
    payment: "$338.49",
    decisionDate: "Mar 3, 2026",
    branchCode: "NAVY",
    service: {
      branch: "U.S. Navy",
      dates: "Jun 2005 – Aug 2017",
      era: "Post-9/11",
      deployments: "Persian Gulf 2008, Bahrain 2012",
      discharge: "Honorable",
    },
    appealDeadline: "March 3, 2027",
    documents: [
      "📄 Rating Decision Letter (Mar 3, 2026)",
      "📄 C&P Exam Results (Feb 2026)",
      "📄 DBQ — Hearing Loss (Feb 2026)",
      "📄 Service Treatment Records (2005–2017)",
    ],
    deniedCount: 2,
    conditions: [
      { name: "Bilateral Hearing Loss",               code: "6100", decision: "Service Connected", rating: "10%", denied: false },
      { name: "Tinnitus",                             code: "6260", decision: "Service Connected", rating: "10%", denied: false },
      { name: "Migraines",                            code: "8100", decision: "Service Connected", rating: "0%",  denied: false },
      { name: "PTSD — Military Sexual Trauma",        code: "9411", decision: "Denied — Insufficient Nexus", rating: "0%", denied: true },
      { name: "Lumbar Disc Disease",                  code: "5243", decision: "Denied — Not Service Connected", rating: "0%", denied: true },
    ],
  },

  darnell: {
    name: "Darnell T. Brooks",
    claimNumber: "634-11-5507",
    lastUpdated: "January 22, 2026",
    rating: "40%",
    payment: "$673.28",
    decisionDate: "Jan 22, 2026",
    branchCode: "MARINES",
    service: {
      branch: "U.S. Marine Corps",
      dates: "Sep 2001 – Dec 2009",
      era: "Post-9/11 / OEF / OIF",
      deployments: "Afghanistan (OEF) 2002, Iraq (OIF) 2005",
      discharge: "Honorable",
    },
    appealDeadline: "January 22, 2027",
    documents: [
      "📄 Rating Decision Letter (Jan 22, 2026)",
      "📄 C&P Exam Results (Dec 2025)",
      "📄 DBQ — Knee (Dec 2025)",
      "📄 DBQ — PTSD (Nov 2025)",
    ],
    deniedCount: 2,
    conditions: [
      { name: "PTSD",                                 code: "9411", decision: "Service Connected", rating: "30%", denied: false },
      { name: "Right Knee — Patellofemoral Syndrome", code: "5260", decision: "Service Connected", rating: "10%", denied: false },
      { name: "Tinnitus",                             code: "6260", decision: "Service Connected", rating: "10%", denied: false },
      { name: "Traumatic Brain Injury (TBI)",         code: "8045", decision: "Denied — No Nexus", rating: "0%",  denied: true  },
      { name: "Sleep Apnea",                          code: "6847", decision: "Denied — No Nexus", rating: "0%",  denied: true  },
    ],
  },

};

// Track the active profile so va_api.js can read the current veteran name
let activeProfileKey = "james";

/**
 * Render the full dashboard for a given profile key.
 * Swaps out every piece of veteran-specific content on the page.
 *
 * @param {string} profileKey - one of "james", "maria", "darnell"
 */
function renderProfile(profileKey) {
  const profile = PROFILES[profileKey];
  if (!profile) return;

  activeProfileKey = profileKey;

  // --- Nav: signed-in name ---
  const userEl = document.querySelector(".va-nav__user");
  if (userEl) {
    userEl.innerHTML = `Signed in as <strong>${profile.name}</strong>`;
  }

  // --- Page subtitle: claim number + last updated ---
  const subtitleEl = document.querySelector(".va-subtitle");
  if (subtitleEl) {
    subtitleEl.innerHTML = `Claim #${profile.claimNumber} &nbsp;&bull;&nbsp; Last updated: ${profile.lastUpdated}`;
  }

  // --- Rating banner ---
  const ratingNumberEl = document.querySelector(".rating-number");
  if (ratingNumberEl) ratingNumberEl.textContent = profile.rating;

  const payAmountEl = document.querySelector(".pay-amount");
  if (payAmountEl) payAmountEl.textContent = profile.payment;

  const payLabelDecisionEl = document.querySelector(".va-rating-banner__item:last-child .pay-label");
  if (payLabelDecisionEl) payLabelDecisionEl.textContent = `Decided ${profile.decisionDate}`;

  // --- Denied callout ---
  const calloutTextEl = document.querySelector(".denied-callout__text");
  if (calloutTextEl) {
    calloutTextEl.innerHTML = `<strong>${profile.deniedCount} of your conditions were denied.</strong> You may be eligible to appeal these decisions.`;
  }

  // --- Conditions table ---
  const tbody = document.querySelector(".va-table tbody");
  if (tbody) {
    tbody.innerHTML = profile.conditions.map(condition => `
      <tr${condition.denied ? ' class="table-row--denied"' : ''}>
        <td>${condition.name}</td>
        <td>${condition.code}</td>
        <td class="${condition.denied ? 'decision-denied' : 'decision-granted'}">${condition.decision}</td>
        <td class="rating-cell${condition.denied ? ' rating-cell--denied' : ''}">${condition.rating}</td>
      </tr>
    `).join("");
  }

  // --- Service information sidebar ---
  const branchEl = document.getElementById("va-service-branch");
  if (branchEl) {
    // Remove any existing VA verified badge before re-rendering
    const existingBadge = branchEl.parentNode.querySelector(".va-verified-badge");
    if (existingBadge) existingBadge.remove();
    branchEl.textContent = profile.service.branch;
  }

  // Update the other service info fields
  const dlItems = document.querySelectorAll(".va-dl dd");
  if (dlItems.length >= 4) {
    // dd[0] = Branch (handled above via #va-service-branch)
    dlItems[1].textContent = profile.service.dates;
    dlItems[2].textContent = profile.service.era;
    dlItems[3].textContent = profile.service.deployments;
    dlItems[4].textContent = profile.service.discharge;
  }

  // --- Appeal deadline ---
  const deadlineEl = document.querySelector(".va-deadline");
  if (deadlineEl) {
    deadlineEl.innerHTML = `Deadline: <strong>${profile.appealDeadline}</strong>`;
  }

  // --- Claim documents ---
  const docListEl = document.querySelector(".va-doc-list");
  if (docListEl) {
    docListEl.innerHTML = profile.documents.map(doc => `<li><a href="#">${doc}</a></li>`).join("");
  }

  // --- Clear any existing submission notification (new veteran = fresh state) ---
  const notificationArea = document.getElementById("submission-notification");
  if (notificationArea) notificationArea.innerHTML = "";

  // --- Re-run VA branch verification for the new profile's branch code ---
  // Pass the branch code so the API lookup targets the right branch
  initVABranchVerificationForProfile(profile.branchCode);

  // --- Update the profile switcher dropdown to show the active name ---
  updateProfileSwitcher(profileKey);
}

/**
 * Build and inject the profile switcher dropdown into the nav.
 * Called once on page load — after that, renderProfile() just updates the active state.
 */
function initProfileSwitcher() {
  const userEl = document.querySelector(".va-nav__user");
  if (!userEl) return;

  // Replace the static text with a clickable dropdown
  userEl.style.position = "relative";
  userEl.style.cursor = "pointer";
  userEl.innerHTML = `
    Signed in as <strong id="active-profile-name">${PROFILES[activeProfileKey].name}</strong>
    <span style="font-size:10px; margin-left:4px; color:#adc6e0;">▼</span>
    <div id="profile-dropdown" class="profile-dropdown" style="display:none;">
      ${Object.entries(PROFILES).map(([key, p]) => `
        <div class="profile-dropdown__item${key === activeProfileKey ? ' profile-dropdown__item--active' : ''}"
             data-profile="${key}">
          <span class="profile-dropdown__name">${p.name}</span>
          <span class="profile-dropdown__meta">${p.rating} · ${p.service.branch.replace("U.S. ", "")}</span>
        </div>
      `).join("")}
    </div>
  `;

  // Toggle dropdown on click
  userEl.addEventListener("click", (event) => {
    const dropdown = document.getElementById("profile-dropdown");
    dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
    event.stopPropagation();
  });

  // Handle profile selection
  document.getElementById("profile-dropdown").addEventListener("click", (event) => {
    const item = event.target.closest(".profile-dropdown__item");
    if (!item) return;
    renderProfile(item.dataset.profile);
    document.getElementById("profile-dropdown").style.display = "none";
    event.stopPropagation();
  });

  // Close dropdown when clicking anywhere else
  document.addEventListener("click", () => {
    const dropdown = document.getElementById("profile-dropdown");
    if (dropdown) dropdown.style.display = "none";
  });
}

/**
 * Update the dropdown to highlight the currently active profile.
 * @param {string} activeKey
 */
function updateProfileSwitcher(activeKey) {
  const nameEl = document.getElementById("active-profile-name");
  if (nameEl) nameEl.textContent = PROFILES[activeKey].name;

  document.querySelectorAll(".profile-dropdown__item").forEach(item => {
    item.classList.toggle("profile-dropdown__item--active", item.dataset.profile === activeKey);
  });
}
