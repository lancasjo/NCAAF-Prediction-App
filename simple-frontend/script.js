document.addEventListener("DOMContentLoaded", function () {
    let currentWeek = 0; // Initialize the current week to Week 1
    let data = []; // Initialize the API data to an empty array

    // Fetch game data from JSON file
    fetch("https://api.ncaaf-betting.papadman.app/api/data")
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
        //create 2 sections, one for the games that satisfy difference(game["Prediction"], game["Spread"]) > 4 and one for the games that don't
        //if the game satisfies the condition, add it to the first section, if not add it to the second section

        const weekCorrect = document.createElement("p");
        const betongamesHeader = document.createElement("h2");
        betongamesHeader.textContent = "Good Bets";
        const betongamesContainer = document.createElement("div");
        betongamesContainer.classList.add("games-container");


        const nobetgamesHeader = document.createElement("h2");
        nobetgamesHeader.textContent = "Other Analysis";
        const nobetgamesContainer = document.createElement("div");
        nobetgamesContainer.classList.add("games-container");

        
        var correct_count = 0;

        week["Games"].forEach(game => {
            const betOnThisGame = difference(game["Prediction"], game["Spread"]) > 4;
            const gameDiv = document.createElement("div");
            gameDiv.classList.add("game");

            gameDiv.onclick = () => window.open(`https://www.google.com/search?q=${game["Home"]}%20vs%20${game["Away"]}%20football%20game`, "_blank");
            
            const gameInfo = document.createElement("p");
            gameInfo.classList.add("game-info");
            gameInfo.textContent = `${game["Away"]} at ${game["Home"]}`;
            gameDiv.appendChild(gameInfo);

            const scores = document.createElement("p");
            scores.classList.add("scores");
            scores.innerHTML = `
                <span class="away-score">${game["Away Score"]}</span>
                <span class="home-score">${game["Home Score"]}</span>
            `;
            gameDiv.appendChild(scores);

            const betInfo = document.createElement("p");
            betInfo.classList.add("bet-info");
            game["Prediction"] = Math.round(game["Prediction"]);
            game["Prediction"] = game["Prediction"] == 0 ? "PK" : game["Prediction"]
            betInfo.innerHTML = `
                <span class="spread">Spread: ${game["Spread"] > 0 ? "+" : ""}${game["Spread"]}</span>
                <span class="algo">Algo: ${game["Prediction"] > 0 ? "+" : ""}${game["Prediction"]}</span>
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
                //if difference between algo and spread is greater than 4, set game to yellow, if not set to gray
                if (betOnThisGame) {
                    gameDiv.style.backgroundColor = "#ffc107";
                    gameDiv.style.borderColor = "#d8a702";
                }
            }
            else if (game["Success"]) {
                //green tint for success
                correct_count++;
                gameDiv.style.backgroundColor = "#008000"
                gameDiv.style.borderColor = "#006400"
            } 
            else if (!game["Success"]) {
                //red tint for failure
                gameDiv.style.backgroundColor = "#b52b27";
                gameDiv.style.borderColor = "#8c2723";
            }

            betOnThisGame ? betongamesContainer.appendChild(gameDiv) : nobetgamesContainer.appendChild(gameDiv);
        });

    
        weekCorrect.textContent = "Correct: " + correct_count + "/" + week["Games"].length;
        weekCorrect.classList.add("week-correct");
        weekDiv.appendChild(weekCorrect);
        weekDiv.appendChild(betongamesHeader);
        weekDiv.appendChild(betongamesContainer);
        weekDiv.appendChild(document.createElement("br"))
        weekDiv.appendChild(document.createElement("br"))
        weekDiv.appendChild(document.createElement("br"))
        weekDiv.appendChild(nobetgamesHeader)
        weekDiv.appendChild(nobetgamesContainer);
        weekList.appendChild(weekDiv);
    }
    correct_count = 0;

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

    function difference(a, b) {
        return Math.abs(a - b);
    }

    function xor(a, b) {
        return (a || b) && !(a && b);
    }

});
