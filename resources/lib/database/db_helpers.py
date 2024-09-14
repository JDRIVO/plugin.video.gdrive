def joinConditions(data):
	return "WHERE " + " AND ".join([f'{k}="{v}"' if str(v)[0] != "(" else f"{k}={v}" for k, v in data.items()])

def rowsToDict(rows):

	if rows:
		return [dict(row) for row in rows]
	else:
		return []
