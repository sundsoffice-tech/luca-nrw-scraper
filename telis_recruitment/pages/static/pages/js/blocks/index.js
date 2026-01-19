/**
 * Block Loader for GrapesJS Builder
 * Loads all block categories: Layout, Basic, Forms, LUCA Custom, Advanced
 */

import loadLayoutBlocks from './layout.js';
import loadBasicBlocks from './basic.js';
import loadFormBlocks from './forms.js';
import loadLucaCustomBlocks from './luca-custom.js';
import loadAdvancedBlocks from './advanced.js';

export default function loadAllBlocks(editor) {
    // Load blocks by category
    loadLayoutBlocks(editor);
    loadBasicBlocks(editor);
    loadFormBlocks(editor);
    loadLucaCustomBlocks(editor);
    loadAdvancedBlocks(editor);
}
