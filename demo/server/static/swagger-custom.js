// Add icon to Swagger UI header
(function() {
    function addIcon() {
        // Try multiple possible selectors for different Swagger UI versions
        const selectors = [
            '.info .title',
            '.info h2.title',
            '.information-container .title',
            'hgroup.main .title',
            '.swagger-ui .info .title'
        ];

        let titleElement = null;
        for (const selector of selectors) {
            titleElement = document.querySelector(selector);
            if (titleElement) break;
        }

        if (titleElement && !titleElement.querySelector('img.i3x-icon')) {
            const icon = document.createElement('img');
	    icon.src = '/v0/static/icon.png';
            icon.alt = 'I3X';
            icon.className = 'i3x-icon';
            icon.style.cssText = 'height: 40px; margin-right: 12px; vertical-align: middle;';
            titleElement.insertBefore(icon, titleElement.firstChild);
            return true;
        }
        return false;
    }

    // Use MutationObserver to wait for Swagger UI to render
    const observer = new MutationObserver(function() {
        if (addIcon()) {
            observer.disconnect();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Also try after delays as backup
    setTimeout(addIcon, 500);
    setTimeout(addIcon, 1000);
    setTimeout(addIcon, 2000);
})();
