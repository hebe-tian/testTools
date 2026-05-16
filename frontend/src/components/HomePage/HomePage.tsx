import { useNavigate } from 'react-router-dom';
import styles from './HomePage.module.css';

interface ToolCard {
  id: string;
  title: string;
  description: string;
  tags: string[];
  icon: React.ReactNode;
  disabled?: boolean;
}

const tools: ToolCard[] = [
  {
    id: 'curl-coder',
    title: 'Curl Coder',
    description: '解析和生成 curl 命令，支持编辑后重新生成',
    tags: ['bash', 'PowerShell', 'CMD'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.cardIcon}>
        <polyline points="4 17 10 11 4 5" />
        <line x1="12" y1="19" x2="20" y2="19" />
      </svg>
    ),
  },
  {
    id: 'more-tools',
    title: '更多工具',
    description: '更多测试工具即将推出，敬请期待',
    tags: ['即将推出'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.cardIcon}>
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="16" />
        <line x1="8" y1="12" x2="16" y2="12" />
      </svg>
    ),
    disabled: true,
  },
];

export default function HomePage() {
  const navigate = useNavigate();

  const handleCardClick = (tool: ToolCard) => {
    if (tool.disabled) return;
    navigate(`/tools/${tool.id}`);
  };

  return (
    <div className={styles.homePage}>
      <div className={styles.header}>
        <div className={styles.headerBrand}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.headerBrandIcon}>
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
          <span className={styles.headerBrandText}>
            test<span className={styles.headerBrandAccent}>Tools</span>
          </span>
        </div>
        <span className={styles.headerVersion}>v0.1.0</span>
      </div>

      <div className={styles.body}>
        <div className={styles.hero}>
          <h1 className={styles.heroTitle}>测试工具集</h1>
          <p className={styles.heroSubtitle}>选择一个工具开始使用</p>
        </div>

        <div className={styles.cardGrid}>
          {tools.map((tool) => (
            <div
              key={tool.id}
              className={`${styles.card} ${tool.disabled ? styles.cardDisabled : ''}`}
              onClick={() => handleCardClick(tool)}
            >
              <div className={styles.cardIconWrap}>{tool.icon}</div>
              <div className={styles.cardContent}>
                <div className={styles.cardTitle}>{tool.title}</div>
                <div className={styles.cardDesc}>{tool.description}</div>
                <div className={styles.cardTags}>
                  {tool.tags.map((tag) => (
                    <span key={tag} className={styles.cardTag}>{tag}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.statusBar}>
        <div className={styles.statusLeft}>
          <span className={styles.statusDot} />
          <span>就绪</span>
        </div>
        <span>testTools v0.1.0</span>
      </div>
    </div>
  );
}
