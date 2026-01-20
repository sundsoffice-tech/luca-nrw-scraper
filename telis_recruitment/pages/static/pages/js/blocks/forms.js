/**
 * Form Blocks for GrapesJS Builder
 * Includes: Input Field, Textarea, Select, Checkbox, Radio, Form Container, Submit Button
 */

export default function loadFormBlocks(editor) {
    const blockManager = editor.BlockManager;

    // Form Container
    blockManager.add('form-container', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">📋</div>
                <div style="font-size: 11px;">Form</div>
            </div>
        `,
        category: 'Forms',
        content: `
            <form class="form" style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p style="font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">Add form fields below</p>
            </form>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Form container - add input fields inside'
        }
    });

    // Input Field
    blockManager.add('input-field', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">📝</div>
                <div style="font-size: 11px;">Text Input</div>
            </div>
        `,
        category: 'Forms',
        content: `
            <div class="form-group" style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">
                    Label
                </label>
                <input type="text" name="field" placeholder="Enter text..." style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 4px; font-family: var(--font-body, sans-serif); font-size: 16px;">
            </div>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Text input field with label'
        }
    });

    // Textarea
    blockManager.add('textarea', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">📄</div>
                <div style="font-size: 11px;">Text Area</div>
            </div>
        `,
        category: 'Forms',
        content: `
            <div class="form-group" style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; font-weight: 600; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529);">
                    Message
                </label>
                <textarea name="message" rows="5" placeholder="Enter your message..." style="width: 100%; padding: 12px; border: 1px solid #dee2e6; border-radius: 4px; font-family: var(--font-body, sans-serif); font-size: 16px; resize: vertical;"></textarea>
            </div>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Multi-line text area for longer messages'
        }
    });

    // Select/Dropdown
    blockManager.add('select', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">▼</div>
                <div style="font-size: 11px;">Dropdown</div>
            </div>
        `,
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
        attributes: { 
            class: 'gjs-block-section',
            title: 'Dropdown select menu'
        }
    });

    // Checkbox
    blockManager.add('checkbox', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">☑️</div>
                <div style="font-size: 11px;">Checkbox</div>
            </div>
        `,
        category: 'Forms',
        content: `
            <div class="form-group" style="margin-bottom: 15px;">
                <label style="display: flex; align-items: center; font-family: var(--font-body, sans-serif); color: var(--brand-text, #212529); cursor: pointer;">
                    <input type="checkbox" name="checkbox" value="yes" style="margin-right: 10px; width: 18px; height: 18px; cursor: pointer;">
                    <span>Checkbox option</span>
                </label>
            </div>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Checkbox for yes/no or agree options'
        }
    });

    // Radio Buttons
    blockManager.add('radio', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">◉</div>
                <div style="font-size: 11px;">Radio</div>
            </div>
        `,
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
        attributes: { 
            class: 'gjs-block-section',
            title: 'Radio buttons - choose one option'
        }
    });

    // Submit Button
    blockManager.add('submit-button', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">✅</div>
                <div style="font-size: 11px;">Submit</div>
            </div>
        `,
        category: 'Forms',
        content: `
            <button type="submit" style="display: inline-block; padding: 14px 40px; background-color: var(--brand-primary, #007bff); color: white; border: none; border-radius: 5px; font-weight: 600; font-family: var(--font-body, sans-serif); font-size: 16px; cursor: pointer; transition: all 0.3s;">
                Submit
            </button>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Submit button for forms'
        }
    });
}
