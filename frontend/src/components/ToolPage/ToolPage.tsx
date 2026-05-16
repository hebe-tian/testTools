import { useParams, useNavigate } from 'react-router-dom';
import { useCallback, useRef } from 'react';
import Sidebar from '../Layout/Sidebar';
import MainContent from '../Layout/MainContent';
import CurlInput from '../CurlCoder/CurlInput';
import ParsedView from '../CurlCoder/ParsedView';
import CurlOutput from '../CurlCoder/CurlOutput';
import { useCurlParser } from '../../hooks/useCurlParser';
import type { CurlGenerateRequest } from '../../types/curl';
import styles from './ToolPage.module.css';

const toolConfig: Record<string, { title: string }> = {
  'curl-coder': { title: 'Curl Coder' },
};

export default function ToolPage() {
  const { toolId } = useParams<{ toolId: string }>();
  const navigate = useNavigate();
  const { parsed, generatedCurl, loading, error, parseCurl, generateCurl, clearAll } = useCurlParser();
  const lastGenerateData = useRef<CurlGenerateRequest | null>(null);

  const config = toolConfig[toolId ?? ''] ?? { title: 'Unknown Tool' };

  const handleParse = useCallback(async (curlText: string) => {
    try {
      await parseCurl(curlText);
    } catch {
      // error handled in hook
    }
  }, [parseCurl]);

  const handleGenerate = useCallback(async (data: CurlGenerateRequest) => {
    lastGenerateData.current = data;
    try {
      await generateCurl(data);
    } catch {
      // error handled in hook
    }
  }, [generateCurl]);

  const handleRegenerate = useCallback(async (shellMode: string, compact: boolean) => {
    if (lastGenerateData.current) {
      const data: CurlGenerateRequest = {
        ...lastGenerateData.current,
        shell_mode: shellMode,
        compact,
      };
      try {
        await generateCurl(data);
      } catch {
        // error handled in hook
      }
    }
  }, [generateCurl]);

  const handleBackHome = useCallback(() => {
    navigate('/');
  }, [navigate]);

  const renderTool = () => {
    if (toolId === 'curl-coder') {
      return (
        <>
          <CurlInput onParse={handleParse} onClear={clearAll} loading={loading} />
          {parsed && (
            <ParsedView data={parsed} onGenerate={handleGenerate} loading={loading} />
          )}
          {generatedCurl && (
            <CurlOutput curlText={generatedCurl} onRegenerate={handleRegenerate} />
          )}
        </>
      );
    }
    return <div style={{ padding: 24, color: 'var(--color-text-secondary)' }}>未找到该工具</div>;
  };

  return (
    <div className={styles.toolPage}>
      <Sidebar />
      <MainContent title={config.title} loading={loading} error={error} onBackHome={handleBackHome}>
        {renderTool()}
      </MainContent>
    </div>
  );
}
