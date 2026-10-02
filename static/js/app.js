/**
 * AlphaPulse - Stock Scanner & Trading Terminal
 * High-performance TradingView Lightweight Charts & Live Scanner
 */

// Application State
const state = {
    activeSymbol: "NVDA",
    activeTimeframe: "1d",
    activeRange: "6mo",
    swingWindow: 3,
    rsiThreshold: 50.0,
    isScanning: false,
    autoRefresh: true,
    autoRefreshTimer: null,
    eventSource: null,
    scanMatches: [],
    indicators: {
        ema20: true,
        ema50: true,
        ema200: false,
        swings: true,
        volume: true
    }
};

// Chart References
let mainChart = null;
let candleSeries = null;
let volumeSeries = null;
let ema20Series = null;
let ema50Series = null;
let ema200Series = null;

let rsiChart = null;
let rsiSeries = null;
let rsi50Line = null;
let rsi70Line = null;
let rsi30Line = null;

let cachedChartData = null;

// Search state
let searchDebounceTimer = null;
let activeSuggestionIndex = -1;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    setupEventListeners();
    setupSearchAutoComplete();
    setupAutoRefresh();

    // Load default initial stock
    loadStockChart(state.activeSymbol);
});

/**
 * Format unix timestamp to YYYY-MM-DD for daily/weekly candles
 */
function formatChartTime(unixSeconds, timeframe) {
    if (timeframe === "1h" || timeframe === "15m") {
        return unixSeconds; // Intraday uses unix seconds
    }
    const d = new Date(unixSeconds * 1000);
    const year = d.getUTCFullYear();
    const month = String(d.getUTCMonth() + 1).padStart(2, "0");
    const day = String(d.getUTCDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

/**
 * Initialize TradingView Lightweight Charts with Responsive ResizeObserver
 */
function initCharts() {
    const mainContainer = document.getElementById("mainChartContainer");
    const rsiContainer = document.getElementById("rsiChartContainer");

    const commonOptions = {
        layout: {
            background: { color: "#0b0f19" },
            textColor: "#94a3b8",
            fontSize: 11,
            fontFamily: "'JetBrains Mono', monospace"
        },
        grid: {
            vertLines: { color: "rgba(36, 48, 72, 0.4)" },
            horzLines: { color: "rgba(36, 48, 72, 0.4)" }
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: { color: "rgba(6, 182, 212, 0.5)", width: 1, style: 2 },
            horzLine: { color: "rgba(6, 182, 212, 0.5)", width: 1, style: 2 }
        },
        timeScale: {
            borderColor: "#243048",
            timeVisible: true,
            secondsVisible: false
        }
    };

    const initialWidth = mainContainer.clientWidth || 800;

    // 1. Create Main Candlestick Chart
    mainChart = LightweightCharts.createChart(mainContainer, {
        ...commonOptions,
        width: initialWidth,
        height: 420,
        rightPriceScale: {
            borderColor: "#243048",
            scaleMargins: { top: 0.1, bottom: 0.2 }
        }
    });

    candleSeries = mainChart.addCandlestickSeries({
        upColor: "#10b981",
        downColor: "#ef4444",
        borderUpColor: "#10b981",
        borderDownColor: "#ef4444",
        wickUpColor: "#10b981",
        wickDownColor: "#ef4444"
    });

    volumeSeries = mainChart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: '', // overlay
        scaleMargins: { top: 0.8, bottom: 0 }
    });

    ema20Series = mainChart.addLineSeries({
        color: '#06b6d4',
        lineWidth: 2,
        title: 'EMA 20'
    });

    ema50Series = mainChart.addLineSeries({
        color: '#f59e0b',
        lineWidth: 2,
        title: 'EMA 50'
    });

    ema200Series = mainChart.addLineSeries({
        color: '#8b5cf6',
        lineWidth: 2,
        title: 'EMA 200',
        visible: false
    });

    // 2. Create Synchronized RSI Subchart
    rsiChart = LightweightCharts.createChart(rsiContainer, {
        ...commonOptions,
        width: initialWidth,
        height: 140,
        rightPriceScale: {
            borderColor: "#243048",
            scaleMargins: { top: 0.1, bottom: 0.1 },
            autoScale: false
        }
    });

    rsiSeries = rsiChart.addLineSeries({
        color: '#10b981',
        lineWidth: 2,
        title: 'RSI(21)'
    });

    // RSI Threshold Guide Lines
    rsi50Line = rsiSeries.createPriceLine({
        price: 50.0,
        color: 'rgba(16, 185, 129, 0.8)',
        lineWidth: 1.5,
        lineStyle: LightweightCharts.LineStyle.Solid,
        axisLabelVisible: true,
        title: '50 Bullish Midline'
    });

    rsi70Line = rsiSeries.createPriceLine({
        price: 70.0,
        color: 'rgba(239, 68, 68, 0.6)',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: '70 Overbought'
    });

    rsi30Line = rsiSeries.createPriceLine({
        price: 30.0,
        color: 'rgba(6, 182, 212, 0.6)',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: '30 Oversold'
    });

    // Synchronize Time Scales between Main & RSI charts
    mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (range) rsiChart.timeScale().setVisibleLogicalRange(range);
    });

    rsiChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (range) mainChart.timeScale().setVisibleLogicalRange(range);
    });

    // Dynamic ResizeObserver ensures crisp 100% responsive display
    const resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
            const width = entry.contentRect.width;
            if (width > 0) {
                if (mainChart) mainChart.applyOptions({ width });
                if (rsiChart) rsiChart.applyOptions({ width });
            }
        }
    });
    resizeObserver.observe(mainContainer);
}

/**
 * Fetch and Render Chart Data for a specific ticker
 */
async function loadStockChart(symbol, isSilentRefresh = false) {
    symbol = symbol.trim().toUpperCase();
    state.activeSymbol = symbol;

    if (!isSilentRefresh) {
        document.getElementById("activeSymbol").innerText = symbol;
        document.getElementById("activeTrendBadge").innerText = "LOADING DATA...";
        document.getElementById("activeTrendBadge").className = "trend-badge";
    }

    try {
        const url = `/api/chart/${encodeURIComponent(symbol)}?timeframe=${state.activeTimeframe}&range_param=${state.activeRange}&rsi_period=21&swing_window=${state.swingWindow}`;
        const res = await fetch(url);
        if (!res.ok) {
            const err = await res.json();
            showToast(err.detail || "Error loading stock data");
            return;
        }

        const data = await res.json();
        cachedChartData = data;
        renderChartData(data, isSilentRefresh);
        renderDiagnosis(data.analysis, data.meta);

        // Flash live tick indicator
        const tick = document.getElementById("lastUpdatedTick");
        if (tick) {
            tick.style.display = "inline";
            tick.innerText = `● ${new Date().toLocaleTimeString()}`;
        }

    } catch (err) {
        console.error("Error loading chart:", err);
        if (!isSilentRefresh) showToast(`Failed to load ${symbol}`);
    }
}

/**
 * Render OHLCV, EMAs, RSI, and Swing Markers on Charts
 */
function renderChartData(data, isSilentRefresh = false) {
    if (!data.candles || data.candles.length === 0) return;

    const tf = state.activeTimeframe;

    // Format candles with appropriate time string or number
    const formattedCandles = data.candles.map(c => ({
        ...c,
        time: formatChartTime(c.time, tf)
    }));

    const formattedVolumes = (data.volumes || []).map(v => ({
        ...v,
        time: formatChartTime(v.time, tf)
    }));

    // 1. Candlestick & Volume series
    candleSeries.setData(formattedCandles);
    volumeSeries.setData(formattedVolumes);

    // 2. EMAs
    if (data.ema_20 && data.ema_20.length > 0) {
        ema20Series.setData(data.ema_20.map(e => ({ ...e, time: formatChartTime(e.time, tf) })));
    }
    if (data.ema_50 && data.ema_50.length > 0) {
        ema50Series.setData(data.ema_50.map(e => ({ ...e, time: formatChartTime(e.time, tf) })));
    }
    if (data.ema_200 && data.ema_200.length > 0) {
        ema200Series.setData(data.ema_200.map(e => ({ ...e, time: formatChartTime(e.time, tf) })));
    }

    // 3. RSI
    if (data.rsi && data.rsi.length > 0) {
        const formattedRsi = data.rsi.map(r => ({ ...r, time: formatChartTime(r.time, tf) }));
        rsiSeries.setData(formattedRsi);

        const lastRsi = data.rsi[data.rsi.length - 1].value;
        const rsiBadge = document.getElementById("rsiCurrentValue");
        rsiBadge.innerText = lastRsi.toFixed(1);
        if (lastRsi >= 50) {
            rsiBadge.style.color = "#10b981";
            rsiSeries.applyOptions({ color: "#10b981" });
        } else {
            rsiBadge.style.color = "#ef4444";
            rsiSeries.applyOptions({ color: "#ef4444" });
        }
    }

    // 4. Swing Markers (HH & HL)
    if (state.indicators.swings && data.markers) {
        const formattedMarkers = data.markers.map(m => ({
            ...m,
            time: formatChartTime(m.time, tf)
        }));
        candleSeries.setMarkers(formattedMarkers);
    } else {
        candleSeries.setMarkers([]);
    }

    // Fit content only on initial load or symbol switch, not silent refresh
    if (!isSilentRefresh) {
        mainChart.timeScale().fitContent();
        rsiChart.timeScale().fitContent();
    }

    // Update Top Banner
    const lastCandle = data.candles[data.candles.length - 1];
    const prevCandle = data.candles.length > 1 ? data.candles[data.candles.length - 2] : lastCandle;
    const change = lastCandle.close - prevCandle.close;
    const changePct = prevCandle.close ? (change / prevCandle.close) * 100 : 0;
    const currency = data.meta.currency === "INR" ? "₹" : "$";

    document.getElementById("activePrice").innerText = `${currency}${lastCandle.close.toFixed(2)}`;
    const changeEl = document.getElementById("activeChange");
    const sign = change >= 0 ? "+" : "";
    changeEl.innerText = `${sign}${change.toFixed(2)} (${sign}${changePct.toFixed(2)}%)`;
    changeEl.className = `price-change ${change >= 0 ? "positive" : "negative"}`;

    document.getElementById("activeExchange").innerText = data.meta.exchange || (state.activeSymbol.endsWith(".NS") ? "NSE" : "US");
    document.getElementById("activeShortName").innerText = data.meta.shortName || state.activeSymbol;

    // Trend badge
    const trendEl = document.getElementById("activeTrendBadge");
    if (data.analysis.passes_scan) {
        trendEl.innerText = "MATCH: UPTREND (HH+HL & RSI>50)";
        trendEl.className = "trend-badge";
    } else {
        trendEl.innerText = data.analysis.trend_status || "STRUCTURE INCOMPLETE";
        trendEl.className = `trend-badge ${data.analysis.has_hh && data.analysis.has_hl ? "" : "bearish"}`;
    }
}

/**
 * Render Strategy Diagnosis Panel & Checklist
 */
function renderDiagnosis(a, meta) {
    const currency = meta.currency === "INR" ? "₹" : "$";

    // 1. Checklist Row: RSI(21) > 50
    const rowRsi = document.getElementById("chkRowRsi");
    const rsiDesc = document.getElementById("diagRsiDesc");
    if (a.rsi_condition) {
        rowRsi.className = "check-row";
        rowRsi.querySelector(".check-icon").innerText = "✓";
        rsiDesc.innerText = `RSI(21) is ${a.rsi_21} (Bullish > 50)`;
    } else {
        rowRsi.className = "check-row failed";
        rowRsi.querySelector(".check-icon").innerText = "✕";
        rsiDesc.innerText = `RSI(21) is ${a.rsi_21} (Below 50)`;
    }

    // 2. Higher High (HH)
    const rowHh = document.getElementById("chkRowHh");
    const hhDesc = document.getElementById("diagHhDesc");
    if (a.has_hh) {
        rowHh.className = "check-row";
        rowHh.querySelector(".check-icon").innerText = "✓";
        hhDesc.innerText = `Peak ${currency}${a.recent_high} > Prev ${currency}${a.prev_high}`;
    } else {
        rowHh.className = "check-row failed";
        rowHh.querySelector(".check-icon").innerText = "✕";
        hhDesc.innerText = `Peak ${currency}${a.recent_high} <= Prev ${currency}${a.prev_high}`;
    }

    // 3. Higher Low (HL)
    const rowHl = document.getElementById("chkRowHl");
    const hlDesc = document.getElementById("diagHlDesc");
    if (a.has_hl) {
        rowHl.className = "check-row";
        rowHl.querySelector(".check-icon").innerText = "✓";
        hlDesc.innerText = `Trough ${currency}${a.recent_low} > Prev ${currency}${a.prev_low}`;
    } else {
        rowHl.className = "check-row failed";
        rowHl.querySelector(".check-icon").innerText = "✕";
        hlDesc.innerText = `Trough ${currency}${a.recent_low} <= Prev ${currency}${a.prev_low}`;
    }

    // 4. Structure Intact
    const rowStruct = document.getElementById("chkRowStructure");
    const structDesc = document.getElementById("diagStructureDesc");
    if (a.structure_intact) {
        rowStruct.className = "check-row";
        rowStruct.querySelector(".check-icon").innerText = "✓";
        structDesc.innerText = `Price ${currency}${a.price} above Low ${currency}${a.recent_low}`;
    } else {
        rowStruct.className = "check-row failed";
        rowStruct.querySelector(".check-icon").innerText = "✕";
        structDesc.innerText = `Price broke below ${currency}${a.recent_low}`;
    }

    // Key Levels
    document.getElementById("lvlResistance").innerText = `${currency}${a.next_resistance || a.recent_high}`;
    document.getElementById("lvlSupport").innerText = `${currency}${a.recent_low}`;
    document.getElementById("lvlStopLoss").innerText = `${currency}${a.suggested_stop_loss}`;
    document.getElementById("lvlVolume").innerText = (a.volume_avg_20 || 0).toLocaleString();
    document.getElementById("lvl52w").innerText = `${currency}${a.low_52w} - ${currency}${a.high_52w}`;
}

/**
 * Setup Instant Search & Suggestions Auto-complete
 */
function setupSearchAutoComplete() {
    const input = document.getElementById("symbolInput");
    const dropdown = document.getElementById("searchSuggestions");
    const btnQuick = document.getElementById("btnQuickAnalyze");

    const fetchSuggestions = async (query) => {
        if (!query.trim()) {
            dropdown.style.display = "none";
            return;
        }

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            if (!res.ok) return;
            const data = await res.json();
            renderSuggestions(data.results || []);
        } catch (e) {
            console.error("Search fetch error:", e);
        }
    };

    const renderSuggestions = (items) => {
        if (items.length === 0) {
            dropdown.style.display = "none";
            return;
        }

        activeSuggestionIndex = -1;
        dropdown.innerHTML = "";

        items.forEach((item, idx) => {
            const div = document.createElement("div");
            div.className = "suggestion-item";
            div.dataset.index = idx;
            div.dataset.symbol = item.symbol;

            const badgeClass = item.exchange.toLowerCase();
            div.innerHTML = `
                <div class="suggestion-left">
                    <span class="suggestion-sym">${item.symbol}</span>
                    <span class="suggestion-name">${item.name}</span>
                </div>
                <div class="suggestion-right">
                    <span class="suggestion-badge ${badgeClass}">${item.exchange}</span>
                </div>
            `;

            div.addEventListener("click", () => {
                selectSuggestion(item.symbol);
            });

            dropdown.appendChild(div);
        });

        dropdown.style.display = "block";
    };

    const selectSuggestion = (symbol) => {
        input.value = symbol;
        dropdown.style.display = "none";
        loadStockChart(symbol);
    };

    // Debounced input handler
    input.addEventListener("input", (e) => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            fetchSuggestions(e.target.value);
        }, 150);
    });

    // Keyboard navigation (Arrow keys + Enter)
    input.addEventListener("keydown", (e) => {
        const items = dropdown.querySelectorAll(".suggestion-item");
        if (items.length === 0 || dropdown.style.display === "none") {
            if (e.key === "Enter") {
                const val = input.value.trim().toUpperCase();
                if (val) loadStockChart(val);
            }
            return;
        }

        if (e.key === "ArrowDown") {
            e.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex + 1) % items.length;
            highlightSuggestion(items);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex - 1 + items.length) % items.length;
            highlightSuggestion(items);
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (activeSuggestionIndex >= 0 && activeSuggestionIndex < items.length) {
                const sym = items[activeSuggestionIndex].dataset.symbol;
                selectSuggestion(sym);
            } else {
                const val = input.value.trim().toUpperCase();
                dropdown.style.display = "none";
                if (val) loadStockChart(val);
            }
        } else if (e.key === "Escape") {
            dropdown.style.display = "none";
        }
    });

    const highlightSuggestion = (items) => {
        items.forEach((it, i) => {
            it.classList.toggle("selected", i === activeSuggestionIndex);
            if (i === activeSuggestionIndex) {
                it.scrollIntoView({ block: "nearest" });
            }
        });
    };

    btnQuick.addEventListener("click", () => {
        const val = input.value.trim().toUpperCase();
        dropdown.style.display = "none";
        if (val) loadStockChart(val);
    });

    // Close dropdown on outside click
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".direct-search-box")) {
            dropdown.style.display = "none";
        }
    });
}

/**
 * Setup Live Auto-Update / Polling
 */
function setupAutoRefresh() {
    const chk = document.getElementById("chkAutoRefresh");
    state.autoRefresh = chk.checked;

    chk.addEventListener("change", (e) => {
        state.autoRefresh = e.target.checked;
        if (state.autoRefresh) {
            startAutoRefreshLoop();
            showToast("Auto-refresh enabled (every 5 seconds).");
        } else {
            clearInterval(state.autoRefreshTimer);
            state.autoRefreshTimer = null;
            showToast("Auto-refresh paused.");
        }
    });

    startAutoRefreshLoop();
}

function startAutoRefreshLoop() {
    if (state.autoRefreshTimer) clearInterval(state.autoRefreshTimer);
    state.autoRefreshTimer = setInterval(() => {
        if (state.autoRefresh && !state.isScanning) {
            loadStockChart(state.activeSymbol, true); // Silent refresh
        }
    }, 5000);
}

/**
 * Event Listeners & Scanner Controls
 */
function setupEventListeners() {
    // Universe change
    const univSelect = document.getElementById("universeSelect");
    const customGroup = document.getElementById("customTickersGroup");
    univSelect.addEventListener("change", () => {
        if (univSelect.value === "custom") {
            customGroup.style.display = "block";
        } else {
            customGroup.style.display = "none";
        }
    });

    // Timeframe buttons
    document.querySelectorAll(".tf-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            state.activeTimeframe = btn.dataset.tf;
            loadStockChart(state.activeSymbol);
        });
    });

    // Range buttons
    document.querySelectorAll(".range-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".range-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            state.activeRange = btn.dataset.range;
            loadStockChart(state.activeSymbol);
        });
    });

    // Sliders
    const rsiSlider = document.getElementById("rsiThreshold");
    const rsiVal = document.getElementById("rsiVal");
    rsiSlider.addEventListener("input", (e) => {
        rsiVal.innerText = e.target.value;
        state.rsiThreshold = parseFloat(e.target.value);
    });

    const swingSlider = document.getElementById("swingWindow");
    const swingVal = document.getElementById("swingVal");
    swingSlider.addEventListener("input", (e) => {
        swingVal.innerText = e.target.value;
        state.swingWindow = parseInt(e.target.value);
    });

    // Indicator Toggles
    document.getElementById("toggleEma20").addEventListener("click", function() {
        state.indicators.ema20 = !state.indicators.ema20;
        this.classList.toggle("active");
        ema20Series.applyOptions({ visible: state.indicators.ema20 });
    });

    document.getElementById("toggleEma50").addEventListener("click", function() {
        state.indicators.ema50 = !state.indicators.ema50;
        this.classList.toggle("active");
        ema50Series.applyOptions({ visible: state.indicators.ema50 });
    });

    document.getElementById("toggleEma200").addEventListener("click", function() {
        state.indicators.ema200 = !state.indicators.ema200;
        this.classList.toggle("active");
        ema200Series.applyOptions({ visible: state.indicators.ema200 });
    });

    document.getElementById("toggleSwings").addEventListener("click", function() {
        state.indicators.swings = !state.indicators.swings;
        this.classList.toggle("active");
        if (state.indicators.swings && cachedChartData && cachedChartData.markers) {
            const tf = state.activeTimeframe;
            candleSeries.setMarkers(cachedChartData.markers.map(m => ({ ...m, time: formatChartTime(m.time, tf) })));
        } else {
            candleSeries.setMarkers([]);
        }
    });

    // Scanner Buttons
    document.getElementById("btnStartScan").addEventListener("click", startScan);
    document.getElementById("btnStopScan").addEventListener("click", stopScan);

    // Table Filter
    document.getElementById("tableFilterInput").addEventListener("input", (e) => {
        filterResultsTable(e.target.value);
    });

    // Copy Symbols & Export CSV
    document.getElementById("btnCopySymbols").addEventListener("click", copySymbolsToClipboard);
    document.getElementById("btnExportCsv").addEventListener("click", exportCsv);
}

/**
 * Start Live Multithreaded Scanner via Server-Sent Events (SSE)
 */
function startScan() {
    if (state.isScanning) return;

    const universe = document.getElementById("universeSelect").value;
    const customSymbols = document.getElementById("customTickersInput").value;

    state.isScanning = true;
    state.scanMatches = [];

    // UI state
    document.getElementById("btnStartScan").disabled = true;
    document.getElementById("btnStopScan").disabled = false;
    document.getElementById("progressBarFill").style.width = "0%";
    document.getElementById("scanStatusText").innerText = "Initializing scan...";
    document.getElementById("matchCountBadge").innerText = "0 Stocks Found";

    // Clear previous results table
    const tbody = document.getElementById("resultsTableBody");
    tbody.innerHTML = `
        <tr class="empty-row">
            <td colspan="8">
                <div class="empty-state">
                    <span class="empty-icon">⏳</span>
                    <p>Scanning in real-time... Stocks meeting HH + HL & RSI(21) > ${state.rsiThreshold} will populate below.</p>
                </div>
            </td>
        </tr>
    `;

    const params = new URLSearchParams({
        universe: universe,
        timeframe: state.activeTimeframe,
        rsi_period: 21,
        rsi_threshold: state.rsiThreshold,
        swing_window: state.swingWindow
    });
    if (universe === "custom" && customSymbols) {
        params.append("custom_symbols", customSymbols);
    }

    state.eventSource = new EventSource(`/api/scan/stream?${params.toString()}`);

    state.eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.event === "start") {
                document.getElementById("scanStatusText").innerText = `Scanning 0 of ${data.total}...`;
                document.getElementById("scanProgressCount").innerText = `0 / ${data.total}`;
            }
            else if (data.event === "progress") {
                const pct = Math.round((data.scanned / data.total) * 100);
                document.getElementById("progressBarFill").style.width = `${pct}%`;
                document.getElementById("scanStatusText").innerText = `Scanning: ${data.current_symbol} (${pct}%)`;
                document.getElementById("scanProgressCount").innerText = `${data.scanned} / ${data.total}`;

                if (data.is_match) {
                    addMatchToTable(data.stock);
                }
            }
            else if (data.event === "complete") {
                stopScan();
                document.getElementById("progressBarFill").style.width = "100%";
                document.getElementById("scanStatusText").innerText = `Completed in ${data.elapsed_seconds}s!`;
                showToast(`Scan complete! Found ${data.matches_count} matching stocks.`);
            }
        } catch (e) {
            console.error("SSE parse error:", e);
        }
    };

    state.eventSource.onerror = (err) => {
        console.error("SSE error:", err);
        stopScan();
        showToast("Scan finished or stream closed.");
    };
}

/**
 * Stop active scan
 */
function stopScan() {
    state.isScanning = false;
    if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
    }
    document.getElementById("btnStartScan").disabled = false;
    document.getElementById("btnStopScan").disabled = true;
}

/**
 * Add a matched stock row dynamically into results table
 */
function addMatchToTable(stock) {
    const tbody = document.getElementById("resultsTableBody");

    const emptyRow = tbody.querySelector(".empty-row");
    if (emptyRow) {
        tbody.innerHTML = "";
    }

    state.scanMatches.push(stock);
    document.getElementById("matchCountBadge").innerText = `${state.scanMatches.length} Stocks Found`;

    const currency = stock.currency === "INR" ? "₹" : "$";
    const changeClass = stock.change_pct >= 0 ? "positive" : "negative";
    const sign = stock.change_pct >= 0 ? "+" : "";

    const tr = document.createElement("tr");
    tr.dataset.symbol = stock.symbol;
    tr.innerHTML = `
        <td class="ticker-cell" onclick="loadStockChart('${stock.symbol}')">${stock.symbol}</td>
        <td class="mono-cell">${currency}${stock.price.toFixed(2)}</td>
        <td class="mono-cell ${changeClass}">${sign}${stock.change_pct.toFixed(2)}%</td>
        <td class="mono-cell" style="color: #10b981; font-weight: 700;">${stock.rsi_21.toFixed(1)}</td>
        <td class="mono-cell">${currency}${stock.recent_high} <span style="color:#10b981; font-size:0.7rem;">(HH)</span></td>
        <td class="mono-cell">${currency}${stock.recent_low} <span style="color:#06b6d4; font-size:0.7rem;">(HL)</span></td>
        <td><span class="status-badge-match">✓ HH + HL + RSI>50</span></td>
        <td>
            <button class="btn-view-chart" onclick="loadStockChart('${stock.symbol}')">View Chart</button>
        </td>
    `;
    tbody.appendChild(tr);
}

/**
 * Filter results table by text
 */
function filterResultsTable(query) {
    const q = query.trim().toUpperCase();
    const rows = document.querySelectorAll("#resultsTableBody tr:not(.empty-row)");
    rows.forEach(r => {
        const sym = r.dataset.symbol || "";
        r.style.display = sym.includes(q) ? "" : "none";
    });
}

/**
 * Copy all matched symbols to clipboard
 */
function copySymbolsToClipboard() {
    if (state.scanMatches.length === 0) {
        showToast("No matched stocks to copy.");
        return;
    }
    const symbols = state.scanMatches.map(s => s.symbol).join(", ");
    navigator.clipboard.writeText(symbols).then(() => {
        showToast(`Copied ${state.scanMatches.length} symbols to clipboard!`);
    });
}

/**
 * Export results as CSV file
 */
function exportCsv() {
    if (state.scanMatches.length === 0) {
        showToast("No scan results to export.");
        return;
    }

    const headers = ["Symbol", "Price", "Change %", "RSI(21)", "Recent High (HH)", "Recent Low (HL)", "Stop Loss", "Volume"];
    const rows = state.scanMatches.map(s => [
        s.symbol,
        s.price,
        s.change_pct,
        s.rsi_21,
        s.recent_high,
        s.recent_low,
        s.suggested_stop_loss,
        s.volume
    ]);

    let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n" + rows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `AlphaPulse_Scan_HH_HL_RSI_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("CSV exported successfully!");
}

/**
 * Show Toast Notification
 */
function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3500);
}
