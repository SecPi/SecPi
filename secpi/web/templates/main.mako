
<%
	active_tab = self.active_tab()
%>
<!DOCTYPE html>
<html ng-app="SecPi">
<head>
	<title>SecPi - ${page_title}</title>
	
	<meta name="viewport" content="width=device-width" />
	
	<link rel="stylesheet" type="text/css" href="/static/css/main.css" />
	
	<link rel="stylesheet" type="text/css" href="/static/css/bootstrap.css" />
	<link rel="stylesheet" type="text/css" href="/static/css/bootstrap-theme.min.css" />
	
	<link rel="stylesheet" type="text/css" media="only screen and (max-width: 480px), only screen and (max-device-width: 480px)" href="/static/css/mobile.css" />
	<link rel="stylesheet" type="text/css" media="only screen and (min-width: 480px) and (max-width: 640px), only screen and (min-device-width: 480px) and (max-width: 640px)" href="/static/css/mobile.css" />
	
	<script type="text/javascript" src="/static/js/jquery.min.js"></script>
	
	<script type="text/javascript" src="/static/js/angular.min.js"></script>
	<script type="text/javascript" src="/static/js/angular-animate.min.js"></script>
	
	<script type="text/javascript" src="/static/js/bootstrap.min.js"></script>
	<script type="text/javascript" src="/static/js/ui-bootstrap-tpls-1.1.2.min.js"></script>
	
	<script type="text/javascript" src="/static/js/app.js"></script>
</head>
<body>

	<div id="nav" ng-controller="NavController as navCtrl">
		<h1 class="header">SecPi</h1>
		<%include file="nav.mako" args="active_tab=active_tab"/>
		<%block name="subnav" />
	</div>
	
	<div id="main">
		${self.body()}
	</div>

	<footer>
		<a href="https://github.com/isarengineering/SecPi" target="_blank">SecPi, a software framework for building alarm systems with Linux.</a>
        <%! from secpi import __version__ %>
		Version ${__version__}.
	</footer>

	<div ng-controller="FlashController as flashCtrl" id="flash_container">
		<div class="flash_message" ng-repeat="msg in flashCtrl.messages" ng-class="msg.type" ng-show="msg.message != null" ng-attr-id="{{ 'flash-msg-' + msg.id }}" ng-mouseenter="flashCtrl.enter(msg.id)" ng-mouseleave="flashCtrl.leave(msg.id)">
			<span ng-show="msg.showpin" ng-class="msg.pinned?'pin_straight':'pin'" ng-click="flashCtrl.togglePin(msg.id)"></span>
			{{msg.message}}
		</div>
	</div>
	
</body>
</html>