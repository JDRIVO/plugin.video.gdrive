form = """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta charset="UTF-8">
	<title>Registration Form</title>
	<style>
		body {
			align-items: center;
			background-color: #080808;
			color: white;
			display: flex;
			font-family: Arial, sans-serif;
			height: 100vh;
			justify-content: center;
			margin: 0;
		}

		.container {
			align-items: center;
			background-color: #0F0F0F;
			border-radius: 8px;
			border: 1px solid black;
			box-shadow: 5px 10px rgba(0, 0, 0, 0.5);
			box-sizing: border-box;
			display: flex;
			height: 250px;
			justify-content: center;
			padding: 20px;
			width: 300px;
		}

		form {
			align-items: center;
			display: flex;
			flex-direction: column;
			gap: 15px;
			width: 100%;
		}

		.input {
			background-color: #080808;
			border-radius: 4px;
			border: none;
			box-sizing: border-box;
			color: white;
			height: 40px;
			padding: 4px;
			text-indent: 2px;
			width: calc(100% - 20px);
		}

		.input:focus {
			outline: 1px solid black;
		}

		.button {
			background-color: #080808;
			border-radius: 4px;
			border: none;
			box-sizing: border-box;
			color: gray;
			cursor: pointer;
			height: 40px;
			padding: 4px;
			width: calc(100% - 20px);
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
			align-items: center;
			background-color: #080808;
			color: white;
			display: flex;
			font-family: Arial, sans-serif;
			height: 100vh;
			justify-content: center;
			margin: 0;
		}

		.container {
			align-items: center;
			background-color: #0F0F0F;
			border-radius: 8px;
			border: 1px solid black;
			box-shadow: 5px 10px rgba(0, 0, 0, 0.5);
			box-sizing: border-box;
			display: flex;
			height: 250px;
			justify-content: center;
			padding: 20px;
			position: relative;
			width: 300px;
		}

		.inner-box {
			align-items: center;
			background-color: #080808;
			border-radius: 8px;
			bottom: 20px;
			box-sizing: border-box;
			color: white;
			display: flex;
			justify-content: center;
			left: 20px;
			padding: 20px;
			position: absolute;
			right: 20px;
			top: 20px;
			width: calc(100%% - 40px);
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
