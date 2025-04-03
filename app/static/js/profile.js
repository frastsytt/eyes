document.addEventListener('DOMContentLoaded', function () {
    const avatarUpload = document.getElementById('avatarUpload');

    if (avatarUpload) {
        avatarUpload.addEventListener('change', function () {
            if (avatarUpload.files && avatarUpload.files.length > 0) {
                Toastify({
                    text: "Press save button to update the profile",
                    duration: 3000,
                    close: true,
                    gravity: "top",
                    position: "right",
                    background: "linear-gradient(to right, #ff5f6d, #ffc371)",
                    stopOnFocus: true
                }).showToast();
            }
        });
    }
});