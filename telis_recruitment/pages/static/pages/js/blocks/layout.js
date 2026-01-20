/**
 * Layout Blocks for GrapesJS Builder
 * Includes: Section, 2/3/4 Column Grids, Divider, Spacer
 */

export default function loadLayoutBlocks(editor) {
    const blockManager = editor.BlockManager;

    // Full-width Section
    blockManager.add('section', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">📦</div>
                <div style="font-size: 11px;">Section</div>
            </div>
        `,
        category: 'Layout',
        content: `
            <section class="section" style="padding: 60px 20px; background-color: #ffffff;">
                <div class="container" style="max-width: 1200px; margin: 0 auto;">
                    <p>Add your content here...</p>
                </div>
            </section>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Full-width section container - holds other elements'
        }
    });

    // 2 Column Grid
    blockManager.add('2-columns', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">⬜⬜</div>
                <div style="font-size: 11px;">2 Columns</div>
            </div>
        `,
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
        attributes: { 
            class: 'gjs-block-section',
            title: 'Two equal-width columns - stacks on mobile'
        }
    });

    // 3 Column Grid
    blockManager.add('3-columns', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 20px; margin-bottom: 5px;">⬜⬜⬜</div>
                <div style="font-size: 11px;">3 Columns</div>
            </div>
        `,
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
        attributes: { 
            class: 'gjs-block-section',
            title: 'Three equal-width columns - stacks on mobile'
        }
    });

    // 4 Column Grid
    blockManager.add('4-columns', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 18px; margin-bottom: 5px;">⬜⬜⬜⬜</div>
                <div style="font-size: 11px;">4 Columns</div>
            </div>
        `,
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
        attributes: { 
            class: 'gjs-block-section',
            title: 'Four equal-width columns - stacks on mobile'
        }
    });

    // Divider
    blockManager.add('divider', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">━━</div>
                <div style="font-size: 11px;">Divider</div>
            </div>
        `,
        category: 'Layout',
        content: `
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 40px 0;">
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Horizontal line to separate content'
        }
    });

    // Spacer
    blockManager.add('spacer', {
        label: `
            <div style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">⬇️</div>
                <div style="font-size: 11px;">Spacer</div>
            </div>
        `,
        category: 'Layout',
        content: `
            <div class="spacer" style="height: 60px;"></div>
        `,
        attributes: { 
            class: 'gjs-block-section',
            title: 'Add vertical space between elements'
        }
    });
}
