
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
