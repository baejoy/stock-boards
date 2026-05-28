(function () {
    const dateInput = document.getElementById("date-input");
    const minInput = document.getElementById("min-input");
    const refreshBtn = document.getElementById("refresh-btn");
    const statusEl = document.getElementById("status");
    const container = document.getElementById("board-container");

    function todayStr() {
        const d = new Date();
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
    }

    function toApiDate(s) {
        return s.replace(/-/g, "");
    }

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
                <span class="label">封板时间</span>
                <span class="val">${s.first_seal || "-"}</span>
            </div>
            <div class="card-row">
                <span class="label">炸板次数</span>
                <span class="val">${s.break_times}</span>
            </div>
            ${s.industry ? `<div class="card-industry">${s.industry}</div>` : ""}
            <div class="card-links">
                <a href="${s.eastmoney_url}" target="_blank" rel="noopener">东方财富</a>
                <a href="${s.ths_url}" target="_blank" rel="noopener">同花顺</a>
                <a href="${s.xueqiu_url}" target="_blank" rel="noopener">雪球</a>
            </div>
        `;
        // 卡片整体点击默认跳东财
        card.addEventListener("click", (e) => {
            if (e.target.tagName === "A") return;
            window.open(s.eastmoney_url, "_blank", "noopener");
        });
        return card;
    }

    function renderGroups(payload) {
        container.innerHTML = "";
        const { groups, total, data_date, requested_date } = payload;

        if (data_date !== requested_date) {
            const tip = document.createElement("div");
            tip.className = "empty";
            tip.style.padding = "10px";
            tip.innerHTML = `请求日期 ${requested_date} 无数据，已回溯到最近的交易日 <b>${data_date}</b>`;
            container.appendChild(tip);
        }

        if (!groups || Object.keys(groups).length === 0) {
            const empty = document.createElement("div");
            empty.className = "empty";
            empty.textContent = "该日期没有满足条件的连板股";
            container.appendChild(empty);
            return;
        }

        const keys = Object.keys(groups).sort((a, b) => parseInt(b) - parseInt(a));
        for (const k of keys) {
            const stocks = groups[k];
            const group = document.createElement("div");
            group.className = "group";

            const header = document.createElement("div");
            header.className = "group-header";
            header.innerHTML = `
                <div class="group-title">${k} 连板</div>
                <div class="group-count">${stocks.length} 只</div>
            `;
            group.appendChild(header);

            const cards = document.createElement("div");
            cards.className = "cards";
            for (const s of stocks) {
                cards.appendChild(renderCard(s));
            }
            group.appendChild(cards);
            container.appendChild(group);
        }

        statusEl.textContent = `共 ${total} 只 · 数据日期 ${data_date}`;
    }

    async function load() {
        const date = toApiDate(dateInput.value || todayStr());
        const min = minInput.value;
        statusEl.textContent = "加载中...";
        refreshBtn.disabled = true;
        container.innerHTML = '<div class="empty">加载中，第一次拉取可能需要几秒...</div>';

        try {
            const resp = await fetch(`/api/boards?date=${date}&min=${min}`);
            const json = await resp.json();
            if (!json.ok) {
                container.innerHTML = `<div class="error">接口出错: ${json.error}</div>`;
                statusEl.textContent = "失败";
                return;
            }
            renderGroups(json);
        } catch (e) {
            container.innerHTML = `<div class="error">网络错误: ${e.message}</div>`;
            statusEl.textContent = "失败";
        } finally {
            refreshBtn.disabled = false;
        }
    }

    dateInput.value = todayStr();
    refreshBtn.addEventListener("click", load);
    dateInput.addEventListener("change", load);
    minInput.addEventListener("change", load);

    load();
})();
