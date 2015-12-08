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

<table width="100%">
	<tr>
		<td class="ack_table">
			<h1>Logs</h1>
			<div ng-controller="AckController as logCtrl" ackclass="log">
				<input type="button" value="stop refresh" id="refresh_toggle_log" name="refresh_toggle" ng-click="logCtrl.toggleRefresh()" />
				<div class="log_entry" ng-repeat="log in logCtrl.entries" ng-show="log.message != null" ng-class="'lvl'+log.level">
					<b>{{log.logtime | date:'dd. MMM. yyyy, HH:mm:ss'}} <i>{{log.sender}}:</i></b> {{log.message}}
					<span class="log_ack"><img src="/static/img/icons/ack.png" title="acknowledge" ng-click="logCtrl.ack($index)" /></span>
				</div>
			</div>
		</td>
		<td class="ack_table">
			<h1>Alarms</h1>
			<div ng-controller="AckController as alarmCtrl" ackclass="alarm">
				<input type="button" value="stop refresh" id="refresh_toggle_alarm" name="refresh_toggle" ng-click="alarmCtrl.toggleRefresh()" />
				<div class="alarm_entry" ng-repeat="alarm in alarmCtrl.entries" ng-show="alarm.message != null">
					<b>{{alarm.alarmtime | date:'dd. MMM. yyyy, HH:mm:ss'}} <i>{{alarm.sensor_id}}:</i></b> {{alarm.message}}
					<span class="alarm_ack"><img src="/static/img/icons/ack.png" title="acknowledge" ng-click="alarmCtrl.ack($index)" /></span>
				</div>
			</div>
		</td>
	</tr>
</table>
