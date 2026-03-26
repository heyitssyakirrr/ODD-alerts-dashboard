function createExpandLabel(text) {
    return `<span class="expand-icon">▶</span> ${text}`;
}

function createErrorRow(message) {
    const row = document.createElement("div");
    row.className = "table-row day-row";

    const left = document.createElement("div");
    left.className = "cell cell-label";
    left.textContent = message;

    const right = document.createElement("div");
    right.className = "cell cell-count";
    right.textContent = "-";

    row.appendChild(left);
    row.appendChild(right);
    return row;
}

async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
}

async function loadNames() {
    const yearList = document.getElementById("yearList");
    if (!yearList) return;

    yearList.innerHTML = `<div class="table-row"><div class="cell cell-label">Loading...</div><div class="cell cell-count">-</div></div>`;

    try {
        const names = await fetchJson("/api/names");
        yearList.innerHTML = "";

        names.forEach(nameItem => {
            const nameWrapper = document.createElement("div");
            nameWrapper.className = "year-wrapper";

            const nameRow = document.createElement("div");
            nameRow.className = "table-row year-row";

            const nameLeft = document.createElement("div");
            nameLeft.className = "cell cell-label";
            nameLeft.innerHTML = createExpandLabel(nameItem.NAME);

            const nameRight = document.createElement("div");
            nameRight.className = "cell cell-count";
            nameRight.textContent = Number(nameItem.total_count).toLocaleString();

            nameRow.appendChild(nameLeft);
            nameRow.appendChild(nameRight);

            const yearContainer = document.createElement("div");
            yearContainer.className = "month-container";
            yearContainer.style.display = "none";

            let yearsLoaded = false;

            nameRow.addEventListener("click", async () => {
                const icon = nameLeft.querySelector(".expand-icon");

                if (yearContainer.style.display === "none") {
                    if (!yearsLoaded) {
                        try {
                            yearContainer.innerHTML = "";
                            const years = await fetchJson(`/api/years?name=${encodeURIComponent(nameItem.NAME)}`);

                            years.forEach(yearItem => {
                                const yearWrapper = document.createElement("div");
                                yearWrapper.className = "month-wrapper";

                                const yearRow = document.createElement("div");
                                yearRow.className = "table-row month-row";

                                const yearLeft = document.createElement("div");
                                yearLeft.className = "cell cell-label";
                                yearLeft.innerHTML = createExpandLabel(yearItem.year);

                                const yearRight = document.createElement("div");
                                yearRight.className = "cell cell-count";
                                yearRight.textContent = Number(yearItem.total_count).toLocaleString();

                                yearRow.appendChild(yearLeft);
                                yearRow.appendChild(yearRight);

                                const monthContainer = document.createElement("div");
                                monthContainer.className = "date-container";
                                monthContainer.style.display = "none";

                                let monthsLoaded = false;

                                yearRow.addEventListener("click", async (event) => {
                                    event.stopPropagation();
                                    const yearIcon = yearLeft.querySelector(".expand-icon");

                                    if (monthContainer.style.display === "none") {
                                        if (!monthsLoaded) {
                                            try {
                                                monthContainer.innerHTML = "";
                                                const months = await fetchJson(`/api/months?name=${encodeURIComponent(nameItem.NAME)}&year=${encodeURIComponent(yearItem.year)}`);

                                                months.forEach(monthItem => {
                                                    const monthWrapper = document.createElement("div");
                                                    monthWrapper.className = "date-wrapper";

                                                    const monthRow = document.createElement("div");
                                                    monthRow.className = "table-row date-row";

                                                    const monthLeft = document.createElement("div");
                                                    monthLeft.className = "cell cell-label";
                                                    monthLeft.innerHTML = createExpandLabel(monthItem.month);

                                                    const monthRight = document.createElement("div");
                                                    monthRight.className = "cell cell-count";
                                                    monthRight.textContent = Number(monthItem.total_count).toLocaleString();

                                                    monthRow.appendChild(monthLeft);
                                                    monthRow.appendChild(monthRight);

                                                    const dateContainer = document.createElement("div");
                                                    dateContainer.className = "day-container";
                                                    dateContainer.style.display = "none";

                                                    let datesLoaded = false;

                                                    monthRow.addEventListener("click", async (event) => {
                                                        event.stopPropagation();
                                                        const monthIcon = monthLeft.querySelector(".expand-icon");

                                                        if (dateContainer.style.display === "none") {
                                                            if (!datesLoaded) {
                                                                try {
                                                                    dateContainer.innerHTML = "";
                                                                    const dates = await fetchJson(`/api/dates?name=${encodeURIComponent(nameItem.NAME)}&year=${encodeURIComponent(yearItem.year)}&month=${encodeURIComponent(monthItem.month_number)}`);

                                                                    if (dates.length === 0) {
                                                                        dateContainer.appendChild(createErrorRow("No daily data available"));
                                                                    } else {
                                                                        dates.forEach(dateItem => {
                                                                            const dateRow = document.createElement("div");
                                                                            dateRow.className = "table-row day-row";

                                                                            const dateLeft = document.createElement("div");
                                                                            dateLeft.className = "cell cell-label";
                                                                            dateLeft.textContent = dateItem.date;

                                                                            const dateRight = document.createElement("div");
                                                                            dateRight.className = "cell cell-count";
                                                                            dateRight.textContent = Number(dateItem.total_count).toLocaleString();

                                                                            dateRow.appendChild(dateLeft);
                                                                            dateRow.appendChild(dateRight);
                                                                            dateContainer.appendChild(dateRow);
                                                                        });
                                                                    }

                                                                    datesLoaded = true;
                                                                } catch (error) {
                                                                    dateContainer.innerHTML = "";
                                                                    dateContainer.appendChild(createErrorRow("Failed to load daily data"));
                                                                }
                                                            }

                                                            dateContainer.style.display = "block";
                                                            monthIcon.textContent = "▼";
                                                        } else {
                                                            dateContainer.style.display = "none";
                                                            monthIcon.textContent = "▶";
                                                        }
                                                    });

                                                    monthWrapper.appendChild(monthRow);
                                                    monthWrapper.appendChild(dateContainer);
                                                    monthContainer.appendChild(monthWrapper);
                                                });

                                                monthsLoaded = true;
                                            } catch (error) {
                                                monthContainer.innerHTML = "";
                                                monthContainer.appendChild(createErrorRow("Failed to load months"));
                                            }
                                        }

                                        monthContainer.style.display = "block";
                                        yearIcon.textContent = "▼";
                                    } else {
                                        monthContainer.style.display = "none";
                                        yearIcon.textContent = "▶";
                                    }
                                });

                                yearWrapper.appendChild(yearRow);
                                yearWrapper.appendChild(monthContainer);
                                yearContainer.appendChild(yearWrapper);
                            });

                            yearsLoaded = true;
                        } catch (error) {
                            yearContainer.innerHTML = "";
                            yearContainer.appendChild(createErrorRow("Failed to load years"));
                        }
                    }

                    yearContainer.style.display = "block";
                    icon.textContent = "▼";
                } else {
                    yearContainer.style.display = "none";
                    icon.textContent = "▶";
                }
            });

            nameWrapper.appendChild(nameRow);
            nameWrapper.appendChild(yearContainer);
            yearList.appendChild(nameWrapper);
        });
    } catch (error) {
        yearList.innerHTML = "";
        yearList.appendChild(createErrorRow("Failed to load names"));
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("yearList")) {
        loadNames();
    }
});