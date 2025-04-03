document.addEventListener('DOMContentLoaded', function () {
    var timestampElements = document.querySelectorAll('.comment-timestamp');

    timestampElements.forEach(function (el) {
        var timestampText = el.textContent.trim();
        var parts = timestampText.split(' ');
        if (parts.length === 2) {
            var datePart = parts[0];
            var timePart = parts[1];
            var dateComponents = datePart.split('.');
            if (dateComponents.length === 3) {
                var day = dateComponents[0];
                var month = dateComponents[1];
                var year = dateComponents[2];
                var isoTimestamp = year + '-' + month + '-' + day + 'T' + timePart + ':00Z';
                var date = new Date(isoTimestamp);
                if (!isNaN(date.getTime())) {
                    el.innerHTML = date.toLocaleString();
                }
            }
        }
    });

    var categoryAuthorDateElements = document.querySelector('.metadata-category p');

    if (categoryAuthorDateElements) {
        var parts = categoryAuthorDateElements.textContent.split('|');
        if (parts.length > 0) {
            var dateStr = parts[0].trim();
            var isoString = dateStr.replace(' ', 'T') + 'Z';
            var dateObj = new Date(isoString);
            if (!isNaN(dateObj.getTime())) {
                var formattedDate = dateObj.toLocaleString();
                parts[0] = formattedDate;
                categoryAuthorDateElements.innerHTML = parts.map(function (part) {
                    return part;
                }).join(' | ');
            }
        }
    }

});
