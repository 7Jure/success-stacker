
// Auto-hide flash messages
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('[class*="bg-red-100"], [class*="bg-green-100"]');
    messages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Dark mode toggle
    const darkModeToggle = document.getElementById('dark-mode-toggle');

    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            const html = document.documentElement;
            const isDark = html.classList.contains('dark');

            if (isDark) {
                html.classList.remove('dark');
                html.classList.add('light');
                localStorage.setItem('darkMode', 'false');
            } else {
                html.classList.remove('light');
                html.classList.add('dark');
                localStorage.setItem('darkMode', 'true');
            }
        });
    }

    // Smooth scroll to top
    window.addEventListener('scroll', function() {
        const scrollBtn = document.getElementById('scroll-to-top');
        if (scrollBtn) {
            if (window.scrollY > 300) {
                scrollBtn.classList.remove('hidden');
            } else {
                scrollBtn.classList.add('hidden');
            }
        }
    });
});
