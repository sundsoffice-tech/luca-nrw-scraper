/**
 * Custom LUCA blocks for GrapesJS landing page builder
 * 
 * Custom blocks:
 * - Lead Form (with Brevo list opt-in)
 * - Stats Counter
 * - Testimonials
 */

// This file can be loaded in the builder to register custom blocks

(function(grapesjs) {
    // Lead Form Block
    grapesjs.BlockManager.add('lead-form', {
        label: 'Lead Form',
        category: 'LUCA Custom',
        content: `
            <form data-landing-form class="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
                <h3 class="text-2xl font-bold mb-4 text-gray-800">Jetzt Kontakt aufnehmen</h3>
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="name">
                        Name *
                    </label>
                    <input 
                        type="text" 
                        id="name" 
                        name="name" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="Ihr Name"
                    >
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                        E-Mail *
                    </label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="ihre@email.de"
                    >
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="phone">
                        Telefon
                    </label>
                    <input 
                        type="tel" 
                        id="phone" 
                        name="phone"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="+49 123 456789"
                    >
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="message">
                        Nachricht
                    </label>
                    <textarea 
                        id="message" 
                        name="message" 
                        rows="4"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="Ihre Nachricht..."
                    ></textarea>
                </div>
                <div class="mb-4">
                    <label class="flex items-center">
                        <input type="checkbox" name="newsletter" value="1" class="mr-2">
                        <span class="text-sm text-gray-600">Ich möchte den Newsletter erhalten</span>
                    </label>
                </div>
                <button 
                    type="submit"
                    class="w-full bg-cyan-500 text-white font-bold py-3 px-4 rounded-md hover:bg-cyan-600 transition duration-300"
                >
                    Absenden
                </button>
            </form>
        `,
        attributes: {
            class: 'fa fa-wpforms'
        }
    });

    // Stats Counter Block
    grapesjs.BlockManager.add('stats-counter', {
        label: 'Stats Counter',
        category: 'LUCA Custom',
        content: `
            <div class="py-16 bg-gradient-to-r from-cyan-500 to-blue-600">
                <div class="container mx-auto px-6">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
                        <div class="stat-item">
                            <div class="text-5xl font-bold text-white mb-2">1000+</div>
                            <div class="text-xl text-white/80">Aktive Nutzer</div>
                        </div>
                        <div class="stat-item">
                            <div class="text-5xl font-bold text-white mb-2">95%</div>
                            <div class="text-xl text-white/80">Mit Handynummer</div>
                        </div>
                        <div class="stat-item">
                            <div class="text-5xl font-bold text-white mb-2">24/7</div>
                            <div class="text-xl text-white/80">Automatisiert</div>
                        </div>
                    </div>
                </div>
            </div>
        `,
        attributes: {
            class: 'fa fa-chart-line'
        }
    });

    // Testimonials Block
    grapesjs.BlockManager.add('testimonials', {
        label: 'Testimonials',
        category: 'LUCA Custom',
        content: `
            <div class="py-16 bg-gray-100">
                <div class="container mx-auto px-6">
                    <h2 class="text-4xl font-bold text-center mb-12 text-gray-800">Was unsere Kunden sagen</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        <div class="testimonial bg-white p-6 rounded-lg shadow-lg">
                            <div class="flex items-center mb-4">
                                <div class="w-12 h-12 bg-cyan-500 rounded-full flex items-center justify-center text-white font-bold text-xl">
                                    M
                                </div>
                                <div class="ml-4">
                                    <div class="font-bold text-gray-800">Max Mustermann</div>
                                    <div class="text-sm text-gray-600">CEO, Firma GmbH</div>
                                </div>
                            </div>
                            <p class="text-gray-700 italic">
                                "Exzellenter Service! Die Leads sind hochwertig und die Automatisierung spart uns enorm viel Zeit."
                            </p>
                        </div>
                        <div class="testimonial bg-white p-6 rounded-lg shadow-lg">
                            <div class="flex items-center mb-4">
                                <div class="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold text-xl">
                                    A
                                </div>
                                <div class="ml-4">
                                    <div class="font-bold text-gray-800">Anna Schmidt</div>
                                    <div class="text-sm text-gray-600">Vertriebsleiterin</div>
                                </div>
                            </div>
                            <p class="text-gray-700 italic">
                                "Die KI-gestützte Lead-Generierung hat unsere Conversion-Rate verdoppelt. Absolut empfehlenswert!"
                            </p>
                        </div>
                        <div class="testimonial bg-white p-6 rounded-lg shadow-lg">
                            <div class="flex items-center mb-4">
                                <div class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white font-bold text-xl">
                                    J
                                </div>
                                <div class="ml-4">
                                    <div class="font-bold text-gray-800">Jonas Weber</div>
                                    <div class="text-sm text-gray-600">Sales Manager</div>
                                </div>
                            </div>
                            <p class="text-gray-700 italic">
                                "Einfach zu bedienen und extrem effektiv. Wir konnten unsere Lead-Anzahl um 300% steigern."
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `,
        attributes: {
            class: 'fa fa-comments'
        }
    });

})(window.grapesjs || {});
