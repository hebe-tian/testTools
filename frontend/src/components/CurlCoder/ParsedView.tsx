import { useState, useCallback, useEffect } from 'react';
import type {
  ParsedCurl,
  QueryParam,
  HeaderItem,
  CookieItem,
  FormItem,
  BodyContent,
  AuthInfo,
  CurlGenerateRequest,
} from '../../types/curl';
import styles from './ParsedView.module.css';

interface ParsedViewProps {
  data: ParsedCurl;
  onGenerate: (data: CurlGenerateRequest) => void;
  loading?: boolean;
}

const METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'];

function getMethodClass(method: string): string {
  const map: Record<string, string> = {
    GET: styles.methodGet,
    POST: styles.methodPost,
    PUT: styles.methodPut,
    DELETE: styles.methodDelete,
    PATCH: styles.methodPatch,
  };
  return map[method.toUpperCase()] || '';
}

interface KvEditorProps<T extends { key: string; value: string; enabled: boolean }> {
  items: T[];
  onChange: (items: T[]) => void;
  keyPlaceholder?: string;
  valuePlaceholder?: string;
}

function KvEditor<T extends { key: string; value: string; enabled: boolean }>({
  items,
  onChange,
  keyPlaceholder = '键',
  valuePlaceholder = '值',
}: KvEditorProps<T>) {
  const handleToggle = (index: number) => {
    const next = [...items];
    next[index] = { ...next[index], enabled: !next[index].enabled };
    onChange(next);
  };

  const handleChange = (index: number, field: 'key' | 'value', val: string) => {
    const next = [...items];
    next[index] = { ...next[index], [field]: val };
    onChange(next);
  };

  const handleDelete = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const handleAdd = () => {
    onChange([...items, { key: '', value: '', enabled: true } as T]);
  };

  return (
    <div>
      {items.map((item, i) => (
        <div key={i} className={styles.kvRow}>
          <input
            type="checkbox"
            className={styles.kvCheckbox}
            checked={item.enabled}
            onChange={() => handleToggle(i)}
          />
          <input
            className={`${styles.kvInput} ${styles.kvKeyInput}`}
            value={item.key}
            onChange={(e) => handleChange(i, 'key', e.target.value)}
            placeholder={keyPlaceholder}
            disabled={!item.enabled}
          />
          <input
            className={styles.kvInput}
            value={item.value}
            onChange={(e) => handleChange(i, 'value', e.target.value)}
            placeholder={valuePlaceholder}
            disabled={!item.enabled}
          />
          <button className={styles.kvDeleteBtn} onClick={() => handleDelete(i)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.kvDeleteIcon}>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      ))}
      <button className={styles.addBtn} onClick={handleAdd}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.addBtnIcon}>
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        添加
      </button>
    </div>
  );
}

type BodyTab = 'json' | 'form' | 'raw';

export default function ParsedView({ data, onGenerate, loading }: ParsedViewProps) {
  const [method, setMethod] = useState(data.method);
  const [url, setUrl] = useState(data.url);
  const [queryParams, setQueryParams] = useState<QueryParam[]>(data.query_params);
  const [headers, setHeaders] = useState<HeaderItem[]>(data.headers);
  const [cookies, setCookies] = useState<CookieItem[]>(data.cookies);
  const [body, setBody] = useState<BodyContent | null>(data.body);
  const [auth, setAuth] = useState<AuthInfo | null>(data.auth);
  const [shellMode] = useState(data.shell_mode || 'bash');

  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    params: data.query_params.length > 0,
    headers: data.headers.length > 0,
    cookies: data.cookies.length > 0,
    body: data.body !== null,
    auth: data.auth !== null && data.auth.auth_type !== 'none',
  });

  const [bodyTab, setBodyTab] = useState<BodyTab>(() => {
    if (!data.body) return 'json';
    if (data.body.content_type === 'application/json') return 'json';
    if (data.body.content_type === 'multipart/form-data' || data.body.content_type === 'application/x-www-form-urlencoded') return 'form';
    return 'raw';
  });

  const toggleSection = useCallback((key: string) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  useEffect(() => {
    setMethod(data.method);
    setUrl(data.url);
    setQueryParams(data.query_params);
    setHeaders(data.headers);
    setCookies(data.cookies);
    setBody(data.body);
    setAuth(data.auth);
    setOpenSections({
      params: data.query_params.length > 0,
      headers: data.headers.length > 0,
      cookies: data.cookies.length > 0,
      body: data.body !== null,
      auth: data.auth !== null && data.auth.auth_type !== 'none',
    });
    if (data.body) {
      if (data.body.content_type === 'application/json') setBodyTab('json');
      else if (data.body.content_type === 'multipart/form-data' || data.body.content_type === 'application/x-www-form-urlencoded') setBodyTab('form');
      else setBodyTab('raw');
    }
  }, [data]);

  const handleGenerate = useCallback(() => {
    const req: CurlGenerateRequest = {
      method,
      url,
      query_params: queryParams,
      headers,
      body,
      auth,
      cookies,
      shell_mode: shellMode,
      compact: false,
    };
    onGenerate(req);
  }, [method, url, queryParams, headers, body, auth, cookies, shellMode, onGenerate]);

  const handleJsonFormat = useCallback(() => {
    if (!body || !body.json_data) return;
    try {
      const formatted = JSON.stringify(body.json_data, null, 2);
      setBody({ ...body, raw: formatted });
    } catch {
      // ignore
    }
  }, [body]);

  const handleBodyRawChange = useCallback((raw: string) => {
    if (!body) return;
    let jsonData: Record<string, unknown> | unknown[] | null = null;
    if (body.content_type === 'application/json') {
      try {
        jsonData = JSON.parse(raw);
      } catch {
        jsonData = null;
      }
    }
    setBody({ ...body, raw, json_data: jsonData });
  }, [body]);

  const handleAuthTypeChange = useCallback((authType: string) => {
    if (authType === 'none') {
      setAuth({ auth_type: 'none', token: null, username: null, password: null, key_name: null, key_value: null, key_location: null });
    } else if (authType === 'bearer') {
      setAuth({ auth_type: 'bearer', token: auth?.token || '', username: null, password: null, key_name: null, key_value: null, key_location: null });
    } else if (authType === 'basic') {
      setAuth({ auth_type: 'basic', token: null, username: auth?.username || '', password: auth?.password || '', key_name: null, key_value: null, key_location: null });
    } else if (authType === 'api_key') {
      setAuth({ auth_type: 'api_key', token: null, username: null, password: null, key_name: auth?.key_name || '', key_value: auth?.key_value || '', key_location: auth?.key_location || 'header' });
    }
  }, [auth]);

  const enabledParams = queryParams.filter((p) => p.enabled).length;
  const enabledHeaders = headers.filter((h) => h.enabled).length;
  const enabledCookies = cookies.filter((c) => c.enabled).length;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.headerIcon}>
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          解析结果
        </div>
      </div>

      <div className={styles.urlRow}>
        <select
          className={`${styles.methodSelect} ${getMethodClass(method)}`}
          value={method}
          onChange={(e) => setMethod(e.target.value)}
        >
          {METHODS.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
        <input
          className={styles.urlInput}
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://api.example.com/endpoint"
          spellCheck={false}
        />
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader} onClick={() => toggleSection('params')}>
          <div className={styles.sectionHeaderLeft}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.sectionChevron + (openSections.params ? ` ${styles.sectionChevronOpen}` : '')}>
              <polyline points="9 18 15 12 9 6" />
            </svg>
            查询参数
            <span className={styles.badge}>{enabledParams}</span>
          </div>
        </div>
        {openSections.params && (
          <div className={styles.sectionBody}>
            <KvEditor items={queryParams} onChange={setQueryParams} keyPlaceholder="参数名" valuePlaceholder="参数值" />
          </div>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader} onClick={() => toggleSection('headers')}>
          <div className={styles.sectionHeaderLeft}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.sectionChevron + (openSections.headers ? ` ${styles.sectionChevronOpen}` : '')}>
              <polyline points="9 18 15 12 9 6" />
            </svg>
            请求头
            <span className={styles.badge}>{enabledHeaders}</span>
          </div>
        </div>
        {openSections.headers && (
          <div className={styles.sectionBody}>
            <KvEditor items={headers} onChange={setHeaders} keyPlaceholder="请求头名称" valuePlaceholder="请求头值" />
          </div>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader} onClick={() => toggleSection('cookies')}>
          <div className={styles.sectionHeaderLeft}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.sectionChevron + (openSections.cookies ? ` ${styles.sectionChevronOpen}` : '')}>
              <polyline points="9 18 15 12 9 6" />
            </svg>
            Cookie
            <span className={styles.badge}>{enabledCookies}</span>
          </div>
        </div>
        {openSections.cookies && (
          <div className={styles.sectionBody}>
            <KvEditor items={cookies} onChange={setCookies} keyPlaceholder="Cookie 名称" valuePlaceholder="Cookie 值" />
          </div>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader} onClick={() => toggleSection('body')}>
          <div className={styles.sectionHeaderLeft}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.sectionChevron + (openSections.body ? ` ${styles.sectionChevronOpen}` : '')}>
              <polyline points="9 18 15 12 9 6" />
            </svg>
            请求体
          </div>
        </div>
        {openSections.body && (
          <>
            <div className={styles.bodyTabs}>
              <button
                className={`${styles.bodyTab} ${bodyTab === 'json' ? styles.bodyTabActive : ''}`}
                onClick={() => setBodyTab('json')}
              >
                JSON
              </button>
              <button
                className={`${styles.bodyTab} ${bodyTab === 'form' ? styles.bodyTabActive : ''}`}
                onClick={() => setBodyTab('form')}
              >
                表单数据
              </button>
              <button
                className={`${styles.bodyTab} ${bodyTab === 'raw' ? styles.bodyTabActive : ''}`}
                onClick={() => setBodyTab('raw')}
              >
                Raw
              </button>
            </div>
            <div className={styles.bodyContent}>
              {bodyTab === 'json' && (
                <>
                  <div className={styles.bodyToolbar}>
                    <button className={styles.formatBtn} onClick={handleJsonFormat}>格式化</button>
                  </div>
                  <textarea
                    className={styles.bodyTextarea}
                    value={body?.raw || ''}
                    onChange={(e) => handleBodyRawChange(e.target.value)}
                    placeholder='{"key": "value"}'
                    spellCheck={false}
                  />
                </>
              )}
              {bodyTab === 'form' && (
                <KvEditor<FormItem>
                  items={body?.form_data || []}
                  onChange={(items) => {
                    if (body) setBody({ ...body, form_data: items });
                    else setBody({ content_type: 'multipart/form-data', raw: '', json_data: null, form_data: items });
                  }}
                  keyPlaceholder="字段名"
                  valuePlaceholder="字段值"
                />
              )}
              {bodyTab === 'raw' && (
                <textarea
                  className={styles.bodyTextarea}
                  value={body?.raw || ''}
                  onChange={(e) => handleBodyRawChange(e.target.value)}
                  placeholder="原始请求体"
                  spellCheck={false}
                />
              )}
            </div>
          </>
        )}
        {openSections.body && !body && (
          <div className={styles.emptyBody}>此请求无请求体内容</div>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader} onClick={() => toggleSection('auth')}>
          <div className={styles.sectionHeaderLeft}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={styles.sectionChevron + (openSections.auth ? ` ${styles.sectionChevronOpen}` : '')}>
              <polyline points="9 18 15 12 9 6" />
            </svg>
            认证
          </div>
        </div>
        {openSections.auth && (
          <div className={styles.sectionBody}>
            <div className={styles.authTypeRow}>
              <span className={styles.authLabel}>类型</span>
              <select
                className={styles.authSelect}
                value={auth?.auth_type || 'none'}
                onChange={(e) => handleAuthTypeChange(e.target.value)}
              >
                <option value="none">无</option>
                <option value="bearer">Bearer Token</option>
                <option value="basic">Basic 认证</option>
                <option value="api_key">API Key</option>
              </select>
            </div>
            {auth?.auth_type === 'bearer' && (
              <div className={styles.authField}>
                <span className={styles.authFieldLabel}>令牌</span>
                <input
                  className={styles.authFieldInput}
                  value={auth.token || ''}
                  onChange={(e) => setAuth({ ...auth, token: e.target.value })}
                  placeholder="Bearer 令牌"
                  spellCheck={false}
                />
              </div>
            )}
            {auth?.auth_type === 'basic' && (
              <>
                <div className={styles.authField}>
                  <span className={styles.authFieldLabel}>用户名</span>
                  <input
                    className={styles.authFieldInput}
                    value={auth.username || ''}
                    onChange={(e) => setAuth({ ...auth, username: e.target.value })}
                    placeholder="用户名"
                    spellCheck={false}
                  />
                </div>
                <div className={styles.authField}>
                  <span className={styles.authFieldLabel}>密码</span>
                  <input
                    className={styles.authFieldInput}
                    type="password"
                    value={auth.password || ''}
                    onChange={(e) => setAuth({ ...auth, password: e.target.value })}
                    placeholder="密码"
                    spellCheck={false}
                  />
                </div>
              </>
            )}
            {auth?.auth_type === 'api_key' && (
              <>
                <div className={styles.authField}>
                  <span className={styles.authFieldLabel}>键名</span>
                  <input
                    className={styles.authFieldInput}
                    value={auth.key_name || ''}
                    onChange={(e) => setAuth({ ...auth, key_name: e.target.value })}
                    placeholder="X-API-Key"
                    spellCheck={false}
                  />
                </div>
                <div className={styles.authField}>
                  <span className={styles.authFieldLabel}>键值</span>
                  <input
                    className={styles.authFieldInput}
                    value={auth.key_value || ''}
                    onChange={(e) => setAuth({ ...auth, key_value: e.target.value })}
                    placeholder="API 密钥值"
                    spellCheck={false}
                  />
                </div>
                <div className={styles.authField}>
                  <span className={styles.authFieldLabel}>位置</span>
                  <select
                    className={styles.authSelect}
                    value={auth.key_location || 'header'}
                    onChange={(e) => setAuth({ ...auth, key_location: e.target.value })}
                  >
                    <option value="header">请求头</option>
                    <option value="query">查询参数</option>
                  </select>
                </div>
              </>
            )}
            {auth?.auth_type === 'none' && (
              <div className={styles.emptyBody}>未配置认证信息</div>
            )}
          </div>
        )}
      </div>

      <div className={styles.generateRow}>
        <button className={styles.generateBtn} onClick={handleGenerate} disabled={loading}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.generateBtnIcon}>
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
          </svg>
          生成 Curl
        </button>
      </div>
    </div>
  );
}
