const createParticles = () => {
    const header = document.querySelector('.site-header');
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles';
    header.appendChild(particlesContainer);

    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.setProperty('--x', `${Math.random() * 100}%`);
        particle.style.setProperty('--y', `${Math.random() * 100}%`);
        particle.style.setProperty('--duration', `${Math.random() * 20 + 10}s`);
        particle.style.setProperty('--delay', `${Math.random() * 5}s`);
        particlesContainer.appendChild(particle);
    }
};

document.addEventListener('DOMContentLoaded', createParticles);