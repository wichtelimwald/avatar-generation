/* Avatar Selector — Application Logic */

// State
let allAvatars = [];
let filteredAvatars = [];
let currentIndex = 0;
let currentPortraitSeedIdx = 0;
let currentBgSeedIdx = 0;
let currentCrossVariantBg = null; // {path, seed, variant, name, key, isSelected?} or null

// Archetype display order
const ARCHETYPE_ORDER = [
    "WILD", "GLAM", "SMART", "KICK", "BEAT",
    "WAVE", "CLIMB", "CARE", "ROAM", "FEAST", "QUEST"
];

// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    loadAvatars();
    checkApiKey();

    // Keyboard navigation
    document.addEventListener("keydown", (e) => {
        // Skip if focus is in an input/select
        if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
        if (e.key === "ArrowLeft") { e.preventDefault(); navigatePrev(); }
        if (e.key === "ArrowRight") { e.preventDefault(); navigateNext(); }
    });
});

// ---------------------------------------------------------------------------
// Data Loading
// ---------------------------------------------------------------------------

async function loadAvatars() {
    try {
        const resp = await fetch("/api/avatars");
        const data = await resp.json();
        allAvatars = data.avatars || [];

        // Sort: by archetype order, then by variant
        const variantOrder = ["adult_male", "adult_female", "teen_male", "teen_female", "child_male", "child_female"];
        allAvatars.sort((a, b) => {
            const ai = ARCHETYPE_ORDER.indexOf(a.archetype);
            const bi = ARCHETYPE_ORDER.indexOf(b.archetype);
            if (ai !== bi) return ai - bi;
            const av = variantOrder.indexOf(a.age_group + "_" + a.gender);
            const bv = variantOrder.indexOf(b.age_group + "_" + b.gender);
            return av - bv;
        });

        populateArchetypeFilter();
        applyFilters();
        loadProgress();
    } catch (err) {
        console.error("Failed to load avatars:", err);
    }
}

function populateArchetypeFilter() {
    const select = document.getElementById("filterArchetype");
    // Clear existing options except "All"
    while (select.options.length > 1) select.remove(1);
    for (const arch of ARCHETYPE_ORDER) {
        const opt = document.createElement("option");
        opt.value = arch;
        opt.textContent = arch;
        select.appendChild(opt);
    }
}

// ---------------------------------------------------------------------------
// Filtering
// ---------------------------------------------------------------------------

function applyFilters() {
    const archFilter = document.getElementById("filterArchetype").value;
    const variantFilter = document.getElementById("filterVariant").value;
    const portraitFilter = document.getElementById("filterPortraitStatus").value;
    const bgFilter = document.getElementById("filterBgStatus").value;

    filteredAvatars = allAvatars.filter(a => {
        if (archFilter && a.archetype !== archFilter) return false;
        if (variantFilter) {
            const v = a.age_group + "_" + a.gender;
            if (v !== variantFilter) return false;
        }
        // Portrait filter: unified — treats key_visual_selected as portrait equivalent
        const hasAnySelected = a.portrait_selected !== null || a.key_visual_selected !== null;
        const hasAnyImages = a.portraits.length > 0 || (a.key_visuals || []).length > 0;
        if (portraitFilter === "selected" && !hasAnySelected) return false;
        if (portraitFilter === "not_selected" && hasAnySelected) return false;
        if (portraitFilter === "no_images" && hasAnyImages) return false;
        if (bgFilter === "selected" && a.background_selected === null) return false;
        if (bgFilter === "not_selected" && a.background_selected !== null) return false;
        if (bgFilter === "no_images" && a.backgrounds.length > 0) return false;
        return true;
    });

    document.getElementById("filterCount").textContent =
        `${filteredAvatars.length} of ${allAvatars.length}`;

    // Reset index if needed
    if (currentIndex >= filteredAvatars.length) {
        currentIndex = Math.max(0, filteredAvatars.length - 1);
    }
    autoSelectSeedIndices();
    displayCurrent();
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function navigatePrev() {
    if (currentIndex > 0) {
        currentIndex--;
        autoSelectSeedIndices();
        displayCurrent();
    }
}

function navigateNext() {
    if (currentIndex < filteredAvatars.length - 1) {
        currentIndex++;
        autoSelectSeedIndices();
        displayCurrent();
    }
}

function autoSelectSeedIndices() {
    const avatar = filteredAvatars[currentIndex];
    currentPortraitSeedIdx = 0;
    currentBgSeedIdx = 0;
    currentCrossVariantBg = null;
    if (!avatar) return;
    // Determine effective portrait source (portraits or key_visuals)
    const ps = getPortraitSource(avatar);
    // Jump to the selected seed if one exists
    if (ps.selected !== null && ps.selected !== "selected") {
        const idx = ps.images.findIndex(p => p.seed === ps.selected);
        if (idx >= 0) currentPortraitSeedIdx = idx;
    }
    if (avatar.background_selected !== null && avatar.background_selected !== "selected") {
        const idx = avatar.backgrounds.findIndex(b => b.seed === avatar.background_selected);
        if (idx >= 0) {
            currentBgSeedIdx = idx;
        } else if (avatar.background_selected_source) {
            // Cross-variant background is selected — preview it
            currentCrossVariantBg = {
                path: avatar.background_selected_path,
                seed: avatar.background_selected_source.seed,
                variant: avatar.background_selected_source.variant,
                name: avatar.background_selected_source.character,
                isSelected: true,
            };
        }
    }
}

// ---------------------------------------------------------------------------
// Portrait Source Helper
// ---------------------------------------------------------------------------

/**
 * Returns the effective "portrait" source for an avatar.
 * If actual portraits exist, use them. Otherwise fall back to key_visuals.
 * This lets key visuals be treated identically to portraits throughout the UI.
 */
function getPortraitSource(avatar) {
    if (avatar.portraits.length > 0) {
        return {
            images: avatar.portraits,
            type: "portrait",
            sortedOut: avatar.portrait_sorted_out,
            selected: avatar.portrait_selected,
            label: "Portrait",
            selectApi: "/api/select-portrait",
            deselectApi: "/api/deselect-portrait",
            sortOutType: "portrait",
            regenType: "portrait",
        };
    }
    const kvList = avatar.key_visuals || [];
    if (kvList.length > 0) {
        return {
            images: kvList,
            type: "keyvisual",
            sortedOut: avatar.key_visual_sorted_out || [],
            selected: avatar.key_visual_selected,
            label: "🎨 Key Visual",
            selectApi: "/api/select-key-visual",
            deselectApi: "/api/deselect-key-visual",
            sortOutType: "keyvisual",
            regenType: "keyvisual",
        };
    }
    // No images yet — determine correct type from character metadata
    const isKvProject = avatar.has_kv_prompt || allAvatars.some(a => (a.key_visuals || []).length > 0);
    return {
        images: [],
        type: isKvProject ? "keyvisual" : "portrait",
        sortedOut: [],
        selected: null,
        label: isKvProject ? "🎨 Key Visual" : "Portrait",
        selectApi: isKvProject ? "/api/select-key-visual" : "/api/select-portrait",
        deselectApi: isKvProject ? "/api/deselect-key-visual" : "/api/deselect-portrait",
        sortOutType: isKvProject ? "keyvisual" : "portrait",
        regenType: isKvProject ? "keyvisual" : "portrait",
    };
}

// ---------------------------------------------------------------------------
// Display
// ---------------------------------------------------------------------------

function displayCurrent() {
    if (filteredAvatars.length === 0) {
        document.getElementById("navPosition").textContent = "0 / 0";
        document.getElementById("navCharacter").textContent = "No avatars match filters";
        clearImages();
        return;
    }

    const avatar = filteredAvatars[currentIndex];
    const ps = getPortraitSource(avatar);

    // Hide cross-variant picker on navigation
    document.getElementById("archetypeBgPicker").style.display = "none";

    // Navigation info
    document.getElementById("navPosition").textContent =
        `${currentIndex + 1} / ${filteredAvatars.length}`;
    document.getElementById("navCharacter").textContent =
        `${avatar.archetype} / ${avatar.variant} / ${avatar.name}`;

    // Navigation button states
    document.getElementById("btnPrev").disabled = currentIndex === 0;
    document.getElementById("btnNext").disabled = currentIndex >= filteredAvatars.length - 1;

    // Character info
    document.getElementById("infoArchetype").textContent = avatar.archetype;
    document.getElementById("infoArchetype").className = `info-value archetype-badge arch-${avatar.archetype}`;
    document.getElementById("infoVariant").textContent = avatar.variant;
    document.getElementById("infoName").textContent = avatar.name;

    // Display images for current seed selections
    displayPortrait(avatar);
    displayBackground(avatar);
    displayComposite(avatar);

    // Build seed navigation — using unified portrait source
    buildSeedNav("portraitSeeds", ps.images, currentPortraitSeedIdx,
        ps.sortedOut, (idx) => { currentPortraitSeedIdx = idx; currentCrossVariantBg = null; displayCurrent(); });
    buildBgSeedNav(avatar);

    // Selection badge — portrait / key visual
    const pBadge = document.getElementById("portraitSelectedBadge");
    if (ps.selected !== null && ps.selected !== undefined) {
        const seedText = ps.selected !== "selected"
            ? ` (s${ps.selected})` : "";
        pBadge.textContent = `✓ Selected${seedText}`;
        pBadge.style.display = "";
    } else {
        pBadge.style.display = "none";
    }

    // Selection badge — background
    const bBadge = document.getElementById("bgSelectedBadge");
    if (avatar.background_selected !== null) {
        let seedText = "";
        if (avatar.background_selected !== "selected") {
            seedText = ` (s${avatar.background_selected})`;
        }
        if (avatar.background_selected_source) {
            seedText += ` · ${avatar.background_selected_source.variant}`;
        }
        bBadge.textContent = `✓ Selected${seedText}`;
        bBadge.style.display = "";
    } else {
        bBadge.style.display = "none";
    }

    // Select/deselect buttons — portrait (unified: works for both portraits and key visuals)
    const hasImages = ps.images.length > 0;
    const hasBg = avatar.backgrounds.length > 0 || currentCrossVariantBg;
    document.getElementById("btnSelectPortrait").style.display =
        hasImages && ps.selected === null ? "" : "none";
    document.getElementById("btnDeselectPortrait").style.display =
        hasImages && ps.selected !== null ? "" : "none";
    // Always show regen button — allows generating first image when none exist
    document.getElementById("btnRegenPortrait").style.display = "";
    const regenBtn = document.getElementById("btnRegenPortrait");
    regenBtn.textContent = hasImages ? "🔄 Regenerate" : "🔄 Generate " + ps.label;
    document.getElementById("btnSortOutPortrait").style.display = hasImages ? "" : "none";
    // Background buttons — always show regen to allow first generation
    const isPreviewingDifferentBg = currentCrossVariantBg && !currentCrossVariantBg.isSelected;
    document.getElementById("btnSelectBg").style.display =
        hasBg && (avatar.background_selected === null || isPreviewingDifferentBg) ? "" : "none";
    document.getElementById("btnDeselectBg").style.display =
        avatar.background_selected !== null && !isPreviewingDifferentBg ? "" : "none";
    document.getElementById("btnSortOutBg").style.display =
        avatar.backgrounds.length > 0 ? "" : "none";
    document.getElementById("btnRegenBg").style.display = "";
    const regenBgBtn = document.getElementById("btnRegenBg");
    regenBgBtn.textContent = avatar.backgrounds.length > 0 ? "🔄 Regenerate" : "🔄 Generate Background";

    // Seed info
    const pSeed = hasImages && ps.images[currentPortraitSeedIdx]
        ? ps.images[currentPortraitSeedIdx].seed : null;
    document.getElementById("infoPortraitSeed").textContent = pSeed !== null ? `s${pSeed}` : "—";
    if (currentCrossVariantBg) {
        const cvLabel = `s${currentCrossVariantBg.seed} (${currentCrossVariantBg.variant})`;
        document.getElementById("infoBgSeed").textContent = cvLabel;
    } else {
        const bSeed = avatar.backgrounds.length > 0 && avatar.backgrounds[currentBgSeedIdx]
            ? avatar.backgrounds[currentBgSeedIdx].seed : null;
        document.getElementById("infoBgSeed").textContent = bSeed !== null ? `s${bSeed}` : "—";
    }

    // Auto-generate banner
    const needsGeneration = !hasImages || !hasBg;
    document.getElementById("autoGenBanner").style.display = needsGeneration ? "" : "none";
}

function displayPortrait(avatar) {
    const img = document.getElementById("imgPortrait");
    const ph = document.getElementById("phPortrait");
    const label = document.getElementById("portraitLabel");
    const ps = getPortraitSource(avatar);
    if (ps.images.length > 0 && ps.images[currentPortraitSeedIdx]) {
        const p = ps.images[currentPortraitSeedIdx];
        img.src = `/api/image/${p.path}`;
        img.style.display = "";
        ph.style.display = "none";
        label.textContent = ps.label;
    } else {
        img.src = "";
        img.style.display = "none";
        ph.style.display = "";
        label.textContent = ps.label;
    }
}

function displayBackground(avatar) {
    const img = document.getElementById("imgBackground");
    const ph = document.getElementById("phBackground");
    if (currentCrossVariantBg) {
        img.src = `/api/image/${currentCrossVariantBg.path}`;
        img.style.display = "";
        ph.style.display = "none";
    } else if (avatar.backgrounds.length > 0 && avatar.backgrounds[currentBgSeedIdx]) {
        const b = avatar.backgrounds[currentBgSeedIdx];
        img.src = `/api/image/${b.path}`;
        img.style.display = "";
        ph.style.display = "none";
    } else {
        img.src = "";
        img.style.display = "none";
        ph.style.display = "";
    }
}

function displayComposite(avatar) {
    const img = document.getElementById("imgComposite");
    const ph = document.getElementById("phComposite");
    const label = document.getElementById("compositeLabel");
    const ps = getPortraitSource(avatar);
    const p = ps.images[currentPortraitSeedIdx];
    const bgPath = currentCrossVariantBg
        ? currentCrossVariantBg.path
        : avatar.backgrounds[currentBgSeedIdx]?.path;

    if (p && bgPath) {
        // Circle-cropped image + neon ring + background (works for both portraits and key visuals)
        const params = new URLSearchParams({
            portrait: p.path,
            background: bgPath,
            archetype: avatar.archetype,
        });
        img.src = `/api/dynamic-composite?${params}`;
        img.style.display = "";
        ph.style.display = "none";
        label.textContent = "Composite";
    } else {
        img.src = "";
        img.style.display = "none";
        ph.style.display = "";
        label.textContent = "Composite";
    }
}

function clearImages() {
    for (const id of ["imgComposite", "imgPortrait", "imgBackground"]) {
        const img = document.getElementById(id);
        img.src = "";
        img.style.display = "none";
    }
    for (const id of ["phComposite", "phPortrait", "phBackground"]) {
        document.getElementById(id).style.display = "";
    }
    document.getElementById("portraitSeeds").innerHTML = "";
    document.getElementById("bgSeeds").innerHTML = "";
    document.getElementById("autoGenBanner").style.display = "none";
    document.getElementById("archetypeBgPicker").style.display = "none";
}

// ---------------------------------------------------------------------------
// Seed Navigation
// ---------------------------------------------------------------------------

function buildSeedNav(containerId, items, activeIdx, sortedOutSeeds, onClick) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";
    if (!items || items.length === 0) return;
    items.forEach((item, idx) => {
        const btn = document.createElement("button");
        btn.className = "seed-btn" + (idx === activeIdx ? " active" : "");
        const seedLabel = item.seed !== null ? `s${item.seed}` : "default";
        btn.textContent = seedLabel;
        if (sortedOutSeeds && sortedOutSeeds.includes(item.seed)) {
            btn.classList.add("sorted-out");
        }
        btn.onclick = () => onClick(idx);
        container.appendChild(btn);
    });
}

function buildBgSeedNav(avatar) {
    const container = document.getElementById("bgSeeds");
    container.innerHTML = "";
    if (!avatar) return;

    // Own backgrounds as seed buttons
    if (avatar.backgrounds && avatar.backgrounds.length > 0) {
        avatar.backgrounds.forEach((item, idx) => {
            const btn = document.createElement("button");
            const isActive = !currentCrossVariantBg && idx === currentBgSeedIdx;
            btn.className = "seed-btn" + (isActive ? " active" : "");
            const seedLabel = item.seed !== null ? `s${item.seed}` : "default";
            btn.textContent = seedLabel;
            if (avatar.background_sorted_out && avatar.background_sorted_out.includes(item.seed)) {
                btn.classList.add("sorted-out");
            }
            btn.onclick = () => {
                currentBgSeedIdx = idx;
                currentCrossVariantBg = null;
                displayCurrent();
            };
            container.appendChild(btn);
        });
    }

    // Load and append cross-variant backgrounds
    loadCrossVariantBgButtons(avatar, container);
}

async function loadCrossVariantBgButtons(avatar, container) {
    try {
        const resp = await fetch(`/api/archetype-backgrounds?archetype=${avatar.archetype}`);
        const data = await resp.json();

        // Filter out backgrounds belonging to the current character
        const otherBgs = (data.backgrounds || []).filter(bg => bg.key !== avatar.key);
        if (otherBgs.length === 0) return;

        // Add separator
        const sep = document.createElement("span");
        sep.className = "seed-separator";
        sep.textContent = "│";
        container.appendChild(sep);

        // Add label
        const label = document.createElement("span");
        label.className = "seed-group-label";
        label.textContent = "other variants:";
        container.appendChild(label);

        // Group by variant for cleaner display
        for (const bg of otherBgs) {
            const btn = document.createElement("button");
            const isActive = currentCrossVariantBg
                && currentCrossVariantBg.path === bg.path;
            btn.className = "seed-btn cross-variant" + (isActive ? " active" : "");
            const seedLabel = bg.seed !== null ? `s${bg.seed}` : "default";
            btn.textContent = `${bg.variant.split(" ").map(w => w[0]).join("")} ${seedLabel}`;
            btn.title = `${bg.variant} · ${bg.name} · s${bg.seed}`;
            btn.onclick = () => {
                currentCrossVariantBg = {
                    path: bg.path,
                    seed: bg.seed,
                    variant: bg.variant,
                    name: bg.name,
                    key: bg.key,
                };
                displayCurrent();
            };
            container.appendChild(btn);
        }
    } catch (err) {
        console.error("Failed to load cross-variant backgrounds:", err);
    }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

async function selectPortrait() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;
    const ps = getPortraitSource(avatar);
    if (ps.images.length === 0) return;
    const seed = ps.images[currentPortraitSeedIdx]?.seed ?? null;
    showLoading("Selecting " + ps.label.toLowerCase() + "...");
    try {
        const resp = await fetch(ps.selectApi, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key, seed }),
        });
        const data = await resp.json();
        if (data.ok) {
            await reloadCurrentAvatar();
        } else {
            alert("Error: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
    hideLoading();
}

async function deselectPortrait() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;
    const ps = getPortraitSource(avatar);
    showLoading("Deselecting " + ps.label.toLowerCase() + "...");
    try {
        const resp = await fetch(ps.deselectApi, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key }),
        });
        const data = await resp.json();
        if (data.ok) {
            await reloadCurrentAvatar();
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
    hideLoading();
}

async function selectBackground() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;

    let body;
    if (currentCrossVariantBg && currentCrossVariantBg.key) {
        // Cross-variant background
        body = {
            key: avatar.key,
            seed: currentCrossVariantBg.seed,
            source_key: currentCrossVariantBg.key,
        };
    } else {
        const seed = avatar.backgrounds[currentBgSeedIdx]?.seed ?? null;
        body = { key: avatar.key, seed };
    }

    showLoading("Selecting background...");
    try {
        const resp = await fetch("/api/select-background", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (data.ok) {
            await reloadCurrentAvatar();
        } else {
            alert("Error: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
    hideLoading();
}

async function deselectBackground() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;
    showLoading("Deselecting background...");
    try {
        const resp = await fetch("/api/deselect-background", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key }),
        });
        const data = await resp.json();
        if (data.ok) {
            await reloadCurrentAvatar();
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
    hideLoading();
}

async function sortOutPortrait() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;
    const ps = getPortraitSource(avatar);
    if (ps.images.length === 0) return;
    const seed = ps.images[currentPortraitSeedIdx]?.seed ?? null;
    if (!confirm(`Sort out ${ps.label.toLowerCase()} (seed: ${seed ?? "default"}) for ${avatar.name}?`)) return;
    showLoading("Moving " + ps.label.toLowerCase() + " to tobedeleted...");
    try {
        const resp = await fetch("/api/sort-out", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key, type: ps.sortOutType, seed }),
        });
        const data = await resp.json();
        if (data.ok) {
            currentPortraitSeedIdx = 0;
            await reloadCurrentAvatar();
        } else {
            alert("Error: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
    hideLoading();
}

async function sortOutBackground() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar || avatar.backgrounds.length === 0) return;
    const seed = avatar.backgrounds[currentBgSeedIdx]?.seed ?? null;
    if (!confirm(`Sort out background (seed: ${seed ?? "default"}) for ${avatar.name}?`)) return;
    showLoading("Moving background to tobedeleted...");
    try {
        const resp = await fetch("/api/sort-out", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key, type: "background", seed }),
        });
        const data = await resp.json();
        if (data.ok) {
            currentBgSeedIdx = 0;
            await reloadCurrentAvatar();
        } else {
            alert("Error: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
    hideLoading();
}

async function regeneratePortrait() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;
    const ps = getPortraitSource(avatar);
    showLoading("Regenerating " + ps.label.toLowerCase() + " (this may take a minute)...");
    try {
        const resp = await fetch("/api/regenerate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key, type: ps.regenType }),
        });
        const data = await resp.json();
        hideLoading();
        if (data.ok) {
            await reloadCurrentAvatar();
        } else {
            showOutput("Regeneration Failed", data.error + "\n\n" + (data.output || ""));
        }
    } catch (err) {
        hideLoading();
        alert("Request failed: " + err.message);
    }
}

async function regenerateBackground() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;
    showLoading("Regenerating background (this may take a minute)...");
    try {
        const resp = await fetch("/api/regenerate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key, type: "background" }),
        });
        const data = await resp.json();
        hideLoading();
        if (data.ok) {
            await reloadCurrentAvatar();
        } else {
            showOutput("Regeneration Failed", data.error + "\n\n" + (data.output || ""));
        }
    } catch (err) {
        hideLoading();
        alert("Request failed: " + err.message);
    }
}

async function autoGenerate() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;
    showLoading("Auto-generating missing assets...");
    try {
        const resp = await fetch("/api/auto-generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: avatar.key }),
        });
        const data = await resp.json();
        hideLoading();
        if (data.ok) {
            await reloadCurrentAvatar();
        } else {
            showOutput("Auto-Generation Failed", data.error + "\n\n" + (data.output || ""));
        }
    } catch (err) {
        hideLoading();
        alert("Request failed: " + err.message);
    }
}

// ---------------------------------------------------------------------------
// Archetype Background Picker
// ---------------------------------------------------------------------------

function toggleArchetypeBgPicker() {
    const picker = document.getElementById("archetypeBgPicker");
    if (picker.style.display === "none") {
        loadArchetypeBackgrounds();
    } else {
        picker.style.display = "none";
    }
}

async function loadArchetypeBackgrounds() {
    const avatar = filteredAvatars[currentIndex];
    if (!avatar) return;

    const picker = document.getElementById("archetypeBgPicker");
    document.getElementById("pickerArchetype").textContent = avatar.archetype;

    try {
        const resp = await fetch(`/api/archetype-backgrounds?archetype=${avatar.archetype}`);
        const data = await resp.json();
        const list = document.getElementById("archetypeBgList");
        list.innerHTML = "";

        // Filter out backgrounds that already belong to the current character
        const otherBgs = (data.backgrounds || []).filter(bg => bg.key !== avatar.key);
        if (otherBgs.length === 0) {
            list.innerHTML = '<span style="color:var(--text-dim);font-size:0.8rem;">No other backgrounds available for this archetype.</span>';
            picker.style.display = "";
            return;
        }

        for (const bg of otherBgs) {
            const item = document.createElement("div");
            item.className = "arch-bg-item";
            item.innerHTML = `
                <img src="/api/image/${bg.path}" alt="${bg.variant} s${bg.seed}">
                <div class="arch-bg-label">${bg.variant}<br>s${bg.seed} · ${bg.name}</div>
            `;
            item.onclick = () => selectCrossVariantBackground(bg);
            list.appendChild(item);
        }
        picker.style.display = "";
    } catch (err) {
        console.error("Failed to load archetype backgrounds:", err);
    }
}

async function selectCrossVariantBackground(bg) {
    // Instead of immediately selecting, preview it in the GUI
    currentCrossVariantBg = {
        path: bg.path,
        seed: bg.seed,
        variant: bg.variant,
        name: bg.name,
        key: bg.key,
    };
    document.getElementById("archetypeBgPicker").style.display = "none";
    displayCurrent();
}

// ---------------------------------------------------------------------------
// Reload
// ---------------------------------------------------------------------------

async function reloadCurrentAvatar() {
    try {
        const resp = await fetch("/api/avatars");
        const data = await resp.json();
        const newAll = data.avatars || [];
        // Update allAvatars in place
        for (const newA of newAll) {
            const idx = allAvatars.findIndex(a => a.key === newA.key);
            if (idx >= 0) allAvatars[idx] = newA;
        }
        // Re-apply filters (preserves index)
        const archFilter = document.getElementById("filterArchetype").value;
        const variantFilter = document.getElementById("filterVariant").value;
        const portraitFilter = document.getElementById("filterPortraitStatus").value;
        const bgFilter = document.getElementById("filterBgStatus").value;

        filteredAvatars = allAvatars.filter(a => {
            if (archFilter && a.archetype !== archFilter) return false;
            if (variantFilter) {
                const v = a.age_group + "_" + a.gender;
                if (v !== variantFilter) return false;
            }
            const hasAnySelected = a.portrait_selected !== null || a.key_visual_selected !== null;
            const hasAnyImages = a.portraits.length > 0 || (a.key_visuals || []).length > 0;
            if (portraitFilter === "selected" && !hasAnySelected) return false;
            if (portraitFilter === "not_selected" && hasAnySelected) return false;
            if (portraitFilter === "no_images" && hasAnyImages) return false;
            if (bgFilter === "selected" && a.background_selected === null) return false;
            if (bgFilter === "not_selected" && a.background_selected !== null) return false;
            if (bgFilter === "no_images" && a.backgrounds.length > 0) return false;
            return true;
        });

        document.getElementById("filterCount").textContent =
            `${filteredAvatars.length} of ${allAvatars.length}`;

        if (currentIndex >= filteredAvatars.length) {
            currentIndex = Math.max(0, filteredAvatars.length - 1);
        }
        displayCurrent();
        loadProgress();
    } catch (err) {
        console.error("Reload failed:", err);
    }
}

// ---------------------------------------------------------------------------
// Progress
// ---------------------------------------------------------------------------

async function loadProgress() {
    try {
        const resp = await fetch("/api/progress");
        const data = await resp.json();

        // Count "portrait or key_visual" selected for unified progress
        const bothCount = allAvatars.filter(a =>
            (a.portrait_selected !== null || a.key_visual_selected !== null) && a.background_selected !== null
        ).length;

        // Unified portrait count: portrait_selected OR key_visual_selected
        const unifiedPortraitCount = data.portraits_selected + data.key_visuals_selected;
        document.getElementById("progressPortraits").textContent =
            `${unifiedPortraitCount}/${data.total}`;
        document.getElementById("progressBackgrounds").textContent =
            `${data.backgrounds_selected}/${data.total}`;
        document.getElementById("progressBoth").textContent =
            `${bothCount}/${data.total}`;

        // Build segmented progress bars — one segment per archetype
        // Use a custom "combined" field for portrait bar
        buildSegmentedBarCombined("progressPortraitsBar", data);
        buildSegmentedBar("progressBackgroundsBar", data, "backgrounds_selected");
        buildSegmentedBothBar("progressBothBar", data);

        // Per-archetype breakdown with mini progress bars
        const archContainer = document.getElementById("progressArchetypes");
        archContainer.innerHTML = "";
        for (const arch of ARCHETYPE_ORDER) {
            const a = data.archetypes[arch];
            if (!a) continue;
            const archPSelected = a.portraits_selected + (a.key_visuals_selected || 0);
            const pPct = a.total > 0 ? (archPSelected / a.total * 100) : 0;
            const bPct = a.total > 0 ? (a.backgrounds_selected / a.total * 100) : 0;
            const div = document.createElement("div");
            div.className = "arch-progress";
            div.innerHTML = `
                <div class="arch-name arch-${arch}" style="display:inline-block; padding:1px 6px; border-radius:8px;">${arch}</div>
                <div class="arch-stats">
                    P: ${archPSelected}/${a.total}
                    <div class="arch-progress-bar"><div class="arch-progress-fill portraits" style="width:${pPct}%"></div></div>
                    B: ${a.backgrounds_selected}/${a.total}
                    <div class="arch-progress-bar"><div class="arch-progress-fill backgrounds" style="width:${bPct}%"></div></div>
                </div>
            `;
            archContainer.appendChild(div);
        }
    } catch (err) {
        console.error("Failed to load progress:", err);
    }
}

function buildSegmentedBar(containerId, data, field) {
    const bar = document.getElementById(containerId);
    bar.innerHTML = "";
    if (!data.total || data.total === 0) return;
    for (const arch of ARCHETYPE_ORDER) {
        const a = data.archetypes[arch];
        if (!a) continue;
        const pct = (a[field] / data.total) * 100;
        if (pct <= 0) continue;
        const seg = document.createElement("div");
        seg.className = `progress-segment seg-${arch}`;
        seg.style.width = pct + "%";
        seg.title = `${arch}: ${a[field]}`;
        bar.appendChild(seg);
    }
}

function buildSegmentedBarCombined(containerId, data) {
    const bar = document.getElementById(containerId);
    bar.innerHTML = "";
    if (!data.total || data.total === 0) return;
    for (const arch of ARCHETYPE_ORDER) {
        const a = data.archetypes[arch];
        if (!a) continue;
        const combined = a.portraits_selected + (a.key_visuals_selected || 0);
        const pct = (combined / data.total) * 100;
        if (pct <= 0) continue;
        const seg = document.createElement("div");
        seg.className = `progress-segment seg-${arch}`;
        seg.style.width = pct + "%";
        seg.title = `${arch}: ${combined}`;
        bar.appendChild(seg);
    }
}

function buildSegmentedBothBar(containerId, data) {
    const bar = document.getElementById(containerId);
    bar.innerHTML = "";
    if (!data.total || data.total === 0) return;
    // Count "both selected" per archetype from local data
    for (const arch of ARCHETYPE_ORDER) {
        const count = allAvatars.filter(a =>
            a.archetype === arch
            && (a.portrait_selected !== null || a.key_visual_selected !== null)
            && a.background_selected !== null
        ).length;
        if (count <= 0) continue;
        const pct = (count / data.total) * 100;
        const seg = document.createElement("div");
        seg.className = `progress-segment seg-${arch}`;
        seg.style.width = pct + "%";
        seg.title = `${arch}: ${count}`;
        bar.appendChild(seg);
    }
}

function showProgressPanel() {
    const panel = document.getElementById("progressPanel");
    panel.style.display = panel.style.display === "none" ? "" : "none";
    if (panel.style.display !== "none") loadProgress();
}

function hideProgressPanel() {
    document.getElementById("progressPanel").style.display = "none";
}

// ---------------------------------------------------------------------------
// API Key
// ---------------------------------------------------------------------------

async function checkApiKey() {
    try {
        const resp = await fetch("/api/api-key-status");
        const data = await resp.json();
        const badge = document.getElementById("apiKeyStatus");
        if (data.configured) {
            badge.textContent = "🔑 " + (data.source || "configured");
            badge.style.background = "rgba(76, 175, 80, 0.2)";
        } else {
            badge.textContent = "🔑 not set";
            badge.style.background = "rgba(244, 67, 54, 0.2)";
        }
    } catch (err) {
        console.error("Failed to check API key:", err);
    }
}

function showApiKeyDialog() {
    document.getElementById("apiKeyDialog").style.display = "";
    document.getElementById("apiKeyInput").value = "";
    document.getElementById("apiKeyInput").focus();
}

function closeApiKeyDialog() {
    document.getElementById("apiKeyDialog").style.display = "none";
}

async function submitApiKey() {
    const key = document.getElementById("apiKeyInput").value.trim();
    if (!key) return;
    try {
        const resp = await fetch("/api/set-api-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key }),
        });
        const data = await resp.json();
        if (data.ok) {
            closeApiKeyDialog();
            checkApiKey();
        } else {
            alert("Error: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
}

// ---------------------------------------------------------------------------
// Dialogs
// ---------------------------------------------------------------------------

function showOutput(title, content) {
    document.getElementById("outputDialogTitle").textContent = title;
    document.getElementById("outputDialogContent").textContent = content;
    document.getElementById("outputDialog").style.display = "";
}

function closeOutputDialog() {
    document.getElementById("outputDialog").style.display = "none";
}

function showLoading(text) {
    document.getElementById("loadingText").textContent = text || "Loading...";
    document.getElementById("loadingOverlay").style.display = "";
}

function hideLoading() {
    document.getElementById("loadingOverlay").style.display = "none";
}
