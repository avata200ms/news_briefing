/**
 * News Briefing AI - Client Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const form = document.getElementById("curation-form");
    const keywordInput = document.getElementById("keyword-input");
    const filterPromptInput = document.getElementById("filter-prompt-input");
    const submitBtn = document.getElementById("submit-btn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnSpinner = submitBtn.querySelector(".btn-spinner");
    
    // Preset Chips
    const presetChips = document.querySelectorAll(".preset-chip");
    
    // Sort Toggle
    const radioBtns = document.querySelectorAll(".radio-toggle-btn");
    
    // Views
    const loadingSection = document.getElementById("loading-section");
    const loadingStepTitle = document.getElementById("loading-step-title");
    const loadingStepDesc = document.getElementById("loading-step-desc");
    const step1 = document.getElementById("step-1");
    const step2 = document.getElementById("step-2");
    const step3 = document.getElementById("step-3");
    const stepLine1 = document.getElementById("step-line-1");
    const stepLine2 = document.getElementById("step-line-2");

    const errorBox = document.getElementById("error-box");
    const errorMessage = document.getElementById("error-message");
    const closeErrorBtn = document.getElementById("close-error-btn");

    const resultsSection = document.getElementById("results-section");
    const overviewCommentText = document.getElementById("overview-comment-text");
    const resultKeywordTag = document.getElementById("result-keyword-tag");
    const resultCountTag = document.getElementById("result-count-tag");
    const curatedCardsGrid = document.getElementById("curated-cards-grid");

    const toggleRawBtn = document.getElementById("toggle-raw-btn");
    const rawArticlesCollapse = document.getElementById("raw-articles-collapse");
    const rawArticlesTbody = document.getElementById("raw-articles-tbody");

    const copyMarkdownBtn = document.getElementById("copy-markdown-btn");
    const copyTextBtn = document.getElementById("copy-text-btn");
    const saveBriefingBtn = document.getElementById("save-briefing-btn");
    const toastContainer = document.getElementById("toast-container");

    let currentResultData = null;
    let stepperTimer = null;

    // 1. CSRF Token Helper
    function getCsrfToken() {
        const csrfCookie = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));
        if (csrfCookie) {
            return csrfCookie.split("=")[1];
        }
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : "";
    }

    // 2. Toast Notification
    function showToast(message, isError = false) {
        if (!toastContainer) return;
        const toast = document.createElement("div");
        toast.className = "toast";
        const icon = isError 
            ? `<i data-lucide="alert-circle" style="color:#f43f5e; width:18px; height:18px;"></i>` 
            : `<i data-lucide="check-circle" style="color:#10b981; width:18px; height:18px;"></i>`;
        toast.innerHTML = `${icon} <span>${message}</span>`;
        toastContainer.appendChild(toast);
        lucide.createIcons();

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(10px)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // 3. Radio Toggle Handlers
    radioBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            radioBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            btn.querySelector("input").checked = true;
        });
    });

    // 4. Preset Chips Handlers
    presetChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const filterText = chip.getAttribute("data-filter");
            filterPromptInput.value = filterText;
            filterPromptInput.focus();
        });
    });

    // 5. Accordion Toggle
    toggleRawBtn.addEventListener("click", () => {
        const isHidden = rawArticlesCollapse.classList.contains("hidden");
        const arrow = toggleRawBtn.querySelector(".accordion-arrow");
        if (isHidden) {
            rawArticlesCollapse.classList.remove("hidden");
            arrow.classList.add("rotated");
        } else {
            rawArticlesCollapse.classList.add("hidden");
            arrow.classList.remove("rotated");
        }
    });

    // 6. Error Box Close
    closeErrorBtn.addEventListener("click", () => {
        errorBox.classList.add("hidden");
    });

    // 7. Loading Stepper Controller
    function startLoadingStepper() {
        // Reset steps
        step1.className = "step-item active";
        step2.className = "step-item";
        step3.className = "step-item";
        stepLine1.className = "step-line";
        stepLine2.className = "step-line";

        loadingStepTitle.textContent = "1단계: 네이버 뉴스 20건 실시간 수집 중...";
        loadingStepDesc.textContent = "네이버 검색 Open API를 통해 키워드 관련 최신 기사 20건을 파싱하고 있습니다.";

        stepperTimer = setTimeout(() => {
            step1.className = "step-item completed";
            stepLine1.className = "step-line active";
            step2.className = "step-item active";
            loadingStepTitle.textContent = "2단계: Gemini AI 기사 선별 중...";
            loadingStepDesc.textContent = "20개 기사의 제목과 내용을 분석하여 필터링 프롬프트에 가장 적합한 3개 기사를 엄선하고 있습니다.";

            stepperTimer = setTimeout(() => {
                step2.className = "step-item completed";
                stepLine2.className = "step-line active";
                step3.className = "step-item active";
                loadingStepTitle.textContent = "3단계: 심층 요약 & 비즈니스 인사이트 생성 중...";
                loadingStepDesc.textContent = "엄선된 3개 기사의 핵심 3줄 요약과 시사점을 도출하여 브리핑 리포트를 완성하고 있습니다.";
            }, 3000);
        }, 1500);
    }

    function stopLoadingStepper() {
        if (stepperTimer) clearTimeout(stepperTimer);
    }

    // 8. Form Submission Handler
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const keyword = keywordInput.value.trim();
        const filterPrompt = filterPromptInput.value.trim();
        const sort = document.querySelector('input[name="sort"]:checked')?.value || "sim";

        if (!keyword || !filterPrompt) {
            alert("키워드와 필터링 프롬프트를 모두 입력해주세요.");
            return;
        }

        // UI 상태 초기화
        errorBox.classList.add("hidden");
        resultsSection.classList.add("hidden");
        loadingSection.classList.remove("hidden");
        submitBtn.disabled = true;
        btnText.classList.add("hidden");
        btnSpinner.classList.remove("hidden");

        startLoadingStepper();

        try {
            const response = await fetch("/api/curate/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({
                    keyword: keyword,
                    filter_prompt: filterPrompt,
                    sort: sort,
                }),
            });

            const data = await response.json();

            stopLoadingStepper();
            loadingSection.classList.add("hidden");
            submitBtn.disabled = false;
            btnText.classList.remove("hidden");
            btnSpinner.classList.add("hidden");

            if (!data.success) {
                showError(data.error || "뉴스 큐레이션 중 문제가 발생했습니다.");
                return;
            }

            // 성공 렌더링
            currentResultData = data;
            renderResults(data);
            resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

        } catch (err) {
            stopLoadingStepper();
            loadingSection.classList.add("hidden");
            submitBtn.disabled = false;
            btnText.classList.remove("hidden");
            btnSpinner.classList.add("hidden");
            showError("네트워크 또는 서버 통신 오류가 발생했습니다: " + err.message);
        }
    });

    function showError(msg) {
        errorMessage.textContent = msg;
        errorBox.classList.remove("hidden");
        errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    // 9. Results Renderer
    function renderResults(data) {
        resultsSection.classList.remove("hidden");

        // Overview Banner
        overviewCommentText.textContent = `"${data.overview_comment}"`;
        resultKeywordTag.textContent = `키워드: ${data.keyword}`;
        resultCountTag.textContent = `20개 기사 중 3건 엄선`;

        // Save Button Reset
        if (saveBriefingBtn) {
            saveBriefingBtn.disabled = false;
            saveBriefingBtn.classList.remove("saved");
            saveBriefingBtn.innerHTML = `<i data-lucide="bookmark-plus"></i> <span class="save-btn-text">결과 저장하기</span>`;
        }

        // Curated Top 3 Cards
        curatedCardsGrid.innerHTML = "";
        data.curated_articles.forEach((article, index) => {
            const card = document.createElement("div");
            card.className = "curated-card glass-card";

            const bulletsHtml = article.summary_bullets
                .map(bullet => `<li class="bullet-item">${escapeHtml(bullet)}</li>`)
                .join("");

            const tagsHtml = (article.tags || [])
                .map(tag => `<span class="article-tag">#${escapeHtml(tag)}</span>`)
                .join("");

            card.innerHTML = `
                <div class="card-top-row">
                    <div class="card-rank-badge">
                        <i data-lucide="award"></i> AI PICK #${index + 1}
                    </div>
                    <span class="card-date">${escapeHtml(article.pub_date || "")}</span>
                </div>

                <h4 class="card-title">
                    <a href="${article.url}" target="_blank" rel="noopener noreferrer">
                        ${escapeHtml(article.title)}
                    </a>
                </h4>

                <div class="reason-box">
                    <div class="reason-title">
                        <i data-lucide="check-circle-2"></i> 선정 이유
                    </div>
                    <p class="reason-text">${escapeHtml(article.selection_reason)}</p>
                </div>

                <div class="bullets-box">
                    <div class="bullets-title">
                        <i data-lucide="align-left"></i> 핵심 요약 3줄
                    </div>
                    <ul class="bullets-list">
                        ${bulletsHtml}
                    </ul>
                </div>

                <div class="insight-box">
                    <div class="insight-header">
                        <i data-lucide="lightbulb"></i> 비즈니스 인사이트 & 시사점
                    </div>
                    <p class="insight-text">${escapeHtml(article.insight)}</p>
                </div>

                <div class="card-bottom-row">
                    <div class="tag-list">
                        ${tagsHtml}
                    </div>
                    <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="card-link-btn">
                        <span>원문 기사 읽기</span>
                        <i data-lucide="external-link"></i>
                    </a>
                </div>
            `;
            curatedCardsGrid.appendChild(card);
        });

        // Raw 20 Articles Table
        rawArticlesTbody.innerHTML = "";
        (data.all_articles || []).forEach(art => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${art.id}</strong></td>
                <td>
                    <a href="${art.url}" target="_blank" rel="noopener noreferrer" class="raw-title-link">
                        ${escapeHtml(art.title)}
                    </a>
                </td>
                <td>${escapeHtml(art.pub_date)}</td>
                <td>
                    <a href="${art.url}" target="_blank" rel="noopener noreferrer" class="card-link-btn" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">
                        <i data-lucide="external-link"></i> 링크
                    </a>
                </td>
            `;
            rawArticlesTbody.appendChild(tr);
        });

        lucide.createIcons();
    }

    // 10. Save Briefing Handler
    if (saveBriefingBtn) {
        saveBriefingBtn.addEventListener("click", async () => {
            if (!currentResultData) {
                showToast("저장할 요약 결과가 없습니다.", true);
                return;
            }

            saveBriefingBtn.disabled = true;
            saveBriefingBtn.innerHTML = `<div class="spinner" style="width:14px; height:14px; border-width:2px; display:inline-block;"></div> <span>저장 중...</span>`;

            try {
                const response = await fetch("/api/save/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },
                    body: JSON.stringify({
                        keyword: currentResultData.keyword,
                        filter_prompt: currentResultData.filter_prompt,
                        overview_comment: currentResultData.overview_comment,
                        curated_articles: currentResultData.curated_articles,
                    }),
                });

                const data = await response.json();

                if (data.success) {
                    saveBriefingBtn.classList.add("saved");
                    saveBriefingBtn.innerHTML = `<i data-lucide="check"></i> <span>저장 완료됨</span>`;
                    lucide.createIcons();
                    showToast("🎉 뉴스 요약 결과가 DB에 저장되었습니다!");
                } else {
                    saveBriefingBtn.disabled = false;
                    saveBriefingBtn.innerHTML = `<i data-lucide="bookmark-plus"></i> <span class="save-btn-text">결과 저장하기</span>`;
                    lucide.createIcons();
                    showToast(data.error || "저장에 실패했습니다.", true);
                }
            } catch (err) {
                saveBriefingBtn.disabled = false;
                saveBriefingBtn.innerHTML = `<i data-lucide="bookmark-plus"></i> <span class="save-btn-text">결과 저장하기</span>`;
                lucide.createIcons();
                showToast("통신 오류가 발생했습니다: " + err.message, true);
            }
        });
    }

    // 11. Copy Markdown Handler
    if (copyMarkdownBtn) {
        copyMarkdownBtn.addEventListener("click", () => {
            if (!currentResultData) return;
            const d = currentResultData;
            let md = `# 📰 AI 뉴스 큐레이션 브리핑: ${d.keyword}\n\n`;
            md += `> **총평**: ${d.overview_comment}\n\n`;
            md += `* **필터링 조건**: ${d.filter_prompt}\n`;
            md += `* **분석 대상**: 네이버 검색 20개 기사 중 핵심 3건 선별\n\n---\n\n`;

            d.curated_articles.forEach((art, idx) => {
                md += `### [AI PICK #${idx + 1}] [${art.title}](${art.url})\n`;
                md += `- **발행일**: ${art.pub_date}\n`;
                md += `- **선정 이유**: ${art.selection_reason}\n\n`;
                md += `**📌 핵심 요약 3줄**:\n`;
                art.summary_bullets.forEach(b => {
                    md += `  * ${b}\n`;
                });
                md += `\n**💡 비즈니스 인사이트**:\n> ${art.insight}\n\n`;
                if (art.tags && art.tags.length > 0) {
                    md += `*태그: ${art.tags.map(t => `#${t}`).join(" ")}*\n\n`;
                }
                md += `---\n\n`;
            });

            navigator.clipboard.writeText(md).then(() => {
                showToast("마크다운 포맷이 클립보드에 복사되었습니다!");
            });
        });
    }

    // 12. Copy Newsletter Text Handler
    if (copyTextBtn) {
        copyTextBtn.addEventListener("click", () => {
            if (!currentResultData) return;
            const d = currentResultData;
            let txt = `[📰 AI 뉴스 브리핑 - ${d.keyword}]\n\n`;
            txt += `💬 브리핑 요약: ${d.overview_comment}\n\n`;
            txt += `========================================\n\n`;

            d.curated_articles.forEach((art, idx) => {
                txt += `[#${idx + 1}] ${art.title}\n`;
                txt += `🔗 링크: ${art.url}\n`;
                txt += `🎯 선정 이유: ${art.selection_reason}\n\n`;
                txt += `[핵심 3줄 요약]\n`;
                art.summary_bullets.forEach(b => {
                    txt += `• ${b}\n`;
                });
                txt += `\n[인사이트]\n👉 ${art.insight}\n\n`;
                txt += `----------------------------------------\n\n`;
            });

            navigator.clipboard.writeText(txt).then(() => {
                showToast("뉴스레터 텍스트가 클립보드에 복사되었습니다!");
            });
        });
    }

    // 13. History Page: Delete Briefing
    document.querySelectorAll(".btn-delete-briefing").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const briefingId = btn.getAttribute("data-id");
            const keyword = btn.getAttribute("data-keyword");
            
            if (!confirm(`'${keyword}' 뉴스 브리핑 저장 기록을 정말 삭제하시겠습니까?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/history/${briefingId}/delete/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },
                });

                const data = await response.json();
                if (data.success) {
                    const card = document.getElementById(`briefing-card-${briefingId}`);
                    if (card) {
                        card.style.opacity = "0";
                        card.style.transform = "scale(0.95)";
                        card.style.transition = "all 0.3s ease";
                        setTimeout(() => {
                            card.remove();
                            // If all removed, refresh
                            const remaining = document.querySelectorAll(".briefing-history-card");
                            if (remaining.length === 0) {
                                location.reload();
                            }
                        }, 300);
                    }
                    showToast(data.message || "삭제되었습니다.");
                } else {
                    showToast(data.error || "삭제에 실패했습니다.", true);
                }
            } catch (err) {
                showToast("삭제 중 통신 오류가 발생했습니다: " + err.message, true);
            }
        });
    });

    // 14. History Page: Copy Markdown for a Card
    document.querySelectorAll(".copy-briefing-md-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const briefingId = btn.getAttribute("data-id");
            const card = document.getElementById(`briefing-card-${briefingId}`);
            if (!card) return;

            const keyword = card.querySelector(".bcard-keyword")?.textContent.trim() || "";
            const date = card.querySelector(".bcard-date")?.textContent.trim() || "";
            const filter = card.querySelector(".bcard-filter-text")?.textContent.trim() || "";
            const overview = card.querySelector(".bcard-overview-text")?.textContent.trim() || "";

            let md = `# 📰 AI 뉴스 큐레이션 브리핑: ${keyword}\n\n`;
            md += `> **저장일시**: ${date}\n`;
            md += `> **총평**: ${overview}\n`;
            md += `> **선별 기준**: ${filter}\n\n---\n\n`;

            card.querySelectorAll(".history-article-card").forEach((artCard, idx) => {
                const titleElem = artCard.querySelector(".h-card-title a");
                const title = titleElem?.textContent.trim() || "";
                const url = titleElem?.getAttribute("href") || "";
                const pubDate = artCard.querySelector(".h-card-date")?.textContent.trim() || "";
                const reason = artCard.querySelector(".h-reason-box .h-box-text")?.textContent.trim() || "";
                const insight = artCard.querySelector(".h-insight-box .h-insight-text")?.textContent.trim() || "";
                
                const bullets = [];
                artCard.querySelectorAll(".h-bullets-list li").forEach(li => {
                    bullets.push(li.textContent.trim());
                });

                md += `### [AI PICK #${idx + 1}] [${title}](${url})\n`;
                if (pubDate) md += `- **발행일**: ${pubDate}\n`;
                if (reason) md += `- **선정 이유**: ${reason}\n\n`;
                if (bullets.length > 0) {
                    md += `**📌 핵심 요약 3줄**:\n`;
                    bullets.forEach(b => {
                        md += `  * ${b}\n`;
                    });
                }
                if (insight) md += `\n**💡 비즈니스 인사이트**:\n> ${insight}\n\n`;
                md += `---\n\n`;
            });

            navigator.clipboard.writeText(md).then(() => {
                showToast("브리핑 마크다운이 클립보드에 복사되었습니다!");
            });
        });
    });

    // Utility: HTML escape
    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});

