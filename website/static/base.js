function profile(username) {
    window.location.href = `/users/${username}`;
}

function handleSearchUserFormSubmit(event) {
    event.preventDefault();

    const username = document.getElementById('search-user-input').value;
    const url = '/users/' + username;

    // Make a request to the server-side check-user-exists API
    fetch('/check-user-exists', {
        method: 'POST',
        body: JSON.stringify({ username: username }),
        headers: {
        'Content-Type': 'application/json',
        },
    })
        .then(response => response.json())
        .then(data => {
        if (data.exists) {
            window.location.href = url; // Redirect to the user's profile page if that user exists
        } else {
            const errorElement = document.getElementById('search-user-error');
            errorElement.textContent = 'User does not exist';
            errorElement.classList.add('search-user-error-show'); // Show the error message element
        }
        })
        .catch(error => {
        console.error('Error:', error);
        });
    }

document.getElementById('search-user-form').addEventListener('submit', handleSearchUserFormSubmit);