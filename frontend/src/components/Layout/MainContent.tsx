import type { ReactNode } from 'react';
import styles from './MainContent.module.css';

interface MainContentProps {
  title: string;
  children: ReactNode;
  loading?: boolean;
  error?: string | null;
  onBackHome?: () => void;
}

export default function MainContent({ title, children, loading, error, onBackHome }: MainContentProps) {
  const statusClass = error
    ? styles.statusDotError
    : loading
      ? styles.statusDotLoading
      : styles.statusDot;

  const statusText = error
    ? `错误: ${error}`
    : loading
      ? '处理中...'
      : '就绪';

  return (
    <div className={styles.mainContent}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          {onBackHome && (
            <button className={styles.backBtn} onClick={onBackHome}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.backIcon}>
                <polyline points="15 18 9 12 15 6" />
              </svg>
              <span>首页</span>
            </button>
          )}
          <div className={styles.headerTitle}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.headerTitleIcon}>
              <polyline points="4 17 10 11 4 5" />
              <line x1="12" y1="19" x2="20" y2="19" />
            </svg>
            {title}
          </div>
        </div>
        <div className={styles.headerBreadcrumb}>
          {onBackHome ? (
            <span className={styles.breadcrumbLink} onClick={onBackHome}>首页</span>
          ) : (
            <span>Tools</span>
          )}
          <span className={styles.headerBreadcrumbSep}>/</span>
          <span>Tools</span>
          <span className={styles.headerBreadcrumbSep}>/</span>
          {title}
        </div>
      </div>

      <div className={styles.body}>
        {children}
      </div>

      <div className={styles.statusBar}>
        <div className={styles.statusLeft}>
          <span className={statusClass} />
          <span>{statusText}</span>
        </div>
        <span>testTools v0.1.0</span>
      </div>
    </div>
  );
}
