// HEAT Labs Discord Bot Page Interactions

// Initialize bot page functionality
function initBotPage() {
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add animation to stat cards when they come into view
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe stat cards for animation
    document.querySelectorAll('.stat-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Observe feature cards for animation
    document.querySelectorAll('.bot-feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Add copy functionality for command names
    document.querySelectorAll('.command-name').forEach(command => {
        command.style.cursor = 'pointer';
        command.title = 'Click to copy command';

        command.addEventListener('click', function() {
            const commandText = this.textContent;
            navigator.clipboard.writeText(commandText).then(() => {
                // Show temporary feedback
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                this.style.background = 'var(--accent-color)';
                this.style.color = 'white';

                setTimeout(() => {
                    this.textContent = originalText;
                    this.style.background = '';
                    this.style.color = '';
                }, 2000);
            });
        });
    });

    // Track button clicks for analytics
    document.querySelectorAll('.btn-invite, .btn-source').forEach(button => {
        button.addEventListener('click', function() {
            const buttonType = this.classList.contains('btn-invite') ? 'invite' : 'source';
            console.log(`HEAT Labs Bot ${buttonType} button clicked`);
            // You can add your analytics tracking here
        });
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initBotPage);

// Export for module use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initBotPage
    };
}