<%page args="flash_message='',flash_type='info'"/>
<html ng-app="SecPi">
<head>
	<title>SecPi - ${page_title}</title>
	<link rel="stylesheet" type="text/css" href="/static/css/main.css" />
	<link rel="stylesheet" type="text/css" href="/static/css/jquery-ui.min.css" />
	<script src="/static/scripts/jquery.min.js"></script>
	<script src="/static/scripts/jquery-ui.min.js"></script>
	<script type="text/javascript" src="/static/js/angular.min.js"></script>
	<script type="text/javascript" src="/static/js/app.js"></script>
</head>
<body >
	<div id="nav">
		<%include file="nav.mako" />
		<%block name="subnav" />
	</div>
	
	<div id="main">
		% if flash_message is not None and not flash_message == "":
			<div id="flash_message" class="${flash_type}">
				${flash_message}
			</div>
		% endif
		${self.body()}
	</div>
</body>
</html>