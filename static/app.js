async function loadNames() {
    const response = await fetch("/api/names");
    const names = await response.json();

    const yearList = document.getElementById("yearList");
    yearList.innerHTML = "";

    names.forEach(nameItem => {
        const nameWrapper = document.createElement("div");
        nameWrapper.className = "year-wrapper";

        const nameRow = document.createElement("div");
        nameRow.className = "table-row year-row";

        const nameLeft = document.createElement("div");
        nameLeft.className = "cell cell-label";
        nameLeft.innerHTML = `<span class="expand-icon">▶</span> ${nameItem.NAME}`;

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
                    const yearResponse = await fetch(
                        `/api/years?name=${encodeURIComponent(nameItem.NAME)}`
                    );
                    const years = await yearResponse.json();

                    yearContainer.innerHTML = "";

                    years.forEach(yearItem => {
                        const yearWrapper = document.createElement("div");
                        yearWrapper.className = "month-wrapper";

                        const yearRow = document.createElement("div");
                        yearRow.className = "table-row month-row";

                        const yearLeft = document.createElement("div");
                        yearLeft.className = "cell cell-label";
                        yearLeft.innerHTML = `<span class="expand-icon">▶</span> ${yearItem.year}`;

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
                                    const monthResponse = await fetch(
                                        `/api/months?name=${encodeURIComponent(nameItem.NAME)}&year=${encodeURIComponent(yearItem.year)}`
                                    );
                                    const months = await monthResponse.json();

                                    monthContainer.innerHTML = "";

                                    months.forEach(monthItem => {
                                        const monthWrapper = document.createElement("div");
                                        monthWrapper.className = "date-wrapper";

                                        const monthRow = document.createElement("div");
                                        monthRow.className = "table-row date-row";

                                        const monthLeft = document.createElement("div");
                                        monthLeft.className = "cell cell-label";
                                        monthLeft.innerHTML = `<span class="expand-icon">▶</span> ${monthItem.month}`;

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
                                                    const dateResponse = await fetch(
                                                        `/api/dates?name=${encodeURIComponent(nameItem.NAME)}&year=${encodeURIComponent(yearItem.year)}&month=${encodeURIComponent(monthItem.month_number)}`
                                                    );
                                                    const dates = await dateResponse.json();

                                                    dateContainer.innerHTML = "";

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
}

loadNames();