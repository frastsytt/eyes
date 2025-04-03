
document.addEventListener('DOMContentLoaded', function () {

    var timeElements = document.querySelectorAll('.meta');

    timeElements.forEach(function (el) {
        var parts = el.textContent.split('|');
        if (parts.length > 0) {
            var dateStr = parts[0].trim();
            var isoString = dateStr.replace(' ', 'T') + 'Z';
            var dateObj = new Date(isoString);
            if (!isNaN(dateObj.getTime())) {
                var formattedDate = dateObj.toLocaleString();
                parts[0] = formattedDate;
                el.innerHTML = parts.map(function (part) {
                    return part;
                }).join(' | ');
            }
        }
    });
});

