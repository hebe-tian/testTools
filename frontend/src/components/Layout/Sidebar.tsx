import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import styles from './Sidebar.module.css';

interface ToolItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const tools: ToolItem[] = [
  {
    id: 'curl-coder',
    label: 'Curl Coder',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.navItemIcon}>
        <polyline points="4 17 10 11 4 5" />
        <line x1="12" y1="19" x2="20" y2="19" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const activeTool = location.pathname.startsWith('/tools/')
    ? location.pathname.replace('/tools/', '')
    : '';

  const handleBrandClick = () => {
    navigate('/');
  };

  const handleToolClick = (toolId: string) => {
    navigate(`/tools/${toolId}`);
  };

  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.sidebarCollapsed : ''}`}>
      <div className={styles.brand} onClick={handleBrandClick}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.brandIcon}>
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        <span className={styles.brandText}>
          test<span className={styles.brandAccent}>Tools</span>
        </span>
      </div>

      <nav className={styles.navSection}>
        <div className={styles.navLabel}>Tools</div>
        {tools.map((tool) => (
          <div
            key={tool.id}
            className={`${styles.navItem} ${activeTool === tool.id ? styles.navItemActive : ''}`}
            onClick={() => handleToolClick(tool.id)}
          >
            {tool.icon}
            <span className={styles.navItemText}>{tool.label}</span>
          </div>
        ))}
      </nav>

      <div className={styles.footer}>
        <button className={styles.collapseBtn} onClick={() => setCollapsed(!collapsed)}>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`${styles.collapseIcon} ${collapsed ? styles.collapseIconFlipped : ''}`}
          >
            <polyline points="11 17 6 12 11 7" />
            <polyline points="18 17 13 12 18 7" />
          </svg>
          <span className={styles.collapseText}>{collapsed ? '' : '收起'}</span>
        </button>
      </div>
    </aside>
  );
}
