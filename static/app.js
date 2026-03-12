async function loadYears() {
    const response = await fetch("/api/years");
    const years = await response.json();

    const yearList = document.getElementById("yearList");
    yearList.innerHTML = "";

    years.forEach(yearItem => {
        const yearWrapper = document.createElement("div");
        yearWrapper.className = "year-wrapper";

        const yearRow = document.createElement("div");
        yearRow.className = "table-row year-row";

        const yearLeft = document.createElement("div");
        yearLeft.className = "cell cell-label";
        yearLeft.innerHTML = `<span class="expand-icon">▶</span> ${yearItem.year}`;

        const yearRight = document.createElement("div");
        yearRight.className = "cell cell-count";
        yearRight.textContent = yearItem.total_rows;

        yearRow.appendChild(yearLeft);
        yearRow.appendChild(yearRight);

        const monthContainer = document.createElement("div");
        monthContainer.className = "month-container";
        monthContainer.style.display = "none";

        let monthsLoaded = false;

        yearRow.addEventListener("click", async () => {
            const icon = yearLeft.querySelector(".expand-icon");

            if (monthContainer.style.display === "none") {
                if (!monthsLoaded) {
                    const monthResponse = await fetch(`/api/months?year=${encodeURIComponent(yearItem.year)}`);
                    const months = await monthResponse.json();

                    monthContainer.innerHTML = "";

                    months.forEach(monthItem => {
                        const monthWrapper = document.createElement("div");
                        monthWrapper.className = "month-wrapper";

                        const monthRow = document.createElement("div");
                        monthRow.className = "table-row month-row";

                        const monthLeft = document.createElement("div");
                        monthLeft.className = "cell cell-label";
                        monthLeft.innerHTML = `<span class="expand-icon">▶</span> ${monthItem.month}`;

                        const monthRight = document.createElement("div");
                        monthRight.className = "cell cell-count";
                        monthRight.textContent = monthItem.total_rows;

                        monthRow.appendChild(monthLeft);
                        monthRow.appendChild(monthRight);

                        const dateContainer = document.createElement("div");
                        dateContainer.className = "date-container";
                        dateContainer.style.display = "none";

                        let datesLoaded = false;

                        monthRow.addEventListener("click", async (event) => {
                            event.stopPropagation();

                            const monthIcon = monthLeft.querySelector(".expand-icon");

                            if (dateContainer.style.display === "none") {
                                if (!datesLoaded) {
                                    const dateResponse = await fetch(`/api/dates?month=${encodeURIComponent(monthItem.month)}`);
                                    const dates = await dateResponse.json();

                                    dateContainer.innerHTML = "";

                                    dates.forEach(dateItem => {
                                        const dateRow = document.createElement("div");
                                        dateRow.className = "table-row date-row";

                                        const dateLeft = document.createElement("div");
                                        dateLeft.className = "cell cell-label";
                                        dateLeft.textContent = dateItem.date;

                                        const dateRight = document.createElement("div");
                                        dateRight.className = "cell cell-count";
                                        dateRight.textContent = dateItem.total_rows;

                                        dateRow.appendChild(dateLeft);
                                        dateRow.appendChild(dateRight);

                                        dateContainer.appendChild(dateRow);
                                    });

                                    datesLoaded = true;
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
                }

                monthContainer.style.display = "block";
                icon.textContent = "▼";
            } else {
                monthContainer.style.display = "none";
                icon.textContent = "▶";
            }
        });

        yearWrapper.appendChild(yearRow);
        yearWrapper.appendChild(monthContainer);
        yearList.appendChild(yearWrapper);
    });
}

loadYears();