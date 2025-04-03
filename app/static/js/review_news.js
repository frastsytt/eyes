document.addEventListener('DOMContentLoaded', function () {
    const images = document.querySelectorAll('.admin-story-image');
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImg');
    const closeBtn = document.querySelector('.close');
    const downloadLink1 = document.getElementById('downloadLink1');
    const downloadLink2 = document.getElementById('downloadLink2');

    images.forEach(img => {
        img.addEventListener('click', () => {
            modal.style.display = 'block';

            modalImg.src = img.src;
            console.log(img.src);
            const parts = img.src.split('/');
            const filename = parts[parts.length - 1] || 'image.jpg';

            downloadLink1.href = img.src;
            downloadLink1.download = filename;
            downloadLink2.href = img.src;
            downloadLink2.download = filename;
        });
    });

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        modalImg.src = '';
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            modalImg.src = '';
        }
    });
});