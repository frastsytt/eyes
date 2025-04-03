document.addEventListener('DOMContentLoaded', function () {

    var timestampElements = document.querySelector('.news-date');

    if (timestampElements) {
        var dateStr = timestampElements.textContent.trim()
        var isoString = dateStr.replace(' ', 'T') + 'Z';
        var dateObj = new Date(isoString);
        if (!isNaN(dateObj.getTime())) {
            var formattedDate = dateObj.toLocaleString();
            timestampElements.innerHTML = formattedDate;
        }
    }
});