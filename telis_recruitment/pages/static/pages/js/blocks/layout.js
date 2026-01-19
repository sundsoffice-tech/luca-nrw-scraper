/**
 * Layout Blocks for GrapesJS Builder
 * Includes: Section, 2/3/4 Column Grids, Divider, Spacer
 */

export default function loadLayoutBlocks(editor) {
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
