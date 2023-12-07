function toggleFollow(username) {
    fetch("/follow/"+username, {
    method: "POST",
    body: JSON.stringify({ username: username }),
    }).then((_res) => {
        window.location.href = "/users/"+username;
        });
}