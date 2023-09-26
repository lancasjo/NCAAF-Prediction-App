function searchTeam() {
    const teamName = document.getElementById("teamName").value;
    
    // Make a fetch request to the /api/teams/{team_name} endpoint
    fetch(`/api/teams/${teamName}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Team not found.");
            }
            return response.json();
        })
        .then(data => {
            // Display team data
            displayTeamData(data);
        })
        .catch(error => {
            // Handle errors
            displayErrorMessage(error.message);
        });
}

function displayTeamData(data) {
    const teamDataDiv = document.getElementById("teamData");
    teamDataDiv.innerHTML = ""; // Clear previous data
    
    // Create a div to display the team data
    const teamInfoDiv = document.createElement("div");
    teamInfoDiv.innerHTML = `<h2>${data.teamName}</h2>
                             <p>Coach: ${data.coach}</p>
                             <p>Location: ${data.location}</p>
                             <!-- Add more data fields as needed -->`;
    
    // Append the team data div to the container
    teamDataDiv.appendChild(teamInfoDiv);
}

function displayErrorMessage(message) {
    const teamDataDiv = document.getElementById("teamData");
    teamDataDiv.innerHTML = `<p>${message}</p>`;
}
