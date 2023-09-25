document.addEventListener("DOMContentLoaded", function () {
    let currentWeek = 0; // Initialize the current week to Week 1
    let data = []; // Initialize the API data to an empty array

    // Fetch game data from JSON file
    fetch("http://127.0.0.1:3000/api/data")
        .then(response => response.json())
        .then(api_data => {
            data = api_data;
            generateTabs(data.length);
            displayGames(data, currentWeek);
            updateTabStyles(currentWeek);
        })
        .catch(error => console.error("Error fetching data:", error));

    // Function to display games for a specific week
    function displayGames(data, weekIndex) {
        const weeks = data;
        const weekList = document.getElementById("weeks");
        weekList.innerHTML = ""; // Clear previous content

        const week = weeks[weekIndex];
        const weekDiv = document.createElement("div");
        weekDiv.classList.add("week");

        //const weekNumber = document.createElement("p");
        //weekNumber.textContent = "Week Number: " + week["Num"];
        //weekDiv.appendChild(weekNumber);

        const gamesContainer = document.createElement("div");
        gamesContainer.classList.add("games-container");

        week["Games"].forEach(game => {
            const gameDiv = document.createElement("div");
            gameDiv.classList.add("game");

            const gameInfo = document.createElement("p");
            gameInfo.classList.add("game-info");
            gameInfo.textContent = `${game["Home"]} Vs ${game["Away"]}`;
            gameDiv.appendChild(gameInfo);

            const scores = document.createElement("p");
            scores.classList.add("scores");
            scores.innerHTML = `
                <span class="home-score">${game["Home Score"]}</span>
                <span class="away-score">${game["Away Score"]}</span>
            `;
            gameDiv.appendChild(scores);

            const betInfo = document.createElement("p");
            betInfo.classList.add("bet-info");
            betInfo.innerHTML = `
                <span class="spread">Spread: ${game["Spread"]}</span>
                <span class="algo">Algo: ${game["Prediction"]}</span>
            `;
            gameDiv.appendChild(betInfo);
            gameDiv.style.backgroundColor = "#555";

            /*  if prediction is positive that means away team is favored by that amount of points
                if prediction is negative that means home team is favored by that amount of points
                to cover the spread, the favored team must win by more than the spread
                the algo is predicting how many points the favored team will win by
                if the abs of the algo is greater than the abs of the spread we should bet that we cover the spread
            */
            if (parseInt(game["Home Score"]) === 0 && parseInt(game["Away Score"]) === 0) {
                //prediction phase
                //if difference between algo and spread is greater than 4, set game to yellow
                if (Math.abs(game["Prediction"]) > Math.abs(game["Spread"])) {
                    gameDiv.style.backgroundColor = "#ffc107";
                    gameDiv.style.borderColor = "#d8a702";
                }
            }
            else if (game["Success"]) {
                //green tint for success
                gameDiv.style.backgroundColor = "#008000"
                gameDiv.style.borderColor = "#006400"
            } 
            else if (!game["Success"]) {
                //red tint for failure
                gameDiv.style.backgroundColor = "#b52b27";
                gameDiv.style.borderColor = "#8c2723";
            }

            gamesContainer.appendChild(gameDiv);
        });

        weekDiv.appendChild(gamesContainer);
        weekList.appendChild(weekDiv);
    }

    // Function to switch between weeks
    function showWeek(weekIndex) {
        currentWeek = weekIndex;
        displayGames(data, currentWeek);
        updateTabStyles(currentWeek);
    }

    // Function to update tab styles based on the current week
    function updateTabStyles(currentIndex) {
        const tabButtons = document.querySelectorAll(".tab-btn");

        tabButtons.forEach((button, index) => {
            if (index === currentIndex) {
                button.classList.add("active");
            } else {
                button.classList.remove("active");
            }
        });
    }

    function generateTabs(numTabs) {
        const tabs = document.getElementById("tabs");
        tabs.innerHTML = ""; // Clear previous content

        for (let i = 0; i < numTabs; i++) {
            const tab = document.createElement("button");
            tab.classList.add("tab-btn");
            tab.textContent = "Week " + (i + 1);
            tab.addEventListener("click", () => showWeek(i));
            tabs.appendChild(tab);
        }
    }
});
