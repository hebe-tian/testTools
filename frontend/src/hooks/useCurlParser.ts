import { useState } from 'react';
import { apiClient } from '../api';
import type { ParsedCurl, CurlGenerateRequest, CurlGenerateResponse } from '../types/curl';

export function useCurlParser() {
  const [parsed, setParsed] = useState<ParsedCurl | null>(null);
  const [generatedCurl, setGeneratedCurl] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parseCurl = async (curlText: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<ParsedCurl>('/api/v1/curl/parse', {
        curl_text: curlText,
      });
      setParsed(data);
      setGeneratedCurl('');
      return data;
    } catch (err) {
      const msg = err instanceof Error ? err.message : '解析失败';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const generateCurl = async (data: CurlGenerateRequest) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.post<CurlGenerateResponse>('/api/v1/curl/generate', data);
      setGeneratedCurl(result.curl_text);
      return result.curl_text;
    } catch (err) {
      const msg = err instanceof Error ? err.message : '生成失败';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setParsed(null);
    setGeneratedCurl('');
    setError(null);
  };

  return { parsed, generatedCurl, loading, error, parseCurl, generateCurl, clearAll, setParsed };
}
