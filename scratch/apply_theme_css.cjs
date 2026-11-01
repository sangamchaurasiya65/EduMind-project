const fs = require('fs');

let css = fs.readFileSync('src/styles/index.css', 'utf-8');

const replacements = [
  // Subjects
  {
    target: `.subjects-search-input {
  width: 100%;
  padding: 0.7rem 2.2rem 0.7rem 2.6rem;
  background: #ffffff;`,
    replacement: `.subjects-search-input {
  width: 100%;
  padding: 0.7rem 2.2rem 0.7rem 2.6rem;
  background: var(--bg-surface);`
  },
  {
    target: `.subjects-category-tabs {
  display: flex;
  background: #f1f5f9;`,
    replacement: `.subjects-category-tabs {
  display: flex;
  background: var(--bg-surface-alt);`
  },
  {
    target: `.category-tab-btn.tab-selected {
  background: #ffffff;`,
    replacement: `.category-tab-btn.tab-selected {
  background: var(--bg-surface);`
  },
  {
    target: `.subject-catalog-card {
  background: #ffffff;`,
    replacement: `.subject-catalog-card {
  background: var(--bg-surface);`
  },
  {
    target: `.sub-card-topic-meta {
  font-size: 0.78rem;
  padding: 0.55rem 0.75rem;
  background: #f8fafc;
  border-radius: var(--radius-md);
  border: 1px solid #f1f5f9;`,
    replacement: `.sub-card-topic-meta {
  font-size: 0.78rem;
  padding: 0.55rem 0.75rem;
  background: var(--bg-surface-alt);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);`
  },
  {
    target: `.subject-detail-hero-card {
  background: #ffffff;`,
    replacement: `.subject-detail-hero-card {
  background: var(--bg-surface);`
  },
  {
    target: `.detail-hero-progress-box {
  width: 280px;
  background: #f8fafc;`,
    replacement: `.detail-hero-progress-box {
  width: 280px;
  background: var(--bg-surface-alt);`
  },
  {
    target: `.chapter-row-item {
  background: #ffffff;`,
    replacement: `.chapter-row-item {
  background: var(--bg-surface);`
  },
  {
    target: `.chapter-row-item:hover {
  border-color: #cbd5e1;
  background: #fbfcfe;
}`,
    replacement: `.chapter-row-item:hover {
  border-color: var(--border-medium);
  background: var(--bg-surface-alt);
}`
  },
  {
    target: `.icon-circle-comp {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #ecfdf5;`,
    replacement: `.icon-circle-comp {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(16, 185, 129, 0.15);`
  },
  {
    target: `.icon-circle-curr {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #ffffff;`,
    replacement: `.icon-circle-curr {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-surface);`
  },
  {
    target: `.icon-circle-lock {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f1f5f9;`,
    replacement: `.icon-circle-lock {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-surface-alt);`
  },
  {
    target: `.resource-card {
  background: #ffffff;`,
    replacement: `.resource-card {
  background: var(--bg-surface);`
  },
  // Progress
  {
    target: `.timeframe-selector-group {
  display: flex;
  background: #f1f5f9;`,
    replacement: `.timeframe-selector-group {
  display: flex;
  background: var(--bg-surface-alt);`
  },
  {
    target: `.timeframe-tab-btn.tab-active {
  background: #ffffff;`,
    replacement: `.timeframe-tab-btn.tab-active {
  background: var(--bg-surface);`
  },
  {
    target: `.quiz-performance-metrics-strip {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 1.25rem;
  background: #f8fafc;`,
    replacement: `.quiz-performance-metrics-strip {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 1.25rem;
  background: var(--bg-surface-alt);`
  },
  {
    target: `.achievement-item-card {
  background: #ffffff;`,
    replacement: `.achievement-item-card {
  background: var(--bg-surface);`
  },
  // Quizzes
  {
    target: `.quiz-select-card {
  background: #ffffff;`,
    replacement: `.quiz-select-card {
  background: var(--bg-surface);`
  },
  {
    target: `.quiz-difficulty-tag {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  background: #f1f5f9;`,
    replacement: `.quiz-difficulty-tag {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-surface-alt);`
  },
  {
    target: `.active-quiz-header-card {
  background: #ffffff;`,
    replacement: `.active-quiz-header-card {
  background: var(--bg-surface);`
  },
  {
    target: `.quiz-timer-box {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.85rem;
  background: #ffffff;`,
    replacement: `.quiz-timer-box {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.85rem;
  background: var(--bg-surface);`
  },
  {
    target: `.quiz-question-card {
  background: #ffffff;`,
    replacement: `.quiz-question-card {
  background: var(--bg-surface);`
  },
  {
    target: `.quiz-option-btn {
  background: #ffffff;
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
  transition: all var(--transition-fast);
  cursor: pointer;
  position: relative;
}`,
    replacement: `.quiz-option-btn {
  background: var(--bg-surface);
  color: var(--text-main);
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
  transition: all var(--transition-fast);
  cursor: pointer;
  position: relative;
}`
  },
  {
    target: `.quiz-option-btn:hover {
  border-color: #c7d2fe;
  background: #f8fafc;
}`,
    replacement: `.quiz-option-btn:hover {
  border-color: #c7d2fe;
  background: var(--bg-surface-alt);
}`
  },
  {
    target: `.option-letter-badge {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: #f1f5f9;`,
    replacement: `.option-letter-badge {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--bg-surface-alt);`
  },
  {
    target: `.quiz-controls-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1.5rem;
  border-top: 1px solid #f1f5f9;
}`,
    replacement: `.quiz-controls-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-light);
}`
  },
  {
    target: `.quiz-result-hero-card {
  background: #ffffff;`,
    replacement: `.quiz-result-hero-card {
  background: var(--bg-surface);`
  },
  {
    target: `.result-trophy-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #ecfdf5;`,
    replacement: `.result-trophy-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(16, 185, 129, 0.15);`
  },
  {
    target: `.result-feedback-box {
  background: #f8fafc;`,
    replacement: `.result-feedback-box {
  background: var(--bg-surface-alt);`
  },
  {
    target: `.review-item-card {
  background: #ffffff;`,
    replacement: `.review-item-card {
  background: var(--bg-surface);`
  },
  {
    target: `.review-explanation-box {
  background: #f8fafc;`,
    replacement: `.review-explanation-box {
  background: var(--bg-surface-alt);`
  },
  // AI Assistant
  {
    target: `.prototype-mode-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: var(--radius-full);
  background: #f1f5f9;`,
    replacement: `.prototype-mode-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: var(--radius-full);
  background: var(--bg-surface-alt);`
  },
  {
    target: `.ai-welcome-box {
  background: #ffffff;`,
    replacement: `.ai-welcome-box {
  background: var(--bg-surface);`
  },
  {
    target: `.suggestion-card-btn {
  background: #f8fafc;`,
    replacement: `.suggestion-card-btn {
  background: var(--bg-surface-alt);`
  },
  {
    target: `.ai-chat-card {
  background: #ffffff;`,
    replacement: `.ai-chat-card {
  background: var(--bg-surface);`
  },
  {
    target: `.ai-chat-card-header {
  padding: 1rem 1.4rem;
  background: #f8fafc;`,
    replacement: `.ai-chat-card-header {
  padding: 1rem 1.4rem;
  background: var(--bg-surface);`
  },
  {
    target: `.clear-chat-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: var(--text-muted);
  padding: 0.3rem 0.65rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  background: white;`,
    replacement: `.clear-chat-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: var(--text-muted);
  padding: 0.3rem 0.65rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  background: var(--bg-surface);`
  },
  {
    target: `.clear-chat-btn:hover {
  background: #f1f5f9;`,
    replacement: `.clear-chat-btn:hover {
  background: var(--bg-surface-alt);`
  },
  {
    target: `.ai-chat-messages-window {
  flex: 1;
  padding: 1.25rem 1.4rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
  background: #fcfdfe;
}`,
    replacement: `.ai-chat-messages-window {
  flex: 1;
  padding: 1.25rem 1.4rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
  background: var(--bg-main);
}`
  },
  {
    target: `.msg-ai .ai-bubble-body {
  background: #f1f5f9;
  color: var(--text-main);
  border-bottom-left-radius: 4px;
  border: 1px solid #e2e8f0;
}`,
    replacement: `.msg-ai .ai-bubble-body {
  background: var(--bg-surface-alt);
  color: var(--text-main);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--border-light);
}`
  },
  {
    target: `.ai-quick-chips-bar {
  padding: 0.65rem 1.25rem;
  background: #f8fafc;`,
    replacement: `.ai-quick-chips-bar {
  padding: 0.65rem 1.25rem;
  background: var(--bg-surface-alt);`
  },
  {
    target: `.quick-chip-btn {
  font-size: 0.78rem;
  font-weight: 500;
  padding: 0.35rem 0.75rem;
  background: #ffffff;`,
    replacement: `.quick-chip-btn {
  font-size: 0.78rem;
  font-weight: 500;
  padding: 0.35rem 0.75rem;
  background: var(--bg-surface);`
  },
  {
    target: `.ai-chat-input-container {
  padding: 0.85rem 1.25rem;
  background: #ffffff;`,
    replacement: `.ai-chat-input-container {
  padding: 0.85rem 1.25rem;
  background: var(--bg-surface);`
  },
  {
    target: `.mic-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  background: #f8fafc;`,
    replacement: `.mic-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  background: var(--bg-surface-alt);`
  },
  {
    target: `.ai-chat-input-field {
  flex: 1;
  padding: 0.7rem 1rem;
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: 0.92rem;
  color: var(--text-main);
  background: #fcfcfd;
  transition: all var(--transition-fast);
}

.ai-chat-input-field:focus {
  outline: none;
  border-color: var(--primary);
  background: white;`,
    replacement: `.ai-chat-input-field {
  flex: 1;
  padding: 0.7rem 1rem;
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: 0.92rem;
  color: var(--text-main);
  background: var(--bg-surface-alt);
  transition: all var(--transition-fast);
}

.ai-chat-input-field:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--bg-surface);`
  },
  {
    target: `.context-suggestion-card {
  background: #f8fafc;`,
    replacement: `.context-suggestion-card {
  background: var(--bg-surface-alt);`
  },
  // Dashboard
  {
    target: `.overview-card {
  background: #ffffff;`,
    replacement: `.overview-card {
  background: var(--bg-surface);`
  },
  {
    target: `.quick-action-card {
  background: #ffffff;`,
    replacement: `.quick-action-card {
  background: var(--bg-surface);`
  },
  {
    target: `.continue-subject-card {
  background: #ffffff;`,
    replacement: `.continue-subject-card {
  background: var(--bg-surface);`
  },
  {
    target: `.continue-subject-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.6rem;
  border-top: 1px solid #f8fafc;
}`,
    replacement: `.continue-subject-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.6rem;
  border-top: 1px solid var(--border-light);
}`
  },
  {
    target: `.weekly-chart-card {
  background: #ffffff;`,
    replacement: `.weekly-chart-card {
  background: var(--bg-surface);`
  },
  {
    target: `.bar-fill {
  width: 100%;
  background: #cbd5e1;`,
    replacement: `.bar-fill {
  width: 100%;
  background: var(--border-medium);`
  },
  {
    target: `.side-widget-card {
  background: #ffffff;`,
    replacement: `.side-widget-card {
  background: var(--bg-surface);`
  },
  {
    target: `.recommendation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0.85rem;
  background: #f8fafc;`,
    replacement: `.recommendation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0.85rem;
  background: var(--bg-surface-alt);`
  },
  {
    target: `.msg-ai .ai-bubble-body {
  background: #f8fafc;
  color: var(--text-main);
  border-bottom-left-radius: 4px;
  border: 1px solid #e2e8f0;
}`,
    replacement: `.msg-ai .ai-bubble-body {
  background: var(--bg-surface-alt);
  color: var(--text-main);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--border-light);
}`
  }
];

let applied = 0;
for (const { target, replacement } of replacements) {
  if (css.includes(target)) {
    css = css.replace(target, replacement);
    applied++;
  } else {
    console.warn('Target not found:', target.slice(0, 40));
  }
}

// Append Dark theme overrides for promo banner gradients and AiChatModal styles
const additionalStyles = `
/* ==============================================================================
   Dark Theme Enhancements & Modal Overlays
   ============================================================================== */
[data-theme="dark"] .ai-assistant-promo-card,
[data-theme="dark"] .quiz-recommended-card {
  background: var(--bg-surface-alt);
  border-color: var(--border-light);
}

[data-theme="dark"] .brand-logo {
  color: #f8fafc;
}

/* Modal Overlay & Dialog Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-content {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  width: 100%;
  max-width: 680px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modalPop 0.2s ease-out;
}

.modal-header {
  padding: 1.1rem 1.5rem;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-surface);
}

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.35rem;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-surface-alt);
  color: var(--text-main);
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: var(--bg-main);
}

.chat-msg {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}

.chat-msg.user {
  align-self: flex-end;
}

.chat-msg.user .msg-bubble {
  background: var(--primary);
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.chat-msg.ai {
  align-self: flex-start;
}

.chat-msg.ai .msg-bubble {
  background: var(--bg-surface-alt);
  color: var(--text-main);
  border: 1px solid var(--border-light);
  border-bottom-left-radius: 4px;
}

.msg-bubble {
  padding: 0.8rem 1.1rem;
  border-radius: var(--radius-lg);
  font-size: 0.92rem;
  line-height: 1.55;
}

.quick-prompts-bar {
  padding: 0.65rem 1.25rem;
  background: var(--bg-surface-alt);
  border-top: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  overflow-x: auto;
  white-space: nowrap;
}

.quick-prompt-pill {
  font-size: 0.78rem;
  font-weight: 500;
  padding: 0.35rem 0.75rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
  color: var(--primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-prompt-pill:hover {
  background: var(--primary-light);
  border-color: var(--primary);
}

.chat-input-box {
  padding: 0.85rem 1.25rem;
  background: var(--bg-surface);
  border-top: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.chat-input {
  flex: 1;
  padding: 0.65rem 1rem;
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  color: var(--text-main);
  background: var(--bg-surface-alt);
  transition: all var(--transition-fast);
}

.chat-input:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--bg-surface);
  box-shadow: 0 0 0 3px var(--primary-glow);
}
`;

if (!css.includes('.modal-overlay {')) {
  css += additionalStyles;
}

fs.writeFileSync('src/styles/index.css', css, 'utf-8');
console.log(`Applied ${applied} of ${replacements.length} replacements and updated styles.`);

