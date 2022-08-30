<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "test" %></%def>

<div ng-controller="TestController as testCtrl">
	Text: <input type="text" name="text" ng-model="testCtrl.msgtext" /><br />
	Zeit: <input type="number" name="time" ng-model="testCtrl.msgtime" /><br />
	<input type="button" value="show flash message" ng-click="testCtrl.showFlash()">
</div>
