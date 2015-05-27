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
		${self.body()}
	</div>
</body>
</html>