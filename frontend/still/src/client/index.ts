export interface IRequestOptions {
  url: string;
  method?: string;
  headers?: { [key: string]: string };
  params?: { [key: string]: any };
  json?: { [key: string]: any };
  form?: FormData;
  abortSignal?: AbortSignal;
  extra?: { [key: string]: any };
}

export interface IWebsocketOptions {
  url: string;
}

export interface IApiClient {
  getToken(): string | undefined;
  setToken(token: string | undefined): void;
  getBaseURL(): string;
  setBaseURL(url: string): void;
  get(options: IRequestOptions): Promise<Response>;
  post(options: IRequestOptions): Promise<Response>;
  put(options: IRequestOptions): Promise<Response>;
  patch(options: IRequestOptions): Promise<Response>;
  delete(options: IRequestOptions): Promise<Response>;
  ws(options: IWebsocketOptions): Promise<WebSocket>;
}

export class ApiClient implements IApiClient {
  protected token: string | undefined = undefined;
  protected baseUrl: string = '';

  getToken() {
    return this.token;
  }

  setToken(token: string | undefined) {
    this.token = token;
  }

  getBaseURL() {
    return this.baseUrl;
  }

  setBaseURL(url: string) {
    this.baseUrl = url;
  }

  get(options: IRequestOptions) {
    return this.request({ ...options, method: 'GET' });
  }

  post(options: IRequestOptions) {
    return this.request({ ...options, method: 'POST' });
  }

  put(options: IRequestOptions) {
    return this.request({ ...options, method: 'PUT' });
  }

  patch(options: IRequestOptions) {
    return this.request({ ...options, method: 'PATCH' });
  }

  delete(options: IRequestOptions) {
    return this.request({ ...options, method: 'DELETE' });
  }

  ws(options: IWebsocketOptions) {
    return new Promise<WebSocket>((resolve, reject) => {
      try {
        const {url} = options;
        const baseUrl = this.getBaseURL().replace('http', 'ws');
        const params: any = {};
        const token = this.getToken();
        if (token !== undefined) {
          params['token'] = token;
        }
        const fullURL = `${baseUrl}/${url}?${new URLSearchParams(
          params
        ).toString()}`;
        const ws = new WebSocket(fullURL);
        ws.onopen = (_ev) => resolve(ws);
        ws.onerror = (ev) => reject(ev);
      } catch(e) {
        reject(e);
      }
    })
  }

  protected request(options: IRequestOptions) {
    return this.rawRequest(options);
  }

  protected rawRequest(options: IRequestOptions) {
    let { url, method, headers, params, json, form, extra, abortSignal } = options;
    if (method === undefined) method = 'GET';
    if (headers === undefined) headers = {};
    if (params === undefined) params = {};
    if (extra === undefined) extra = {};

    const baseURL = this.getBaseURL();
    const token = this.getToken();

    if (token) {
      headers = {
        ...headers,
        // Add appropriate auth header
        Authorization: `bearer ${token}`,
      };
    }

    let body: any = undefined;

    if (json) {
      if (!headers['Content-Type']) {
        headers = { ...headers, 'Content-Type': 'application/json' };
      }

      if (headers['Content-Type'] === 'application/json') {
        body = JSON.stringify(json);
      }
    } else if (form) {
      body = form;
    }

    const fullURL = `${baseURL}/${url}?${new URLSearchParams(
      params
    ).toString()}`;
    const requestParams = {
      ...extra,
      method,
      headers,
      body,
      signal: abortSignal,
    };

    return new Promise<Response>((resolve, reject) => {
      fetch(fullURL, requestParams)
        .then(res => {
          if (res.status >= 200 && res.status < 300) {
            resolve(res);
          } else {
            reject(res);
          }
        })
        .catch(reject);
    })
  }
}

interface IRequestTask {
  options: IRequestOptions;
  resolve: (response: Response) => void;
  reject: (error?: any) => void;
}

export class ThrottledApiClient extends ApiClient implements IApiClient {
  private tasks: IRequestTask[] = [];
  private runningTasksLimit = 4;
  private runningTasks = 0;

  protected request(options: IRequestOptions) {
    return new Promise<Response>((resolve, reject) => {
      this.tasks.push({
        options,
        resolve,
        reject,
      });

      this.popTask();
    });
  }

  private popTask() {
    if (this.tasks.length === 0) {
      return;
    }

    if (
      this.runningTasks >= this.runningTasksLimit &&
      this.runningTasksLimit > 0
    ) {
      return;
    }

    const [task] = this.tasks.splice(0, 1);
    this.executeTask(task);
  }

  private executeTask(task: IRequestTask) {
    this.runningTasks += 1;
    const { options, resolve, reject } = task;
    this.rawRequest(options)
      .then(resolve)
      .catch(reject);
  }
}

const apiClient: IApiClient = new ApiClient();

export { apiClient };

export const staticURL = process.env.REACT_APP_STATIC_URL || `${window.location.hostname}`;
