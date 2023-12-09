//Function to toggle follow/unfollow when visiting a different user's profile
function toggleFollow(username) {
    fetch("/follow/"+username, {
    method: "POST",
    body: JSON.stringify({ username: username }),
    }).then((_res) => {
        window.location.href = "/users/"+username;
        });
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