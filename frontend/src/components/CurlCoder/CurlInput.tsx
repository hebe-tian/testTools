import { useState, useCallback } from 'react';
import styles from './CurlInput.module.css';

interface CurlInputProps {
  onParse: (curlText: string) => void;
  onClear: () => void;
  loading?: boolean;
}

function detectShell(text: string): string {
  const lower = text.toLowerCase();
  if (lower.includes('invoke-webrequest') || lower.includes('curl.exe') && lower.includes('-usebasicparsing')) {
    return 'PowerShell';
  }
  if (lower.includes('cmd') || (lower.includes('curl') && !lower.includes('bash'))) {
    if (lower.includes('^') && lower.includes('\\')) return 'CMD';
  }
  return 'bash';
}

export default function CurlInput({ onParse, onClear, loading }: CurlInputProps) {
  const [text, setText] = useState('');
  const shellTag = text.trim() ? detectShell(text) : '';

  const handleParse = useCallback(() => {
    if (text.trim()) {
      onParse(text.trim());
    }
  }, [text, onParse]);

  const handleClear = useCallback(() => {
    setText('');
    onClear();
  }, [onClear]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleParse();
    }
  }, [handleParse]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.headerIcon}>
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Curl 输入
        </div>
        {shellTag && <span className={styles.shellTag}>{shellTag}</span>}
      </div>

      <div className={styles.textareaWrap}>
        <textarea
          className={styles.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="在此粘贴 curl 命令... (Ctrl+Enter 解析)"
          spellCheck={false}
        />
      </div>

      <div className={styles.toolbar}>
        <span className={styles.charCount}>{text.length} 字符</span>
        <div className={styles.actions}>
          <button className={styles.clearBtn} onClick={handleClear} disabled={!text && !loading}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.clearBtnIcon}>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            清空
          </button>
          <button className={styles.parseBtn} onClick={handleParse} disabled={!text.trim() || loading}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.parseBtnIcon}>
              <polyline points="16 18 22 12 16 6" />
              <polyline points="8 6 2 12 8 18" />
            </svg>
            解析
          </button>
        </div>
      </div>
    </div>
  );
}
