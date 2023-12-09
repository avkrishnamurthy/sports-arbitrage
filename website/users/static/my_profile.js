
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

  function toggleDropdownTeam() {
    document.getElementById("update-team-dropdown").classList.toggle("show");
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
  

function toggleFollowModal(username, id, whichModal) {
  fetch("/follow/"+username, {
  method: "POST",
  body: JSON.stringify({ username: username }),
  }).then((_res) => {
      const button = document.getElementById(whichModal+"-"+id.toString())
      if ((button.innerText)[0]=="U") {
        button.innerText = "Follow"
      }
      else {
        button.innerText = "Unfollow"
      }
      });
}
var firstModal = document.getElementById("myModal1");
var secondModal = document.getElementById("myModal2");

// Get buttons that open the modals
var firstBtn = document.getElementById("follower-button");
var secondBtn = document.getElementById("following-button");

var firstSpan = document.getElementsByClassName("firstClose")[0];
var secondSpan = document.getElementsByClassName("secondClose")[0];

// When the user clicks the button, open the first modal 
firstBtn.onclick = function() {
    firstModal.style.display = "block";
}

// When the user clicks the button, open the second modal 
secondBtn.onclick = function() {
    secondModal.style.display = "block";
}

firstSpan.onclick = function() {
    firstModal.style.display = "none";
    location.reload();
}

secondSpan.onclick = function() {
    secondModal.style.display = "none";
    location.reload();
}

// When the user clicks anywhere outside of the modals, close them
window.onclick = function(event) {
    if (event.target == firstModal) {
        firstModal.style.display = "none";
        location.reload();
    } else if (event.target == secondModal) {
        secondModal.style.display = "none";
        location.reload();
    }
}
  // Binding the click event to the button
  document.getElementById("dropbtn").addEventListener("click", toggleDropdown);
  document.getElementById("teambtn").addEventListener("click", toggleDropdownTeam);
