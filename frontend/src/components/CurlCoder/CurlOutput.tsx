import { useState, useCallback, useEffect, useRef } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-powershell';
import 'prismjs/themes/prism-tomorrow.css';
import styles from './CurlOutput.module.css';

interface CurlOutputProps {
  curlText: string;
  onRegenerate?: (shellMode: string, compact: boolean) => void;
}

const SHELL_MODES = [
  { id: 'bash', label: 'Bash' },
  { id: 'powershell', label: 'PS' },
  { id: 'cmd', label: 'CMD' },
];

export default function CurlOutput({ curlText, onRegenerate }: CurlOutputProps) {
  const [shellMode, setShellMode] = useState('bash');
  const [compact, setCompact] = useState(false);
  const [copied, setCopied] = useState(false);
  const codeRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (codeRef.current && curlText) {
      Prism.highlightElement(codeRef.current, false, () => {
        // highlight complete
      });
    }
  }, [curlText, shellMode]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(curlText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const textarea = document.createElement('textarea');
      textarea.value = curlText;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [curlText]);

  const handleShellChange = useCallback((mode: string) => {
    setShellMode(mode);
    if (onRegenerate) {
      onRegenerate(mode, compact);
    }
  }, [compact, onRegenerate]);

  const handleCompactToggle = useCallback(() => {
    const next = !compact;
    setCompact(next);
    if (onRegenerate) {
      onRegenerate(shellMode, next);
    }
  }, [compact, shellMode, onRegenerate]);

  const lines = curlText.split('\n');

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.headerIcon}>
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
          </svg>
          生成的 Curl
        </div>
      </div>

      <div className={styles.toolbar}>
        <div className={styles.shellBtnGroup}>
          {SHELL_MODES.map((mode) => (
            <button
              key={mode.id}
              className={`${styles.shellBtn} ${shellMode === mode.id ? styles.shellBtnActive : ''}`}
              onClick={() => handleShellChange(mode.id)}
            >
              {mode.label}
            </button>
          ))}
        </div>
        <div className={styles.toolbarSpacer} />
        <button
          className={`${styles.compactToggle} ${compact ? styles.compactToggleActive : ''}`}
          onClick={handleCompactToggle}
        >
          紧凑
        </button>
        <button
          className={`${styles.copyBtn} ${copied ? styles.copyBtnCopied : ''}`}
          onClick={handleCopy}
        >
          {copied ? (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.copyBtnIcon}>
                <polyline points="20 6 9 17 4 12" />
              </svg>
              已复制
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.copyBtnIcon}>
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              复制
            </>
          )}
        </button>
      </div>

      <div className={styles.codeBlock}>
        <div className={styles.lineNumbers}>
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>
        <div className={styles.codeContent}>
          <pre>
            <code ref={codeRef} className={`language-${shellMode === 'powershell' ? 'powershell' : 'bash'}`}>
              {curlText}
            </code>
          </pre>
        </div>
      </div>
    </div>
  );
}
