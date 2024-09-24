
document.getElementById('login').addEventListener('click', function() {
    // Example AJAX call using fetch API
    document.getElementById('msgs').innerHTML = '';
    console.log('sending data');
    fetch('/ajaxkeyvalue', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 'username': document.getElementById('username').value,
                               "password": document.getElementById('password').value}),
    })
    .then(response => response.json())
    .then(data => {
      if (data.status == 'ok') {
          // Redirect to profile.html on successful login
          window.location.href = 'profile';
      } else {
        // Update the 'msgs' div with the error message
         document.getElementById('msgs').innerHTML = '<p style= "color:red;">Error: ..........</p>';
      }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
