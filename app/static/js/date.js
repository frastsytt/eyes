document.addEventListener('DOMContentLoaded', function() {
    fetch('/date')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error fetching date: ${response.status}`);
            }
            return response.text();
        })
        .then(result => {
            document.querySelector('footer').innerText = `© ${result} Berylia's Eyes | All rights reserved.`;
        })
        .catch(error => {
            console.error('Error fetching date:', error);
            document.querySelector('footer').innerText = `© Berylia's Eyes | All rights reserved.`;
        });

});

// If we want another format for the date, use something like the format from bellow

// document.addEventListener('DOMContentLoaded', function() {
// fetch('/date/%25Y-%25m-%25d')
//     .then(response => {
//         if (!response.ok) {
//             throw new Error(`Error fetching date: ${response.status}`);
//         }
//         return response.text();
//     })
//     .then(result => {
//         document.querySelector('footer').innerText = `© ${result} Berylia's Eyes | All rights reserved.`;
//     })
//     .catch(error => {
//         console.error('Error fetching date:', error);
//         document.querySelector('footer').innerText = `© Berylia's Eyes | All rights reserved.`;
//     });
// });


