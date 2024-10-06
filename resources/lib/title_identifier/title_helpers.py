def getTMDBSettings(folderSettings):
	tmdbSettings = {"api_key": "98d275ee6cbf27511b53b1ede8c50c67"}

	for key, value in {"tmdb_language": "language", "tmdb_region": "region", "tmdb_adult": "include_adult"}.items():

		if folderSettings[key]:
			tmdbSettings[value] = folderSettings[key]

	return tmdbSettings
