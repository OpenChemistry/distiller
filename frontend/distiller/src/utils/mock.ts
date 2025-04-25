import fetchMock from 'fetch-mock';

const createApiRegex = (url: string) => new RegExp(`^.*\/api\/v1\/${url}$`);

export const mockEndpoints = () => {
  fetchMock.mockGlobal();

  fetchMock.route(createApiRegex('refresh_token.*'), {
    access_token: '',
    token_type: 'bearer',
    exp: 600.0,
  });

  const scans = JSON.parse('"<<%~ scans %>>"'.slice(1, -1));

  fetchMock.route(
    createApiRegex('scans\\?microscope_id=1&skip=0&limit=20'),
    scans,
  );

  const microscopes = JSON.parse('"<<%~ microscopes %>>"'.slice(1, -1));

  fetchMock.route(createApiRegex('microscopes\\??'), microscopes);

  const machines = JSON.parse('"<<%~ machines %>>"'.slice(1, -1));

  fetchMock.route(createApiRegex('machines\\??'), machines);

  const user = JSON.parse('"<<%~ user %>>"'.slice(1, -1));

  fetchMock.route(createApiRegex('users/me\\??'), user);

  fetchMock.route(createApiRegex('notebooks\\??'), {});

  const scanRegEx = createApiRegex('scans/(\\d+)\\??');
  fetchMock.route(scanRegEx, (url: string, options: RequestInit) => {
    const match = url.match(scanRegEx);
    if (match) {
      const scanID = Number.parseInt(match[1]);
      return scans.find((scan: { [id: string]: number }) => scan.id === scanID);
    }
  });

  fetchMock.route(createApiRegex('jobs\\?scan_id=\\d+'), {});
};
