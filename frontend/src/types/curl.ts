export interface QueryParam {
  key: string;
  value: string;
  enabled: boolean;
}

export interface HeaderItem {
  key: string;
  value: string;
  enabled: boolean;
}

export interface FormItem {
  key: string;
  value: string;
  enabled: boolean;
}

export interface CookieItem {
  key: string;
  value: string;
  enabled: boolean;
}

export interface BodyContent {
  content_type: string;
  raw: string;
  json_data: Record<string, unknown> | unknown[] | null;
  form_data: FormItem[] | null;
}

export interface AuthInfo {
  auth_type: string;
  token: string | null;
  username: string | null;
  password: string | null;
  key_name: string | null;
  key_value: string | null;
  key_location: string | null;
}

export interface ParsedCurl {
  method: string;
  url: string;
  base_url: string;
  query_params: QueryParam[];
  headers: HeaderItem[];
  body: BodyContent | null;
  auth: AuthInfo | null;
  cookies: CookieItem[];
  shell_mode: string;
}

export interface CurlGenerateRequest {
  method: string;
  url: string;
  query_params: QueryParam[];
  headers: HeaderItem[];
  body: BodyContent | null;
  auth: AuthInfo | null;
  cookies: CookieItem[];
  shell_mode: string;
  compact: boolean;
}

export interface CurlGenerateResponse {
  curl_text: string;
  shell_mode: string;
}
