import urllib.parse


def addQueryString(url, params):
	return f"{url}?{urllib.parse.urlencode(params)}"

def mergePaths(baseURL, paths):

	if isinstance(paths, str):
		return f"{baseURL}/{paths}"
	else:
		return f"{baseURL}/{'/'.join(paths)}"

def quote(string):
	return urllib.parse.quote(string)
