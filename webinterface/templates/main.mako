<%page args="flash_message=''"/>
<html>
<head>
	<title>SecPi - ${page_title}</title>
	<link rel="stylesheet" type="text/css" href="/static/css/main.css">
	<script type="text/javascript" src="/static/js/angular.min.js"></script>
</head>
<body>
	<div id="nav">
		<%include file="nav.mako" />
		<%block name="subnav" />
	</div>
	
	<div id="main">
		% if flash_message is not None and not flash_message == "":
			<div id="flash_message">
				${flash_message}
			</div>
		% endif
		${self.body()}
	</div>
</body>
</html>