<%page args="flash_message='',flash_type='info'"/>
<%
	active_tab = self.active_tab()
%>
<!DOCTYPE html>
<html ng-app="SecPi">
<head>
	<title>SecPi - ${page_title}</title>
	<link rel="stylesheet" type="text/css" href="/static/css/main.css" />
	<link rel="stylesheet" type="text/css" href="/static/css/jquery-ui.min.css" />
	<link rel="stylesheet" type="text/css" href="/static/css/jquery-ui.theme.min.css" />
	<link rel="stylesheet" type="text/css" media="only screen and (max-width: 480px), only screen and (max-device-width: 480px)" href="/static/css/mobile.css" />
	<script src="/static/js/jquery.min.js"></script>
	<script src="/static/js/jquery-ui.min.js"></script>
	<script type="text/javascript" src="/static/js/angular.min.js"></script>
	<script type="text/javascript" src="/static/js/angular-animate.js"></script>
	<script type="text/javascript" src="/static/js/app.js"></script>
</head>
<body>
<div id="container">
	<div id="nav">
		<h1 class="header">SecPi</h1>
		<%include file="nav.mako" args="active_tab=active_tab"/>
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
	<footer>
		SecPi, a project by Martin Liebl and Philip W&ouml;lfel
	</footer>
</div>
<div ng-controller="FlashController as flashCtrl" id="flash_container">
	<div class="flash_message" ng-repeat="msg in flashCtrl.messages" ng-class="msg.type" ng-show="msg.message != null">
		{{msg.message}}
	</div>
</div>
</body>
</html>