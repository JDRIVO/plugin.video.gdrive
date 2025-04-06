def getTMDBSettings(folderSettings):
	tmdbSettings = {"api_key": "98d275ee6cbf27511b53b1ede8c50c67", "include_adult": "true" if folderSettings["tmdb_adult"] else "false"}

	for key, value in {"tmdb_language": "language", "tmdb_region": "region"}.items():
		tmdbSettings[value] = folderSettings[key]

	return tmdbSettings
