<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "change_credentials" %></%def>

<div ng-controller="CredentialsController as credentialsCtrl">
	Username: <input type="text" name="username" ng-model="credentialsCtrl.username" /><br />
	Password: <input type="password" name="password" ng-model="credentialsCtrl.password" /><br />
	<input type="button" value="Change Login Credentials" ng-click="credentialsCtrl.changeCredentials()">
</div>