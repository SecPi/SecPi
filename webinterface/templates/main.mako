<html>
<head>
	<title>${page_title}</title>
	<link rel="stylesheet" type="text/css" href="/static/css/main.css">
</head>
<body>
	<div id="nav">
		<%include file="nav.mako" />
	</div>
	
	<div id="main">
		% if flash_message is not None:
			<div id="flash_message">
				${flash_message}
			</div>
		% endif
		${self.body()}
	</div>
</body>
</html>