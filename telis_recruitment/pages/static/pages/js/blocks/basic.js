/**
 * Basic Blocks for GrapesJS Builder
 * Includes: Heading, Paragraph, Image, Button, Link, List, Quote
 */

export default function loadBasicBlocks(editor) {
    const blockManager = editor.BlockManager;

    // Heading
    blockManager.add('heading', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">H</div>
                <div style="font-size: 11px;">Heading</div>
            </div>
        `,
        category: 'Basic',
        content: '<h1 style="font-family: var(--font-heading, sans-serif); color: var(--brand-text, #212529); margin-bottom: 20px;">Your Heading Here</h1>',
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add a heading - click to edit text'
        }
    });

    // Paragraph
    blockManager.add('paragraph', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">¶</div>
                <div style="font-size: 11px;">Paragraph</div>
            </div>
        `,
        category: 'Basic',
        content: '<p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.6; margin-bottom: 15px;">Your paragraph text goes here. Edit this text to add your content.</p>',
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add a paragraph - double-click to edit'
        }
    });

    // Image
    blockManager.add('image', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">🖼️</div>
                <div style="font-size: 11px;">Image</div>
            </div>
        `,
        category: 'Basic',
        content: '<img src="https://via.placeholder.com/600x400" alt="Placeholder image" style="max-width: 100%; height: auto; display: block;">',
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add an image - upload in Assets panel or change URL'
        }
    });

    // Button
    blockManager.add('button', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">🔘</div>
                <div style="font-size: 11px;">Button</div>
            </div>
        `,
        category: 'Basic',
        content: `
            <a href="#" class="btn" style="display: inline-block; padding: 12px 30px; background-color: var(--brand-primary, #007bff); color: white; text-decoration: none; border-radius: 5px; font-weight: 600; font-family: var(--font-body, sans-serif); transition: all 0.3s;">
                Click Me
            </a>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add a button - click to change text and link'
        }
    });

    // Link
    blockManager.add('link', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">🔗</div>
                <div style="font-size: 11px;">Link</div>
            </div>
        `,
        category: 'Basic',
        content: '<a href="#" style="color: var(--brand-primary, #007bff); text-decoration: underline;">Click here</a>',
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add a text link'
        }
    });

    // Unordered List
    blockManager.add('list', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">📋</div>
                <div style="font-size: 11px;">List</div>
            </div>
        `,
        category: 'Basic',
        content: `
            <ul style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); line-height: 1.8; padding-left: 20px;">
                <li>List item 1</li>
                <li>List item 2</li>
                <li>List item 3</li>
            </ul>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add a bullet list'
        }
    });

    // Quote/Blockquote
    blockManager.add('quote', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">💬</div>
                <div style="font-size: 11px;">Quote</div>
            </div>
        `,
        category: 'Basic',
        content: `
            <blockquote style="border-left: 4px solid var(--brand-primary, #007bff); padding-left: 20px; margin: 20px 0; font-style: italic; color: var(--brand-text, #212529); font-family: var(--font-body, sans-serif);">
                "This is a quote. Replace this text with your inspiring quote or customer testimonial."
            </blockquote>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add a quote or testimonial'
        }
    });
}
