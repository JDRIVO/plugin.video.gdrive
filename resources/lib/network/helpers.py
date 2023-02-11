import urllib.parse


def addQueryString(url, params):
	return url + "?" + urllib.parse.urlencode(params)

def mergePaths(baseURL, paths):

	if isinstance(paths, str):
		return f'{baseURL}/{paths}'
	else:
		return f'{baseURL}/{"/".join(paths)}'
