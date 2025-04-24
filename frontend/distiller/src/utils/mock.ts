import fetchMock from 'fetch-mock';

const createApiRegex = (url: string) => new RegExp(`^.*\/api\/v1\/${url}$`);

export const mockEndpoints = () => {
  fetchMock.mock(createApiRegex('refresh_token.*'), {
    access_token: '',
    token_type: 'bearer',
    exp: 600.0,
  });

  const scans = JSON.parse('"<<%~ scans %>>"'.slice(1, -1));

  fetchMock.mock(
    createApiRegex('scans\\?microscope_id=1&skip=0&limit=20'),
    scans,
  );

  const microscopes = JSON.parse('"<<%~ microscopes %>>"'.slice(1, -1));

  fetchMock.mock(createApiRegex('microscopes\\??'), microscopes);

  const machines = JSON.parse('"<<%~ machines %>>"'.slice(1, -1));

  fetchMock.mock(createApiRegex('machines\\??'), machines);

  const user = JSON.parse('"<<%~ user %>>"'.slice(1, -1));

  fetchMock.mock(createApiRegex('users/me\\??'), user);

  fetchMock.mock(createApiRegex('notebooks\\??'), {});

  const scanRegEx = createApiRegex('scans/(\\d+)\\??');
  fetchMock.mock(scanRegEx, (url, options) => {
    const match = url.match(scanRegEx);
    if (match) {
      const scanID = Number.parseInt(match[1]);
      return scans.find((scan: { [id: string]: number }) => scan.id === scanID);
    }
  });

  fetchMock.mock(createApiRegex('jobs\\?scan_id=\\d+'), {});
};
