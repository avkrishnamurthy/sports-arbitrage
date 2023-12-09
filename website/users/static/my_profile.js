
//Function to make POST request to endpoint when clicking button to set favorite bookmaker
function setFavorite(username, favoriteId) {
    fetch(`/users/${username}/bookmaker`, {
        method: "POST",
        body: JSON.stringify({ favoriteId: favoriteId }),
        }).then((_res) => {
            window.location.href = `/users/${username}`;
            });
}

function toggleDropdown() {
    document.getElementById("bookmakerDropdown").classList.toggle("show");
  }
  
  // Close the dropdown if the user clicks outside of it
  window.onclick = function(event) {
    if (!event.target.matches('.dropbtn')) {
      var dropdowns = document.getElementsByClassName("dropdown-content");
      var i;
      for (i = 0; i < dropdowns.length; i++) {
        var openDropdown = dropdowns[i];
        if (openDropdown.classList.contains('show')) {
          openDropdown.classList.remove('show');
        }
      }
    }
  }
  
  // Binding the click event to the button
  document.getElementById("dropbtn").addEventListener("click", toggleDropdown);