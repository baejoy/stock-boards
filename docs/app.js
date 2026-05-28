(function () {
    const minInput = document.getElementById("min-input");
    const refreshBtn = document.getElementById("refresh-btn");
    const statusEl = document.getElementById("status");
    const container = document.getElementById("board-container");

    let cachedPayload = null;

    function fmtMoney(n) {
        if (!n) return "-";
        if (n >= 1e8) return (n / 1e8).toFixed(2) + " 亿";
        if (n >= 1e4) return (n / 1e4).toFixed(2) + " 万";
        return n.toFixed(0);
    }

    function fmtPct(n) {
        if (n === null || n === undefined) return "-";
        return n.toFixed(2) + "%";
    }

    function fmtTime(t) {
        if (!t) return "-";
        const s = String(t).padStart(6, "0");
        if (s.length !== 6 || !/^\d{6}$/.test(s)) return t;
        return `${s.slice(0, 2)}:${s.slice(2, 4)}:${s.slice(4, 6)}`;
    }

    function fmtUpdated(iso) {
        if (!iso) return "";
        const d = new Date(iso);
        // 显示为北京时间
        const bj = new Date(d.getTime());
        const opts = { timeZone: "Asia/Shanghai", hour12: false,
                       year: "numeric", month: "2-digit", day: "2-digit",
                       hour: "2-digit", minute: "2-digit" };
        return bj.toLocaleString("zh-CN", opts);
    }

    function renderCard(s) {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <div class="card-top">
                <div>
                    <span class="card-name">${s.name}</span>
                    <span class="card-code">${s.code}</span>
                </div>
                <div class="card-boards">${s.boards} 连板</div>
            </div>
            <div class="card-row">
                <span class="label">最新价</span>
                <span class="val up">${s.price.toFixed(2)} (${fmtPct(s.change_pct)})</span>
            </div>
            <div class="card-row">
                <span class="label">成交额</span>
                <span class="val">${fmtMoney(s.turnover)}</span>
            </div>
            <div class="card-row">
                <span class="label">流通市值</span>
                <span class="val">${fmtMoney(s.float_cap)}</span>
            </div>
            <div class="card-row">
                <span class="label">${s.break_times > 0 ? "首次封板" : "封板时间"}</span>
                <span class="val">${fmtTime(s.first_seal)}</span>
            </div>
            ${s.break_times > 0 ? `
            <div class="card-row">
                <span class="label">最后封板</span>
                <span class="val">${fmtTime(s.last_seal)}</span>
            </div>
            <div class="card-row">
                <span class="label">炸板次数</span>
                <span class="val" style="color:#f0b232">${s.break_times} 次</span>
            </div>` : ""}
            ${s.industry ? `<div class="card-industry">${s.industry}</div>` : ""}
            <div class="card-links">
                <a href="${s.eastmoney_url}" target="_blank" rel="noopener">东方财富</a>
                <a href="${s.ths_url}" target="_blank" rel="noopener">同花顺</a>
                <a href="${s.xueqiu_url}" target="_blank" rel="noopener">雪球</a>
            </div>
        `;
        card.addEventListener("click", (e) => {
            if (e.target.tagName === "A") return;
            window.open(s.eastmoney_url, "_blank", "noopener");
        });
        return card;
    }

    function render() {
        container.innerHTML = "";
        if (!cachedPayload) {
            container.innerHTML = '<div class="empty">没有数据</div>';
            return;
        }
        const { groups, data_date, updated_at } = cachedPayload;
        const minBoards = parseInt(minInput.value, 10);

        if (!groups || Object.keys(groups).length === 0) {
            container.innerHTML = '<div class="empty">该交易日暂无满足条件的连板股</div>';
            statusEl.textContent = `数据日期 ${data_date} · 更新于 ${fmtUpdated(updated_at)}`;
            return;
        }

        const keys = Object.keys(groups)
            .map((k) => parseInt(k, 10))
            .filter((n) => n >= minBoards)
            .sort((a, b) => b - a);

        let total = 0;
        for (const n of keys) {
            const stocks = groups[String(n)];
            total += stocks.length;
            const group = document.createElement("div");
            group.className = "group";

            const header = document.createElement("div");
            header.className = "group-header";
            header.innerHTML = `
                <div class="group-title">${n} 连板</div>
                <div class="group-count">${stocks.length} 只</div>
            `;
            group.appendChild(header);

            const cards = document.createElement("div");
            cards.className = "cards";
            for (const s of stocks) cards.appendChild(renderCard(s));
            group.appendChild(cards);
            container.appendChild(group);
        }

        if (total === 0) {
            container.innerHTML = '<div class="empty">该条件下没有股票</div>';
        }

        statusEl.textContent = `共 ${total} 只 · 数据日期 ${data_date} · 更新于 ${fmtUpdated(updated_at)}`;
    }

    async function load() {
        statusEl.textContent = "加载中...";
        refreshBtn.disabled = true;
        container.innerHTML = '<div class="empty">加载中...</div>';

        try {
            // 加时间戳防缓存
            const url = `data/boards.json?t=${Date.now()}`;
            const resp = await fetch(url, { cache: "no-store" });
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }
            cachedPayload = await resp.json();
            render();
        } catch (e) {
            container.innerHTML = `<div class="error">加载失败: ${e.message}<br>数据可能还没生成。请稍后刷新，或检查 GitHub Actions 是否已成功运行。</div>`;
            statusEl.textContent = "失败";
        } finally {
            refreshBtn.disabled = false;
        }
    }

    refreshBtn.addEventListener("click", load);
    minInput.addEventListener("change", render);

    load();
})();
