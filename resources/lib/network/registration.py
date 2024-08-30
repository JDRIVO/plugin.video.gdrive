form = """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta charset="UTF-8">
	<title>Registration Form</title>
	<style>
		body {
			background-color: #080808;
			margin: 0;
			font-family: Arial, sans-serif;
			color: white;
			display: flex;
			justify-content: center;
			align-items: center;
			height: 100vh;
		}

		.container {
			border: 1px solid black;
			width: 300px;
			height: 250px;
			padding: 20px;
			background-color: #0F0F0F;
			box-shadow: 5px 10px rgba(0, 0, 0, 0.5);
			border-radius: 8px;
			display: flex;
			justify-content: center;
			align-items: center;
			box-sizing: border-box;
		}

		form {
			display: flex;
			flex-direction: column;
			align-items: center;
			gap: 15px;
			width: 100%;
		}

		.input {
			width: calc(100% - 20px);
			height: 40px;
			padding: 4px;
			background-color: #080808;
			color: white;
			border: none;
			border-radius: 4px;
			box-sizing: border-box;
			text-indent: 2px;
		}

		.button {
			width: calc(100% - 20px);
			height: 40px;
			padding: 4px;
			background-color: #080808;
			color: gray;
			border: none;
			border-radius: 4px;
			cursor: pointer;
			box-sizing: border-box;
		}

		.button:hover {
			color: white;
		}
	</style>
</head>
<body>
	<main class="container">
		<form action="/register" method="post">
			<input class="input" type="text" id="account" name="account" placeholder="Account Name" required>
			<input class="input" type="text" id="client_id" name="client_id" placeholder="Client ID" required>
			<input class="input" type="text" id="client_secret" name="client_secret" placeholder="Client Secret" required>
			<input class="button" type="submit" value="Submit">
		</form>
	</main>
</body>
</html>
"""

def status(output):
	return """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta charset="UTF-8">
	<title>Registration Status</title>
	<style>
		body {
			background-color: #080808;
			margin: 0;
			font-family: Arial, sans-serif;
			color: white;
			display: flex;
			justify-content: center;
			align-items: center;
			height: 100vh;
		}

		.container {
			border: 1px solid black;
			width: 300px;
			height: 250px;
			padding: 20px;
			background-color: #0F0F0F;
			box-shadow: 5px 10px rgba(0, 0, 0, 0.5);
			border-radius: 8px;
			display: flex;
			justify-content: center;
			align-items: center;
			box-sizing: border-box;
			position: relative;
		}

		.inner-box {
			background-color: #080808;
			color: white;
			padding: 20px;
			border-radius: 8px;
			width: calc(100%% - 40px);
			box-sizing: border-box;
			position: absolute;
			top: 20px;
			bottom: 20px;
			left: 20px;
			right: 20px;
			display: flex;
			justify-content: center;
			align-items: center;
		}

		.message {
			font-size: 14px;
			text-align: center;
		}
	</style>
</head>
<body>
	<main class="container">
		<div class="inner-box">
			<p class="message">%s</p>
		</div>
	</main>
</body>
</html>
""" % (output)
