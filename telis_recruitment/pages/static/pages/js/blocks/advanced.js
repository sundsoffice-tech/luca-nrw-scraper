/**
 * Advanced Blocks for GrapesJS Builder
 * Includes: Google Maps, Video Embed, Social Media Icons, Icon Box
 */

export default function loadAdvancedBlocks(editor) {
    const blockManager = editor.BlockManager;

    // Google Maps Embed
    blockManager.add('google-maps', {
        label: '🗺️ Google Maps',
        category: 'Advanced',
        content: `
            <div class="map-container" style="width: 100%; height: 400px; margin: 20px 0;">
                <iframe 
                    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2428.4092366996424!2d13.404953999999999!3d52.520008!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47a851c655f20989%3A0x26bbfb4e84674c63!2sBrandenburger%20Tor!5e0!3m2!1sde!2sde!4v1234567890123!5m2!1sde!2sde" 
                    width="100%" 
                    height="100%" 
                    style="border:0;" 
                    allowfullscreen="" 
                    loading="lazy" 
                    referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            </div>
        `,
        attributes: { class: 'gjs-block-section' }
    });

    // Video Embed (YouTube/Vimeo)
    blockManager.add('video-embed', {
        label: '🎥 Video',
        category: 'Advanced',
        content: `
            <div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin: 20px 0;">
                <iframe 
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                    src="https://www.youtube.com/embed/dQw4w9WgXcQ" 
                    title="YouTube video player" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
        `,
        attributes: { class: 'gjs-block-section' }
    });

    // Social Media Icons
    blockManager.add('social-icons', {
        label: '👥 Social Icons',
        category: 'Advanced',
        content: `
            <div class="social-icons" style="display: flex; gap: 15px; justify-content: center; align-items: center; margin: 30px 0;">
                <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background-color: #1877f2; color: white; border-radius: 50%; text-decoration: none; font-size: 20px; transition: all 0.3s;">
                    <span>f</span>
                </a>
                <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white; border-radius: 50%; text-decoration: none; font-size: 20px; transition: all 0.3s;">
                    <span>📷</span>
                </a>
                <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background-color: #0077b5; color: white; border-radius: 50%; text-decoration: none; font-size: 20px; transition: all 0.3s;">
                    <span>in</span>
                </a>
                <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background-color: #1da1f2; color: white; border-radius: 50%; text-decoration: none; font-size: 20px; transition: all 0.3s;">
                    <span>🐦</span>
                </a>
            </div>
        `,
        attributes: { class: 'gjs-block-section' }
    });

    // Icon Box
    blockManager.add('icon-box', {
        label: '📦 Icon Box',
        category: 'Advanced',
        content: `
            <div class="icon-box" style="text-align: center; padding: 30px; background-color: #f8f9fa; border-radius: 8px; margin: 20px 0;">
                <div class="icon" style="font-size: 48px; margin-bottom: 15px; color: var(--brand-primary, #007bff);">
                    ✨
                </div>
                <h3 style="font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529); margin-bottom: 10px; font-size: 24px;">
                    Feature Title
                </h3>
                <p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.6;">
                    Short description of this feature or benefit.
                </p>
            </div>
        `,
        attributes: { class: 'gjs-block-section' }
    });
}
