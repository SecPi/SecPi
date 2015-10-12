<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "home" %></%def>

<h1>Welcome...</h1>
... to the SecPi control interface.

<h1>Activate</h1>

<div ng-controller="ActivateController as actCtrl">
	<div ng-show="actCtrl.inactive_setups.length > 0">
		Inactive: <select name="activate_setup" id="activate_setup"
			ng-options="sup.name for sup in actCtrl.inactive_setups track by sup.id"
			ng-model="actCtrl.activate_setup"></select>
			<input type="button" ng-click="actCtrl.activate()" value="activate" />
	</div>
	<div ng-show="actCtrl.active_setups.length > 0">
		Active: <select name="deactivate_setup" id="deactivate_setup"
			ng-options="sup.name for sup in actCtrl.active_setups track by sup.id"
			ng-model="actCtrl.deactivate_setup"></select>
			<input type="button" ng-click="actCtrl.deactivate()" value="deactivate" />
	</div>
</div>

<h1>Logs</h1>
<div ng-controller="LogController as logCtrl">
	<div class="log_entry" ng-repeat="log in logCtrl.log_entries" ng-show="log.message != null" ng-class="'lvl'+log.level">
		{{log.logtime}} {{log.message}}
		<span class="log_ack"><img src="/static/img/icons/ack.png" title="acknowledge" ng-click="logCtrl.ack($index)" /></span>
	</div>
</div>