/**
 * GrapesJS Blocks Bundle - All blocks in one file
 * Loads: Layout, Basic, Forms, LUCA Custom, Advanced blocks
 * 
 * This file bundles all block loaders into a single IIFE (Immediately Invoked Function Expression)
 * to avoid ES module import issues with Django template tags.
 */
(function() {
    'use strict';
    
    /**
     * Main function to load all blocks into GrapesJS editor
     * @param {Object} editor - GrapesJS editor instance
     */
    window.loadAllBlocks = function(editor) {
        console.log('🔄 Loading GrapesJS blocks...');
        
        // Load blocks by category
        loadLayoutBlocks(editor);
        loadBasicBlocks(editor);
        loadFormBlocks(editor);
        loadLucaCustomBlocks(editor);
        loadAdvancedBlocks(editor);
        
        console.log('✅ All GrapesJS blocks loaded successfully');
    };
    
    // === LAYOUT BLOCKS ===
    function loadLayoutBlocks(editor) {
        const blockManager = editor.BlockManager;

        // Full-width Section
        blockManager.add('section', {
            label: '📦 Section',
            category: 'Layout',
            content: `
                <section class="section" style="padding: 60px 20px; background-color: #ffffff;">
                    <div class="container" style="max-width: 1200px; margin: 0 auto;">
                        <p>Add your content here...</p>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 2 Column Grid
        blockManager.add('2-columns', {
            label: '📐 2 Columns',
            category: 'Layout',
            content: `
                <div class="row-2-cols" style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div class="col" style="flex: 1; min-width: 250px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 1</p>
                    </div>
                    <div class="col" style="flex: 1; min-width: 250px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 2</p>
                    </div>
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 3 Column Grid
        blockManager.add('3-columns', {
            label: '📐 3 Columns',
            category: 'Layout',
            content: `
                <div class="row-3-cols" style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div class="col" style="flex: 1; min-width: 200px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 1</p>
                    </div>
                    <div class="col" style="flex: 1; min-width: 200px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 2</p>
                    </div>
                    <div class="col" style="flex: 1; min-width: 200px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 3</p>
                    </div>
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 4 Column Grid
        blockManager.add('4-columns', {
            label: '📐 4 Columns',
            category: 'Layout',
            content: `
                <div class="row-4-cols" style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div class="col" style="flex: 1; min-width: 150px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 1</p>
                    </div>
                    <div class="col" style="flex: 1; min-width: 150px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 2</p>
                    </div>
                    <div class="col" style="flex: 1; min-width: 150px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 3</p>
                    </div>
                    <div class="col" style="flex: 1; min-width: 150px; padding: 20px; background-color: #f8f9fa;">
                        <p>Column 4</p>
                    </div>
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Divider
        blockManager.add('divider', {
            label: '➖ Divider',
            category: 'Layout',
            content: `
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 40px 0;">
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Spacer
        blockManager.add('spacer', {
            label: '⬇️ Spacer',
            category: 'Layout',
            content: `
                <div class="spacer" style="height: 60px;"></div>
            `,
            attributes: { class: 'gjs-block-section' }
        });
    }
    
    // === BASIC BLOCKS ===
    function loadBasicBlocks(editor) {
        const blockManager = editor.BlockManager;

        // Heading
        blockManager.add('heading', {
            label: '📝 Heading',
            category: 'Basic',
            content: '<h1 style="font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529); margin-bottom: 20px;">Your Heading Here</h1>',
            attributes: { class: 'gjs-block-section' }
        });

        // Paragraph
        blockManager.add('paragraph', {
            label: '📄 Paragraph',
            category: 'Basic',
            content: '<p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.6; margin-bottom: 15px;">Your paragraph text goes here. Edit this text to add your content.</p>',
            attributes: { class: 'gjs-block-section' }
        });

        // Image
        blockManager.add('image', {
            label: '🖼️ Image',
            category: 'Basic',
            content: '<img src="https://via.placeholder.com/600x400" alt="Placeholder image" style="max-width: 100%; height: auto; display: block;">',
            attributes: { class: 'gjs-block-section' }
        });

        // Button
        blockManager.add('button', {
            label: '🔘 Button',
            category: 'Basic',
            content: `
                <a href="#" class="btn" style="display: inline-block; padding: 12px 30px; background-color: var(--brand-primary, #007bff); color: white; text-decoration: none; border-radius: 5px; font-weight: 600; font-family: var(--font-body, sans-serif); transition: all 0.3s;">
                    Click Me
                </a>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Link
        blockManager.add('link', {
            label: '🔗 Link',
            category: 'Basic',
            content: '<a href="#" style="color: var(--brand-primary, #007bff); text-decoration: underline;">Click here</a>',
            attributes: { class: 'gjs-block-section' }
        });

        // Unordered List
        blockManager.add('list', {
            label: '📋 List',
            category: 'Basic',
            content: `
                <ul style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.8; padding-left: 20px;">
                    <li>List item 1</li>
                    <li>List item 2</li>
                    <li>List item 3</li>
                </ul>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Quote/Blockquote
        blockManager.add('quote', {
            label: '💬 Quote',
            category: 'Basic',
            content: `
                <blockquote style="border-left: 4px solid var(--brand-primary, #007bff); padding-left: 20px; margin: 20px 0; font-style: italic; color: var(--brand-text, #212529); font-family: var(--font-body, sans-serif);">
                    "This is a quote. Replace this text with your inspiring quote or customer testimonial."
                </blockquote>
            `,
            attributes: { class: 'gjs-block-section' }
        });
    }
    
    // === FORM BLOCKS ===
    function loadFormBlocks(editor) {
        const blockManager = editor.BlockManager;

        // Form Container
        blockManager.add('form-container', {
            label: '📋 Form',
            category: 'Forms',
            content: `
                <form class="form" style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">Add form fields below</p>
                </form>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Input Field
        blockManager.add('input-field', {
            label: '📝 Input Field',
            category: 'Forms',
            content: `
                <div class="form-group" style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">
                        Label
                    </label>
                    <input type="text" name="field" placeholder="Enter text..." style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 4px; font-family: var(--font-body, sans-serif); font-size: 16px;">
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Textarea
        blockManager.add('textarea', {
            label: '📝 Textarea',
            category: 'Forms',
            content: `
                <div class="form-group" style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">
                        Message
                    </label>
                    <textarea name="message" rows="5" placeholder="Enter your message..." style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 4px; font-family: var(--font-body, sans-serif); font-size: 16px; resize: vertical;"></textarea>
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Select/Dropdown
        blockManager.add('select', {
            label: '📋 Select',
            category: 'Forms',
            content: `
                <div class="form-group" style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">
                        Choose an option
                    </label>
                    <select name="select" style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 4px; font-family: var(--font-body, sans-serif); font-size: 16px;">
                        <option value="">Select...</option>
                        <option value="option1">Option 1</option>
                        <option value="option2">Option 2</option>
                        <option value="option3">Option 3</option>
                    </select>
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Checkbox
        blockManager.add('checkbox', {
            label: '☑️ Checkbox',
            category: 'Forms',
            content: `
                <div class="form-group" style="margin-bottom: 15px;">
                    <label style="display: flex; align-items: center; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); cursor: pointer;">
                        <input type="checkbox" name="checkbox" value="yes" style="margin-right: 10px; width: 18px; height: 18px; cursor: pointer;">
                        <span>Checkbox option</span>
                    </label>
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Radio Buttons
        blockManager.add('radio', {
            label: '🔘 Radio',
            category: 'Forms',
            content: `
                <div class="form-group" style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 12px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">
                        Choose one
                    </label>
                    <div style="margin-bottom: 8px;">
                        <label style="display: flex; align-items: center; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); cursor: pointer;">
                            <input type="radio" name="radio" value="option1" style="margin-right: 10px; cursor: pointer;">
                            <span>Option 1</span>
                        </label>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <label style="display: flex; align-items: center; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); cursor: pointer;">
                            <input type="radio" name="radio" value="option2" style="margin-right: 10px; cursor: pointer;">
                            <span>Option 2</span>
                        </label>
                    </div>
                </div>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // Submit Button
        blockManager.add('submit-button', {
            label: '✅ Submit Button',
            category: 'Forms',
            content: `
                <button type="submit" style="display: inline-block; padding: 14px 40px; background-color: var(--brand-primary, #007bff); color: white; border: none; border-radius: 5px; font-weight: 600; font-family: var(--font-body, sans-serif); font-size: 16px; cursor: pointer; transition: all 0.3s;">
                    Submit
                </button>
            `,
            attributes: { class: 'gjs-block-section' }
        });
    }
    
    // === LUCA CUSTOM BLOCKS ===
    function loadLucaCustomBlocks(editor) {
        const blockManager = editor.BlockManager;

        // 1. Hero Section (Centered)
        blockManager.add('hero-centered', {
            label: '🎯 Hero Zentriert',
            category: 'LUCA Sections',
            content: `
                <section class="luca-hero luca-hero--centered" style="padding: 100px 20px; text-align: center; background: linear-gradient(135deg, var(--brand-primary, #007bff) 0%, var(--brand-secondary, #6c757d) 100%); position: relative;">
                    <div class="container" style="max-width: 900px; margin: 0 auto; position: relative; z-index: 2;">
                        <h1 style="font-size: 56px; color: white; margin-bottom: 24px; font-family: var(--font-heading, sans-serif); font-weight: 700; line-height: 1.2;">
                            Ihre überzeugende Headline
                        </h1>
                        <p style="font-size: 22px; color: rgba(255,255,255,0.95); margin-bottom: 40px; font-family: var(--font-body, sans-serif); line-height: 1.6;">
                            Eine kurze, prägnante Beschreibung, die den Nutzen für den Besucher hervorhebt und zum Handeln animiert.
                        </p>
                        <a href="#" class="btn-primary" style="display: inline-block; padding: 18px 45px; background: white; color: var(--brand-primary, #007bff); text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 18px; font-family: var(--font-body, sans-serif); box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: all 0.3s;">
                            Jetzt starten
                        </a>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 2. Hero Section (Split)
        blockManager.add('hero-split', {
            label: '🎯 Hero Split',
            category: 'LUCA Sections',
            content: `
                <section class="luca-hero luca-hero--split" style="padding: 80px 20px; background-color: #f8f9fa;">
                    <div class="container" style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 60px; flex-wrap: wrap;">
                        <div class="hero-content" style="flex: 1; min-width: 300px;">
                            <h1 style="font-size: 48px; color: var(--brand-text, #212529); margin-bottom: 20px; font-family: var(--font-heading, sans-serif); font-weight: 700; line-height: 1.2;">
                                Transformieren Sie Ihr Business
                            </h1>
                            <p style="font-size: 20px; color: #6c757d; margin-bottom: 30px; font-family: var(--font-body, sans-serif); line-height: 1.6;">
                                Professionelle Lösungen für moderne Unternehmen. Starten Sie noch heute und erleben Sie den Unterschied.
                            </p>
                            <a href="#" class="btn-primary" style="display: inline-block; padding: 16px 40px; background: var(--brand-primary, #007bff); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 18px; font-family: var(--font-body, sans-serif); transition: all 0.3s;">
                                Mehr erfahren
                            </a>
                        </div>
                        <div class="hero-image" style="flex: 1; min-width: 300px;">
                            <img src="https://via.placeholder.com/600x450" alt="Hero Image" style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.15);">
                        </div>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 3. Stats Counter (Animated)
        blockManager.add('stats-counter', {
            label: '📊 Stats Counter',
            category: 'LUCA Sections',
            content: `
                <section class="luca-stats" style="padding: 80px 20px; background-color: var(--brand-primary, #007bff); color: white;">
                    <div class="container" style="max-width: 1200px; margin: 0 auto;">
                        <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 40px; text-align: center;">
                            <div class="stat-item">
                                <div class="stat-icon" style="font-size: 48px; margin-bottom: 15px;">🎯</div>
                                <div class="stat-number" style="font-size: 48px; font-weight: 700; margin-bottom: 10px; font-family: var(--font-heading, sans-serif);">1000+</div>
                                <div class="stat-label" style="font-size: 18px; opacity: 0.9; font-family: var(--font-body, sans-serif);">Zufriedene Kunden</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-icon" style="font-size: 48px; margin-bottom: 15px;">⚡</div>
                                <div class="stat-number" style="font-size: 48px; font-weight: 700; margin-bottom: 10px; font-family: var(--font-heading, sans-serif);">99.9%</div>
                                <div class="stat-label" style="font-size: 18px; opacity: 0.9; font-family: var(--font-body, sans-serif);">Verfügbarkeit</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-icon" style="font-size: 48px; margin-bottom: 15px;">🏆</div>
                                <div class="stat-number" style="font-size: 48px; font-weight: 700; margin-bottom: 10px; font-family: var(--font-heading, sans-serif);">15+</div>
                                <div class="stat-label" style="font-size: 18px; opacity: 0.9; font-family: var(--font-body, sans-serif);">Jahre Erfahrung</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-icon" style="font-size: 48px; margin-bottom: 15px;">💼</div>
                                <div class="stat-number" style="font-size: 48px; font-weight: 700; margin-bottom: 10px; font-family: var(--font-heading, sans-serif);">500+</div>
                                <div class="stat-label" style="font-size: 18px; opacity: 0.9; font-family: var(--font-body, sans-serif);">Projekte</div>
                            </div>
                        </div>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 4. Testimonials Grid
        blockManager.add('testimonials-grid', {
            label: '⭐ Testimonials',
            category: 'LUCA Sections',
            content: `
                <section class="luca-testimonials" style="padding: 80px 20px; background-color: #ffffff;">
                    <div class="container" style="max-width: 1200px; margin: 0 auto;">
                        <h2 style="text-align: center; font-size: 42px; margin-bottom: 60px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                            Was unsere Kunden sagen
                        </h2>
                        <div class="testimonials-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px;">
                            <div class="testimonial-card" style="background: #f8f9fa; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                                <div class="stars" style="color: #ffc107; font-size: 20px; margin-bottom: 15px;">★★★★★</div>
                                <p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.7; margin-bottom: 20px; font-style: italic;">
                                    "Hervorragender Service und erstklassige Ergebnisse. Wir sind sehr zufrieden mit der Zusammenarbeit."
                                </p>
                                <div class="testimonial-author" style="display: flex; align-items: center; gap: 15px;">
                                    <img src="https://via.placeholder.com/60" alt="Author" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">
                                    <div>
                                        <div style="font-weight: 600; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">Max Mustermann</div>
                                        <div style="font-size: 14px; color: #6c757d; font-family: var(--font-body, sans-serif);">CEO, Firma GmbH</div>
                                    </div>
                                </div>
                            </div>
                            <div class="testimonial-card" style="background: #f8f9fa; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                                <div class="stars" style="color: #ffc107; font-size: 20px; margin-bottom: 15px;">★★★★★</div>
                                <p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.7; margin-bottom: 20px; font-style: italic;">
                                    "Professionell, schnell und zuverlässig. Genau das, was wir gebraucht haben!"
                                </p>
                                <div class="testimonial-author" style="display: flex; align-items: center; gap: 15px;">
                                    <img src="https://via.placeholder.com/60" alt="Author" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">
                                    <div>
                                        <div style="font-weight: 600; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">Anna Schmidt</div>
                                        <div style="font-size: 14px; color: #6c757d; font-family: var(--font-body, sans-serif);">Marketing Manager</div>
                                    </div>
                                </div>
                            </div>
                            <div class="testimonial-card" style="background: #f8f9fa; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                                <div class="stars" style="color: #ffc107; font-size: 20px; margin-bottom: 15px;">★★★★★</div>
                                <p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.7; margin-bottom: 20px; font-style: italic;">
                                    "Beste Entscheidung für unser Projekt. Würden wir jederzeit wieder wählen."
                                </p>
                                <div class="testimonial-author" style="display: flex; align-items: center; gap: 15px;">
                                    <img src="https://via.placeholder.com/60" alt="Author" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">
                                    <div>
                                        <div style="font-weight: 600; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">Thomas Weber</div>
                                        <div style="font-size: 14px; color: #6c757d; font-family: var(--font-body, sans-serif);">Geschäftsführer</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 5. Pricing Table
        blockManager.add('pricing-table', {
            label: '💰 Pricing Table',
            category: 'LUCA Sections',
            content: `
                <section class="luca-pricing" style="padding: 80px 20px; background-color: #f8f9fa;">
                    <div class="container" style="max-width: 1200px; margin: 0 auto;">
                        <h2 style="text-align: center; font-size: 42px; margin-bottom: 20px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                            Unsere Preise
                        </h2>
                        <p style="text-align: center; font-size: 20px; color: #6c757d; margin-bottom: 60px; font-family: var(--font-body, sans-serif);">
                            Wählen Sie das passende Paket für Ihre Bedürfnisse
                        </p>
                        <div class="pricing-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; max-width: 1000px; margin: 0 auto;">
                            <div class="pricing-card" style="background: white; padding: 40px 30px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                                <h3 style="font-size: 28px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">Basic</h3>
                                <div class="price" style="font-size: 48px; font-weight: 700; color: var(--brand-primary, #007bff); margin-bottom: 20px; font-family: var(--font-heading, sans-serif);">
                                    €29<span style="font-size: 20px; font-weight: 400;">/Monat</span>
                                </div>
                                <ul style="list-style: none; padding: 0; margin: 0 0 30px 0; text-align: left;">
                                    <li style="padding: 10px 0; border-bottom: 1px solid #e9ecef; font-family: var(--font-body, sans-serif);">✓ Feature 1</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid #e9ecef; font-family: var(--font-body, sans-serif);">✓ Feature 2</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid #e9ecef; font-family: var(--font-body, sans-serif);">✓ Feature 3</li>
                                </ul>
                                <a href="#" style="display: block; padding: 14px; background: var(--brand-primary, #007bff); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); transition: all 0.3s;">
                                    Jetzt starten
                                </a>
                            </div>
                            <div class="pricing-card pricing-card--featured" style="background: var(--brand-primary, #007bff); padding: 40px 30px; border-radius: 12px; text-align: center; box-shadow: 0 8px 30px rgba(0,0,0,0.15); transform: scale(1.05); color: white;">
                                <div style="background: var(--brand-accent, #28a745); color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 15px;">EMPFOHLEN</div>
                                <h3 style="font-size: 28px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: white;">Pro</h3>
                                <div class="price" style="font-size: 48px; font-weight: 700; color: white; margin-bottom: 20px; font-family: var(--font-heading, sans-serif);">
                                    €79<span style="font-size: 20px; font-weight: 400;">/Monat</span>
                                </div>
                                <ul style="list-style: none; padding: 0; margin: 0 0 30px 0; text-align: left;">
                                    <li style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.2); font-family: var(--font-body, sans-serif); color: white;">✓ Alle Basic Features</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.2); font-family: var(--font-body, sans-serif); color: white;">✓ Pro Feature 1</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.2); font-family: var(--font-body, sans-serif); color: white;">✓ Pro Feature 2</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.2); font-family: var(--font-body, sans-serif); color: white;">✓ Priority Support</li>
                                </ul>
                                <a href="#" style="display: block; padding: 14px; background: white; color: var(--brand-primary, #007bff); text-decoration: none; border-radius: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); transition: all 0.3s;">
                                    Jetzt starten
                                </a>
                            </div>
                            <div class="pricing-card" style="background: white; padding: 40px 30px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                                <h3 style="font-size: 28px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">Enterprise</h3>
                                <div class="price" style="font-size: 48px; font-weight: 700; color: var(--brand-primary, #007bff); margin-bottom: 20px; font-family: var(--font-heading, sans-serif);">
                                    Custom
                                </div>
                                <ul style="list-style: none; padding: 0; margin: 0 0 30px 0; text-align: left;">
                                    <li style="padding: 10px 0; border-bottom: 1px solid #e9ecef; font-family: var(--font-body, sans-serif);">✓ Alle Pro Features</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid #e9ecef; font-family: var(--font-body, sans-serif);">✓ Unbegrenzt</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid #e9ecef; font-family: var(--font-body, sans-serif);">✓ Dedicated Support</li>
                                    <li style="padding: 10px 0; border-bottom: 1px solid #e9ecef; font-family: var(--font-body, sans-serif);">✓ Custom Integration</li>
                                </ul>
                                <a href="#" style="display: block; padding: 14px; background: var(--brand-primary, #007bff); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); transition: all 0.3s;">
                                    Kontakt
                                </a>
                            </div>
                        </div>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 6. FAQ Accordion
        blockManager.add('faq-accordion', {
            label: '❓ FAQ Accordion',
            category: 'LUCA Sections',
            content: `
                <section class="luca-faq" style="padding: 80px 20px; background-color: #ffffff;">
                    <div class="container" style="max-width: 900px; margin: 0 auto;">
                        <h2 style="text-align: center; font-size: 42px; margin-bottom: 60px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                            Häufig gestellte Fragen
                        </h2>
                        <div class="faq-list">
                            <div class="faq-item" style="margin-bottom: 20px; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden;">
                                <div class="faq-question" style="padding: 20px; background: #f8f9fa; cursor: pointer; font-weight: 600; font-size: 18px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529); display: flex; justify-content: space-between; align-items: center;">
                                    <span>Wie funktioniert Ihr Service?</span>
                                    <span style="font-size: 24px; color: var(--brand-primary, #007bff);">+</span>
                                </div>
                                <div class="faq-answer" style="padding: 20px; font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7; display: none;">
                                    Unser Service ist einfach zu nutzen. Nach der Anmeldung erhalten Sie sofortigen Zugang zu allen Features und können direkt loslegen.
                                </div>
                            </div>
                            <div class="faq-item" style="margin-bottom: 20px; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden;">
                                <div class="faq-question" style="padding: 20px; background: #f8f9fa; cursor: pointer; font-weight: 600; font-size: 18px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529); display: flex; justify-content: space-between; align-items: center;">
                                    <span>Welche Zahlungsmethoden akzeptieren Sie?</span>
                                    <span style="font-size: 24px; color: var(--brand-primary, #007bff);">+</span>
                                </div>
                                <div class="faq-answer" style="padding: 20px; font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7; display: none;">
                                    Wir akzeptieren alle gängigen Kreditkarten, PayPal, SEPA-Lastschrift und Rechnung für Enterprise-Kunden.
                                </div>
                            </div>
                            <div class="faq-item" style="margin-bottom: 20px; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden;">
                                <div class="faq-question" style="padding: 20px; background: #f8f9fa; cursor: pointer; font-weight: 600; font-size: 18px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529); display: flex; justify-content: space-between; align-items: center;">
                                    <span>Kann ich jederzeit kündigen?</span>
                                    <span style="font-size: 24px; color: var(--brand-primary, #007bff);">+</span>
                                </div>
                                <div class="faq-answer" style="padding: 20px; font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7; display: none;">
                                    Ja, Sie können Ihr Abonnement jederzeit mit einer Kündigungsfrist von 30 Tagen beenden. Keine versteckten Kosten oder langfristige Bindung.
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 7. CTA Section
        blockManager.add('cta-section', {
            label: '📞 CTA Section',
            category: 'LUCA Sections',
            content: `
                <section class="luca-cta" style="padding: 100px 20px; background: linear-gradient(135deg, var(--brand-primary, #007bff) 0%, var(--brand-accent, #28a745) 100%); text-align: center; position: relative;">
                    <div class="container" style="max-width: 800px; margin: 0 auto; position: relative; z-index: 2;">
                        <h2 style="font-size: 48px; color: white; margin-bottom: 24px; font-family: var(--font-heading, sans-serif); font-weight: 700; line-height: 1.2;">
                            Bereit durchzustarten?
                        </h2>
                        <p style="font-size: 22px; color: rgba(255,255,255,0.95); margin-bottom: 40px; font-family: var(--font-body, sans-serif); line-height: 1.6;">
                            Starten Sie noch heute und erleben Sie den Unterschied. Keine Kreditkarte erforderlich.
                        </p>
                        <a href="#" class="btn-cta" style="display: inline-block; padding: 18px 45px; background: white; color: var(--brand-primary, #007bff); text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 20px; font-family: var(--font-body, sans-serif); box-shadow: 0 4px 20px rgba(0,0,0,0.2); transition: all 0.3s;">
                            Kostenlos testen
                        </a>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 8. Features Grid
        blockManager.add('features-grid', {
            label: '🏆 Features Grid',
            category: 'LUCA Sections',
            content: `
                <section class="luca-features" style="padding: 80px 20px; background-color: #ffffff;">
                    <div class="container" style="max-width: 1200px; margin: 0 auto;">
                        <h2 style="text-align: center; font-size: 42px; margin-bottom: 20px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                            Unsere Features
                        </h2>
                        <p style="text-align: center; font-size: 20px; color: #6c757d; margin-bottom: 60px; font-family: var(--font-body, sans-serif);">
                            Alles was Sie brauchen, um erfolgreich zu sein
                        </p>
                        <div class="features-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 40px;">
                            <div class="feature-card" style="text-align: center; padding: 30px;">
                                <div class="feature-icon" style="font-size: 56px; margin-bottom: 20px; color: var(--brand-primary, #007bff);">🚀</div>
                                <h3 style="font-size: 24px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                                    Schnell & Effizient
                                </h3>
                                <p style="font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7;">
                                    Blitzschnelle Performance für optimale Ergebnisse und Produktivität.
                                </p>
                            </div>
                            <div class="feature-card" style="text-align: center; padding: 30px;">
                                <div class="feature-icon" style="font-size: 56px; margin-bottom: 20px; color: var(--brand-primary, #007bff);">🔒</div>
                                <h3 style="font-size: 24px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                                    100% Sicher
                                </h3>
                                <p style="font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7;">
                                    Höchste Sicherheitsstandards zum Schutz Ihrer Daten und Privatsphäre.
                                </p>
                            </div>
                            <div class="feature-card" style="text-align: center; padding: 30px;">
                                <div class="feature-icon" style="font-size: 56px; margin-bottom: 20px; color: var(--brand-primary, #007bff);">💡</div>
                                <h3 style="font-size: 24px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                                    Innovativ
                                </h3>
                                <p style="font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7;">
                                    Modernste Technologie für zukunftssichere Lösungen.
                                </p>
                            </div>
                            <div class="feature-card" style="text-align: center; padding: 30px;">
                                <div class="feature-icon" style="font-size: 56px; margin-bottom: 20px; color: var(--brand-primary, #007bff);">🎯</div>
                                <h3 style="font-size: 24px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                                    Zielgerichtet
                                </h3>
                                <p style="font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7;">
                                    Präzise auf Ihre Bedürfnisse zugeschnittene Funktionen.
                                </p>
                            </div>
                            <div class="feature-card" style="text-align: center; padding: 30px;">
                                <div class="feature-icon" style="font-size: 56px; margin-bottom: 20px; color: var(--brand-primary, #007bff);">📈</div>
                                <h3 style="font-size: 24px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                                    Skalierbar
                                </h3>
                                <p style="font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7;">
                                    Wächst mit Ihrem Unternehmen und Ihren Anforderungen.
                                </p>
                            </div>
                            <div class="feature-card" style="text-align: center; padding: 30px;">
                                <div class="feature-icon" style="font-size: 56px; margin-bottom: 20px; color: var(--brand-primary, #007bff);">🤝</div>
                                <h3 style="font-size: 24px; margin-bottom: 15px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                                    Top Support
                                </h3>
                                <p style="font-family: var(--font-body, sans-serif); color: #6c757d; line-height: 1.7;">
                                    Exzellenter Kundenservice, der immer für Sie da ist.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 9. Lead Form (Advanced)
        blockManager.add('lead-form-advanced', {
            label: '📧 Lead Form',
            category: 'LUCA Sections',
            content: `
                <section class="luca-lead-form" style="padding: 80px 20px; background-color: #f8f9fa;">
                    <div class="container" style="max-width: 700px; margin: 0 auto;">
                        <h2 style="text-align: center; font-size: 42px; margin-bottom: 20px; font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529);">
                            Jetzt Kontakt aufnehmen
                        </h2>
                        <p style="text-align: center; font-size: 18px; color: #6c757d; margin-bottom: 40px; font-family: var(--font-body, sans-serif);">
                            Füllen Sie das Formular aus und wir melden uns innerhalb von 24 Stunden bei Ihnen.
                        </p>
                        <form class="lead-form" style="background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                            <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                <div class="form-group">
                                    <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">Vorname *</label>
                                    <input type="text" name="first_name" required placeholder="Max" style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 6px; font-family: var(--font-body, sans-serif); font-size: 16px;">
                                </div>
                                <div class="form-group">
                                    <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">Nachname *</label>
                                    <input type="text" name="last_name" required placeholder="Mustermann" style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 6px; font-family: var(--font-body, sans-serif); font-size: 16px;">
                                </div>
                            </div>
                            <div class="form-group" style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">E-Mail *</label>
                                <input type="email" name="email" required placeholder="max@beispiel.de" style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 6px; font-family: var(--font-body, sans-serif); font-size: 16px;">
                            </div>
                            <div class="form-group" style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">Telefon</label>
                                <input type="tel" name="phone" placeholder="+49 123 456789" style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 6px; font-family: var(--font-body, sans-serif); font-size: 16px;">
                            </div>
                            <div class="form-group" style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">Nachricht *</label>
                                <textarea name="message" required rows="5" placeholder="Ihre Nachricht..." style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 6px; font-family: var(--font-body, sans-serif); font-size: 16px; resize: vertical;"></textarea>
                            </div>
                            <div class="form-group" style="margin-bottom: 25px;">
                                <label style="display: flex; align-items: flex-start; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); cursor: pointer; font-size: 14px;">
                                    <input type="checkbox" name="privacy" required style="margin-right: 10px; margin-top: 4px; width: 18px; height: 18px; cursor: pointer;">
                                    <span>Ich habe die <a href="#" style="color: var(--brand-primary, #007bff);">Datenschutzerklärung</a> gelesen und akzeptiere diese. *</span>
                                </label>
                            </div>
                            <button type="submit" style="width: 100%; padding: 16px; background: var(--brand-primary, #007bff); color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 18px; font-family: var(--font-body, sans-serif); cursor: pointer; transition: all 0.3s;">
                                Absenden
                            </button>
                        </form>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 10. Countdown Timer
        blockManager.add('countdown-timer', {
            label: '⏰ Countdown',
            category: 'LUCA Sections',
            content: `
                <section class="luca-countdown" style="padding: 80px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); text-align: center;">
                    <div class="container" style="max-width: 900px; margin: 0 auto;">
                        <h2 style="font-size: 42px; color: white; margin-bottom: 20px; font-family: var(--font-heading, sans-serif); font-weight: 700;">
                            Limitiertes Angebot endet bald!
                        </h2>
                        <p style="font-size: 20px; color: rgba(255,255,255,0.9); margin-bottom: 50px; font-family: var(--font-body, sans-serif);">
                            Sichern Sie sich jetzt Ihren Rabatt
                        </p>
                        <div class="countdown-timer" style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;">
                            <div class="countdown-item" style="background: rgba(255,255,255,0.15); padding: 30px 40px; border-radius: 12px; backdrop-filter: blur(10px);">
                                <div class="countdown-value" style="font-size: 56px; font-weight: 700; color: white; font-family: var(--font-heading, sans-serif); line-height: 1;">23</div>
                                <div class="countdown-label" style="font-size: 16px; color: rgba(255,255,255,0.9); margin-top: 10px; font-family: var(--font-body, sans-serif); text-transform: uppercase; letter-spacing: 1px;">Tage</div>
                            </div>
                            <div class="countdown-item" style="background: rgba(255,255,255,0.15); padding: 30px 40px; border-radius: 12px; backdrop-filter: blur(10px);">
                                <div class="countdown-value" style="font-size: 56px; font-weight: 700; color: white; font-family: var(--font-heading, sans-serif); line-height: 1;">15</div>
                                <div class="countdown-label" style="font-size: 16px; color: rgba(255,255,255,0.9); margin-top: 10px; font-family: var(--font-body, sans-serif); text-transform: uppercase; letter-spacing: 1px;">Stunden</div>
                            </div>
                            <div class="countdown-item" style="background: rgba(255,255,255,0.15); padding: 30px 40px; border-radius: 12px; backdrop-filter: blur(10px);">
                                <div class="countdown-value" style="font-size: 56px; font-weight: 700; color: white; font-family: var(--font-heading, sans-serif); line-height: 1;">42</div>
                                <div class="countdown-label" style="font-size: 16px; color: rgba(255,255,255,0.9); margin-top: 10px; font-family: var(--font-body, sans-serif); text-transform: uppercase; letter-spacing: 1px;">Minuten</div>
                            </div>
                            <div class="countdown-item" style="background: rgba(255,255,255,0.15); padding: 30px 40px; border-radius: 12px; backdrop-filter: blur(10px);">
                                <div class="countdown-value" style="font-size: 56px; font-weight: 700; color: white; font-family: var(--font-heading, sans-serif); line-height: 1;">18</div>
                                <div class="countdown-label" style="font-size: 16px; color: rgba(255,255,255,0.9); margin-top: 10px; font-family: var(--font-body, sans-serif); text-transform: uppercase; letter-spacing: 1px;">Sekunden</div>
                            </div>
                        </div>
                        <a href="#" style="display: inline-block; margin-top: 50px; padding: 18px 45px; background: white; color: #667eea; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 18px; font-family: var(--font-body, sans-serif); box-shadow: 0 4px 20px rgba(0,0,0,0.2); transition: all 0.3s;">
                            Jetzt zugreifen
                        </a>
                    </div>
                </section>
            `,
            attributes: { class: 'gjs-block-section' }
        });

        // 11. Footer
        blockManager.add('footer', {
            label: '🦶 Footer',
            category: 'LUCA Sections',
            content: `
                <footer class="luca-footer" style="padding: 60px 20px 30px; background-color: #212529; color: white;">
                    <div class="container" style="max-width: 1200px; margin: 0 auto;">
                        <div class="footer-content" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 40px; margin-bottom: 40px;">
                            <div class="footer-col">
                                <img src="https://via.placeholder.com/150x50" alt="Logo" style="max-width: 150px; margin-bottom: 20px;">
                                <p style="font-family: var(--font-body, sans-serif); color: rgba(255,255,255,0.7); line-height: 1.7; margin: 0;">
                                    Ihre vertrauenswürdige Lösung für moderne Geschäftsprozesse.
                                </p>
                            </div>
                            <div class="footer-col">
                                <h4 style="font-family: var(--font-heading, sans-serif); color: white; margin-bottom: 20px; font-size: 18px; font-weight: 600;">Produkt</h4>
                                <ul style="list-style: none; padding: 0; margin: 0;">
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Features</a></li>
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Preise</a></li>
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Demos</a></li>
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Updates</a></li>
                                </ul>
                            </div>
                            <div class="footer-col">
                                <h4 style="font-family: var(--font-heading, sans-serif); color: white; margin-bottom: 20px; font-size: 18px; font-weight: 600;">Unternehmen</h4>
                                <ul style="list-style: none; padding: 0; margin: 0;">
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Über uns</a></li>
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Karriere</a></li>
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Blog</a></li>
                                    <li style="margin-bottom: 12px;"><a href="#" style="color: rgba(255,255,255,0.7); text-decoration: none; font-family: var(--font-body, sans-serif); transition: color 0.3s;">Kontakt</a></li>
                                </ul>
                            </div>
                            <div class="footer-col">
                                <h4 style="font-family: var(--font-heading, sans-serif); color: white; margin-bottom: 20px; font-size: 18px; font-weight: 600;">Social Media</h4>
                                <div class="social-icons" style="display: flex; gap: 15px;">
                                    <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background-color: rgba(255,255,255,0.1); color: white; border-radius: 50%; text-decoration: none; font-size: 18px; transition: all 0.3s;">f</a>
                                    <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background-color: rgba(255,255,255,0.1); color: white; border-radius: 50%; text-decoration: none; font-size: 18px; transition: all 0.3s;">📷</a>
                                    <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background-color: rgba(255,255,255,0.1); color: white; border-radius: 50%; text-decoration: none; font-size: 18px; transition: all 0.3s;">in</a>
                                    <a href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background-color: rgba(255,255,255,0.1); color: white; border-radius: 50%; text-decoration: none; font-size: 18px; transition: all 0.3s;">🐦</a>
                                </div>
                            </div>
                        </div>
                        <div class="footer-bottom" style="padding-top: 30px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
                            <p style="font-family: var(--font-body, sans-serif); color: rgba(255,255,255,0.5); margin: 0; font-size: 14px;">
                                © 2024 Firmenname. Alle Rechte vorbehalten.
                            </p>
                            <div class="footer-legal" style="display: flex; gap: 20px;">
                                <a href="#" style="color: rgba(255,255,255,0.5); text-decoration: none; font-family: var(--font-body, sans-serif); font-size: 14px; transition: color 0.3s;">Datenschutz</a>
                                <a href="#" style="color: rgba(255,255,255,0.5); text-decoration: none; font-family: var(--font-body, sans-serif); font-size: 14px; transition: color 0.3s;">Impressum</a>
                                <a href="#" style="color: rgba(255,255,255,0.5); text-decoration: none; font-family: var(--font-body, sans-serif); font-size: 14px; transition: color 0.3s;">AGB</a>
                            </div>
                        </div>
                    </div>
                </footer>
            `,
            attributes: { class: 'gjs-block-section' }
        });
    }
    
    // === ADVANCED BLOCKS ===
    function loadAdvancedBlocks(editor) {
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
})();
